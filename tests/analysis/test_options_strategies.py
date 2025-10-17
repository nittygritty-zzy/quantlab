"""
Tests for Options Strategies Module

Tests all strategy types, P&L calculations, risk metrics, and edge cases.
"""

import pytest
from datetime import date, timedelta
from quantlab.analysis.options_strategies import (
    OptionLeg, OptionsStrategy, StrategyBuilder,
    OptionType, PositionType, StrategyType
)


class TestOptionLeg:
    """Test OptionLeg class"""

    def test_long_call_pnl(self):
        """Test P&L calculation for long call"""
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1
        )

        # Stock below strike - lose premium
        assert leg.pnl_at_price(95.0) == -500.0

        # Stock at strike - lose premium
        assert leg.pnl_at_price(100.0) == -500.0

        # Stock at breakeven
        assert leg.pnl_at_price(105.0) == 0.0

        # Stock above breakeven - profit
        assert leg.pnl_at_price(110.0) == 500.0

    def test_short_put_pnl(self):
        """Test P&L calculation for short put"""
        leg = OptionLeg(
            option_type=OptionType.PUT,
            position_type=PositionType.SHORT,
            strike=100.0,
            premium=3.0,
            quantity=1
        )

        # Stock below strike - lose
        assert leg.pnl_at_price(90.0) == -700.0  # received 300, pay 1000

        # Stock at strike - keep premium
        assert leg.pnl_at_price(100.0) == 300.0

        # Stock above strike - keep premium
        assert leg.pnl_at_price(110.0) == 300.0

    def test_multiple_contracts(self):
        """Test P&L with multiple contracts"""
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=3
        )

        # 3x the loss
        assert leg.pnl_at_price(95.0) == -1500.0

        # 3x the profit
        assert leg.pnl_at_price(110.0) == 1500.0


class TestOptionsStrategy:
    """Test OptionsStrategy class"""

    def test_net_premium_debit(self):
        """Test net premium calculation for debit spread"""
        legs = [
            OptionLeg(OptionType.CALL, PositionType.LONG, 100.0, 7.0, 1),
            OptionLeg(OptionType.CALL, PositionType.SHORT, 105.0, 4.0, 1),
        ]
        strategy = OptionsStrategy(
            name="Bull Call Spread",
            strategy_type=StrategyType.BULL_CALL_SPREAD,
            legs=legs,
            current_stock_price=102.0,
            stock_position=0
        )

        # Net debit = 700 - 400 = -300 (paid 300)
        assert strategy.net_premium() == -300.0

    def test_net_premium_credit(self):
        """Test net premium calculation for credit spread"""
        legs = [
            OptionLeg(OptionType.PUT, PositionType.LONG, 95.0, 2.0, 1),
            OptionLeg(OptionType.PUT, PositionType.SHORT, 100.0, 5.0, 1),
        ]
        strategy = OptionsStrategy(
            name="Bull Put Spread",
            strategy_type=StrategyType.BULL_PUT_SPREAD,
            legs=legs,
            current_stock_price=102.0,
            stock_position=0
        )

        # Net credit = 500 - 200 = 300 (received 300)
        assert strategy.net_premium() == 300.0

    def test_pnl_at_price_simple(self):
        """Test P&L calculation at different stock prices"""
        leg = OptionLeg(OptionType.CALL, PositionType.LONG, 100.0, 5.0, 1)
        strategy = OptionsStrategy(
            name="Long Call",
            strategy_type=StrategyType.LONG_CALL,
            legs=[leg],
            current_stock_price=95.0,
            stock_position=0
        )

        # Below strike
        assert strategy.pnl_at_price(95.0) == -500.0

        # At strike
        assert strategy.pnl_at_price(100.0) == -500.0

        # Breakeven
        assert strategy.pnl_at_price(105.0) == 0.0

        # Profit
        assert strategy.pnl_at_price(110.0) == 500.0

    def test_pnl_with_stock_position(self):
        """Test P&L calculation with stock position (covered call)"""
        leg = OptionLeg(OptionType.CALL, PositionType.SHORT, 105.0, 3.0, 1)
        strategy = OptionsStrategy(
            name="Covered Call",
            strategy_type=StrategyType.COVERED_CALL,
            legs=[leg],
            current_stock_price=100.0,
            stock_position=100
        )

        # Stock at 95: lose 500 on stock, gain 300 on option = -200
        assert strategy.pnl_at_price(95.0) == -200.0

        # Stock at 100: no change on stock, gain 300 on option = 300
        assert strategy.pnl_at_price(100.0) == 300.0

        # Stock at 110: gain 1000 on stock, lose 200 on option = 800
        assert strategy.pnl_at_price(110.0) == 800.0

    def test_breakeven_single_leg(self):
        """Test breakeven calculation for single-leg strategy"""
        leg = OptionLeg(OptionType.CALL, PositionType.LONG, 100.0, 5.0, 1)
        strategy = OptionsStrategy(
            name="Long Call",
            strategy_type=StrategyType.LONG_CALL,
            legs=[leg],
            current_stock_price=95.0,
            stock_position=0
        )

        breakevens = strategy.breakeven_points()
        assert len(breakevens) == 1
        assert abs(breakevens[0] - 105.0) < 0.1  # Allow small tolerance

    def test_payoff_diagram_generation(self):
        """Test payoff diagram data generation"""
        leg = OptionLeg(OptionType.CALL, PositionType.LONG, 100.0, 5.0, 1)
        strategy = OptionsStrategy(
            name="Long Call",
            strategy_type=StrategyType.LONG_CALL,
            legs=[leg],
            current_stock_price=100.0,
            stock_position=0
        )

        prices, pnls = strategy.payoff_diagram()

        # Should generate arrays
        assert len(prices) == len(pnls) == 100  # default num_points

        # Prices should be in range (50% to 150% of current)
        assert prices[0] == 50.0
        assert prices[-1] == 150.0

        # P&L should increase as price increases (long call)
        assert pnls[-1] > pnls[0]


class TestStrategyBuilder:
    """Test StrategyBuilder for all strategy types"""

    def test_long_call(self):
        """Test long call builder"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.long_call(
            stock_price=100.0,
            strike=105.0,
            premium=3.0,
            quantity=2,
            expiration=expiration,
            ticker="TEST"
        )

        assert strategy.name == "Long Call on TEST"
        assert strategy.strategy_type == StrategyType.LONG_CALL
        assert len(strategy.legs) == 1
        assert strategy.legs[0].option_type == OptionType.CALL
        assert strategy.legs[0].position_type == PositionType.LONG
        assert strategy.legs[0].strike == 105.0
        assert strategy.legs[0].quantity == 2

    def test_covered_call(self):
        """Test covered call builder"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.covered_call(
            stock_price=100.0,
            shares=200,
            call_strike=105.0,
            call_premium=3.0,
            expiration=expiration,
            ticker="TEST"
        )

        assert strategy.strategy_type == StrategyType.COVERED_CALL
        assert strategy.stock_position == 200
        assert len(strategy.legs) == 1
        assert strategy.legs[0].option_type == OptionType.CALL
        assert strategy.legs[0].position_type == PositionType.SHORT
        assert strategy.legs[0].quantity == 2  # 200 shares / 100

    def test_bull_call_spread(self):
        """Test bull call spread builder"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.bull_call_spread(
            stock_price=100.0,
            long_strike=95.0,
            short_strike=105.0,
            long_premium=8.0,
            short_premium=3.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        assert strategy.strategy_type == StrategyType.BULL_CALL_SPREAD
        assert len(strategy.legs) == 2

        # First leg: long lower strike
        assert strategy.legs[0].option_type == OptionType.CALL
        assert strategy.legs[0].position_type == PositionType.LONG
        assert strategy.legs[0].strike == 95.0

        # Second leg: short higher strike
        assert strategy.legs[1].option_type == OptionType.CALL
        assert strategy.legs[1].position_type == PositionType.SHORT
        assert strategy.legs[1].strike == 105.0

        # Net debit = 800 - 300 = 500
        assert strategy.net_premium() == -500.0

    def test_iron_condor(self):
        """Test iron condor builder"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.iron_condor(
            stock_price=100.0,
            put_long_strike=90.0,
            put_short_strike=95.0,
            call_short_strike=105.0,
            call_long_strike=110.0,
            put_long_premium=1.0,
            put_short_premium=2.5,
            call_short_premium=2.5,
            call_long_premium=1.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        assert strategy.strategy_type == StrategyType.IRON_CONDOR
        assert len(strategy.legs) == 4

        # Should be a credit spread (net credit)
        assert strategy.net_premium() > 0

        # Net credit = (2.5 - 1.0 + 2.5 - 1.0) * 100 = 300
        assert strategy.net_premium() == 300.0

    def test_butterfly(self):
        """Test butterfly builder"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.butterfly(
            stock_price=100.0,
            lower_strike=95.0,
            middle_strike=100.0,
            upper_strike=105.0,
            lower_premium=7.0,
            middle_premium=3.0,
            upper_premium=1.0,
            quantity=1,
            expiration=expiration,
            option_type="call",
            ticker="TEST"
        )

        assert strategy.strategy_type == StrategyType.BUTTERFLY
        assert len(strategy.legs) == 3

        # Lower: long 1
        assert strategy.legs[0].quantity == 1
        assert strategy.legs[0].position_type == PositionType.LONG

        # Middle: short 2
        assert strategy.legs[1].quantity == 2
        assert strategy.legs[1].position_type == PositionType.SHORT

        # Upper: long 1
        assert strategy.legs[2].quantity == 1
        assert strategy.legs[2].position_type == PositionType.LONG

    def test_straddle_long(self):
        """Test long straddle builder"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.straddle(
            stock_price=100.0,
            strike=100.0,
            call_premium=5.0,
            put_premium=5.0,
            quantity=1,
            expiration=expiration,
            position="long",
            ticker="TEST"
        )

        assert strategy.strategy_type == StrategyType.STRADDLE
        assert len(strategy.legs) == 2

        # Both legs should be long
        assert all(leg.position_type == PositionType.LONG for leg in strategy.legs)

        # Should be a debit
        assert strategy.net_premium() < 0

        # Net debit = -(5 + 5) * 100 = -1000
        assert strategy.net_premium() == -1000.0

    def test_strangle_short(self):
        """Test short strangle builder"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.strangle(
            stock_price=100.0,
            put_strike=95.0,
            call_strike=105.0,
            put_premium=3.0,
            call_premium=3.0,
            quantity=1,
            expiration=expiration,
            position="short",
            ticker="TEST"
        )

        assert strategy.strategy_type == StrategyType.STRANGLE
        assert len(strategy.legs) == 2

        # Both legs should be short
        assert all(leg.position_type == PositionType.SHORT for leg in strategy.legs)

        # Should be a credit
        assert strategy.net_premium() > 0

        # Net credit = (3 + 3) * 100 = 600
        assert strategy.net_premium() == 600.0

    def test_calendar_spread(self):
        """Test calendar spread builder"""
        near_exp = date.today() + timedelta(days=30)
        far_exp = date.today() + timedelta(days=60)
        strategy = StrategyBuilder.calendar_spread(
            stock_price=100.0,
            strike=100.0,
            near_premium=3.0,
            far_premium=5.0,
            near_expiration=near_exp,
            far_expiration=far_exp,
            quantity=1,
            option_type="call",
            ticker="TEST"
        )

        assert strategy.strategy_type == StrategyType.CALENDAR_SPREAD
        assert len(strategy.legs) == 2

        # Near: short
        assert strategy.legs[0].position_type == PositionType.SHORT
        assert strategy.legs[0].expiration == near_exp

        # Far: long
        assert strategy.legs[1].position_type == PositionType.LONG
        assert strategy.legs[1].expiration == far_exp

        # Should be a debit (buy far, sell near)
        assert strategy.net_premium() < 0


class TestRiskMetrics:
    """Test risk metrics calculations"""

    def test_max_profit_bull_call_spread(self):
        """Test max profit calculation for bull call spread"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.bull_call_spread(
            stock_price=100.0,
            long_strike=95.0,
            short_strike=105.0,
            long_premium=8.0,
            short_premium=3.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        # Max profit = spread width - net debit = (105-95)*100 - 500 = 500
        assert strategy.max_profit() == 500.0

    def test_max_loss_bull_call_spread(self):
        """Test max loss calculation for bull call spread"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.bull_call_spread(
            stock_price=100.0,
            long_strike=95.0,
            short_strike=105.0,
            long_premium=8.0,
            short_premium=3.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        # Max loss = net debit = -500
        assert strategy.max_loss() == -500.0

    def test_max_profit_iron_condor(self):
        """Test max profit for iron condor"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.iron_condor(
            stock_price=100.0,
            put_long_strike=90.0,
            put_short_strike=95.0,
            call_short_strike=105.0,
            call_long_strike=110.0,
            put_long_premium=1.0,
            put_short_premium=2.5,
            call_short_premium=2.5,
            call_long_premium=1.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        # Max profit = net credit = 300
        assert strategy.max_profit() == 300.0

    def test_risk_metrics_structure(self):
        """Test risk metrics returns complete structure"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.long_call(
            stock_price=100.0,
            strike=105.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        metrics = strategy.risk_metrics()

        # Check all required fields
        assert "max_profit" in metrics
        assert "max_loss" in metrics
        assert "net_premium" in metrics
        assert "breakeven_points" in metrics
        assert "risk_reward_ratio" in metrics
        assert "probability_of_profit" in metrics
        assert "current_pnl" in metrics
        assert "debit_credit" in metrics

        # Long call should be debit
        assert metrics["debit_credit"] == "Debit"

    def test_to_dict_serialization(self):
        """Test strategy serialization to dict"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.long_call(
            stock_price=100.0,
            strike=105.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        data = strategy.to_dict()

        # Check structure
        assert "name" in data
        assert "strategy_type" in data
        assert "current_stock_price" in data
        assert "stock_position" in data
        assert "legs" in data
        assert "risk_metrics" in data
        assert "metadata" in data

        # Check leg serialization
        assert len(data["legs"]) == 1
        assert "option_type" in data["legs"][0]
        assert "position_type" in data["legs"][0]
        assert "strike" in data["legs"][0]


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_zero_premium(self):
        """Test strategy with zero premium (edge case)"""
        leg = OptionLeg(OptionType.CALL, PositionType.LONG, 100.0, 0.0, 1)
        strategy = OptionsStrategy(
            name="Zero Premium Call",
            strategy_type=StrategyType.LONG_CALL,
            legs=[leg],
            current_stock_price=100.0,
            stock_position=0
        )

        # Breakeven should be at strike
        assert strategy.pnl_at_price(100.0) == 0.0

    def test_deep_itm_call(self):
        """Test deeply in-the-money call"""
        leg = OptionLeg(OptionType.CALL, PositionType.LONG, 50.0, 45.0, 1)
        strategy = OptionsStrategy(
            name="Deep ITM Call",
            strategy_type=StrategyType.LONG_CALL,
            legs=[leg],
            current_stock_price=100.0,
            stock_position=0
        )

        # Should have profit when stock moves up
        assert strategy.pnl_at_price(100.0) == 500.0  # (100-50-45)*100

    def test_far_otm_put(self):
        """Test far out-of-the-money put"""
        leg = OptionLeg(OptionType.PUT, PositionType.LONG, 50.0, 1.0, 1)
        strategy = OptionsStrategy(
            name="Far OTM Put",
            strategy_type=StrategyType.LONG_PUT,
            legs=[leg],
            current_stock_price=100.0,
            stock_position=0
        )

        # Worthless when stock is high
        assert strategy.pnl_at_price(100.0) == -100.0  # Lose premium
