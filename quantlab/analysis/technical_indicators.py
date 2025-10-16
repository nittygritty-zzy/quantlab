"""
Technical Indicators Module

Provides common technical analysis indicators:
- Trend: SMA, EMA, MACD
- Momentum: RSI, Stochastic
- Volatility: Bollinger Bands, ATR
- Volume: OBV, Volume SMA
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class TechnicalIndicators:
    """
    Calculate technical indicators from price data

    All methods accept pandas DataFrame with OHLCV columns:
    - open, high, low, close, volume
    """

    @staticmethod
    def sma(data: pd.Series, period: int = 20) -> pd.Series:
        """
        Simple Moving Average

        Args:
            data: Price series (usually close)
            period: Number of periods

        Returns:
            SMA series
        """
        return data.rolling(window=period).mean()

    @staticmethod
    def ema(data: pd.Series, period: int = 20) -> pd.Series:
        """
        Exponential Moving Average

        Args:
            data: Price series (usually close)
            period: Number of periods

        Returns:
            EMA series
        """
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index

        Args:
            data: Price series (usually close)
            period: Number of periods (default: 14)

        Returns:
            RSI series (0-100)
        """
        # Calculate price changes
        delta = data.diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def macd(
        data: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence

        Args:
            data: Price series (usually close)
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line period (default: 9)

        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        # Calculate EMAs
        fast_ema = TechnicalIndicators.ema(data, fast_period)
        slow_ema = TechnicalIndicators.ema(data, slow_period)

        # MACD line
        macd_line = fast_ema - slow_ema

        # Signal line
        signal_line = TechnicalIndicators.ema(macd_line, signal_period)

        # Histogram
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(
        data: pd.Series,
        period: int = 20,
        num_std: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands

        Args:
            data: Price series (usually close)
            period: SMA period (default: 20)
            num_std: Number of standard deviations (default: 2.0)

        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        # Middle band (SMA)
        middle_band = TechnicalIndicators.sma(data, period)

        # Standard deviation
        std = data.rolling(window=period).std()

        # Upper and lower bands
        upper_band = middle_band + (std * num_std)
        lower_band = middle_band - (std * num_std)

        return upper_band, middle_band, lower_band

    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Average True Range (volatility indicator)

        Args:
            df: DataFrame with high, low, close columns
            period: Number of periods (default: 14)

        Returns:
            ATR series
        """
        # True Range components
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        # True Range (max of three values)
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # ATR (smoothed TR)
        atr = tr.rolling(window=period).mean()

        return atr

    @staticmethod
    def stochastic(
        df: pd.DataFrame,
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator

        Args:
            df: DataFrame with high, low, close columns
            period: Lookback period (default: 14)
            smooth_k: %K smoothing (default: 3)
            smooth_d: %D smoothing (default: 3)

        Returns:
            Tuple of (%K, %D)
        """
        # Lowest low and highest high
        low_min = df['low'].rolling(window=period).min()
        high_max = df['high'].rolling(window=period).max()

        # %K (fast stochastic)
        k_fast = 100 * (df['close'] - low_min) / (high_max - low_min)

        # Smooth %K
        k = k_fast.rolling(window=smooth_k).mean()

        # %D (signal line)
        d = k.rolling(window=smooth_d).mean()

        return k, d

    @staticmethod
    def obv(df: pd.DataFrame) -> pd.Series:
        """
        On-Balance Volume

        Args:
            df: DataFrame with close and volume columns

        Returns:
            OBV series
        """
        # Price direction
        direction = np.sign(df['close'].diff())

        # OBV
        obv = (direction * df['volume']).cumsum()

        return obv

    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Average Directional Index (trend strength)

        Args:
            df: DataFrame with high, low, close columns
            period: Number of periods (default: 14)

        Returns:
            ADX series
        """
        # True Range
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # Directional Movement
        up_move = df['high'] - df['high'].shift()
        down_move = df['low'].shift() - df['low']

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        # Smoothed values
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).mean() / atr)

        # DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx


class TechnicalAnalysis:
    """
    High-level technical analysis combining multiple indicators
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV DataFrame

        Args:
            df: DataFrame with columns: open, high, low, close, volume
        """
        self.df = df.copy()
        self.close = df['close']

    def calculate_all(self) -> Dict[str, Any]:
        """
        Calculate all technical indicators

        Returns:
            Dictionary with all indicators and interpretations
        """
        logger.info("Calculating technical indicators...")

        # Trend indicators
        sma_20 = TechnicalIndicators.sma(self.close, 20)
        sma_50 = TechnicalIndicators.sma(self.close, 50)
        sma_200 = TechnicalIndicators.sma(self.close, 200)
        ema_12 = TechnicalIndicators.ema(self.close, 12)
        ema_26 = TechnicalIndicators.ema(self.close, 26)

        # Momentum indicators
        rsi_14 = TechnicalIndicators.rsi(self.close, 14)
        macd_line, signal_line, histogram = TechnicalIndicators.macd(self.close)
        stoch_k, stoch_d = TechnicalIndicators.stochastic(self.df)

        # Volatility indicators
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(self.close)
        atr_14 = TechnicalIndicators.atr(self.df, 14)

        # Volume indicators
        obv = TechnicalIndicators.obv(self.df)

        # Trend strength
        adx_14 = TechnicalIndicators.adx(self.df, 14)

        # Get latest values
        current_price = self.close.iloc[-1]

        result = {
            "timestamp": datetime.now().isoformat(),
            "current_price": float(current_price),

            # Trend
            "trend": {
                "sma_20": float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None,
                "sma_50": float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else None,
                "sma_200": float(sma_200.iloc[-1]) if not pd.isna(sma_200.iloc[-1]) else None,
                "ema_12": float(ema_12.iloc[-1]) if not pd.isna(ema_12.iloc[-1]) else None,
                "ema_26": float(ema_26.iloc[-1]) if not pd.isna(ema_26.iloc[-1]) else None,
            },

            # Momentum
            "momentum": {
                "rsi_14": float(rsi_14.iloc[-1]) if not pd.isna(rsi_14.iloc[-1]) else None,
                "macd_line": float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None,
                "macd_signal": float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None,
                "macd_histogram": float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None,
                "stochastic_k": float(stoch_k.iloc[-1]) if not pd.isna(stoch_k.iloc[-1]) else None,
                "stochastic_d": float(stoch_d.iloc[-1]) if not pd.isna(stoch_d.iloc[-1]) else None,
            },

            # Volatility
            "volatility": {
                "bb_upper": float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None,
                "bb_middle": float(bb_middle.iloc[-1]) if not pd.isna(bb_middle.iloc[-1]) else None,
                "bb_lower": float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None,
                "atr_14": float(atr_14.iloc[-1]) if not pd.isna(atr_14.iloc[-1]) else None,
            },

            # Volume
            "volume": {
                "obv": float(obv.iloc[-1]) if not pd.isna(obv.iloc[-1]) else None,
            },

            # Trend strength
            "trend_strength": {
                "adx_14": float(adx_14.iloc[-1]) if not pd.isna(adx_14.iloc[-1]) else None,
            }
        }

        # Add interpretations
        result["signals"] = self._interpret_signals(result)

        logger.info("✓ Technical indicators calculated")
        return result

    def _interpret_signals(self, indicators: Dict[str, Any]) -> Dict[str, str]:
        """
        Interpret technical indicators into trading signals

        Args:
            indicators: Dictionary of calculated indicators

        Returns:
            Dictionary of signal interpretations
        """
        signals = {}
        current_price = indicators["current_price"]

        # RSI signal
        rsi = indicators["momentum"].get("rsi_14")
        if rsi:
            if rsi > 70:
                signals["rsi"] = "Overbought (>70)"
            elif rsi < 30:
                signals["rsi"] = "Oversold (<30)"
            else:
                signals["rsi"] = "Neutral (30-70)"

        # MACD signal
        macd_hist = indicators["momentum"].get("macd_histogram")
        if macd_hist:
            if macd_hist > 0:
                signals["macd"] = "Bullish (histogram > 0)"
            else:
                signals["macd"] = "Bearish (histogram < 0)"

        # Bollinger Bands signal
        bb_upper = indicators["volatility"].get("bb_upper")
        bb_lower = indicators["volatility"].get("bb_lower")
        if bb_upper and bb_lower:
            if current_price > bb_upper:
                signals["bollinger"] = "Overbought (above upper band)"
            elif current_price < bb_lower:
                signals["bollinger"] = "Oversold (below lower band)"
            else:
                signals["bollinger"] = "Normal range"

        # Stochastic signal
        stoch_k = indicators["momentum"].get("stochastic_k")
        if stoch_k:
            if stoch_k > 80:
                signals["stochastic"] = "Overbought (>80)"
            elif stoch_k < 20:
                signals["stochastic"] = "Oversold (<20)"
            else:
                signals["stochastic"] = "Neutral (20-80)"

        # ADX trend strength
        adx = indicators["trend_strength"].get("adx_14")
        if adx:
            if adx > 25:
                signals["trend_strength"] = "Strong trend (ADX > 25)"
            elif adx > 20:
                signals["trend_strength"] = "Moderate trend (ADX 20-25)"
            else:
                signals["trend_strength"] = "Weak/No trend (ADX < 20)"

        # Moving average crossover
        sma_20 = indicators["trend"].get("sma_20")
        sma_50 = indicators["trend"].get("sma_50")
        if sma_20 and sma_50:
            if current_price > sma_20 > sma_50:
                signals["ma_trend"] = "Bullish (price > SMA20 > SMA50)"
            elif current_price < sma_20 < sma_50:
                signals["ma_trend"] = "Bearish (price < SMA20 < SMA50)"
            else:
                signals["ma_trend"] = "Mixed signals"

        return signals
