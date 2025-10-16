"""
Options Chain Analyzer

Analyzes options chains with:
- ITM call/put recommendations
- Advanced Greeks analysis
- Risk metrics
- Liquidity analysis
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..data.data_manager import DataManager

from ..models.ticker_data import OptionContract
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class OptionsAnalyzer:
    """
    Analyze options chains and provide recommendations

    Features:
    - ITM call/put analysis
    - Greeks-based ranking
    - Liquidity scoring
    - Risk assessment
    """

    def __init__(self, data_manager: "DataManager"):
        """
        Initialize options analyzer

        Args:
            data_manager: Data manager instance
        """
        self.data = data_manager

    def analyze_itm_calls(
        self,
        ticker: str,
        min_itm_pct: float = 5.0,
        max_itm_pct: float = 20.0,
        min_open_interest: int = 100,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Analyze ITM call options and provide recommendations

        Args:
            ticker: Stock ticker symbol
            min_itm_pct: Minimum ITM percentage (default: 5%)
            max_itm_pct: Maximum ITM percentage (default: 20%)
            min_open_interest: Minimum open interest for liquidity
            top_n: Number of top recommendations

        Returns:
            List of recommended call options with analysis
        """
        try:
            # Get options chain
            options = self.data.get_options_chain(
                ticker=ticker,
                option_type="call",
                min_itm_pct=min_itm_pct,
                max_itm_pct=max_itm_pct
            )

            if not options:
                logger.warning(f"No ITM calls found for {ticker}")
                return []

            # Filter by liquidity
            liquid_options = [
                opt for opt in options
                if opt.open_interest and opt.open_interest >= min_open_interest
            ]

            if not liquid_options:
                logger.warning(f"No liquid ITM calls found (min OI: {min_open_interest})")
                liquid_options = options  # Fall back to all options

            # Score and rank options
            scored_options = []
            for opt in liquid_options:
                score = self._score_call_option(opt)
                scored_options.append({
                    "contract": opt,
                    "score": score,
                    "analysis": self._analyze_option(opt)
                })

            # Sort by score (descending)
            scored_options.sort(key=lambda x: x["score"], reverse=True)

            # Return top N
            recommendations = scored_options[:top_n]

            logger.info(f"✓ Analyzed {len(options)} ITM calls, returning top {len(recommendations)}")

            return recommendations

        except Exception as e:
            logger.error(f"Failed to analyze ITM calls for {ticker}: {e}")
            return []

    def analyze_itm_puts(
        self,
        ticker: str,
        min_itm_pct: float = 5.0,
        max_itm_pct: float = 20.0,
        min_open_interest: int = 100,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Analyze ITM put options and provide recommendations

        Args:
            ticker: Stock ticker symbol
            min_itm_pct: Minimum ITM percentage (default: 5%)
            max_itm_pct: Maximum ITM percentage (default: 20%)
            min_open_interest: Minimum open interest for liquidity
            top_n: Number of top recommendations

        Returns:
            List of recommended put options with analysis
        """
        try:
            # Get options chain
            options = self.data.get_options_chain(
                ticker=ticker,
                option_type="put",
                min_itm_pct=min_itm_pct,
                max_itm_pct=max_itm_pct
            )

            if not options:
                logger.warning(f"No ITM puts found for {ticker}")
                return []

            # Filter by liquidity
            liquid_options = [
                opt for opt in options
                if opt.open_interest and opt.open_interest >= min_open_interest
            ]

            if not liquid_options:
                logger.warning(f"No liquid ITM puts found (min OI: {min_open_interest})")
                liquid_options = options

            # Score and rank options
            scored_options = []
            for opt in liquid_options:
                score = self._score_put_option(opt)
                scored_options.append({
                    "contract": opt,
                    "score": score,
                    "analysis": self._analyze_option(opt)
                })

            # Sort by score (descending)
            scored_options.sort(key=lambda x: x["score"], reverse=True)

            # Return top N
            recommendations = scored_options[:top_n]

            logger.info(f"✓ Analyzed {len(options)} ITM puts, returning top {len(recommendations)}")

            return recommendations

        except Exception as e:
            logger.error(f"Failed to analyze ITM puts for {ticker}: {e}")
            return []

    def _score_call_option(self, opt: OptionContract) -> float:
        """
        Score a call option based on multiple factors

        Factors:
        - Delta (higher is better for ITM)
        - Theta (lower absolute value is better)
        - Vega (positive exposure)
        - Open interest (liquidity)
        - Charm (positive for ITM calls)
        - Vanna (check sensitivity)

        Returns:
            Score (higher is better)
        """
        score = 0.0

        # Delta score: Prefer 0.7-0.9 for ITM calls
        if opt.delta:
            if 0.7 <= opt.delta <= 0.9:
                score += 30
            elif opt.delta > 0.9:
                score += 20  # Too deep ITM
            else:
                score += 10

        # Theta score: Lower absolute value is better
        if opt.theta:
            theta_abs = abs(opt.theta)
            if theta_abs < 0.20:
                score += 25
            elif theta_abs < 0.50:
                score += 15
            else:
                score += 5

        # Liquidity score: Open interest
        if opt.open_interest:
            if opt.open_interest > 1000:
                score += 20
            elif opt.open_interest > 500:
                score += 15
            elif opt.open_interest > 100:
                score += 10
            else:
                score += 5

        # Charm score: Positive charm for ITM calls is good
        if opt.charm:
            if opt.charm > 0:
                score += 15
            else:
                score += 5

        # Vanna score: Depends on volatility view
        if opt.vanna:
            # Negative vanna means delta decreases if IV rises
            # Could be good or bad depending on view
            score += 5  # Neutral for now

        # Vomma score: Positive vomma is generally good
        if opt.vomma and opt.vomma > 0:
            score += 5

        return score

    def _score_put_option(self, opt: OptionContract) -> float:
        """
        Score a put option based on multiple factors

        Returns:
            Score (higher is better)
        """
        score = 0.0

        # Delta score: Prefer -0.7 to -0.9 for ITM puts
        if opt.delta:
            delta_abs = abs(opt.delta)
            if 0.7 <= delta_abs <= 0.9:
                score += 30
            elif delta_abs > 0.9:
                score += 20
            else:
                score += 10

        # Theta score
        if opt.theta:
            theta_abs = abs(opt.theta)
            if theta_abs < 0.20:
                score += 25
            elif theta_abs < 0.50:
                score += 15
            else:
                score += 5

        # Liquidity score
        if opt.open_interest:
            if opt.open_interest > 1000:
                score += 20
            elif opt.open_interest > 500:
                score += 15
            elif opt.open_interest > 100:
                score += 10
            else:
                score += 5

        # Charm score for puts
        if opt.charm:
            if opt.charm < 0:
                score += 15  # Negative charm for ITM puts
            else:
                score += 5

        # Vanna and vomma
        if opt.vomma and opt.vomma > 0:
            score += 5

        return score

    def _analyze_option(self, opt: OptionContract) -> Dict[str, Any]:
        """
        Provide detailed analysis of an option

        Returns:
            Dictionary with analysis insights
        """
        analysis = {
            "liquidity": self._assess_liquidity(opt),
            "time_decay": self._assess_time_decay(opt),
            "volatility_exposure": self._assess_volatility_exposure(opt),
            "greeks_summary": self._summarize_greeks(opt)
        }

        return analysis

    def _assess_liquidity(self, opt: OptionContract) -> str:
        """Assess option liquidity"""
        if not opt.open_interest:
            return "Unknown"

        if opt.open_interest > 1000:
            return "Excellent"
        elif opt.open_interest > 500:
            return "Good"
        elif opt.open_interest > 100:
            return "Fair"
        else:
            return "Low"

    def _assess_time_decay(self, opt: OptionContract) -> str:
        """Assess time decay risk"""
        if not opt.theta:
            return "Unknown"

        theta_abs = abs(opt.theta)
        if theta_abs < 0.20:
            return "Low decay"
        elif theta_abs < 0.50:
            return "Moderate decay"
        else:
            return "High decay"

    def _assess_volatility_exposure(self, opt: OptionContract) -> str:
        """Assess volatility exposure"""
        if not opt.vega:
            return "Unknown"

        if opt.vega > 0.10:
            return "High vega exposure"
        elif opt.vega > 0.05:
            return "Moderate vega exposure"
        else:
            return "Low vega exposure"

    def _summarize_greeks(self, opt: OptionContract) -> str:
        """Provide human-readable Greeks summary"""
        parts = []

        if opt.delta:
            parts.append(f"Δ={opt.delta:.3f}")

        if opt.gamma:
            parts.append(f"Γ={opt.gamma:.4f}")

        if opt.theta:
            parts.append(f"Θ={opt.theta:.3f}")

        if opt.vega:
            parts.append(f"ν={opt.vega:.3f}")

        return ", ".join(parts) if parts else "No Greeks available"
