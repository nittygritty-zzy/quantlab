"""
QuantLab Feature Handler for Qlib

Bridges QuantLab DataManager to Qlib's backtesting framework.
Provides access to real-time technical indicators, fundamentals, and sentiment.
"""

from typing import List, Union
import pandas as pd
import sys
import os

# Add qlib_repo to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../qlib_repo'))

from qlib.data.dataset.handler import DataHandlerLP
from qlib.data.dataset.loader import DataLoader

from ..data.data_manager import DataManager
from ..data.database import DatabaseManager
from ..data.parquet_reader import ParquetReader
from ..utils.config import load_config
from ..utils.logger import setup_logger
from .realtime_features import RealtimeIndicatorFetcher

logger = setup_logger(__name__)


class QuantLabDataLoader(DataLoader):
    """
    Custom DataLoader that fetches features from QuantLab data sources

    This loader integrates with:
    - Polygon API (technical indicators)
    - yfinance (fundamentals)
    - Alpha Vantage (sentiment)
    """

    def __init__(
        self,
        config=None,
        feature_names: List[str] = None,
        data_manager: DataManager = None,
        **kwargs
    ):
        """
        Initialize QuantLabDataLoader

        Args:
            config: Feature configuration dict (optional)
            feature_names: List of feature names to fetch
            data_manager: QuantLab DataManager instance
        """
        super().__init__(**kwargs)

        self.feature_names = feature_names or []

        # Initialize DataManager if not provided
        #  Note: Don't store data_manager to avoid pickling issues
        if data_manager is None:
            qlab_config = load_config()
            db = DatabaseManager(db_path=qlab_config.database_path)
            parquet = ParquetReader(parquet_root=qlab_config.parquet_root)
            data_manager = DataManager(qlab_config, db, parquet)

        # Store data_manager for feature and label fetching
        # Note: Make it pickleable by storing only essential components
        self.fetcher = RealtimeIndicatorFetcher(data_manager)
        self._parquet = data_manager.parquet  # Store parquet reader for label calculation

        logger.info(f"✓ QuantLabDataLoader initialized with {len(self.feature_names)} features")

    def load(
        self,
        instruments: Union[str, List[str]] = None,
        start_time: str = None,
        end_time: str = None
    ) -> pd.DataFrame:
        """
        Load features from QuantLab data sources

        Args:
            instruments: Ticker symbols (list or string)
            start_time: Start date (YYYY-MM-DD)
            end_time: End date (YYYY-MM-DD)

        Returns:
            MultiIndex DataFrame with (datetime, instrument) index and ('feature'/'label', column_name) columns
        """
        try:
            # Handle instruments parameter
            if isinstance(instruments, str):
                # Single instrument
                instruments = [instruments]
            elif instruments is None:
                logger.error("No instruments specified")
                return pd.DataFrame()

            logger.info(f"Loading data for {len(instruments)} instruments: {start_time} to {end_time}")

            # Fetch features using RealtimeIndicatorFetcher
            df_features = self.fetcher.fetch_features(
                instruments=instruments,
                start_time=start_time,
                end_time=end_time,
                feature_names=self.feature_names if self.feature_names else None
            )

            if df_features.empty:
                logger.warning("No data loaded")
                return pd.DataFrame()

            # Create multi-level column headers: ('feature', feature_name) and ('label', label_name)
            # Qlib expects this format for proper feature/label separation

            # Features - create ('feature', <feature_name>) columns
            feature_columns = pd.MultiIndex.from_product([['feature'], df_features.columns])
            df_features.columns = feature_columns

            # Labels - calculate next-period returns from actual price data
            # We need to fetch close prices to calculate forward returns
            label_data = []
            for instrument in instruments:
                # Get historical OHLCV data for label calculation
                df_ohlcv = self._parquet.get_stock_daily(
                    tickers=[instrument],
                    start_date=start_time,
                    end_date=end_time
                )

                if df_ohlcv is not None and not df_ohlcv.empty:
                    # Calculate 1-day forward return: (close[t+1] / close[t]) - 1
                    df_ohlcv['forward_return'] = df_ohlcv['close'].shift(-1) / df_ohlcv['close'] - 1

                    # Create label dataframe
                    labels = pd.DataFrame({
                        'datetime': pd.to_datetime(df_ohlcv['date']),
                        'instrument': instrument,
                        'LABEL0': df_ohlcv['forward_return']
                    }).set_index(['datetime', 'instrument'])

                    label_data.append(labels)

            if label_data:
                df_labels = pd.concat(label_data)
                # Drop NaN labels (last day has no forward return)
                df_labels = df_labels.dropna()
                df_labels.columns = pd.MultiIndex.from_product([['label'], df_labels.columns])

                # Combine features and labels
                # Important: Only keep rows that have both features and labels
                df_combined = pd.concat([df_features, df_labels], axis=1, join='inner')
            else:
                df_combined = df_features

            logger.info(f"✓ Loaded {len(df_combined)} rows × {len(df_combined.columns)} columns")
            return df_combined

        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()


class QuantLabFeatureHandler(DataHandlerLP):
    """
    QuantLab Feature Handler for Qlib Backtest

    Extends Qlib's DataHandlerLP to provide access to QuantLab features:
    - Technical indicators from Polygon API
    - Fundamental metrics from yfinance
    - Sentiment scores from Alpha Vantage

    Usage:
        handler = QuantLabFeatureHandler(
            instruments=["AAPL", "MSFT", "GOOGL"],
            start_time="2024-01-01",
            end_time="2024-12-31",
            feature_names=["polygon_rsi_14", "yf_pe_ratio", "av_sentiment_score"]
        )
    """

    def __init__(
        self,
        instruments=None,
        start_time=None,
        end_time=None,
        feature_names: List[str] = None,
        data_manager: DataManager = None,
        infer_processors: List = [],
        learn_processors: List = [],
        **kwargs
    ):
        """
        Initialize QuantLabFeatureHandler

        Args:
            instruments: List of ticker symbols or ticker universe name
            start_time: Start date (YYYY-MM-DD)
            end_time: End date (YYYY-MM-DD)
            feature_names: List of feature names to fetch
                         (e.g., ["polygon_rsi_14", "yf_pe_ratio"])
            data_manager: Optional QuantLab DataManager instance
            infer_processors: Qlib processors for inference data
            learn_processors: Qlib processors for learning data
        """

        # Create custom data loader
        data_loader = QuantLabDataLoader(
            feature_names=feature_names,
            data_manager=data_manager
        )

        # Initialize parent class
        super().__init__(
            instruments=instruments,
            start_time=start_time,
            end_time=end_time,
            data_loader=data_loader,
            infer_processors=infer_processors,
            learn_processors=learn_processors,
            **kwargs
        )

        logger.info("✓ QuantLabFeatureHandler initialized")


    def get_label_config(self):
        """
        Return default label configuration

        Uses next-period return as label:
        Label = Ref($close, -2) / Ref($close, -1) - 1
        """
        return (["Ref($close, -2)/Ref($close, -1) - 1"], ["LABEL0"])
