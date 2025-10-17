"""
Parquet file reader using DuckDB

Leverages DuckDB's native Parquet support to query files directly
without importing into the database.
"""

import duckdb
import threading
from pathlib import Path
from typing import Optional, List
from datetime import date, datetime

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ParquetReader:
    """
    Read Parquet files using DuckDB queries

    Features:
    - Direct Parquet querying (no import needed)
    - Filter by ticker, date range
    - Aggregate across multiple files
    - Fast columnar operations
    """

    def __init__(self, parquet_root: str):
        """
        Initialize Parquet reader

        Args:
            parquet_root: Root directory containing Parquet files
                         Expected: /Volumes/sandisk/quantmini-data/data/parquet
        """
        self.parquet_root = Path(parquet_root)
        self.stocks_daily_path = self.parquet_root / "stocks_daily"
        self.stocks_minute_path = self.parquet_root / "stocks_minute"
        self.options_daily_path = self.parquet_root / "options_daily"
        self.options_minute_path = self.parquet_root / "options_minute"

        # Thread-local storage for DuckDB connections (one per thread)
        self._local = threading.local()

        # Main connection for single-threaded operations
        self.conn = self._create_connection()

        # Verify paths exist
        if not self.parquet_root.exists():
            logger.warning(f"Parquet root does not exist: {self.parquet_root}")

    def _create_connection(self):
        """Create a new DuckDB connection with optimal settings"""
        conn = duckdb.connect(":memory:")
        # Limit threads per connection to reduce file handle usage
        conn.execute("SET threads TO 2")
        # Set memory limit to encourage DuckDB to close files sooner
        conn.execute("SET memory_limit = '2GB'")
        return conn

    def _get_connection(self):
        """Get thread-local DuckDB connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = self._create_connection()
            logger.debug(f"Created new DuckDB connection for thread {threading.current_thread().name}")
        return self._local.conn

    def get_stock_daily(
        self,
        tickers: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ):
        """
        Query daily stock data from Parquet files

        Args:
            tickers: List of ticker symbols
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Optional row limit

        Returns:
            Pandas DataFrame with OHLCV data
        """
        if not self.stocks_daily_path.exists():
            logger.error(f"Stock daily path does not exist: {self.stocks_daily_path}")
            return None

        try:
            # Build query
            query_parts = [
                "SELECT symbol as ticker, date, open, high, low, close, volume"
            ]

            # Build more specific glob pattern if date range is provided
            # This prevents DuckDB from opening thousands of unnecessary files
            if start_date and end_date:
                # Get year range
                years = range(start_date.year, end_date.year + 1)
                patterns = [str(self.stocks_daily_path / f"year={year}/**/*.parquet") for year in years]
                pattern_list = ", ".join(f"'{p}'" for p in patterns)
                query_parts.append(f"FROM read_parquet([{pattern_list}])")
            else:
                # Fall back to full scan if no date filter
                parquet_pattern = str(self.stocks_daily_path / "**/*.parquet")
                query_parts.append(f"FROM '{parquet_pattern}'")

            # Add filters
            where_clauses = []

            if tickers:
                ticker_list = ", ".join(f"'{t}'" for t in tickers)
                where_clauses.append(f"symbol IN ({ticker_list})")

            if start_date:
                where_clauses.append(f"date >= '{start_date}'")

            if end_date:
                where_clauses.append(f"date <= '{end_date}'")

            if where_clauses:
                query_parts.append("WHERE " + " AND ".join(where_clauses))

            # Order and limit
            query_parts.append("ORDER BY date DESC, symbol")

            if limit:
                query_parts.append(f"LIMIT {limit}")

            query = "\n".join(query_parts)

            logger.info(f"Querying stock daily data for {len(tickers)} tickers")
            logger.debug(f"Query: {query}")

            # Execute query using thread-local connection
            conn = self._get_connection()
            result = conn.execute(query).df()

            logger.info(f"✓ Retrieved {len(result)} rows of stock data")
            return result

        except Exception as e:
            logger.error(f"Failed to query stock daily data: {e}")
            raise

    def get_options_daily(
        self,
        underlying_tickers: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        option_type: Optional[str] = None,
        limit: Optional[int] = None
    ):
        """
        Query daily options data from Parquet files

        Args:
            underlying_tickers: List of underlying ticker symbols
            start_date: Optional start date filter
            end_date: Optional end date filter
            option_type: Optional 'call' or 'put' filter
            limit: Optional row limit

        Returns:
            Pandas DataFrame with options data
        """
        if not self.options_daily_path.exists():
            logger.warning(f"Options daily path does not exist: {self.options_daily_path}")
            return None

        try:
            # Build query
            query_parts = [
                "SELECT *"
            ]

            # Build more specific glob pattern if date range is provided
            if start_date and end_date:
                years = range(start_date.year, end_date.year + 1)
                patterns = [str(self.options_daily_path / f"year={year}/**/*.parquet") for year in years]
                pattern_list = ", ".join(f"'{p}'" for p in patterns)
                query_parts.append(f"FROM read_parquet([{pattern_list}])")
            else:
                parquet_pattern = str(self.options_daily_path / "**/*.parquet")
                query_parts.append(f"FROM '{parquet_pattern}'")

            # Add filters
            where_clauses = []

            if underlying_tickers:
                ticker_list = ", ".join(f"'{t}'" for t in underlying_tickers)
                where_clauses.append(f"underlying_ticker IN ({ticker_list})")

            if start_date:
                where_clauses.append(f"date >= '{start_date}'")

            if end_date:
                where_clauses.append(f"date <= '{end_date}'")

            if option_type:
                where_clauses.append(f"option_type = '{option_type}'")

            if where_clauses:
                query_parts.append("WHERE " + " AND ".join(where_clauses))

            # Order and limit
            query_parts.append("ORDER BY date DESC, underlying_ticker, strike_price")

            if limit:
                query_parts.append(f"LIMIT {limit}")

            query = "\n".join(query_parts)

            logger.info(f"Querying options daily data for {len(underlying_tickers)} tickers")

            # Execute query using thread-local connection
            conn = self._get_connection()
            result = conn.execute(query).df()

            logger.info(f"✓ Retrieved {len(result)} rows of options data")
            return result

        except Exception as e:
            logger.error(f"Failed to query options daily data: {e}")
            raise

    def get_available_tickers(self, data_type: str = "stocks_daily") -> List[str]:
        """
        Get list of available tickers in Parquet files

        Args:
            data_type: 'stocks_daily', 'stocks_minute', 'options_daily', or 'options_minute'

        Returns:
            List of unique ticker symbols
        """
        path_map = {
            "stocks_daily": self.stocks_daily_path,
            "stocks_minute": self.stocks_minute_path,
            "options_daily": self.options_daily_path,
            "options_minute": self.options_minute_path,
        }

        data_path = path_map.get(data_type)
        if not data_path or not data_path.exists():
            logger.warning(f"Path does not exist for {data_type}: {data_path}")
            return []

        try:
            parquet_pattern = str(data_path / "**/*.parquet")

            if "stocks" in data_type:
                query = f"SELECT DISTINCT symbol FROM '{parquet_pattern}' ORDER BY symbol"
            else:
                query = f"SELECT DISTINCT underlying_ticker FROM '{parquet_pattern}' ORDER BY underlying_ticker"

            conn = self._get_connection()
            result = conn.execute(query).df()

            tickers = result.iloc[:, 0].tolist()
            logger.info(f"✓ Found {len(tickers)} unique tickers in {data_type}")

            return tickers

        except Exception as e:
            logger.error(f"Failed to get available tickers: {e}")
            return []

    def get_date_range(self, data_type: str = "stocks_daily") -> tuple:
        """
        Get available date range in Parquet files

        Args:
            data_type: Type of data to check

        Returns:
            Tuple of (min_date, max_date)
        """
        path_map = {
            "stocks_daily": self.stocks_daily_path,
            "stocks_minute": self.stocks_minute_path,
            "options_daily": self.options_daily_path,
            "options_minute": self.options_minute_path,
        }

        data_path = path_map.get(data_type)
        if not data_path or not data_path.exists():
            return None, None

        try:
            parquet_pattern = str(data_path / "**/*.parquet")
            query = f"SELECT MIN(date) as min_date, MAX(date) as max_date FROM '{parquet_pattern}'"

            conn = self._get_connection()
            result = conn.execute(query).df()

            min_date = result['min_date'].iloc[0]
            max_date = result['max_date'].iloc[0]

            logger.info(f"✓ Date range for {data_type}: {min_date} to {max_date}")

            return min_date, max_date

        except Exception as e:
            logger.error(f"Failed to get date range: {e}")
            return None, None

    def get_options_minute(
        self,
        underlying_tickers: List[str],
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        option_type: Optional[str] = None,
        min_strike: Optional[float] = None,
        max_strike: Optional[float] = None,
        expiration_start: Optional[date] = None,
        expiration_end: Optional[date] = None,
        limit: Optional[int] = None
    ):
        """
        Query minute-level options data from Parquet files

        NOTE: Options minute data has 1-day delay (downloaded from S3).
        Perfect for historical analysis, backtesting, and research.

        IMPORTANT: Due to schema changes, only data from August 2025 onwards
        is currently supported. Earlier data uses a different schema where
        metadata is encoded in the ticker string.

        Args:
            underlying_tickers: List of underlying ticker symbols
            start_datetime: Start datetime filter
            end_datetime: End datetime filter
            option_type: Optional 'call' or 'put' filter
            min_strike: Minimum strike price filter
            max_strike: Maximum strike price filter
            expiration_start: Minimum expiration date
            expiration_end: Maximum expiration date
            limit: Optional row limit (recommended for large queries)

        Returns:
            Pandas DataFrame with minute-level options data

        Example:
            # Analyze AAPL call options intraday behavior
            df = reader.get_options_minute(
                underlying_tickers=['AAPL'],
                start_datetime=datetime(2025, 10, 14, 9, 30),
                end_datetime=datetime(2025, 10, 14, 16, 0),
                option_type='call',
                min_strike=175,
                max_strike=185,
                limit=10000
            )
        """
        if not self.options_minute_path.exists():
            logger.warning(f"Options minute path does not exist: {self.options_minute_path}")
            return None

        try:
            # Build query - metadata is encoded in ticker string, not separate columns
            # Ticker format: O:AAPL251003C00220000 (Options:Symbol+Date+Type+Strike)
            query_parts = [
                """SELECT
                    timestamp,
                    ticker,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    transactions
                """
            ]

            # Only query August 2025 onwards due to schema change
            # Earlier files have different schema
            # Build list of existing month patterns
            parquet_patterns = []
            base_path = self.options_minute_path / "year=2025"
            if base_path.exists():
                for month in range(8, 13):  # Aug-Dec
                    month_path = base_path / f"month={month:02d}"
                    if month_path.exists():
                        parquet_patterns.append(str(month_path / "**/*.parquet"))

            # Add future years if they exist
            year_2026_path = self.options_minute_path / "year=2026"
            if year_2026_path.exists():
                parquet_patterns.append(str(year_2026_path / "**/*.parquet"))

            if not parquet_patterns:
                logger.error("No options_minute data found for Aug 2025 onwards")
                return None

            # Combine patterns with array syntax
            pattern_list = ", ".join(f"'{p}'" for p in parquet_patterns)
            query_parts.append(f"FROM read_parquet([{pattern_list}])")

            # Add filters using ticker pattern matching
            where_clauses = []

            if underlying_tickers:
                # Filter by ticker prefix (e.g., 'O:AAPL%' for AAPL)
                ticker_patterns = " OR ".join(f"ticker LIKE 'O:{t}%'" for t in underlying_tickers)
                where_clauses.append(f"({ticker_patterns})")

            if start_datetime:
                where_clauses.append(f"timestamp >= TIMESTAMP '{start_datetime}'")

            if end_datetime:
                where_clauses.append(f"timestamp <= TIMESTAMP '{end_datetime}'")

            if option_type:
                # Filter by call/put in ticker string
                # Ticker format: O:AAPL251003C00220000 (C/P after 6-digit date)
                type_char = option_type[0].upper()  # 'C' for call, 'P' for put
                # Use regex to match digit followed by C or P (more precise than LIKE)
                where_clauses.append(f"regexp_matches(ticker, '\\d{type_char}')")

            # NOTE: Strike price filtering not supported since it's encoded in ticker
            # Would need complex string parsing. Use post-processing if needed.
            if min_strike or max_strike:
                logger.warning("Strike price filtering not supported for options_minute (encoded in ticker). Ignoring strike filters.")

            if expiration_start or expiration_end:
                logger.warning("Expiration date filtering not supported for options_minute (encoded in ticker). Ignoring expiration filters.")

            if where_clauses:
                query_parts.append("WHERE " + " AND ".join(where_clauses))

            # Order and limit
            query_parts.append("ORDER BY timestamp DESC, ticker")

            if limit:
                query_parts.append(f"LIMIT {limit}")

            query = "\n".join(query_parts)

            logger.info(f"Querying options minute data for {len(underlying_tickers)} tickers")
            logger.debug(f"Query: {query}")
            if not limit and not start_datetime:
                logger.warning("No time range or limit specified - query may return large dataset")

            # Execute query using thread-local connection
            conn = self._get_connection()
            result = conn.execute(query).df()

            logger.info(f"✓ Retrieved {len(result)} rows of minute options data")
            return result

        except Exception as e:
            logger.error(f"Failed to query options minute data: {e}")
            raise

    def get_tickers_with_recent_data(
        self,
        days_back: int = 7,
        min_rows: int = 50
    ) -> List[str]:
        """
        Get tickers that have recent data (useful for screening)

        Args:
            days_back: How many days back to check (default: 7)
            min_rows: Minimum number of rows required (default: 50 for technical indicators)

        Returns:
            List of ticker symbols with sufficient recent data
        """
        if not self.stocks_daily_path.exists():
            logger.error(f"Stock daily path does not exist: {self.stocks_daily_path}")
            return []

        try:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days_back)).date()

            parquet_pattern = str(self.stocks_daily_path / "**/*.parquet")

            query = f"""
            SELECT symbol, COUNT(*) as row_count
            FROM '{parquet_pattern}'
            WHERE date >= '{cutoff_date}'
            GROUP BY symbol
            HAVING COUNT(*) >= {min_rows}
            ORDER BY symbol
            """

            conn = self._get_connection()
            result = conn.execute(query).df()

            tickers = result['symbol'].tolist()
            logger.info(f"✓ Found {len(tickers)} tickers with recent data (>= {min_rows} rows in last {days_back} days)")

            return tickers

        except Exception as e:
            logger.error(f"Failed to get tickers with recent data: {e}")
            return []

    def get_stock_daily_batch(
        self,
        tickers: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        batch_size: int = 100
    ):
        """
        Query daily stock data for multiple tickers in batches

        This is more efficient than calling get_stock_daily() for each ticker individually.

        Args:
            tickers: List of ticker symbols
            start_date: Optional start date filter
            end_date: Optional end date filter
            batch_size: Number of tickers to query per batch (default: 100)

        Returns:
            Dictionary mapping ticker to DataFrame
        """
        results = {}

        # Process tickers in batches
        for i in range(0, len(tickers), batch_size):
            batch_tickers = tickers[i:i + batch_size]

            # Query the batch
            df = self.get_stock_daily(batch_tickers, start_date, end_date)

            if df is not None and not df.empty:
                # Split results by ticker
                for ticker in batch_tickers:
                    ticker_data = df[df['ticker'] == ticker]
                    if not ticker_data.empty:
                        results[ticker] = ticker_data

        return results

    def check_data_availability(self) -> dict:
        """
        Check what Parquet data is available

        Returns:
            Dictionary with availability status
        """
        availability = {
            "stocks_daily": {
                "exists": self.stocks_daily_path.exists(),
                "path": str(self.stocks_daily_path)
            },
            "stocks_minute": {
                "exists": self.stocks_minute_path.exists(),
                "path": str(self.stocks_minute_path)
            },
            "options_daily": {
                "exists": self.options_daily_path.exists(),
                "path": str(self.options_daily_path)
            },
            "options_minute": {
                "exists": self.options_minute_path.exists(),
                "path": str(self.options_minute_path),
                "note": "1-day delayed data from S3 - perfect for historical analysis"
            }
        }

        # Get date ranges for existing data
        for data_type, info in availability.items():
            if info["exists"]:
                min_date, max_date = self.get_date_range(data_type)
                info["min_date"] = str(min_date) if min_date else None
                info["max_date"] = str(max_date) if max_date else None
                info["tickers"] = len(self.get_available_tickers(data_type))

        return availability

    def __getstate__(self):
        """Exclude DuckDB connections from pickle"""
        state = self.__dict__.copy()
        # Remove the unpickleable DuckDB connections
        state.pop('conn', None)
        state.pop('_local', None)
        return state

    def __setstate__(self, state):
        """Restore DuckDB connections after unpickling"""
        self.__dict__.update(state)
        # Recreate thread-local storage and main connection
        self._local = threading.local()
        self.conn = self._create_connection()
