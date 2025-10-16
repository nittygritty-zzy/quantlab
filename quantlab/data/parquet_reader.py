"""
Parquet file reader using DuckDB

Leverages DuckDB's native Parquet support to query files directly
without importing into the database.
"""

import duckdb
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

        # Verify paths exist
        if not self.parquet_root.exists():
            logger.warning(f"Parquet root does not exist: {self.parquet_root}")

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

            # Use glob pattern to read all parquet files (including partitioned directories)
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

            # Execute query
            result = duckdb.sql(query).df()

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

            # Execute query
            result = duckdb.sql(query).df()

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

            result = duckdb.sql(query).df()

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

            result = duckdb.sql(query).df()

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

            # Execute query
            result = duckdb.sql(query).df()

            logger.info(f"✓ Retrieved {len(result)} rows of minute options data")
            return result

        except Exception as e:
            logger.error(f"Failed to query options minute data: {e}")
            raise

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
