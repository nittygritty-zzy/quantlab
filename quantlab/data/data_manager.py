"""
Unified Data Manager

Routes data requests to appropriate sources:
- Historical data: Parquet files (fast, local)
- Real-time data: Polygon API
- Sentiment: Alpha Vantage API
- Fundamentals: yfinance API

Implements smart routing and fallback strategies.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import json

from .api_clients import PolygonClient, AlphaVantageClient, YFinanceClient
from .parquet_reader import ParquetReader
from .database import DatabaseManager
from .lookup_tables import LookupTableManager
from ..models.ticker_data import TickerSnapshot, OptionContract, FundamentalData, SentimentData
from ..analysis.greeks_calculator import BlackScholesGreeks, calculate_advanced_greeks
from ..analysis.technical_indicators import TechnicalAnalysis
from ..utils.logger import setup_logger
from ..utils.config import Config

logger = setup_logger(__name__)


class DataManager:
    """
    Unified data manager with smart routing

    Features:
    - Automatic source selection (Parquet vs API)
    - Caching with TTL
    - Fallback strategies
    - Greeks calculation
    """

    def __init__(
        self,
        config: Config,
        db: DatabaseManager,
        parquet: ParquetReader
    ):
        """
        Initialize data manager

        Args:
            config: Configuration object
            db: Database manager
            parquet: Parquet reader
        """
        self.config = config
        self.db = db
        self.parquet = parquet

        # Initialize API clients
        self.polygon = PolygonClient(
            api_key=config.polygon_api_key,
            rate_limit=config.polygon_rate_limit
        )
        self.alphavantage = AlphaVantageClient(
            api_key=config.alphavantage_api_key,
            rate_limit=config.alphavantage_rate_limit
        )
        self.yfinance = YFinanceClient()

        # Initialize lookup table manager
        self.lookup = LookupTableManager(db)

        logger.info("✓ Data manager initialized with all sources")

    # ===== STOCK DATA =====

    def get_stock_price(
        self,
        ticker: str,
        date: Optional[date] = None,
        use_cache: bool = True
    ) -> Optional[TickerSnapshot]:
        """
        Get stock price data

        Strategy:
        - If date is None (real-time): Use Polygon API
        - If date is provided: Use Parquet (historical)
        - Cache results in database

        Args:
            ticker: Stock ticker symbol
            date: Optional date (None = real-time)
            use_cache: Whether to use cached data

        Returns:
            TickerSnapshot or None
        """
        try:
            # Check cache first
            if use_cache:
                cached = self._get_cached_snapshot(ticker, date)
                if cached:
                    logger.debug(f"Cache hit for {ticker}")
                    return cached

            # Real-time: Use Polygon API
            if date is None:
                data = self.polygon.get_stock_snapshot(ticker)
                if not data:
                    return None

                snapshot = TickerSnapshot(
                    ticker=ticker,
                    date=datetime.now().date(),
                    open=data["open"],
                    high=data["high"],
                    low=data["low"],
                    close=data["price"],
                    volume=data["volume"],
                    vwap=data.get("vwap"),
                    change_percent=data.get("change_percent"),
                    data_source="polygon",
                    fetched_at=datetime.now()
                )

                # Cache it
                self._cache_snapshot(snapshot)

                return snapshot

            # Historical: Use Parquet
            df = self.parquet.get_stock_daily(
                tickers=[ticker],
                start_date=date,
                end_date=date,
                limit=1
            )

            if df is None or df.empty:
                logger.warning(f"No historical data for {ticker} on {date}")
                return None

            row = df.iloc[0]
            snapshot = TickerSnapshot(
                ticker=ticker,
                date=row['date'].date() if hasattr(row['date'], 'date') else row['date'],
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                data_source="parquet",
                fetched_at=datetime.now()
            )

            return snapshot

        except Exception as e:
            logger.error(f"Failed to get stock price for {ticker}: {e}")
            return None

    def get_intraday_prices(
        self,
        ticker: str,
        interval: str = "1min",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 50000,
        include_extended_hours: bool = False
    ) -> Optional[Any]:  # Returns pandas DataFrame
        """
        Get intraday price data at minute/hour intervals

        Args:
            ticker: Stock ticker symbol
            interval: Time interval ('1min', '5min', '15min', '30min', '1hour')
            from_date: Start date in YYYY-MM-DD format (default: today)
            to_date: End date in YYYY-MM-DD format (default: today)
            limit: Maximum number of bars (default: 50000)
            include_extended_hours: If True, include pre-market and after-hours data.
                                   If False (default), only include regular market hours (9:30 AM - 4 PM ET)

        Returns:
            pandas DataFrame with columns: date, open, high, low, close, volume, vwap
            or None if no data available

        Example:
            >>> # Get today's 5-minute data (regular hours only)
            >>> df = data_manager.get_intraday_prices("AAPL", interval="5min")
            >>> # Get 1 year of 5-minute data including pre/post market
            >>> df = data_manager.get_intraday_prices("AAPL", interval="5min",
            ...     from_date="2024-01-01", to_date="2025-01-01", include_extended_hours=True)
        """
        try:
            import pandas as pd

            # Parse interval string to multiplier and timespan
            interval_map = {
                "1min": (1, "minute"),
                "5min": (5, "minute"),
                "15min": (15, "minute"),
                "30min": (30, "minute"),
                "1hour": (1, "hour"),
            }

            if interval not in interval_map:
                logger.error(f"Invalid interval: {interval}. Valid options: {list(interval_map.keys())}")
                return None

            multiplier, timespan = interval_map[interval]

            # Fetch from Polygon API
            aggregates = self.polygon.get_intraday_aggregates(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                from_date=from_date,
                to_date=to_date,
                limit=limit
            )

            if not aggregates:
                logger.warning(f"No intraday data for {ticker}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(aggregates)

            # Filter to regular market hours if requested (default)
            if not include_extended_hours:
                # Regular US market hours: 9:30 AM - 4:00 PM ET
                # Keep bars where: (hour > 9 OR (hour == 9 AND minute >= 30)) AND hour < 16
                original_count = len(df)

                df = df[
                    ((df['date'].dt.hour > 9) | ((df['date'].dt.hour == 9) & (df['date'].dt.minute >= 30))) &
                    (df['date'].dt.hour < 16)
                ].copy()

                filtered_count = original_count - len(df)
                if filtered_count > 0:
                    logger.info(f"   Filtered out {filtered_count} extended hours bars (pre-market/after-hours)")

            logger.info(f"✓ Retrieved {len(df)} intraday bars for {ticker} ({interval})")
            return df

        except Exception as e:
            logger.error(f"Failed to get intraday prices for {ticker}: {e}")
            return None

    # ===== OPTIONS DATA =====

    def get_options_chain(
        self,
        ticker: str,
        expiration_date: Optional[date] = None,
        option_type: Optional[str] = None,
        min_itm_pct: float = 5.0,
        max_itm_pct: float = 20.0,
        use_cache: bool = True
    ) -> List[OptionContract]:
        """
        Get options chain with calculated advanced Greeks

        Args:
            ticker: Underlying ticker symbol
            expiration_date: Optional specific expiration
            option_type: Optional 'call' or 'put' filter
            min_itm_pct: Minimum ITM percentage
            max_itm_pct: Maximum ITM percentage
            use_cache: Whether to use cached data

        Returns:
            List of OptionContract objects with Greeks
        """
        try:
            # Get current stock price
            current_price_snap = self.get_stock_price(ticker)
            if not current_price_snap:
                logger.error(f"Cannot get options: no price for {ticker}")
                return []

            current_price = float(current_price_snap.close)  # Convert Decimal to float

            # Get risk-free rate
            risk_free_rate = self._get_risk_free_rate()

            # Get options from Polygon
            options_data = self.polygon.get_options_chain(
                ticker=ticker,
                expiration_date=expiration_date,
                contract_type=option_type
            )

            if not options_data:
                logger.warning(f"No options data for {ticker}")
                return []

            # Process and filter options
            options = []
            for opt in options_data:
                # Calculate ITM percentage
                strike = float(opt["strike_price"])  # Convert Decimal to float
                if opt["option_type"] == "call":
                    itm_pct = ((current_price - strike) / strike) * 100
                else:
                    itm_pct = ((strike - current_price) / strike) * 100

                # Filter by ITM range
                if not (min_itm_pct <= itm_pct <= max_itm_pct):
                    continue

                # Calculate advanced Greeks if we have IV
                iv = opt.get("implied_volatility")
                if iv:
                    days = BlackScholesGreeks.days_to_expiry(opt["expiration_date"])

                    greeks = calculate_advanced_greeks(
                        stock_price=current_price,
                        strike_price=strike,
                        days_to_expiry=days,
                        risk_free_rate=risk_free_rate,
                        implied_volatility=iv,
                        option_type=opt["option_type"]
                    )

                    # Override with calculated Greeks if Polygon doesn't provide them
                    if not opt.get("delta"):
                        opt.update(greeks)
                    else:
                        # Add advanced Greeks to existing first-order Greeks
                        opt["vanna"] = greeks.get("vanna")
                        opt["charm"] = greeks.get("charm")
                        opt["vomma"] = greeks.get("vomma")

                # Create OptionContract
                contract = OptionContract(
                    contract_ticker=opt["contract_ticker"],
                    underlying_ticker=ticker,
                    strike_price=strike,
                    expiration_date=opt["expiration_date"],
                    option_type=opt["option_type"],
                    bid=opt.get("bid"),
                    ask=opt.get("ask"),
                    last_price=opt.get("last_price"),
                    volume=opt.get("volume"),
                    open_interest=opt.get("open_interest"),
                    implied_volatility=iv,
                    delta=opt.get("delta"),
                    gamma=opt.get("gamma"),
                    theta=opt.get("theta"),
                    vega=opt.get("vega"),
                    vanna=opt.get("vanna"),
                    charm=opt.get("charm"),
                    vomma=opt.get("vomma"),
                    itm_percentage=itm_pct,
                    data_source="polygon",
                    fetched_at=datetime.now()
                )

                options.append(contract)

            logger.info(f"✓ Retrieved {len(options)} options for {ticker} (ITM: {min_itm_pct}-{max_itm_pct}%)")
            return options

        except Exception as e:
            logger.error(f"Failed to get options chain for {ticker}: {e}")
            return []

    # ===== FUNDAMENTALS =====

    def get_fundamentals(
        self,
        ticker: str,
        use_cache: bool = True
    ) -> Optional[FundamentalData]:
        """
        Get fundamental data from yfinance

        Args:
            ticker: Stock ticker symbol
            use_cache: Whether to use cached data

        Returns:
            FundamentalData or None
        """
        try:
            # Check cache
            if use_cache:
                cached = self._get_cached_fundamentals(ticker)
                if cached:
                    return cached

            # Fetch from yfinance
            data = self.yfinance.get_fundamentals(ticker)
            if not data:
                return None

            fundamentals = FundamentalData(
                ticker=ticker,
                date=datetime.now().date(),
                market_cap=data.get("market_cap"),
                pe_ratio=data.get("pe_ratio"),
                forward_pe=data.get("forward_pe"),
                peg_ratio=data.get("peg_ratio"),
                price_to_book=data.get("price_to_book"),
                profit_margin=data.get("profit_margin"),
                operating_margin=data.get("operating_margin"),
                return_on_equity=data.get("return_on_equity"),
                return_on_assets=data.get("return_on_assets"),
                revenue_growth=data.get("revenue_growth"),
                earnings_growth=data.get("earnings_growth"),
                total_cash=data.get("total_cash"),
                total_debt=data.get("total_debt"),
                debt_to_equity=data.get("debt_to_equity"),
                current_ratio=data.get("current_ratio"),
                target_price=data.get("target_price"),
                recommendation=data.get("recommendation"),
                num_analysts=data.get("num_analysts"),
                data_source="yfinance",
                fetched_at=datetime.now()
            )

            # Cache it
            self._cache_fundamentals(fundamentals)

            return fundamentals

        except Exception as e:
            logger.error(f"Failed to get fundamentals for {ticker}: {e}")
            return None

    # ===== SENTIMENT =====

    def get_sentiment(
        self,
        tickers: List[str],
        use_cache: bool = True
    ) -> Optional[SentimentData]:
        """
        Get news sentiment from Alpha Vantage

        Args:
            tickers: List of ticker symbols
            use_cache: Whether to use cached data

        Returns:
            SentimentData or None
        """
        try:
            # Check cache (use first ticker as key)
            if use_cache and len(tickers) == 1:
                cached = self._get_cached_sentiment(tickers[0])
                if cached:
                    return cached

            # Fetch from Alpha Vantage
            data = self.alphavantage.get_news_sentiment(tickers)
            if not data:
                return None

            sentiment = SentimentData(
                ticker=tickers[0] if len(tickers) == 1 else ",".join(tickers),
                date=datetime.now().date(),
                sentiment_score=data["sentiment_score"],
                sentiment_label=data["sentiment_label"],
                articles_analyzed=data["articles_analyzed"],
                positive_articles=data["positive_articles"],
                negative_articles=data["negative_articles"],
                neutral_articles=data["neutral_articles"],
                average_relevance=data["average_relevance"],
                data_source="alphavantage",
                fetched_at=datetime.now()
            )

            # Cache it
            if len(tickers) == 1:
                self._cache_sentiment(sentiment)

            return sentiment

        except Exception as e:
            logger.error(f"Failed to get sentiment for {tickers}: {e}")
            return None

    # ===== MARKET DATA =====

    def get_vix(self) -> Optional[Dict[str, float]]:
        """
        Get VIX data from yfinance

        Returns:
            Dictionary with VIX metrics or None
        """
        return self.yfinance.get_vix()

    def _get_risk_free_rate(self) -> float:
        """
        Get current risk-free rate (3-month Treasury)

        Strategy:
        1. Check lookup table (refreshed daily)
        2. Fallback to Alpha Vantage API
        3. Default to 4.5%

        Returns:
            Risk-free rate as decimal, or default 0.045
        """
        try:
            # Try lookup table first (much faster!)
            rate = self.lookup.get_treasury_rate('3month', max_age_days=1)
            if rate:
                logger.debug(f"Using cached Treasury rate: {rate*100:.3f}%")
                return rate

            # Fallback to API
            logger.debug("Treasury rate not in cache, fetching from API...")
            rate = self.alphavantage.get_treasury_rate("3month")
            if rate:
                return rate

            logger.warning("Using default risk-free rate: 4.5%")
            return 0.045
        except:
            return 0.045

    # ===== CACHING HELPERS =====

    def _get_cached_snapshot(self, ticker: str, date: Optional[date]) -> Optional[TickerSnapshot]:
        """Get cached ticker snapshot"""
        try:
            if date is None:
                date = datetime.now().date()

            # DuckDB compatible timestamp comparison
            result = self.db.execute(
                """
                SELECT * FROM ticker_snapshots
                WHERE ticker = ? AND date = ?
                AND fetched_at > (CURRENT_TIMESTAMP - INTERVAL '15 minutes')
                ORDER BY fetched_at DESC LIMIT 1
                """,
                [ticker, date]
            ).fetchone()

            if result:
                return TickerSnapshot(
                    ticker=result[1],
                    date=result[2],
                    open=result[3],
                    high=result[4],
                    low=result[5],
                    close=result[6],
                    volume=result[7],
                    vwap=result[8],
                    change_percent=result[9],
                    data_source=result[10],
                    fetched_at=result[11]
                )

            return None

        except Exception as e:
            logger.debug(f"Cache lookup failed: {e}")
            return None

    def _cache_snapshot(self, snapshot: TickerSnapshot):
        """Cache ticker snapshot"""
        try:
            # Generate unique ID
            import uuid
            snapshot_id = int(uuid.uuid4().int & (1 << 63) - 1)

            self.db.execute(
                """
                INSERT INTO ticker_snapshots
                (id, ticker, date, open, high, low, close, volume, vwap, change_percent, data_source, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (ticker, date, data_source) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    vwap = EXCLUDED.vwap,
                    change_percent = EXCLUDED.change_percent,
                    fetched_at = EXCLUDED.fetched_at
                """,
                [
                    snapshot_id,
                    snapshot.ticker,
                    snapshot.date,
                    snapshot.open,
                    snapshot.high,
                    snapshot.low,
                    snapshot.close,
                    snapshot.volume,
                    snapshot.vwap,
                    snapshot.change_percent,
                    snapshot.data_source,
                    snapshot.fetched_at
                ]
            )
        except Exception as e:
            logger.debug(f"Failed to cache snapshot: {e}")

    def _get_cached_fundamentals(self, ticker: str) -> Optional[FundamentalData]:
        """Get cached fundamentals (24hr TTL)"""
        try:
            result = self.db.execute(
                """
                SELECT * FROM fundamental_data
                WHERE ticker = ?
                AND fetched_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
                ORDER BY fetched_at DESC LIMIT 1
                """,
                [ticker]
            ).fetchone()

            if result:
                return FundamentalData(
                    ticker=result[1],
                    date=result[2],
                    market_cap=result[3],
                    pe_ratio=result[4],
                    forward_pe=result[5],
                    peg_ratio=result[6],
                    price_to_book=result[7],
                    profit_margin=result[8],
                    operating_margin=result[9],
                    return_on_equity=result[10],
                    return_on_assets=result[11],
                    revenue_growth=result[12],
                    earnings_growth=result[13],
                    total_cash=result[14],
                    total_debt=result[15],
                    debt_to_equity=result[16],
                    current_ratio=result[17],
                    target_price=result[18],
                    recommendation=result[19],
                    num_analysts=result[20],
                    data_source=result[23],
                    fetched_at=result[24]
                )

            return None

        except Exception as e:
            logger.debug(f"Cache lookup failed: {e}")
            return None

    def _cache_fundamentals(self, data: FundamentalData):
        """Cache fundamental data"""
        try:
            import uuid
            data_id = int(uuid.uuid4().int & (1 << 63) - 1)

            self.db.execute(
                """
                INSERT INTO fundamental_data
                (id, ticker, date, market_cap, pe_ratio, forward_pe, peg_ratio, price_to_book,
                 profit_margin, operating_margin, return_on_equity, return_on_assets,
                 revenue_growth, earnings_growth, total_cash, total_debt, debt_to_equity,
                 current_ratio, target_price, recommendation, num_analysts, institutional_ownership,
                 insider_ownership, data_source, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (ticker, date, data_source) DO UPDATE SET
                    market_cap = EXCLUDED.market_cap,
                    pe_ratio = EXCLUDED.pe_ratio,
                    forward_pe = EXCLUDED.forward_pe,
                    peg_ratio = EXCLUDED.peg_ratio,
                    price_to_book = EXCLUDED.price_to_book,
                    profit_margin = EXCLUDED.profit_margin,
                    operating_margin = EXCLUDED.operating_margin,
                    return_on_equity = EXCLUDED.return_on_equity,
                    return_on_assets = EXCLUDED.return_on_assets,
                    revenue_growth = EXCLUDED.revenue_growth,
                    earnings_growth = EXCLUDED.earnings_growth,
                    total_cash = EXCLUDED.total_cash,
                    total_debt = EXCLUDED.total_debt,
                    debt_to_equity = EXCLUDED.debt_to_equity,
                    current_ratio = EXCLUDED.current_ratio,
                    target_price = EXCLUDED.target_price,
                    recommendation = EXCLUDED.recommendation,
                    num_analysts = EXCLUDED.num_analysts,
                    institutional_ownership = EXCLUDED.institutional_ownership,
                    insider_ownership = EXCLUDED.insider_ownership,
                    fetched_at = EXCLUDED.fetched_at
                """,
                [
                    data_id, data.ticker, data.date, data.market_cap, data.pe_ratio,
                    data.forward_pe, data.peg_ratio, data.price_to_book, data.profit_margin,
                    data.operating_margin, data.return_on_equity, data.return_on_assets,
                    data.revenue_growth, data.earnings_growth, data.total_cash, data.total_debt,
                    data.debt_to_equity, data.current_ratio, data.target_price, data.recommendation,
                    data.num_analysts, data.institutional_ownership, data.insider_ownership,
                    data.data_source, data.fetched_at
                ]
            )
        except Exception as e:
            logger.debug(f"Failed to cache fundamentals: {e}")

    def _get_cached_sentiment(self, ticker: str) -> Optional[SentimentData]:
        """Get cached sentiment (1hr TTL)"""
        try:
            result = self.db.execute(
                """
                SELECT * FROM sentiment_data
                WHERE ticker = ?
                AND fetched_at > (CURRENT_TIMESTAMP - INTERVAL '1 hour')
                ORDER BY fetched_at DESC LIMIT 1
                """,
                [ticker]
            ).fetchone()

            if result:
                return SentimentData(
                    ticker=result[1],
                    date=result[2],
                    sentiment_score=result[3],
                    sentiment_label=result[4],
                    articles_analyzed=result[5],
                    positive_articles=result[6],
                    negative_articles=result[7],
                    neutral_articles=result[8],
                    average_relevance=result[9],
                    buzz_score=result[10],
                    data_source=result[11],
                    fetched_at=result[12]
                )

            return None

        except Exception as e:
            logger.debug(f"Cache lookup failed: {e}")
            return None

    def _cache_sentiment(self, data: SentimentData):
        """Cache sentiment data"""
        try:
            import uuid
            data_id = int(uuid.uuid4().int & (1 << 63) - 1)

            self.db.execute(
                """
                INSERT INTO sentiment_data
                (id, ticker, date, sentiment_score, sentiment_label, articles_analyzed,
                 positive_articles, negative_articles, neutral_articles, average_relevance,
                 buzz_score, data_source, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (ticker, date, data_source) DO UPDATE SET
                    sentiment_score = EXCLUDED.sentiment_score,
                    sentiment_label = EXCLUDED.sentiment_label,
                    articles_analyzed = EXCLUDED.articles_analyzed,
                    positive_articles = EXCLUDED.positive_articles,
                    negative_articles = EXCLUDED.negative_articles,
                    neutral_articles = EXCLUDED.neutral_articles,
                    average_relevance = EXCLUDED.average_relevance,
                    buzz_score = EXCLUDED.buzz_score,
                    fetched_at = EXCLUDED.fetched_at
                """,
                [
                    data_id, data.ticker, data.date, data.sentiment_score, data.sentiment_label,
                    data.articles_analyzed, data.positive_articles, data.negative_articles,
                    data.neutral_articles, data.average_relevance, data.buzz_score,
                    data.data_source, data.fetched_at
                ]
            )
        except Exception as e:
            logger.debug(f"Failed to cache sentiment: {e}")

    # ===== TECHNICAL INDICATORS =====

    def get_technical_indicators(
        self,
        ticker: str,
        days: int = 200,
        verify_calculations: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get technical indicators using hybrid approach:
        - Primary: Polygon API for SMA, EMA, MACD, RSI (faster, pre-calculated)
        - Fallback: Calculate from Parquet historical data
        - Always calculate: Bollinger Bands, ATR, Stochastic, OBV, ADX (not in Polygon)

        Args:
            ticker: Stock ticker symbol
            days: Number of days of historical data for fallback/calculated indicators (default: 200)
            verify_calculations: If True, compare calculated vs API values for verification

        Returns:
            Dictionary with all technical indicators or None
        """
        try:
            result = {
                "timestamp": datetime.now().isoformat(),
                "trend": {},
                "momentum": {},
                "volatility": {},
                "volume": {},
                "trend_strength": {},
                "data_source": {}  # Track which source was used for each indicator
            }

            # Step 1: Try to get indicators from Polygon API first
            polygon_indicators = None
            try:
                polygon_indicators = self.polygon.get_technical_indicators(ticker)
                if polygon_indicators:
                    logger.debug(f"✓ Got technical indicators from Polygon API for {ticker}")
            except Exception as e:
                logger.debug(f"Polygon API indicators failed, will use fallback: {e}")

            # Step 2: Get historical data for calculated indicators (and fallback)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            df = self.parquet.get_stock_daily(
                tickers=[ticker],
                start_date=start_date,
                end_date=end_date
            )

            if df is None or df.empty:
                # If we have Polygon data, we can still proceed
                if polygon_indicators:
                    logger.warning(f"No historical data for {ticker}, using Polygon API only")
                else:
                    logger.error(f"No historical data and no Polygon data for {ticker}")
                    return None

            # Ensure required columns exist for calculations
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            has_historical_data = df is not None and not df.empty and all(col in df.columns for col in required_cols)

            # Step 3: Calculate indicators from historical data (for fallback and non-Polygon indicators)
            calculated_indicators = {}
            if has_historical_data:
                from ..analysis.technical_indicators import TechnicalIndicators
                import pandas as pd

                # Current price
                result["current_price"] = float(df['close'].iloc[-1])

                # Calculate SMA, EMA, RSI, MACD (for fallback or verification)
                calculated_indicators["sma_20"] = float(TechnicalIndicators.sma(df['close'], 20).iloc[-1])
                calculated_indicators["sma_50"] = float(TechnicalIndicators.sma(df['close'], 50).iloc[-1])
                calculated_indicators["ema_12"] = float(TechnicalIndicators.ema(df['close'], 12).iloc[-1])
                calculated_indicators["ema_26"] = float(TechnicalIndicators.ema(df['close'], 26).iloc[-1])
                calculated_indicators["rsi_14"] = float(TechnicalIndicators.rsi(df['close'], 14).iloc[-1])

                macd_line, signal_line, histogram = TechnicalIndicators.macd(df['close'], 12, 26, 9)
                calculated_indicators["macd_line"] = float(macd_line.iloc[-1])
                calculated_indicators["macd_signal"] = float(signal_line.iloc[-1])
                calculated_indicators["macd_histogram"] = float(histogram.iloc[-1])

                # Calculate Bollinger Bands (not in Polygon API)
                bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(df['close'], 20, 2.0)
                result["volatility"]["bb_upper"] = float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None
                result["volatility"]["bb_middle"] = float(bb_middle.iloc[-1]) if not pd.isna(bb_middle.iloc[-1]) else None
                result["volatility"]["bb_lower"] = float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None

                # Calculate ATR (not in Polygon API)
                atr = TechnicalIndicators.atr(df, 14)
                result["volatility"]["atr_14"] = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else None

                # Calculate Stochastic (not in Polygon API)
                stoch_k, stoch_d = TechnicalIndicators.stochastic(df, 14, 3, 3)
                result["momentum"]["stochastic_k"] = float(stoch_k.iloc[-1]) if not pd.isna(stoch_k.iloc[-1]) else None
                result["momentum"]["stochastic_d"] = float(stoch_d.iloc[-1]) if not pd.isna(stoch_d.iloc[-1]) else None

                # Calculate OBV (not in Polygon API)
                obv = TechnicalIndicators.obv(df)
                result["volume"]["obv"] = float(obv.iloc[-1]) if not pd.isna(obv.iloc[-1]) else None

                # Calculate ADX (not in Polygon API)
                adx = TechnicalIndicators.adx(df, 14)
                result["trend_strength"]["adx_14"] = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else None

            # Step 4: Use Polygon API data when available, fallback to calculated
            # Trend indicators (SMA, EMA)
            if polygon_indicators and polygon_indicators.get("sma_20"):
                result["trend"]["sma_20"] = polygon_indicators["sma_20"]
                result["data_source"]["sma_20"] = "polygon"
            elif "sma_20" in calculated_indicators:
                result["trend"]["sma_20"] = calculated_indicators["sma_20"]
                result["data_source"]["sma_20"] = "calculated"

            if polygon_indicators and polygon_indicators.get("sma_50"):
                result["trend"]["sma_50"] = polygon_indicators["sma_50"]
                result["data_source"]["sma_50"] = "polygon"
            elif "sma_50" in calculated_indicators:
                result["trend"]["sma_50"] = calculated_indicators["sma_50"]
                result["data_source"]["sma_50"] = "calculated"

            if polygon_indicators and polygon_indicators.get("ema_12"):
                result["trend"]["ema_12"] = polygon_indicators["ema_12"]
                result["data_source"]["ema_12"] = "polygon"
            elif "ema_12" in calculated_indicators:
                result["trend"]["ema_12"] = calculated_indicators["ema_12"]
                result["data_source"]["ema_12"] = "calculated"

            if polygon_indicators and polygon_indicators.get("ema_26"):
                result["trend"]["ema_26"] = polygon_indicators["ema_26"]
                result["data_source"]["ema_26"] = "polygon"
            elif "ema_26" in calculated_indicators:
                result["trend"]["ema_26"] = calculated_indicators["ema_26"]
                result["data_source"]["ema_26"] = "calculated"

            # Momentum indicators (RSI, MACD)
            if polygon_indicators and polygon_indicators.get("rsi_14"):
                result["momentum"]["rsi_14"] = polygon_indicators["rsi_14"]
                result["data_source"]["rsi_14"] = "polygon"
            elif "rsi_14" in calculated_indicators:
                result["momentum"]["rsi_14"] = calculated_indicators["rsi_14"]
                result["data_source"]["rsi_14"] = "calculated"

            if polygon_indicators and polygon_indicators.get("macd_line"):
                result["momentum"]["macd_line"] = polygon_indicators["macd_line"]
                result["momentum"]["macd_signal"] = polygon_indicators["macd_signal"]
                result["momentum"]["macd_histogram"] = polygon_indicators["macd_histogram"]
                result["data_source"]["macd"] = "polygon"
            elif "macd_line" in calculated_indicators:
                result["momentum"]["macd_line"] = calculated_indicators["macd_line"]
                result["momentum"]["macd_signal"] = calculated_indicators["macd_signal"]
                result["momentum"]["macd_histogram"] = calculated_indicators["macd_histogram"]
                result["data_source"]["macd"] = "calculated"

            # Step 5: Verification - compare calculated vs API values
            if verify_calculations and polygon_indicators and calculated_indicators:
                verification = self._verify_indicator_calculations(polygon_indicators, calculated_indicators)
                result["verification"] = verification
                logger.info(f"Verification: {verification}")

            # Step 6: Generate trading signals
            result["signals"] = self._interpret_technical_signals(result)

            source_summary = "Polygon API" if polygon_indicators else "calculated"
            logger.info(f"✓ Retrieved technical indicators for {ticker} (primary source: {source_summary})")
            return result

        except Exception as e:
            logger.error(f"Failed to get technical indicators for {ticker}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _verify_indicator_calculations(
        self,
        polygon_data: Dict[str, float],
        calculated_data: Dict[str, float],
        tolerance_pct: float = 1.0
    ) -> Dict[str, Any]:
        """
        Verify that our calculated indicators match Polygon API values

        Args:
            polygon_data: Indicators from Polygon API
            calculated_data: Indicators calculated from historical data
            tolerance_pct: Acceptable difference percentage (default: 1%)

        Returns:
            Dictionary with verification results
        """
        verification = {
            "status": "pass",
            "differences": {},
            "tolerance_pct": tolerance_pct
        }

        indicators_to_check = ["sma_20", "sma_50", "ema_12", "ema_26", "rsi_14", "macd_line", "macd_signal", "macd_histogram"]

        for indicator in indicators_to_check:
            if indicator in polygon_data and indicator in calculated_data:
                polygon_val = polygon_data[indicator]
                calculated_val = calculated_data[indicator]

                # Calculate percentage difference
                if polygon_val != 0:
                    diff_pct = abs((calculated_val - polygon_val) / polygon_val) * 100
                else:
                    diff_pct = 0 if calculated_val == 0 else 100

                verification["differences"][indicator] = {
                    "polygon": polygon_val,
                    "calculated": calculated_val,
                    "diff_pct": diff_pct,
                    "within_tolerance": diff_pct <= tolerance_pct
                }

                if diff_pct > tolerance_pct:
                    verification["status"] = "fail"
                    logger.warning(f"Indicator {indicator} diff: {diff_pct:.2f}% (Polygon: {polygon_val:.4f}, Calculated: {calculated_val:.4f})")

        return verification

    def _interpret_technical_signals(self, indicators: Dict[str, Any]) -> Dict[str, str]:
        """
        Interpret technical indicators into trading signals

        Args:
            indicators: Dictionary of calculated indicators

        Returns:
            Dictionary of signal interpretations
        """
        signals = {}
        current_price = indicators.get("current_price")

        # RSI signal
        rsi = indicators.get("momentum", {}).get("rsi_14")
        if rsi:
            if rsi > 70:
                signals["rsi"] = "Overbought (>70)"
            elif rsi < 30:
                signals["rsi"] = "Oversold (<30)"
            else:
                signals["rsi"] = "Neutral (30-70)"

        # MACD signal
        macd_hist = indicators.get("momentum", {}).get("macd_histogram")
        if macd_hist is not None:
            if macd_hist > 0:
                signals["macd"] = "Bullish (histogram > 0)"
            else:
                signals["macd"] = "Bearish (histogram < 0)"

        # Bollinger Bands signal
        bb_upper = indicators.get("volatility", {}).get("bb_upper")
        bb_lower = indicators.get("volatility", {}).get("bb_lower")
        if current_price and bb_upper and bb_lower:
            if current_price > bb_upper:
                signals["bollinger"] = "Overbought (above upper band)"
            elif current_price < bb_lower:
                signals["bollinger"] = "Oversold (below lower band)"
            else:
                signals["bollinger"] = "Normal range"

        # Stochastic signal
        stoch_k = indicators.get("momentum", {}).get("stochastic_k")
        if stoch_k:
            if stoch_k > 80:
                signals["stochastic"] = "Overbought (>80)"
            elif stoch_k < 20:
                signals["stochastic"] = "Oversold (<20)"
            else:
                signals["stochastic"] = "Neutral (20-80)"

        # ADX trend strength
        adx = indicators.get("trend_strength", {}).get("adx_14")
        if adx:
            if adx > 25:
                signals["trend_strength"] = "Strong trend (ADX > 25)"
            elif adx > 20:
                signals["trend_strength"] = "Moderate trend (ADX 20-25)"
            else:
                signals["trend_strength"] = "Weak/No trend (ADX < 20)"

        # Moving average crossover
        sma_20 = indicators.get("trend", {}).get("sma_20")
        sma_50 = indicators.get("trend", {}).get("sma_50")
        if current_price and sma_20 and sma_50:
            if current_price > sma_20 > sma_50:
                signals["ma_trend"] = "Bullish (price > SMA20 > SMA50)"
            elif current_price < sma_20 < sma_50:
                signals["ma_trend"] = "Bearish (price < SMA20 < SMA50)"
            else:
                signals["ma_trend"] = "Mixed signals"

        return signals
