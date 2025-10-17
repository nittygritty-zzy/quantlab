"""
Options Trading Strategies Module

Implements common options strategies with profit/loss calculations,
risk analysis, and breakeven points.

Supported Strategies:
- Single-leg: Covered Call, Protective Put, Cash-Secured Put
- Vertical Spreads: Bull Call/Put, Bear Call/Put
- Horizontal: Calendar Spread
- Advanced: Iron Condor, Butterfly, Straddle, Strangle
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np
from datetime import date, datetime

from ..models.ticker_data import OptionContract
from ..utils.logger import setup_logger
from ..analysis.greeks_calculator import calculate_advanced_greeks

logger = setup_logger(__name__)


class OptionType(Enum):
    """Option type"""
    CALL = "call"
    PUT = "put"


class PositionType(Enum):
    """Position type (long or short)"""
    LONG = "long"
    SHORT = "short"


class StrategyType(Enum):
    """Options strategy types"""
    # Single-leg strategies
    COVERED_CALL = "covered_call"
    PROTECTIVE_PUT = "protective_put"
    CASH_SECURED_PUT = "cash_secured_put"
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"

    # Vertical spreads
    BULL_CALL_SPREAD = "bull_call_spread"
    BULL_PUT_SPREAD = "bull_put_spread"
    BEAR_CALL_SPREAD = "bear_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"

    # Horizontal spreads
    CALENDAR_SPREAD = "calendar_spread"

    # Advanced strategies
    IRON_CONDOR = "iron_condor"
    BUTTERFLY = "butterfly"
    STRADDLE = "straddle"
    STRANGLE = "strangle"


@dataclass
class OptionLeg:
    """Single option leg in a strategy"""
    option_type: OptionType
    position_type: PositionType  # long or short
    strike: float
    premium: float  # Price paid/received
    quantity: int = 1
    expiration: Optional[date] = None

    # For advanced Greeks calculation
    implied_volatility: Optional[float] = None  # As decimal (e.g., 0.35 for 35%)
    risk_free_rate: float = 0.05  # Default 5%

    def pnl_at_price(self, stock_price: float) -> float:
        """Calculate P&L for this leg at a given stock price"""
        if self.option_type == OptionType.CALL:
            intrinsic_value = max(0, stock_price - self.strike)
        else:  # PUT
            intrinsic_value = max(0, self.strike - stock_price)

        if self.position_type == PositionType.LONG:
            # Long: paid premium, receive intrinsic value
            pnl = (intrinsic_value - self.premium) * 100 * self.quantity
        else:  # SHORT
            # Short: received premium, pay intrinsic value
            pnl = (self.premium - intrinsic_value) * 100 * self.quantity

        return pnl

    def calculate_advanced_greeks(self, stock_price: float) -> Dict[str, float]:
        """
        Calculate advanced Greeks using existing calculator

        Requires implied_volatility and expiration to be set.
        Returns dictionary with delta, gamma, vega, theta, vanna, charm, vomma.
        """
        if not self.implied_volatility or not self.expiration:
            logger.debug("Cannot calculate advanced Greeks without IV and expiration")
            return {}

        days_to_expiry = (self.expiration - date.today()).days
        if days_to_expiry <= 0:
            logger.debug("Option expired, cannot calculate Greeks")
            return {}

        # Calculate Greeks using existing calculator
        greeks = calculate_advanced_greeks(
            stock_price=stock_price,
            strike_price=self.strike,
            days_to_expiry=days_to_expiry,
            risk_free_rate=self.risk_free_rate,
            implied_volatility=self.implied_volatility,
            option_type=self.option_type.value
        )

        # Adjust for position type (short reverses signs)
        multiplier = -1 if self.position_type == PositionType.SHORT else 1

        # Adjust for quantity
        adjusted_greeks = {
            k: v * multiplier * self.quantity
            for k, v in greeks.items()
        }

        return adjusted_greeks


@dataclass
class OptionsStrategy:
    """
    Complete options strategy with multiple legs

    Attributes:
        name: Strategy name
        strategy_type: Type of strategy
        legs: List of option legs
        stock_position: Shares of underlying stock (positive=long, negative=short)
        current_stock_price: Current price of underlying
        target_date: Target date for P&L calculation (default: expiration)
    """
    name: str
    strategy_type: StrategyType
    legs: List[OptionLeg]
    current_stock_price: float
    stock_position: int = 0  # Number of shares
    target_date: Optional[date] = None
    metadata: Dict = field(default_factory=dict)

    def net_premium(self) -> float:
        """Calculate net premium (positive = credit, negative = debit)"""
        premium = 0
        for leg in self.legs:
            if leg.position_type == PositionType.LONG:
                premium -= leg.premium * 100 * leg.quantity
            else:  # SHORT
                premium += leg.premium * 100 * leg.quantity
        return premium

    def max_profit(self) -> float:
        """Calculate maximum profit potential"""
        if self.strategy_type == StrategyType.COVERED_CALL:
            # Max profit: stock gains + premium received
            strike = self.legs[0].strike
            stock_gain = (strike - self.current_stock_price) * self.stock_position
            return stock_gain + self.net_premium()

        elif self.strategy_type in [StrategyType.BULL_CALL_SPREAD, StrategyType.BEAR_PUT_SPREAD]:
            # Max profit: spread width - net debit
            strikes = sorted([leg.strike for leg in self.legs])
            spread_width = (strikes[1] - strikes[0]) * 100
            return spread_width - abs(self.net_premium())

        elif self.strategy_type in [StrategyType.BEAR_CALL_SPREAD, StrategyType.BULL_PUT_SPREAD]:
            # Max profit: net credit received
            return self.net_premium()

        elif self.strategy_type == StrategyType.IRON_CONDOR:
            # Max profit: net credit received
            return self.net_premium()

        else:
            # For undefined strategies, calculate at extreme prices
            max_pnl = float('-inf')
            for price in np.linspace(0, self.current_stock_price * 3, 1000):
                pnl = self.pnl_at_price(price)
                max_pnl = max(max_pnl, pnl)
            return max_pnl if max_pnl > float('-inf') else None

    def max_loss(self) -> float:
        """Calculate maximum loss potential"""
        if self.strategy_type == StrategyType.COVERED_CALL:
            # Max loss: stock goes to zero minus premium received
            stock_loss = -self.current_stock_price * self.stock_position
            return stock_loss + self.net_premium()

        elif self.strategy_type == StrategyType.PROTECTIVE_PUT:
            # Max loss: strike - current price - premium paid
            strike = self.legs[0].strike
            return (strike - self.current_stock_price) * self.stock_position + self.net_premium()

        elif self.strategy_type in [StrategyType.BULL_CALL_SPREAD, StrategyType.BEAR_PUT_SPREAD]:
            # Max loss: net debit paid
            return self.net_premium()

        elif self.strategy_type in [StrategyType.BEAR_CALL_SPREAD, StrategyType.BULL_PUT_SPREAD]:
            # Max loss: spread width - net credit
            strikes = sorted([leg.strike for leg in self.legs])
            spread_width = (strikes[1] - strikes[0]) * 100
            return self.net_premium() - spread_width

        elif self.strategy_type == StrategyType.IRON_CONDOR:
            # Max loss: width of widest spread - net credit
            strikes = sorted([leg.strike for leg in self.legs])
            call_spread = (strikes[3] - strikes[2]) * 100
            put_spread = (strikes[1] - strikes[0]) * 100
            max_spread = max(call_spread, put_spread)
            return self.net_premium() - max_spread

        else:
            # For undefined strategies, calculate at extreme prices
            min_pnl = float('inf')
            for price in np.linspace(0, self.current_stock_price * 3, 1000):
                pnl = self.pnl_at_price(price)
                min_pnl = min(min_pnl, pnl)
            return min_pnl if min_pnl < float('inf') else None

    def breakeven_points(self) -> List[float]:
        """Calculate breakeven stock prices"""
        breakevens = []

        # Sample prices and find where P&L crosses zero
        prices = np.linspace(0, self.current_stock_price * 3, 1000)
        pnls = [self.pnl_at_price(p) for p in prices]

        for i in range(len(pnls) - 1):
            # Check for zero crossing
            if (pnls[i] <= 0 and pnls[i+1] >= 0) or (pnls[i] >= 0 and pnls[i+1] <= 0):
                # Linear interpolation to find exact breakeven
                t = -pnls[i] / (pnls[i+1] - pnls[i])
                breakeven = prices[i] + t * (prices[i+1] - prices[i])
                breakevens.append(round(breakeven, 2))

        return breakevens

    def pnl_at_price(self, stock_price: float) -> float:
        """Calculate total P&L at a given stock price"""
        total_pnl = 0

        # Add stock position P&L
        if self.stock_position != 0:
            stock_pnl = (stock_price - self.current_stock_price) * self.stock_position
            total_pnl += stock_pnl

        # Add options P&L
        for leg in self.legs:
            total_pnl += leg.pnl_at_price(stock_price)

        return total_pnl

    def payoff_diagram(self, price_range: Optional[Tuple[float, float]] = None,
                      num_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate data for payoff diagram

        Returns:
            (prices, pnls): Arrays for plotting
        """
        if price_range is None:
            # Default range: ±50% from current price
            min_price = self.current_stock_price * 0.5
            max_price = self.current_stock_price * 1.5
        else:
            min_price, max_price = price_range

        prices = np.linspace(min_price, max_price, num_points)
        pnls = np.array([self.pnl_at_price(p) for p in prices])

        return prices, pnls

    def risk_metrics(self) -> Dict:
        """Calculate risk metrics for the strategy"""
        max_p = self.max_profit()
        max_l = self.max_loss()
        breakevens = self.breakeven_points()
        net_prem = self.net_premium()

        # Calculate risk/reward ratio
        if max_l and max_l < 0:
            risk_reward = abs(max_p / max_l) if max_p else 0
        else:
            risk_reward = None

        # Calculate probability of profit (simplified)
        # This is a rough estimate based on breakeven points
        if len(breakevens) == 1:
            # Single breakeven (e.g., long call/put)
            if breakevens[0] > self.current_stock_price:
                pop = 50 * (1 - (breakevens[0] - self.current_stock_price) / self.current_stock_price)
            else:
                pop = 50 * (1 + (self.current_stock_price - breakevens[0]) / self.current_stock_price)
            pop = max(0, min(100, pop))
        elif len(breakevens) == 2:
            # Two breakevens (e.g., iron condor)
            range_width = breakevens[1] - breakevens[0]
            current_in_range = breakevens[0] <= self.current_stock_price <= breakevens[1]
            if current_in_range:
                pop = 70  # Rough estimate
            else:
                pop = 30
        else:
            pop = None

        return {
            "max_profit": max_p,
            "max_loss": max_l,
            "net_premium": net_prem,
            "breakeven_points": breakevens,
            "risk_reward_ratio": risk_reward,
            "probability_of_profit": pop,
            "current_pnl": self.pnl_at_price(self.current_stock_price),
            "debit_credit": "Credit" if net_prem > 0 else "Debit",
        }

    def advanced_greeks(self) -> Dict[str, float]:
        """
        Calculate aggregate advanced Greeks for entire strategy

        Returns dictionary with all Greeks summed across legs:
        - delta, gamma, theta, vega (first-order)
        - vanna, charm, vomma (second-order/advanced)
        """
        totals = {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'vanna': 0.0,
            'charm': 0.0,
            'vomma': 0.0
        }

        # Aggregate Greeks from all legs
        for leg in self.legs:
            leg_greeks = leg.calculate_advanced_greeks(self.current_stock_price)

            for greek in totals:
                if greek in leg_greeks:
                    totals[greek] += leg_greeks[greek]

        # Add stock position delta (100 shares = 1.0 delta)
        if self.stock_position != 0:
            totals['delta'] += self.stock_position / 100

        return totals

    def to_dict(self) -> Dict:
        """Convert strategy to dictionary for serialization"""
        data = {
            "name": self.name,
            "strategy_type": self.strategy_type.value,
            "current_stock_price": self.current_stock_price,
            "stock_position": self.stock_position,
            "legs": [
                {
                    "option_type": leg.option_type.value,
                    "position_type": leg.position_type.value,
                    "strike": leg.strike,
                    "premium": leg.premium,
                    "quantity": leg.quantity,
                    "expiration": leg.expiration.isoformat() if leg.expiration else None,
                    "implied_volatility": leg.implied_volatility,
                    "risk_free_rate": leg.risk_free_rate,
                }
                for leg in self.legs
            ],
            "risk_metrics": self.risk_metrics(),
            "metadata": self.metadata,
        }

        # Add advanced Greeks if available
        if any(leg.implied_volatility for leg in self.legs):
            data["advanced_greeks"] = self.advanced_greeks()

        return data


class StrategyBuilder:
    """Builder for common options strategies"""

    @staticmethod
    def covered_call(stock_price: float, shares: int, call_strike: float,
                     call_premium: float, expiration: date, ticker: str = "UNKNOWN",
                     implied_volatility: Optional[float] = None,
                     risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Covered Call: Own stock + Sell call

        Strategy: Generate income on existing stock position
        Max Profit: (Strike - Stock Price) + Premium
        Max Loss: Stock price - Premium
        Breakeven: Stock Price - Premium

        Args:
            implied_volatility: IV as decimal (e.g., 0.35 for 35%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.SHORT,
            strike=call_strike,
            premium=call_premium,
            quantity=shares // 100,
            expiration=expiration,
            implied_volatility=implied_volatility,
            risk_free_rate=risk_free_rate
        )

        return OptionsStrategy(
            name=f"Covered Call on {ticker}",
            strategy_type=StrategyType.COVERED_CALL,
            legs=[leg],
            stock_position=shares,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "implied_volatility": implied_volatility,
                "strategy_description": "Generate income by selling calls against stock position"
            }
        )

    @staticmethod
    def protective_put(stock_price: float, shares: int, put_strike: float,
                      put_premium: float, expiration: date, ticker: str = "UNKNOWN",
                      implied_volatility: Optional[float] = None,
                      risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Protective Put: Own stock + Buy put

        Strategy: Protect downside on stock position
        Max Profit: Unlimited (stock can rise infinitely)
        Max Loss: (Stock Price - Strike) + Premium
        Breakeven: Stock Price + Premium

        Args:
            implied_volatility: IV as decimal (e.g., 0.25 for 25%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        leg = OptionLeg(
            option_type=OptionType.PUT,
            position_type=PositionType.LONG,
            strike=put_strike,
            premium=put_premium,
            quantity=shares // 100,
            expiration=expiration,
            implied_volatility=implied_volatility,
            risk_free_rate=risk_free_rate
        )

        return OptionsStrategy(
            name=f"Protective Put on {ticker}",
            strategy_type=StrategyType.PROTECTIVE_PUT,
            legs=[leg],
            stock_position=shares,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "implied_volatility": implied_volatility,
                "strategy_description": "Protect stock position with downside insurance"
            }
        )

    @staticmethod
    def cash_secured_put(stock_price: float, put_strike: float, put_premium: float,
                         quantity: int, expiration: date, ticker: str = "UNKNOWN",
                         implied_volatility: Optional[float] = None,
                         risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Cash-Secured Put: Sell put (with cash to buy stock if assigned)

        Strategy: Generate income or acquire stock at lower price
        Max Profit: Premium received
        Max Loss: Strike - Premium (if stock goes to zero)
        Breakeven: Strike - Premium

        Args:
            implied_volatility: IV as decimal (e.g., 0.30 for 30%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        leg = OptionLeg(
            option_type=OptionType.PUT,
            position_type=PositionType.SHORT,
            strike=put_strike,
            premium=put_premium,
            quantity=quantity,
            expiration=expiration,
            implied_volatility=implied_volatility,
            risk_free_rate=risk_free_rate
        )

        return OptionsStrategy(
            name=f"Cash-Secured Put on {ticker}",
            strategy_type=StrategyType.CASH_SECURED_PUT,
            legs=[leg],
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "implied_volatility": implied_volatility,
                "cash_required": put_strike * 100 * quantity,
                "strategy_description": "Generate income or acquire stock at discount"
            }
        )

    @staticmethod
    def bull_call_spread(stock_price: float, long_strike: float, short_strike: float,
                        long_premium: float, short_premium: float, quantity: int,
                        expiration: date, ticker: str = "UNKNOWN",
                        implied_volatility: Optional[float] = None,
                        risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Bull Call Spread: Buy lower strike call + Sell higher strike call

        Strategy: Moderately bullish with limited risk
        Max Profit: (Short Strike - Long Strike) - Net Debit
        Max Loss: Net Debit
        Breakeven: Long Strike + Net Debit

        Args:
            implied_volatility: IV as decimal (e.g., 0.35 for 35%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        legs = [
            OptionLeg(OptionType.CALL, PositionType.LONG, long_strike, long_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate),
            OptionLeg(OptionType.CALL, PositionType.SHORT, short_strike, short_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate)
        ]

        return OptionsStrategy(
            name=f"Bull Call Spread on {ticker}",
            strategy_type=StrategyType.BULL_CALL_SPREAD,
            legs=legs,
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "implied_volatility": implied_volatility,
                "spread_width": short_strike - long_strike,
                "strategy_description": "Bullish strategy with capped profit and loss"
            }
        )

    @staticmethod
    def iron_condor(stock_price: float,
                    put_long_strike: float, put_short_strike: float,
                    call_short_strike: float, call_long_strike: float,
                    put_long_premium: float, put_short_premium: float,
                    call_short_premium: float, call_long_premium: float,
                    quantity: int, expiration: date, ticker: str = "UNKNOWN",
                    implied_volatility: Optional[float] = None,
                    risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Iron Condor: Sell put spread + Sell call spread

        Strategy: Profit from low volatility (stock stays in range)
        Max Profit: Net Credit
        Max Loss: Width of widest spread - Net Credit
        Breakevens: Two points (at put spread and call spread)

        Args:
            implied_volatility: IV as decimal (e.g., 0.20 for 20%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        legs = [
            OptionLeg(OptionType.PUT, PositionType.LONG, put_long_strike, put_long_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate),
            OptionLeg(OptionType.PUT, PositionType.SHORT, put_short_strike, put_short_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate),
            OptionLeg(OptionType.CALL, PositionType.SHORT, call_short_strike, call_short_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate),
            OptionLeg(OptionType.CALL, PositionType.LONG, call_long_strike, call_long_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate)
        ]

        return OptionsStrategy(
            name=f"Iron Condor on {ticker}",
            strategy_type=StrategyType.IRON_CONDOR,
            legs=legs,
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "implied_volatility": implied_volatility,
                "profit_range": (put_short_strike, call_short_strike),
                "strategy_description": "Profit from range-bound stock movement"
            }
        )

    @staticmethod
    def long_call(stock_price: float, strike: float, premium: float,
                  quantity: int, expiration: date, ticker: str = "UNKNOWN",
                  implied_volatility: Optional[float] = None,
                  risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Long Call: Buy call option

        Strategy: Bullish - profit from stock rise with limited risk
        Max Profit: Unlimited (stock can rise infinitely)
        Max Loss: Premium paid
        Breakeven: Strike + Premium

        Args:
            implied_volatility: IV as decimal (e.g., 0.35 for 35%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=strike,
            premium=premium,
            quantity=quantity,
            expiration=expiration,
            implied_volatility=implied_volatility,
            risk_free_rate=risk_free_rate
        )

        return OptionsStrategy(
            name=f"Long Call on {ticker}",
            strategy_type=StrategyType.LONG_CALL,
            legs=[leg],
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "implied_volatility": implied_volatility,
                "strategy_description": "Bullish speculation with limited risk"
            }
        )

    @staticmethod
    def long_put(stock_price: float, strike: float, premium: float,
                 quantity: int, expiration: date, ticker: str = "UNKNOWN",
                 implied_volatility: Optional[float] = None,
                 risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Long Put: Buy put option

        Strategy: Bearish - profit from stock decline with limited risk
        Max Profit: Strike - Premium (if stock goes to zero)
        Max Loss: Premium paid
        Breakeven: Strike - Premium

        Args:
            implied_volatility: IV as decimal (e.g., 0.35 for 35%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        leg = OptionLeg(
            option_type=OptionType.PUT,
            position_type=PositionType.LONG,
            strike=strike,
            premium=premium,
            quantity=quantity,
            expiration=expiration,
            implied_volatility=implied_volatility,
            risk_free_rate=risk_free_rate
        )

        return OptionsStrategy(
            name=f"Long Put on {ticker}",
            strategy_type=StrategyType.LONG_PUT,
            legs=[leg],
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "implied_volatility": implied_volatility,
                "strategy_description": "Bearish speculation with limited risk"
            }
        )

    @staticmethod
    def bull_put_spread(stock_price: float, long_strike: float, short_strike: float,
                       long_premium: float, short_premium: float, quantity: int,
                       expiration: date, ticker: str = "UNKNOWN",
                       implied_volatility: Optional[float] = None,
                       risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Bull Put Spread: Buy lower strike put + Sell higher strike put

        Strategy: Moderately bullish with limited risk (credit spread)
        Max Profit: Net Credit
        Max Loss: (Short Strike - Long Strike) - Net Credit
        Breakeven: Short Strike - Net Credit

        Args:
            implied_volatility: IV as decimal (e.g., 0.25 for 25%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        legs = [
            OptionLeg(OptionType.PUT, PositionType.LONG, long_strike, long_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate),
            OptionLeg(OptionType.PUT, PositionType.SHORT, short_strike, short_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate)
        ]

        return OptionsStrategy(
            name=f"Bull Put Spread on {ticker}",
            strategy_type=StrategyType.BULL_PUT_SPREAD,
            legs=legs,
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "implied_volatility": implied_volatility,
                "spread_width": short_strike - long_strike,
                "strategy_description": "Bullish credit spread with capped profit and loss"
            }
        )

    @staticmethod
    def bear_call_spread(stock_price: float, long_strike: float, short_strike: float,
                        long_premium: float, short_premium: float, quantity: int,
                        expiration: date, ticker: str = "UNKNOWN",
                        implied_volatility: Optional[float] = None,
                        risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Bear Call Spread: Sell lower strike call + Buy higher strike call

        Strategy: Moderately bearish with limited risk (credit spread)
        Max Profit: Net Credit
        Max Loss: (Long Strike - Short Strike) - Net Credit
        Breakeven: Short Strike + Net Credit

        Args:
            implied_volatility: IV as decimal (e.g., 0.25 for 25%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        legs = [
            OptionLeg(OptionType.CALL, PositionType.SHORT, short_strike, short_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate),
            OptionLeg(OptionType.CALL, PositionType.LONG, long_strike, long_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate)
        ]

        return OptionsStrategy(
            name=f"Bear Call Spread on {ticker}",
            strategy_type=StrategyType.BEAR_CALL_SPREAD,
            legs=legs,
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "implied_volatility": implied_volatility,
                "spread_width": long_strike - short_strike,
                "strategy_description": "Bearish credit spread with capped profit and loss"
            }
        )

    @staticmethod
    def bear_put_spread(stock_price: float, long_strike: float, short_strike: float,
                       long_premium: float, short_premium: float, quantity: int,
                       expiration: date, ticker: str = "UNKNOWN",
                       implied_volatility: Optional[float] = None,
                       risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Bear Put Spread: Buy higher strike put + Sell lower strike put

        Strategy: Moderately bearish with limited risk (debit spread)
        Max Profit: (Long Strike - Short Strike) - Net Debit
        Max Loss: Net Debit
        Breakeven: Long Strike - Net Debit

        Args:
            implied_volatility: IV as decimal (e.g., 0.30 for 30%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        legs = [
            OptionLeg(OptionType.PUT, PositionType.LONG, long_strike, long_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate),
            OptionLeg(OptionType.PUT, PositionType.SHORT, short_strike, short_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate)
        ]

        return OptionsStrategy(
            name=f"Bear Put Spread on {ticker}",
            strategy_type=StrategyType.BEAR_PUT_SPREAD,
            legs=legs,
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "implied_volatility": implied_volatility,
                "spread_width": long_strike - short_strike,
                "strategy_description": "Bearish debit spread with capped profit and loss"
            }
        )

    @staticmethod
    def butterfly(stock_price: float, lower_strike: float, middle_strike: float, upper_strike: float,
                  lower_premium: float, middle_premium: float, upper_premium: float,
                  quantity: int, expiration: date, option_type: str = "call",
                  ticker: str = "UNKNOWN",
                  implied_volatility: Optional[float] = None,
                  risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Butterfly Spread: Buy 1 low strike + Sell 2 middle strikes + Buy 1 high strike

        Strategy: Profit from low volatility (stock stays near middle strike)
        Max Profit: (Middle Strike - Lower Strike) - Net Debit
        Max Loss: Net Debit
        Breakevens: Two points around middle strike

        Args:
            implied_volatility: IV as decimal (e.g., 0.25 for 25%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        opt_type = OptionType.CALL if option_type.lower() == "call" else OptionType.PUT

        legs = [
            OptionLeg(opt_type, PositionType.LONG, lower_strike, lower_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate),
            OptionLeg(opt_type, PositionType.SHORT, middle_strike, middle_premium, quantity * 2, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate),
            OptionLeg(opt_type, PositionType.LONG, upper_strike, upper_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate)
        ]

        return OptionsStrategy(
            name=f"{option_type.capitalize()} Butterfly on {ticker}",
            strategy_type=StrategyType.BUTTERFLY,
            legs=legs,
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "implied_volatility": implied_volatility,
                "target_price": middle_strike,
                "strategy_description": "Profit from low volatility around middle strike"
            }
        )

    @staticmethod
    def straddle(stock_price: float, strike: float, call_premium: float, put_premium: float,
                 quantity: int, expiration: date, position: str = "long",
                 ticker: str = "UNKNOWN",
                 implied_volatility: Optional[float] = None,
                 risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Straddle: Buy/Sell both call and put at same strike

        Long Straddle: Profit from high volatility (big move in either direction)
        Short Straddle: Profit from low volatility (stock stays near strike)

        Long Straddle:
          Max Profit: Unlimited
          Max Loss: Total premium paid
          Breakevens: Strike ± Total Premium

        Short Straddle:
          Max Profit: Total premium received
          Max Loss: Unlimited
          Breakevens: Strike ± Total Premium

        Args:
            implied_volatility: IV as decimal (e.g., 0.30 for 30%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        pos_type = PositionType.LONG if position.lower() == "long" else PositionType.SHORT

        legs = [
            OptionLeg(OptionType.CALL, pos_type, strike, call_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate),
            OptionLeg(OptionType.PUT, pos_type, strike, put_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate)
        ]

        return OptionsStrategy(
            name=f"{position.capitalize()} Straddle on {ticker}",
            strategy_type=StrategyType.STRADDLE,
            legs=legs,
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "position": position,
                "implied_volatility": implied_volatility,
                "strategy_description": f"{position.capitalize()} volatility play"
            }
        )

    @staticmethod
    def strangle(stock_price: float, put_strike: float, call_strike: float,
                 put_premium: float, call_premium: float, quantity: int,
                 expiration: date, position: str = "long",
                 ticker: str = "UNKNOWN",
                 implied_volatility: Optional[float] = None,
                 risk_free_rate: float = 0.05) -> OptionsStrategy:
        """
        Strangle: Buy/Sell call and put at different strikes

        Long Strangle: Profit from high volatility (cheaper than straddle)
        Short Strangle: Profit from low volatility (higher risk than short straddle)

        Long Strangle:
          Max Profit: Unlimited
          Max Loss: Total premium paid
          Breakevens: Put Strike - Premium, Call Strike + Premium

        Short Strangle:
          Max Profit: Total premium received
          Max Loss: Unlimited
          Breakevens: Put Strike - Premium, Call Strike + Premium

        Args:
            implied_volatility: IV as decimal (e.g., 0.30 for 30%) - optional for Greeks
            risk_free_rate: Risk-free rate as decimal (default: 0.05)
        """
        pos_type = PositionType.LONG if position.lower() == "long" else PositionType.SHORT

        legs = [
            OptionLeg(OptionType.PUT, pos_type, put_strike, put_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate),
            OptionLeg(OptionType.CALL, pos_type, call_strike, call_premium, quantity, expiration,
                     implied_volatility=implied_volatility, risk_free_rate=risk_free_rate)
        ]

        return OptionsStrategy(
            name=f"{position.capitalize()} Strangle on {ticker}",
            strategy_type=StrategyType.STRANGLE,
            legs=legs,
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "position": position,
                "implied_volatility": implied_volatility,
                "strike_range": (put_strike, call_strike),
                "strategy_description": f"{position.capitalize()} volatility play with OTM options"
            }
        )

    @staticmethod
    def calendar_spread(stock_price: float, strike: float,
                       near_premium: float, far_premium: float,
                       near_expiration: date, far_expiration: date,
                       quantity: int, option_type: str = "call",
                       ticker: str = "UNKNOWN") -> OptionsStrategy:
        """
        Calendar Spread (Time Spread): Sell near-term + Buy far-term at same strike

        Strategy: Profit from time decay difference and volatility
        Max Profit: Varies (depends on volatility changes)
        Max Loss: Net Debit
        Best Case: Stock stays near strike at near expiration
        """
        opt_type = OptionType.CALL if option_type.lower() == "call" else OptionType.PUT

        legs = [
            OptionLeg(opt_type, PositionType.SHORT, strike, near_premium, quantity, near_expiration),
            OptionLeg(opt_type, PositionType.LONG, strike, far_premium, quantity, far_expiration)
        ]

        return OptionsStrategy(
            name=f"{option_type.capitalize()} Calendar Spread on {ticker}",
            strategy_type=StrategyType.CALENDAR_SPREAD,
            legs=legs,
            stock_position=0,
            current_stock_price=stock_price,
            metadata={
                "ticker": ticker,
                "target_price": strike,
                "time_spread_days": (far_expiration - near_expiration).days,
                "strategy_description": "Profit from time decay and volatility changes"
            }
        )
