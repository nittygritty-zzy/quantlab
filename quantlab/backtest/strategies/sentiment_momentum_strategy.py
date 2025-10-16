"""
Sentiment-Driven Momentum Strategy

Combines price momentum (SMA crossovers) with news sentiment scores
to identify stocks with strong technical momentum and positive market sentiment.

Weight Calculation:
- Momentum Signal: SMA(20) vs SMA(50) crossover
- Sentiment Boost: Multiply by (1 + sentiment_score)
- Analyst Factor: Adjust based on analyst recommendations
"""

import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../qlib_repo'))

from qlib.contrib.strategy.signal_strategy import WeightStrategyBase
from qlib.log import get_module_logger

logger = get_module_logger("SentimentMomentumStrategy")


class SentimentMomentumStrategy(WeightStrategyBase):
    """
    Sentiment-Driven Momentum Strategy

    Weights stocks based on:
    1. Momentum signal: SMA crossovers (SMA 20 vs SMA 50)
    2. Sentiment multiplier: News sentiment score from Alpha Vantage
    3. Analyst factor: Adjust based on yfinance recommendations

    Features used:
    - polygon_sma_20: 20-day SMA from Polygon
    - polygon_sma_50: 50-day SMA from Polygon
    - av_sentiment_score: Sentiment (-1 to 1) from Alpha Vantage
    - yf_forward_pe: Forward P/E for valuation filter

    Parameters
    ----------
    momentum_weight : float
        Weight for momentum component (default: 0.6)
    sentiment_weight : float
        Weight for sentiment component (default: 0.4)
    min_sentiment : float
        Minimum sentiment score to consider (default: -0.3)
    max_pe : float
        Maximum forward P/E for filter (default: 40)
    """

    def __init__(
        self,
        *,
        momentum_weight=0.6,
        sentiment_weight=0.4,
        min_sentiment=-0.3,
        max_pe=40,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.momentum_weight = momentum_weight
        self.sentiment_weight = sentiment_weight
        self.min_sentiment = min_sentiment
        self.max_pe = max_pe

        logger.info(f"✓ SentimentMomentumStrategy initialized:")
        logger.info(f"  - Weights: Momentum={momentum_weight}, Sentiment={sentiment_weight}")
        logger.info(f"  - Filters: Sentiment>{min_sentiment}, P/E<{max_pe}")

    def generate_target_weight_position(self, score, current, trade_start_time, trade_end_time):
        """
        Generate target weights for each stock

        Args:
            score: Prediction scores (from model)
            current: Current position
            trade_start_time: Trade window start
            trade_end_time: Trade window end

        Returns:
            Dictionary of {stock_id: target_weight}
        """
        try:
            logger.info(f"Generating weights for {len(score)} stocks")

            # For now, use base scores directly
            # TODO: Implement full logic to access features and compute weights
            # This requires:
            # 1. Access to SMA values for momentum calculation
            # 2. Access to sentiment scores
            # 3. Computing composite weights

            # Convert scores to weights (top stocks get higher weights)
            scores_normalized = (score - score.min()) / (score.max() - score.min() + 1e-8)
            weights = scores_normalized / scores_normalized.sum()

            # Return as dictionary (only positive weights)
            # Use float() to ensure scalar comparison
            target_weight_position = {}
            for stock, weight in weights.items():
                weight_scalar = float(weight) if hasattr(weight, 'item') else float(weight)
                if weight_scalar > 0.01:  # Minimum 1% weight
                    target_weight_position[stock] = weight_scalar

            logger.info(f"Generated {len(target_weight_position)} positions")
            return target_weight_position

        except Exception as e:
            logger.error(f"Error generating weights: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}

    def _compute_momentum_signal(self, sma_20: float, sma_50: float, price: float) -> float:
        """
        Compute momentum signal from SMA crossover

        Returns:
            1.0 = strong bullish (price > SMA20 > SMA50)
            0.0 = bearish (price < SMA20 < SMA50)
            0.5 = mixed signals
        """
        if pd.isna(sma_20) or pd.isna(sma_50) or pd.isna(price):
            return 0.5

        if price > sma_20 > sma_50:
            # Bullish: price above both MAs, short above long
            return 1.0
        elif price < sma_20 < sma_50:
            # Bearish: price below both MAs, short below long
            return 0.0
        else:
            # Mixed signals
            return 0.5

    def _apply_sentiment_boost(self, base_weight: float, sentiment_score: float) -> float:
        """
        Apply sentiment multiplier to base weight

        sentiment_score ranges from -1 (bearish) to +1 (bullish)
        Multiplier ranges from 0.5x to 1.5x
        """
        if pd.isna(sentiment_score):
            return base_weight

        # Filter out very negative sentiment
        if sentiment_score < self.min_sentiment:
            return 0.0

        # Boost factor: 1.0 + sentiment_score
        # -0.3 sentiment -> 0.7x multiplier
        #  0.0 sentiment -> 1.0x multiplier
        # +0.5 sentiment -> 1.5x multiplier
        multiplier = 1.0 + sentiment_score
        return base_weight * multiplier
