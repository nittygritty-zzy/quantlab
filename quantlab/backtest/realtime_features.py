"""
Real-Time Feature Fetcher for Qlib Backtest

Fetches features from QuantLab data sources (Polygon, yfinance, Alpha Vantage)
and maps them to Qlib-compatible format for backtesting.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from ..data.data_manager import DataManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class RealtimeIndicatorFetcher:
    """
    Fetch real-time features from QuantLab data sources

    Features fetched:
    - Technical indicators (Polygon API): SMA, EMA, MACD, RSI
    - Fundamental data (yfinance): P/E ratio, revenue growth, etc.
    - Sentiment scores (Alpha Vantage): News sentiment

    Output format:
    - MultiIndex DataFrame: (datetime, instrument)
    - Columns: feature names (e.g., polygon_rsi_14, yf_pe_ratio)
    """

    def __init__(self, data_manager: DataManager):
        """
        Initialize fetcher

        Args:
            data_manager: QuantLab DataManager instance
        """
        self.data_manager = data_manager
        logger.info("✓ RealtimeIndicatorFetcher initialized")

    def __getstate__(self):
        """Prepare for pickling - exclude data_manager"""
        state = self.__dict__.copy()
        # Store only what's needed to recreate data_manager
        if hasattr(self, 'data_manager'):
            state['_parquet_root'] = self.data_manager.parquet.parquet_root
            state['data_manager'] = None
        return state

    def __setstate__(self, state):
        """Restore from pickle - recreate data_manager if needed"""
        self.__dict__.update(state)
        # Recreate data_manager only if needed
        if self.data_manager is None and hasattr(self, '_parquet_root'):
            from ..utils.config import load_config
            from ..data.database import DatabaseManager
            from ..data.parquet_reader import ParquetReader
            from ..data.data_manager import DataManager

            qlab_config = load_config()
            db = DatabaseManager(db_path=qlab_config.database_path)
            parquet = ParquetReader(parquet_root=self._parquet_root)
            self.data_manager = DataManager(qlab_config, db, parquet)

    def fetch_features(
        self,
        instruments: List[str],
        start_time: str,
        end_time: str,
        feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Fetch features for given instruments and time range

        Args:
            instruments: List of ticker symbols
            start_time: Start date (YYYY-MM-DD)
            end_time: End date (YYYY-MM-DD)
            feature_names: Optional list of feature names to fetch
                         If None, fetch all available features

        Returns:
            MultiIndex DataFrame with (datetime, instrument) index and feature columns
        """
        try:
            logger.info(f"Fetching features for {len(instruments)} instruments from {start_time} to {end_time}")

            # Parse dates
            start_date = pd.to_datetime(start_time).date()
            end_date = pd.to_datetime(end_time).date()

            # Determine which features to fetch
            if feature_names is None:
                feature_names = self._get_default_features()

            # Fetch features for each instrument
            all_data = []
            for ticker in instruments:
                ticker_data = self._fetch_ticker_features(
                    ticker=ticker,
                    start_date=start_date,
                    end_date=end_date,
                    feature_names=feature_names
                )
                if ticker_data is not None:
                    all_data.append(ticker_data)

            if not all_data:
                logger.warning("No data fetched for any instruments")
                return pd.DataFrame()

            # Combine all ticker data
            df = pd.concat(all_data, ignore_index=True)

            # Set MultiIndex
            df = df.set_index(['datetime', 'instrument'])
            df = df.sort_index()

            logger.info(f"✓ Fetched {len(df)} rows × {len(df.columns)} features")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch features: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()

    def _fetch_ticker_features(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        feature_names: List[str]
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical features for a single ticker

        Returns:
            DataFrame with columns: datetime, instrument, [features...]
        """
        try:
            # Get historical OHLCV data from parquet
            df_ohlcv = self.data_manager.parquet.get_stock_daily(
                tickers=[ticker],
                start_date=start_date,
                end_date=end_date
            )

            if df_ohlcv is None or df_ohlcv.empty:
                logger.debug(f"No historical data for {ticker}")
                return None

            # Calculate technical indicators from historical data
            from ..analysis.technical_indicators import TechnicalIndicators

            features_df = pd.DataFrame()
            features_df['datetime'] = pd.to_datetime(df_ohlcv['date'])
            features_df['instrument'] = ticker

            # Calculate technical indicators for each date
            for feat_name in feature_names:
                if feat_name.startswith("polygon_"):
                    # Calculate from historical OHLCV
                    if feat_name == 'polygon_rsi_14':
                        features_df[feat_name] = TechnicalIndicators.rsi(df_ohlcv['close'], 14)
                    elif feat_name == 'polygon_macd_hist':
                        _, _, hist = TechnicalIndicators.macd(df_ohlcv['close'], 12, 26, 9)
                        features_df[feat_name] = hist
                    elif feat_name == 'polygon_macd_line':
                        line, _, _ = TechnicalIndicators.macd(df_ohlcv['close'], 12, 26, 9)
                        features_df[feat_name] = line
                    elif feat_name == 'polygon_macd_signal':
                        _, signal, _ = TechnicalIndicators.macd(df_ohlcv['close'], 12, 26, 9)
                        features_df[feat_name] = signal
                    elif feat_name == 'polygon_sma_20':
                        features_df[feat_name] = TechnicalIndicators.sma(df_ohlcv['close'], 20)
                    elif feat_name == 'polygon_sma_50':
                        features_df[feat_name] = TechnicalIndicators.sma(df_ohlcv['close'], 50)
                    elif feat_name == 'polygon_ema_12':
                        features_df[feat_name] = TechnicalIndicators.ema(df_ohlcv['close'], 12)
                    elif feat_name == 'polygon_ema_26':
                        features_df[feat_name] = TechnicalIndicators.ema(df_ohlcv['close'], 26)

                elif feat_name.startswith("yf_"):
                    # Fetch fundamentals once and forward-fill (fundamentals change quarterly)
                    fundamentals = self.data_manager.get_fundamentals(ticker)
                    if fundamentals:
                        feat_dict = self._extract_fundamental_features(fundamentals, [feat_name])
                        if feat_name in feat_dict:
                            features_df[feat_name] = feat_dict[feat_name]

                elif feat_name.startswith("av_"):
                    # Fetch sentiment once and forward-fill
                    sentiment = self.data_manager.get_sentiment([ticker])
                    if sentiment:
                        feat_dict = self._extract_sentiment_features(sentiment, [feat_name])
                        if feat_name in feat_dict:
                            features_df[feat_name] = feat_dict[feat_name]

            # Drop rows with NaN values (from indicator warm-up periods)
            features_df = features_df.dropna()

            if features_df.empty:
                logger.debug(f"No valid features after calculation for {ticker}")
                return None

            logger.debug(f"✓ Fetched {len(features_df)} rows for {ticker}")
            return features_df

        except Exception as e:
            logger.debug(f"Failed to fetch features for {ticker}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    def _extract_technical_features(
        self,
        tech_data: Dict[str, Any],
        feature_names: List[str]
    ) -> Dict[str, float]:
        """Extract technical indicator features"""
        features = {}

        # Mapping from feature names to data paths
        mapping = {
            'polygon_sma_20': ('trend', 'sma_20'),
            'polygon_sma_50': ('trend', 'sma_50'),
            'polygon_ema_12': ('trend', 'ema_12'),
            'polygon_ema_26': ('trend', 'ema_26'),
            'polygon_rsi_14': ('momentum', 'rsi_14'),
            'polygon_macd_line': ('momentum', 'macd_line'),
            'polygon_macd_signal': ('momentum', 'macd_signal'),
            'polygon_macd_hist': ('momentum', 'macd_histogram'),
        }

        for feat_name in feature_names:
            if feat_name in mapping:
                category, key = mapping[feat_name]
                value = tech_data.get(category, {}).get(key)
                if value is not None:
                    features[feat_name] = float(value)

        return features

    def _extract_fundamental_features(
        self,
        fundamental_data: Any,
        feature_names: List[str]
    ) -> Dict[str, float]:
        """Extract fundamental features"""
        features = {}

        # Mapping from feature names to attributes
        mapping = {
            'yf_pe_ratio': 'pe_ratio',
            'yf_forward_pe': 'forward_pe',
            'yf_peg_ratio': 'peg_ratio',
            'yf_profit_margin': 'profit_margin',
            'yf_roe': 'return_on_equity',
            'yf_revenue_growth': 'revenue_growth',
            'yf_earnings_growth': 'earnings_growth',
            'yf_price_to_book': 'price_to_book',
            'yf_debt_to_equity': 'debt_to_equity',
        }

        for feat_name in feature_names:
            if feat_name in mapping:
                attr_name = mapping[feat_name]
                value = getattr(fundamental_data, attr_name, None)
                if value is not None:
                    features[feat_name] = float(value)

        return features

    def _extract_sentiment_features(
        self,
        sentiment_data: Any,
        feature_names: List[str]
    ) -> Dict[str, float]:
        """Extract sentiment features"""
        features = {}

        # Mapping from feature names to attributes
        mapping = {
            'av_sentiment_score': 'sentiment_score',
            'av_articles_positive': 'positive_articles',
            'av_articles_negative': 'negative_articles',
            'av_articles_neutral': 'neutral_articles',
            'av_relevance': 'average_relevance',
        }

        for feat_name in feature_names:
            if feat_name in mapping:
                attr_name = mapping[feat_name]
                value = getattr(sentiment_data, attr_name, None)
                if value is not None:
                    # Convert to float (some might be integers)
                    features[feat_name] = float(value)

        return features

    def _get_default_features(self) -> List[str]:
        """Get list of all available features"""
        return [
            # Technical indicators (Polygon)
            'polygon_sma_20',
            'polygon_sma_50',
            'polygon_ema_12',
            'polygon_ema_26',
            'polygon_rsi_14',
            'polygon_macd_line',
            'polygon_macd_signal',
            'polygon_macd_hist',

            # Fundamentals (yfinance)
            'yf_pe_ratio',
            'yf_forward_pe',
            'yf_peg_ratio',
            'yf_profit_margin',
            'yf_roe',
            'yf_revenue_growth',

            # Sentiment (Alpha Vantage)
            'av_sentiment_score',
            'av_articles_positive',
        ]
