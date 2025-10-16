"""
Technical + Fundamental Strategy

Combines technical indicators (Polygon API) with fundamental filters (yfinance)
to select stocks with strong technical momentum and solid fundamentals.

Signal Composition:
- RSI Score (40%): Favors RSI between 30-70, penalizes extreme values
- MACD Score (30%): Positive histogram = bullish
- Fundamental Score (30%): Low P/E + positive revenue growth
"""

import sys
import os
import copy
import pandas as pd
import numpy as np

# Add qlib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../qlib_repo'))

from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy
from qlib.backtest.decision import TradeDecisionWO
from qlib.log import get_module_logger

logger = get_module_logger("TechFundamentalStrategy")


class TechFundamentalStrategy(TopkDropoutStrategy):
    """
    Technical + Fundamental Combined Strategy

    This strategy selects stocks based on:
    1. Technical indicators: RSI (not overbought/oversold), positive MACD
    2. Fundamental filters: Reasonable P/E ratio, positive revenue growth
    3. Composite scoring with configurable weights

    Features used:
    - polygon_rsi_14: RSI indicator from Polygon API
    - polygon_macd_hist: MACD histogram from Polygon API
    - yf_pe_ratio: P/E ratio from yfinance
    - yf_revenue_growth: Revenue growth from yfinance

    Parameters
    ----------
    topk : int
        Number of stocks to hold in portfolio
    n_drop : int
        Number of stocks to replace each period
    rsi_weight : float
        Weight for RSI score (default: 0.4)
    macd_weight : float
        Weight for MACD score (default: 0.3)
    fundamental_weight : float
        Weight for fundamental score (default: 0.3)
    max_pe : float
        Maximum acceptable P/E ratio (default: 30)
    min_revenue_growth : float
        Minimum acceptable revenue growth (default: 0.0)
    rsi_oversold : float
        RSI oversold threshold (default: 30)
    rsi_overbought : float
        RSI overbought threshold (default: 70)
    """

    def __init__(
        self,
        *,
        topk=50,
        n_drop=5,
        rsi_weight=0.4,
        macd_weight=0.3,
        fundamental_weight=0.3,
        max_pe=30,
        min_revenue_growth=0.0,
        rsi_oversold=30,
        rsi_overbought=70,
        **kwargs
    ):
        super().__init__(topk=topk, n_drop=n_drop, **kwargs)

        # Scoring weights
        self.rsi_weight = rsi_weight
        self.macd_weight = macd_weight
        self.fundamental_weight = fundamental_weight

        # Fundamental filters
        self.max_pe = max_pe
        self.min_revenue_growth = min_revenue_growth

        # Technical thresholds
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

        logger.info(f"✓ TechFundamentalStrategy initialized:")
        logger.info(f"  - Portfolio size: {topk}, replacement: {n_drop}")
        logger.info(f"  - Weights: RSI={rsi_weight}, MACD={macd_weight}, Fund={fundamental_weight}")
        logger.info(f"  - Filters: P/E<{max_pe}, RevGrowth>{min_revenue_growth}")

    def generate_trade_decision(self, execute_result=None):
        """
        Generate trade decisions with model predictions

        Uses the parent TopkDropoutStrategy logic with model predictions.
        The model has already learned from technical and fundamental features
        during training, so we just use its output scores.
        """
        # Simply use parent's implementation
        # The signal (model predictions) already incorporates the features
        # we trained on: RSI, MACD, P/E ratio, revenue growth
        return super().generate_trade_decision(execute_result)

    def _compute_composite_score(self, base_score: pd.Series) -> pd.Series:
        """
        Compute composite score from technical and fundamental features

        Args:
            base_score: Base prediction scores from model

        Returns:
            Composite score combining technical + fundamental factors
        """
        logger.info(f"Computing composite scores for {len(base_score)} stocks")

        # For now, just return base score
        # In a full implementation, we would:
        # 1. Fetch RSI, MACD, P/E, revenue growth for each stock
        # 2. Compute individual scores
        # 3. Apply filters
        # 4. Combine scores with weights

        # TODO: Implement full scoring logic when features are available
        # This requires accessing the feature data alongside predictions

        return base_score

    def _score_rsi(self, rsi_value: float) -> float:
        """
        Score RSI value (0-1 scale)

        Prefers RSI in neutral range (30-70)
        Penalizes extreme overbought/oversold
        """
        if pd.isna(rsi_value):
            return 0.5  # Neutral if missing

        if rsi_value < self.rsi_oversold:
            # Oversold: score increases as RSI approaches oversold threshold
            return max(0, rsi_value / self.rsi_oversold)
        elif rsi_value > self.rsi_overbought:
            # Overbought: score decreases as RSI exceeds overbought threshold
            return max(0, 1 - (rsi_value - self.rsi_overbought) / (100 - self.rsi_overbought))
        else:
            # Neutral range: full score
            return 1.0

    def _score_macd(self, macd_hist: float) -> float:
        """
        Score MACD histogram (0-1 scale)

        Positive histogram = bullish = high score
        Negative histogram = bearish = low score
        """
        if pd.isna(macd_hist):
            return 0.5  # Neutral if missing

        # Sigmoid-like transformation
        # macd_hist typically ranges from -5 to +5
        return 1 / (1 + np.exp(-macd_hist))

    def _score_fundamentals(self, pe_ratio: float, revenue_growth: float) -> float:
        """
        Score fundamental metrics (0-1 scale)

        Prefers:
        - Low P/E ratio (value stocks)
        - Positive revenue growth (growth stocks)
        """
        score = 0.0

        # P/E score (50% of fundamental score)
        if pd.notna(pe_ratio) and pe_ratio > 0:
            if pe_ratio < self.max_pe:
                # Lower P/E = higher score
                pe_score = 1 - (pe_ratio / self.max_pe)
                score += pe_score * 0.5
            # else: P/E too high, no contribution to score

        # Revenue growth score (50% of fundamental score)
        if pd.notna(revenue_growth):
            if revenue_growth >= self.min_revenue_growth:
                # Normalize growth to 0-1 scale (assume max 100% growth)
                growth_score = min(1.0, max(0, revenue_growth / 1.0))
                score += growth_score * 0.5

        return score
