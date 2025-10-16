"""
Lookup Table Manager

Manages slowly-changing data that should be refreshed on a schedule:
- Company info (sector, industry) - Refresh: Weekly
- Financial statements - Refresh: Quarterly
- Analyst ratings - Refresh: Daily
- Treasury rates - Refresh: Daily
- Corporate actions - Refresh: Weekly
"""

from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from .database import DatabaseManager
from .api_clients import YFinanceClient, AlphaVantageClient
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class RefreshFrequency(Enum):
    """Data refresh frequencies"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class LookupTableManager:
    """
    Manages lookup tables for slowly-changing data

    Features:
    - Automatic refresh scheduling
    - Stale data detection
    - Batch updates
    - Refresh history tracking
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize lookup table manager

        Args:
            db: Database manager instance
        """
        self.db = db
        self.yfinance = YFinanceClient()

        logger.info("✓ Lookup table manager initialized")

    def initialize_tables(self):
        """Create lookup tables if they don't exist"""
        try:
            # Company info table
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS company_info (
                    ticker VARCHAR(20) PRIMARY KEY,
                    company_name VARCHAR(255),
                    sector VARCHAR(100),
                    industry VARCHAR(100),
                    description TEXT,
                    website VARCHAR(255),
                    employees INTEGER,
                    exchange VARCHAR(50),
                    currency VARCHAR(10),
                    country VARCHAR(50),
                    last_refreshed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Financial statements table (quarterly snapshots)
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS financial_statements (
                    id BIGINT PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL,
                    fiscal_quarter VARCHAR(10) NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    revenue DECIMAL(20,2),
                    gross_profit DECIMAL(20,2),
                    operating_income DECIMAL(20,2),
                    net_income DECIMAL(20,2),
                    eps DECIMAL(10,4),
                    total_assets DECIMAL(20,2),
                    total_liabilities DECIMAL(20,2),
                    shareholders_equity DECIMAL(20,2),
                    operating_cash_flow DECIMAL(20,2),
                    free_cash_flow DECIMAL(20,2),
                    last_refreshed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, fiscal_quarter, fiscal_year)
                )
            """)

            # Analyst ratings table
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS analyst_ratings (
                    ticker VARCHAR(20) PRIMARY KEY,
                    strong_buy INTEGER DEFAULT 0,
                    buy INTEGER DEFAULT 0,
                    hold INTEGER DEFAULT 0,
                    sell INTEGER DEFAULT 0,
                    strong_sell INTEGER DEFAULT 0,
                    average_rating DECIMAL(3,2),
                    target_high DECIMAL(18,6),
                    target_low DECIMAL(18,6),
                    target_mean DECIMAL(18,6),
                    target_median DECIMAL(18,6),
                    last_refreshed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Treasury rates table
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS treasury_rates (
                    rate_date DATE PRIMARY KEY,
                    three_month DECIMAL(8,6),
                    two_year DECIMAL(8,6),
                    five_year DECIMAL(8,6),
                    ten_year DECIMAL(8,6),
                    thirty_year DECIMAL(8,6),
                    last_refreshed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Corporate actions table
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS corporate_actions (
                    id BIGINT PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL,
                    action_type VARCHAR(50) NOT NULL,
                    action_date DATE NOT NULL,
                    ex_date DATE,
                    amount DECIMAL(18,6),
                    split_ratio VARCHAR(20),
                    description TEXT,
                    last_refreshed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, action_type, action_date)
                )
            """)

            # Refresh log table
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS lookup_refresh_log (
                    id BIGINT PRIMARY KEY,
                    table_name VARCHAR(100) NOT NULL,
                    ticker VARCHAR(20),
                    refresh_started TIMESTAMP NOT NULL,
                    refresh_completed TIMESTAMP,
                    status VARCHAR(20) NOT NULL,
                    records_updated INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)

            # Create indexes
            self.db.execute("CREATE INDEX IF NOT EXISTS idx_financial_ticker ON financial_statements(ticker, fiscal_year)")
            self.db.execute("CREATE INDEX IF NOT EXISTS idx_corporate_ticker ON corporate_actions(ticker, action_date)")
            self.db.execute("CREATE INDEX IF NOT EXISTS idx_refresh_log ON lookup_refresh_log(table_name, refresh_started)")

            logger.info("✓ Lookup tables initialized")

        except Exception as e:
            logger.error(f"Failed to initialize lookup tables: {e}")
            raise

    # ===== COMPANY INFO =====

    def refresh_company_info(self, ticker: str) -> bool:
        """
        Refresh company info for a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            True if successful
        """
        try:
            import yfinance as yf

            stock = yf.Ticker(ticker)
            info = stock.info

            if not info:
                logger.warning(f"No company info for {ticker}")
                return False

            self.db.execute("""
                INSERT INTO company_info
                (ticker, company_name, sector, industry, description, website,
                 employees, exchange, currency, country, last_refreshed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (ticker) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    sector = EXCLUDED.sector,
                    industry = EXCLUDED.industry,
                    description = EXCLUDED.description,
                    website = EXCLUDED.website,
                    employees = EXCLUDED.employees,
                    exchange = EXCLUDED.exchange,
                    currency = EXCLUDED.currency,
                    country = EXCLUDED.country,
                    last_refreshed = EXCLUDED.last_refreshed
            """, [
                ticker,
                info.get('longName'),
                info.get('sector'),
                info.get('industry'),
                info.get('longBusinessSummary'),
                info.get('website'),
                info.get('fullTimeEmployees'),
                info.get('exchange'),
                info.get('currency'),
                info.get('country'),
                datetime.now()
            ])

            logger.info(f"✓ Refreshed company info for {ticker}")
            return True

        except Exception as e:
            logger.error(f"Failed to refresh company info for {ticker}: {e}")
            return False

    def get_company_info(self, ticker: str, max_age_days: int = 7) -> Optional[Dict[str, Any]]:
        """
        Get company info from lookup table

        Args:
            ticker: Stock ticker symbol
            max_age_days: Maximum age in days before refresh needed

        Returns:
            Company info dict or None
        """
        try:
            result = self.db.execute(f"""
                SELECT * FROM company_info
                WHERE ticker = ?
                AND last_refreshed > (CURRENT_TIMESTAMP - INTERVAL '{max_age_days}' DAY)
            """, [ticker]).fetchone()

            if result:
                return {
                    'ticker': result[0],
                    'company_name': result[1],
                    'sector': result[2],
                    'industry': result[3],
                    'description': result[4],
                    'website': result[5],
                    'employees': result[6],
                    'exchange': result[7],
                    'currency': result[8],
                    'country': result[9],
                    'last_refreshed': result[10]
                }

            # Data is stale or doesn't exist - refresh it
            logger.info(f"Company info for {ticker} is stale, refreshing...")
            if self.refresh_company_info(ticker):
                return self.get_company_info(ticker, max_age_days=365)  # Don't re-refresh

            return None

        except Exception as e:
            logger.error(f"Failed to get company info for {ticker}: {e}")
            return None

    # ===== ANALYST RATINGS =====

    def refresh_analyst_ratings(self, ticker: str) -> bool:
        """
        Refresh analyst ratings for a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            True if successful
        """
        try:
            import yfinance as yf

            stock = yf.Ticker(ticker)
            recommendations = stock.recommendations

            if recommendations is None or recommendations.empty:
                logger.warning(f"No analyst ratings for {ticker}")
                return False

            # yfinance now provides aggregated counts by period
            # Use the most recent period (row 0)
            recent = recommendations.iloc[0]

            strong_buy = int(recent.get('strongBuy', 0))
            buy = int(recent.get('buy', 0))
            hold = int(recent.get('hold', 0))
            sell = int(recent.get('sell', 0))
            strong_sell = int(recent.get('strongSell', 0))

            # Get target prices from info
            info = stock.info
            target_high = info.get('targetHighPrice')
            target_low = info.get('targetLowPrice')
            target_mean = info.get('targetMeanPrice')
            target_median = info.get('targetMedianPrice')

            # Calculate average rating (1=Strong Buy, 5=Strong Sell)
            total_ratings = strong_buy + buy + hold + sell + strong_sell
            if total_ratings > 0:
                weighted_sum = (strong_buy * 1 + buy * 2 + hold * 3 + sell * 4 + strong_sell * 5)
                average_rating = weighted_sum / total_ratings
            else:
                average_rating = None

            self.db.execute("""
                INSERT INTO analyst_ratings
                (ticker, strong_buy, buy, hold, sell, strong_sell, average_rating,
                 target_high, target_low, target_mean, target_median, last_refreshed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (ticker) DO UPDATE SET
                    strong_buy = EXCLUDED.strong_buy,
                    buy = EXCLUDED.buy,
                    hold = EXCLUDED.hold,
                    sell = EXCLUDED.sell,
                    strong_sell = EXCLUDED.strong_sell,
                    average_rating = EXCLUDED.average_rating,
                    target_high = EXCLUDED.target_high,
                    target_low = EXCLUDED.target_low,
                    target_mean = EXCLUDED.target_mean,
                    target_median = EXCLUDED.target_median,
                    last_refreshed = EXCLUDED.last_refreshed
            """, [
                ticker, strong_buy, buy, hold, sell, strong_sell, average_rating,
                target_high, target_low, target_mean, target_median, datetime.now()
            ])

            logger.info(f"✓ Refreshed analyst ratings for {ticker} ({total_ratings} ratings)")
            return True

        except Exception as e:
            logger.error(f"Failed to refresh analyst ratings for {ticker}: {e}")
            return False

    def get_analyst_ratings(self, ticker: str, max_age_days: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get analyst ratings from lookup table

        Args:
            ticker: Stock ticker symbol
            max_age_days: Maximum age in days before refresh needed

        Returns:
            Analyst ratings dict or None
        """
        try:
            result = self.db.execute(f"""
                SELECT * FROM analyst_ratings
                WHERE ticker = ?
                AND last_refreshed > (CURRENT_TIMESTAMP - INTERVAL '{max_age_days}' DAY)
            """, [ticker]).fetchone()

            if result:
                return {
                    'ticker': result[0],
                    'strong_buy': result[1],
                    'buy': result[2],
                    'hold': result[3],
                    'sell': result[4],
                    'strong_sell': result[5],
                    'average_rating': float(result[6]) if result[6] else None,
                    'target_high': float(result[7]) if result[7] else None,
                    'target_low': float(result[8]) if result[8] else None,
                    'target_mean': float(result[9]) if result[9] else None,
                    'target_median': float(result[10]) if result[10] else None,
                    'last_refreshed': result[11]
                }

            # Data is stale - refresh it
            logger.info(f"Analyst ratings for {ticker} are stale, refreshing...")
            if self.refresh_analyst_ratings(ticker):
                return self.get_analyst_ratings(ticker, max_age_days=365)

            return None

        except Exception as e:
            logger.error(f"Failed to get analyst ratings for {ticker}: {e}")
            return None

    # ===== TREASURY RATES =====

    def refresh_treasury_rates(self, alphavantage_api_key: str) -> bool:
        """
        Refresh treasury rates for today

        Args:
            alphavantage_api_key: Alpha Vantage API key

        Returns:
            True if successful
        """
        try:
            av_client = AlphaVantageClient(alphavantage_api_key)

            rates = {}
            maturities = {
                '3month': 'three_month',
                '2year': 'two_year',
                '5year': 'five_year',
                '10year': 'ten_year',
                '30year': 'thirty_year'
            }

            for maturity, column in maturities.items():
                rate = av_client.get_treasury_rate(maturity)
                if rate:
                    rates[column] = rate

            if not rates:
                logger.warning("No treasury rates retrieved")
                return False

            today = date.today()

            self.db.execute("""
                INSERT INTO treasury_rates
                (rate_date, three_month, two_year, five_year, ten_year, thirty_year, last_refreshed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (rate_date) DO UPDATE SET
                    three_month = EXCLUDED.three_month,
                    two_year = EXCLUDED.two_year,
                    five_year = EXCLUDED.five_year,
                    ten_year = EXCLUDED.ten_year,
                    thirty_year = EXCLUDED.thirty_year,
                    last_refreshed = EXCLUDED.last_refreshed
            """, [
                today,
                rates.get('three_month'),
                rates.get('two_year'),
                rates.get('five_year'),
                rates.get('ten_year'),
                rates.get('thirty_year'),
                datetime.now()
            ])

            logger.info(f"✓ Refreshed treasury rates for {today}")
            return True

        except Exception as e:
            logger.error(f"Failed to refresh treasury rates: {e}")
            return False

    def get_treasury_rate(self, maturity: str = '3month', max_age_days: int = 1) -> Optional[float]:
        """
        Get treasury rate from lookup table

        Args:
            maturity: '3month', '2year', '5year', '10year', '30year'
            max_age_days: Maximum age in days

        Returns:
            Treasury rate as decimal or None
        """
        try:
            column_map = {
                '3month': 'three_month',
                '2year': 'two_year',
                '5year': 'five_year',
                '10year': 'ten_year',
                '30year': 'thirty_year'
            }

            column = column_map.get(maturity, 'three_month')

            result = self.db.execute(f"""
                SELECT {column} FROM treasury_rates
                WHERE rate_date >= (CURRENT_DATE - INTERVAL '{max_age_days}' DAY)
                ORDER BY rate_date DESC
                LIMIT 1
            """).fetchone()

            if result and result[0]:
                return float(result[0])

            return None

        except Exception as e:
            logger.error(f"Failed to get treasury rate: {e}")
            return None

    # ===== BATCH OPERATIONS =====

    def batch_refresh_company_info(self, tickers: List[str]) -> Dict[str, bool]:
        """
        Refresh company info for multiple tickers

        Args:
            tickers: List of ticker symbols

        Returns:
            Dict mapping ticker to success status
        """
        results = {}

        logger.info(f"Batch refreshing company info for {len(tickers)} tickers...")

        for i, ticker in enumerate(tickers, 1):
            logger.info(f"  [{i}/{len(tickers)}] {ticker}")
            results[ticker] = self.refresh_company_info(ticker)

        success_count = sum(results.values())
        logger.info(f"✓ Batch refresh complete: {success_count}/{len(tickers)} successful")

        return results

    def batch_refresh_analyst_ratings(self, tickers: List[str]) -> Dict[str, bool]:
        """
        Refresh analyst ratings for multiple tickers

        Args:
            tickers: List of ticker symbols

        Returns:
            Dict mapping ticker to success status
        """
        results = {}

        logger.info(f"Batch refreshing analyst ratings for {len(tickers)} tickers...")

        for i, ticker in enumerate(tickers, 1):
            logger.info(f"  [{i}/{len(tickers)}] {ticker}")
            results[ticker] = self.refresh_analyst_ratings(ticker)

        success_count = sum(results.values())
        logger.info(f"✓ Batch refresh complete: {success_count}/{len(tickers)} successful")

        return results

    # ===== UTILITIES =====

    def check_staleness(self) -> Dict[str, Any]:
        """
        Check which lookup tables have stale data

        Returns:
            Dict with staleness information
        """
        try:
            staleness = {}

            # Check company info (7 days)
            result = self.db.execute("""
                SELECT COUNT(*) FROM company_info
                WHERE last_refreshed < (CURRENT_TIMESTAMP - INTERVAL '7' DAY)
            """).fetchone()
            staleness['company_info_stale'] = result[0] if result else 0

            # Check analyst ratings (1 day)
            result = self.db.execute("""
                SELECT COUNT(*) FROM analyst_ratings
                WHERE last_refreshed < (CURRENT_TIMESTAMP - INTERVAL '1' DAY)
            """).fetchone()
            staleness['analyst_ratings_stale'] = result[0] if result else 0

            # Check treasury rates (1 day)
            result = self.db.execute("""
                SELECT COUNT(*) FROM treasury_rates
                WHERE last_refreshed < (CURRENT_TIMESTAMP - INTERVAL '1' DAY)
            """).fetchone()
            staleness['treasury_rates_stale'] = result[0] if result else 0

            return staleness

        except Exception as e:
            logger.error(f"Failed to check staleness: {e}")
            return {}

    def get_refresh_stats(self) -> Dict[str, Any]:
        """
        Get statistics about lookup tables

        Returns:
            Dict with table statistics
        """
        try:
            stats = {}

            # Company info stats
            result = self.db.execute("SELECT COUNT(*) FROM company_info").fetchone()
            stats['company_info_count'] = result[0] if result else 0

            # Analyst ratings stats
            result = self.db.execute("SELECT COUNT(*) FROM analyst_ratings").fetchone()
            stats['analyst_ratings_count'] = result[0] if result else 0

            # Treasury rates stats
            result = self.db.execute("SELECT COUNT(*) FROM treasury_rates").fetchone()
            stats['treasury_rates_count'] = result[0] if result else 0

            # Financial statements stats
            result = self.db.execute("SELECT COUNT(*) FROM financial_statements").fetchone()
            stats['financial_statements_count'] = result[0] if result else 0

            # Corporate actions stats
            result = self.db.execute("SELECT COUNT(*) FROM corporate_actions").fetchone()
            stats['corporate_actions_count'] = result[0] if result else 0

            # Staleness check
            stats.update(self.check_staleness())

            return stats

        except Exception as e:
            logger.error(f"Failed to get refresh stats: {e}")
            return {}
