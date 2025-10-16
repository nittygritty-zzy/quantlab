"""
DuckDB database manager for QuantLab
"""

import duckdb
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseManager:
    """
    Manages DuckDB database operations

    Features:
    - Native Parquet file queries (no import needed)
    - Portfolio and position management
    - Analysis results caching
    - SQL analytics
    """

    SCHEMA_VERSION = "1.0.0"

    def __init__(self, db_path: str):
        """
        Initialize database manager

        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = os.path.expanduser(db_path)
        self.conn = None

        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._connect()

    def _connect(self) -> None:
        """Establish database connection"""
        try:
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"✓ Connected to DuckDB at: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise

    def close(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("✓ Database connection closed")

    def initialize_schema(self) -> None:
        """
        Create all database tables with proper schema

        Tables:
        - portfolios: Portfolio definitions
        - portfolio_positions: Ticker positions in portfolios
        - ticker_snapshots: Stock price snapshots
        - options_analysis: Options chain analysis results
        - fundamental_data: Fundamental metrics
        - sentiment_data: News sentiment analysis
        - analysis_cache: Cached analysis results
        """
        try:
            # Portfolios table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    portfolio_id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Portfolio positions table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_positions (
                    id BIGINT PRIMARY KEY,
                    portfolio_id VARCHAR NOT NULL,
                    ticker VARCHAR(20) NOT NULL,
                    weight DECIMAL(5,4),
                    shares INTEGER,
                    cost_basis DECIMAL(18,6),
                    entry_date DATE,
                    notes TEXT,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
                    UNIQUE(portfolio_id, ticker)
                )
            """)

            # Ticker snapshots table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS ticker_snapshots (
                    id BIGINT PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL,
                    date DATE NOT NULL,
                    open DECIMAL(18,6),
                    high DECIMAL(18,6),
                    low DECIMAL(18,6),
                    close DECIMAL(18,6),
                    volume BIGINT,
                    vwap DECIMAL(18,6),
                    change_percent DECIMAL(10,4),
                    data_source VARCHAR(50),
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, date, data_source)
                )
            """)

            # Options analysis table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS options_analysis (
                    id BIGINT PRIMARY KEY,
                    contract_ticker VARCHAR(50) NOT NULL,
                    underlying_ticker VARCHAR(20) NOT NULL,
                    strike_price DECIMAL(18,6) NOT NULL,
                    expiration_date DATE NOT NULL,
                    option_type VARCHAR(10) NOT NULL,
                    bid DECIMAL(18,6),
                    ask DECIMAL(18,6),
                    last_price DECIMAL(18,6),
                    mark DECIMAL(18,6),
                    volume BIGINT,
                    open_interest BIGINT,
                    implied_volatility DECIMAL(10,6),
                    delta DECIMAL(10,6),
                    gamma DECIMAL(10,6),
                    theta DECIMAL(10,6),
                    vega DECIMAL(10,6),
                    rho DECIMAL(10,6),
                    vanna DECIMAL(10,6),
                    charm DECIMAL(10,6),
                    vomma DECIMAL(10,6),
                    itm_percentage DECIMAL(10,4),
                    data_source VARCHAR(50),
                    analysis_date DATE NOT NULL,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(contract_ticker, analysis_date)
                )
            """)

            # Fundamental data table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS fundamental_data (
                    id BIGINT PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL,
                    date DATE NOT NULL,
                    market_cap DECIMAL(20,2),
                    pe_ratio DECIMAL(10,4),
                    forward_pe DECIMAL(10,4),
                    peg_ratio DECIMAL(10,4),
                    price_to_book DECIMAL(10,4),
                    profit_margin DECIMAL(10,6),
                    operating_margin DECIMAL(10,6),
                    return_on_equity DECIMAL(10,6),
                    return_on_assets DECIMAL(10,6),
                    revenue_growth DECIMAL(10,6),
                    earnings_growth DECIMAL(10,6),
                    total_cash DECIMAL(20,2),
                    total_debt DECIMAL(20,2),
                    debt_to_equity DECIMAL(10,4),
                    current_ratio DECIMAL(10,4),
                    target_price DECIMAL(18,6),
                    recommendation VARCHAR(20),
                    num_analysts INTEGER,
                    institutional_ownership DECIMAL(10,6),
                    insider_ownership DECIMAL(10,6),
                    data_source VARCHAR(50),
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, date, data_source)
                )
            """)

            # Sentiment data table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_data (
                    id BIGINT PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL,
                    date DATE NOT NULL,
                    sentiment_score DECIMAL(5,4),
                    sentiment_label VARCHAR(20),
                    articles_analyzed INTEGER,
                    positive_articles INTEGER,
                    negative_articles INTEGER,
                    neutral_articles INTEGER,
                    average_relevance DECIMAL(5,4),
                    buzz_score DECIMAL(10,4),
                    data_source VARCHAR(50),
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, date, data_source)
                )
            """)

            # Analysis cache table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    cache_key VARCHAR PRIMARY KEY,
                    ticker VARCHAR(20),
                    analysis_type VARCHAR(50),
                    result_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)

            # Create indexes for common queries
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON portfolio_positions(portfolio_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_ticker ON ticker_snapshots(ticker, date)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_options_underlying ON options_analysis(underlying_ticker, expiration_date)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_fundamental_ticker ON fundamental_data(ticker, date)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_ticker ON sentiment_data(ticker, date)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON analysis_cache(expires_at)")

            # Store schema version
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_info (
                    key VARCHAR PRIMARY KEY,
                    value VARCHAR
                )
            """)
            self.conn.execute(
                "INSERT OR REPLACE INTO schema_info (key, value) VALUES ('version', ?)",
                [self.SCHEMA_VERSION]
            )

            logger.info(f"✓ Database schema initialized (version {self.SCHEMA_VERSION})")

        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise

    def execute(self, query: str, params: Optional[List] = None) -> Any:
        """
        Execute a SQL query

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            Query result
        """
        try:
            if params:
                return self.conn.execute(query, params)
            else:
                return self.conn.execute(query)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            raise

    def query_df(self, query: str, params: Optional[List] = None):
        """
        Execute a SQL query and return pandas DataFrame

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            Pandas DataFrame with results
        """
        result = self.execute(query, params)
        return result.df()

    def get_schema_version(self) -> str:
        """Get current database schema version"""
        try:
            result = self.conn.execute(
                "SELECT value FROM schema_info WHERE key = 'version'"
            ).fetchone()
            return result[0] if result else "unknown"
        except:
            return "unknown"

    def vacuum(self) -> None:
        """Optimize database (VACUUM)"""
        try:
            self.conn.execute("VACUUM")
            logger.info("✓ Database vacuumed")
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
            raise

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __getstate__(self):
        """Prepare object for pickling (exclude DuckDB connection)"""
        state = self.__dict__.copy()
        # Remove the unpickleable connection object
        state['conn'] = None
        return state

    def __setstate__(self, state):
        """Restore object from pickle"""
        self.__dict__.update(state)
        # Reconnect to database
        if self.conn is None:
            self._connect()
