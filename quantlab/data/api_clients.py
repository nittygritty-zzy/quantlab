"""
API client wrappers for external data sources

Provides unified interface to:
- Polygon.io (real-time quotes, options chains)
- Alpha Vantage (news sentiment, treasury rates)
- yfinance (fundamentals, analyst data)
"""

import time
import requests
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from polygon import RESTClient as PolygonRESTClient
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, requests_per_minute: int):
        """
        Initialize rate limiter

        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0.0

    def wait_if_needed(self):
        """Wait if necessary to respect rate limit"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()


class PolygonClient:
    """
    Wrapper for Polygon.io API

    Provides:
    - Real-time stock quotes
    - Options chains
    - Historical OHLCV data
    - Company details
    - Technical indicators (SMA, EMA, MACD, RSI)
    """

    def __init__(self, api_key: str, rate_limit: int = 10000):
        """
        Initialize Polygon client

        Args:
            api_key: Polygon API key
            rate_limit: Requests per minute (default: 10000 for unlimited Starter plan)
        """
        self.client = PolygonRESTClient(api_key)
        self.rate_limiter = RateLimiter(rate_limit)
        self.api_key = api_key
        logger.info("✓ Polygon client initialized")

    def get_stock_snapshot(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get current stock snapshot

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with price data or None
        """
        try:
            # No rate limiting for unlimited Polygon plan
            snapshot = self.client.get_snapshot_ticker("stocks", ticker)

            if not snapshot or not snapshot.day:
                logger.warning(f"No snapshot data for {ticker}")
                return None

            return {
                "ticker": ticker,
                "price": snapshot.day.close,
                "open": snapshot.day.open,
                "high": snapshot.day.high,
                "low": snapshot.day.low,
                "volume": snapshot.day.volume,
                "vwap": snapshot.day.vwap if hasattr(snapshot.day, 'vwap') else None,
                "change_percent": snapshot.todaysChangePerc if hasattr(snapshot, 'todaysChangePerc') else None,
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Failed to get snapshot for {ticker}: {e}")
            return None

    def _fetch_option_snapshot(self, ticker: str, contract) -> Optional[Dict[str, Any]]:
        """Fetch single option snapshot (for parallel execution)"""
        try:
            snapshot = self.client.get_snapshot_option(ticker, contract.ticker)

            option_data = {
                "contract_ticker": contract.ticker,
                "underlying_ticker": ticker,
                "strike_price": contract.strike_price,
                "expiration_date": contract.expiration_date,
                "option_type": contract.contract_type,
            }

            # Add pricing and Greeks from snapshot
            if snapshot and snapshot.details:
                details = snapshot.details
                option_data.update({
                    "bid": details.bid if hasattr(details, 'bid') else None,
                    "ask": details.ask if hasattr(details, 'ask') else None,
                    "last_price": details.last_price if hasattr(details, 'last_price') else None,
                    "volume": details.volume if hasattr(details, 'volume') else None,
                    "open_interest": details.open_interest if hasattr(details, 'open_interest') else None,
                })

            if snapshot and snapshot.greeks:
                greeks = snapshot.greeks
                option_data.update({
                    "delta": greeks.delta if hasattr(greeks, 'delta') else None,
                    "gamma": greeks.gamma if hasattr(greeks, 'gamma') else None,
                    "theta": greeks.theta if hasattr(greeks, 'theta') else None,
                    "vega": greeks.vega if hasattr(greeks, 'vega') else None,
                })

            if snapshot and snapshot.implied_volatility:
                option_data["implied_volatility"] = snapshot.implied_volatility

            return option_data

        except Exception as e:
            logger.debug(f"Failed to get snapshot for {contract.ticker}: {e}")
            return None

    def get_options_chain(
        self,
        ticker: str,
        expiration_date: Optional[date] = None,
        contract_type: Optional[str] = None,
        max_workers: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get options chain for a ticker (parallel fetching)

        Args:
            ticker: Underlying ticker symbol
            expiration_date: Optional specific expiration date
            contract_type: Optional 'call' or 'put' filter
            max_workers: Number of parallel threads (default: 50 for unlimited API)

        Returns:
            List of option contracts
        """
        try:
            # Get options contracts list
            contracts = list(self.client.list_options_contracts(
                underlying_ticker=ticker,
                expiration_date=expiration_date.isoformat() if expiration_date else None,
                contract_type=contract_type,
                limit=1000
            ))

            logger.info(f"Fetching {len(contracts)} option contracts in parallel with {max_workers} workers...")

            options = []

            # Fetch snapshots in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all fetch tasks
                future_to_contract = {
                    executor.submit(self._fetch_option_snapshot, ticker, contract): contract
                    for contract in contracts
                }

                # Collect results as they complete
                completed = 0
                for future in as_completed(future_to_contract):
                    completed += 1
                    if completed % 50 == 0:
                        logger.info(f"Progress: {completed}/{len(contracts)} contracts fetched...")

                    result = future.result()
                    if result:
                        options.append(result)

            logger.info(f"✓ Retrieved {len(options)} option contracts for {ticker} (parallel)")
            return options

        except Exception as e:
            logger.error(f"Failed to get options chain for {ticker}: {e}")
            return []

    def get_market_holidays(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[str]:
        """
        Get market holidays from Polygon API

        Args:
            start_date: Start date in YYYY-MM-DD format (default: current year)
            end_date: End date in YYYY-MM-DD format (default: next year)

        Returns:
            List of holiday dates in YYYY-MM-DD format
        """
        try:
            # Default to current year through next year if not specified
            if not start_date:
                start_date = f"{datetime.now().year}-01-01"
            if not end_date:
                end_date = f"{datetime.now().year + 1}-12-31"

            # Use the marketstatus endpoint to get market holidays
            url = f"https://api.polygon.io/v1/marketstatus/upcoming"
            params = {"apiKey": self.api_key}

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            holidays = []
            if data and isinstance(data, list):
                for item in data:
                    if item.get('status') == 'closed' and item.get('date'):
                        holidays.append(item['date'])

            logger.info(f"✓ Retrieved {len(holidays)} market holidays from Polygon")
            return holidays

        except Exception as e:
            logger.warning(f"Failed to get market holidays from Polygon: {e}, using default US holidays")
            # Fallback to common US market holidays for current and next year
            year = datetime.now().year
            default_holidays = [
                # Current year
                f"{year}-01-01",  # New Year's Day
                f"{year}-01-15",  # MLK Day (approx)
                f"{year}-02-19",  # Presidents Day (approx)
                f"{year}-04-07",  # Good Friday (approx)
                f"{year}-05-27",  # Memorial Day (approx)
                f"{year}-06-19",  # Juneteenth
                f"{year}-07-04",  # Independence Day
                f"{year}-09-02",  # Labor Day (approx)
                f"{year}-11-28",  # Thanksgiving (approx)
                f"{year}-12-25",  # Christmas
                # Next year
                f"{year+1}-01-01",
                f"{year+1}-01-20",
                f"{year+1}-02-17",
                f"{year+1}-04-18",
                f"{year+1}-05-26",
                f"{year+1}-06-19",
                f"{year+1}-07-04",
                f"{year+1}-09-01",
                f"{year+1}-11-27",
                f"{year+1}-12-25",
            ]
            return default_holidays

    def get_intraday_aggregates(
        self,
        ticker: str,
        multiplier: int = 1,
        timespan: str = "minute",
        from_date: str = None,
        to_date: str = None,
        limit: int = 50000
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get intraday aggregate bars (minute-level data) from Polygon.

        Args:
            ticker: Stock ticker symbol
            multiplier: Size of the timespan multiplier (e.g., 1, 5, 15, 30)
            timespan: Size of the time window ('minute', 'hour')
            from_date: Start date in YYYY-MM-DD format (default: today)
            to_date: End date in YYYY-MM-DD format (default: today)
            limit: Maximum number of results (default: 50000, max: 50000)

        Returns:
            List of dictionaries with OHLCV data or None

        Example:
            >>> client.get_intraday_aggregates("AAPL", multiplier=5, timespan="minute")
            >>> # Get 1 year of 5-minute data
            >>> client.get_intraday_aggregates("AAPL", multiplier=5, from_date="2024-01-01", to_date="2025-01-01")
        """
        try:
            from datetime import datetime, timedelta
            import pandas as pd

            # Default to today if not specified
            if not from_date:
                from_date = datetime.now().date().isoformat()
            if not to_date:
                to_date = datetime.now().date().isoformat()

            logger.info(f"Fetching {multiplier}-{timespan} aggregates for {ticker} from {from_date} to {to_date}")

            # Use Polygon SDK to get aggregates
            aggs = list(self.client.list_aggs(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                from_=from_date,
                to=to_date,
                limit=limit,
                adjusted=True,
                sort="asc"
            ))

            if not aggs:
                logger.warning(f"No intraday data for {ticker}")
                return None

            # Convert to list of dicts with timestamps in ET timezone
            from datetime import timezone
            import pytz

            # US Eastern timezone
            et_tz = pytz.timezone('US/Eastern')

            result = []
            for agg in aggs:
                # Polygon returns timestamps in milliseconds (UTC)
                # Convert to ET for proper display and rangebreaks
                utc_dt = datetime.fromtimestamp(agg.timestamp / 1000, tz=timezone.utc)
                et_dt = utc_dt.astimezone(et_tz)

                # Convert to naive datetime for consistency with existing code
                # (Plotly works better with naive datetimes when using rangebreaks)
                result.append({
                    "date": et_dt.replace(tzinfo=None),  # Store as naive datetime in ET
                    "open": agg.open,
                    "high": agg.high,
                    "low": agg.low,
                    "close": agg.close,
                    "volume": agg.volume,
                    "vwap": agg.vwap if hasattr(agg, 'vwap') else None,
                    "transactions": agg.transactions if hasattr(agg, 'transactions') else None,
                })

            logger.info(f"✓ Retrieved {len(result)} {multiplier}-{timespan} bars for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Failed to get intraday aggregates for {ticker}: {e}")
            return None

    def get_technical_indicators(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get technical indicators from Polygon API

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with SMA, EMA, MACD, RSI or None
        """
        try:
            indicators = {}

            # Get SMA (20-day and 50-day)
            sma_20 = self.client.get_sma(
                ticker=ticker,
                timespan="day",
                adjusted=True,
                window=20,
                series_type="close",
                order="desc",
                limit=1,
            )
            if sma_20.values:
                indicators["sma_20"] = sma_20.values[0].value

            sma_50 = self.client.get_sma(
                ticker=ticker,
                timespan="day",
                adjusted=True,
                window=50,
                series_type="close",
                order="desc",
                limit=1,
            )
            if sma_50.values:
                indicators["sma_50"] = sma_50.values[0].value

            # Get EMA (12-day and 26-day)
            ema_12 = self.client.get_ema(
                ticker=ticker,
                timespan="day",
                adjusted=True,
                window=12,
                series_type="close",
                order="desc",
                limit=1,
            )
            if ema_12.values:
                indicators["ema_12"] = ema_12.values[0].value

            ema_26 = self.client.get_ema(
                ticker=ticker,
                timespan="day",
                adjusted=True,
                window=26,
                series_type="close",
                order="desc",
                limit=1,
            )
            if ema_26.values:
                indicators["ema_26"] = ema_26.values[0].value

            # Get RSI (14-day)
            rsi = self.client.get_rsi(
                ticker=ticker,
                timespan="day",
                adjusted=True,
                window=14,
                series_type="close",
                order="desc",
                limit=1,
            )
            if rsi.values:
                indicators["rsi_14"] = rsi.values[0].value

            # Get MACD
            macd = self.client.get_macd(
                ticker=ticker,
                timespan="day",
                adjusted=True,
                short_window=12,
                long_window=26,
                signal_window=9,
                series_type="close",
                order="desc",
                limit=1,
            )
            if macd.values:
                macd_val = macd.values[0]
                indicators["macd_line"] = macd_val.value
                indicators["macd_signal"] = macd_val.signal
                indicators["macd_histogram"] = macd_val.histogram

            logger.info(f"✓ Retrieved technical indicators from Polygon for {ticker}")
            return indicators

        except Exception as e:
            logger.error(f"Failed to get technical indicators for {ticker}: {e}")
            return None


class AlphaVantageClient:
    """
    Wrapper for Alpha Vantage API

    Provides:
    - News sentiment analysis
    - Treasury rates
    - Economic indicators
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str, rate_limit: int = 5):
        """
        Initialize Alpha Vantage client

        Args:
            api_key: Alpha Vantage API key
            rate_limit: Requests per minute (default: 5 for free tier)
        """
        self.api_key = api_key
        self.rate_limiter = RateLimiter(rate_limit)
        logger.info("✓ Alpha Vantage client initialized")

    def get_treasury_rate(self, maturity: str = "3month") -> Optional[float]:
        """
        Get current Treasury rate

        Args:
            maturity: '3month', '2year', '5year', '10year', '30year'

        Returns:
            Treasury rate as decimal (e.g., 0.0407 for 4.07%) or None
        """
        try:
            self.rate_limiter.wait_if_needed()

            params = {
                "function": "TREASURY_YIELD",
                "interval": "daily",
                "maturity": maturity,
                "apikey": self.api_key
            }

            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if "data" in data and len(data["data"]) > 0:
                # Get most recent rate
                latest = data["data"][0]
                rate = float(latest["value"]) / 100  # Convert to decimal
                logger.info(f"✓ Treasury rate ({maturity}): {rate*100:.3f}%")
                return rate

            logger.warning("No Treasury rate data available")
            return None

        except Exception as e:
            logger.error(f"Failed to get Treasury rate: {e}")
            return None

    def get_news_sentiment(
        self,
        tickers: List[str],
        limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """
        Get news sentiment for tickers

        Args:
            tickers: List of ticker symbols
            limit: Maximum number of articles

        Returns:
            Dictionary with sentiment data or None
        """
        try:
            self.rate_limiter.wait_if_needed()

            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": ",".join(tickers),
                "limit": limit,
                "apikey": self.api_key
            }

            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if "feed" not in data:
                logger.warning("No news sentiment data available")
                return None

            articles = data["feed"]

            # Aggregate sentiment scores
            sentiment_scores = []
            relevance_scores = []

            for article in articles:
                if "overall_sentiment_score" in article:
                    sentiment_scores.append(float(article["overall_sentiment_score"]))

                # Check ticker-specific sentiment
                for ticker_sentiment in article.get("ticker_sentiment", []):
                    if ticker_sentiment.get("ticker") in tickers:
                        if "relevance_score" in ticker_sentiment:
                            relevance_scores.append(float(ticker_sentiment["relevance_score"]))

            if not sentiment_scores:
                logger.warning("No sentiment scores found")
                return None

            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0

            # Classify sentiment
            if avg_sentiment > 0.15:
                label = "bullish"
            elif avg_sentiment < -0.15:
                label = "bearish"
            else:
                label = "neutral"

            result = {
                "sentiment_score": avg_sentiment,
                "sentiment_label": label,
                "articles_analyzed": len(articles),
                "average_relevance": avg_relevance,
                "positive_articles": sum(1 for s in sentiment_scores if s > 0.15),
                "negative_articles": sum(1 for s in sentiment_scores if s < -0.15),
                "neutral_articles": sum(1 for s in sentiment_scores if -0.15 <= s <= 0.15),
            }

            logger.info(f"✓ Analyzed {len(articles)} articles: {label} ({avg_sentiment:.3f})")
            return result

        except Exception as e:
            logger.error(f"Failed to get news sentiment: {e}")
            return None


class YFinanceClient:
    """
    Wrapper for yfinance library

    Provides:
    - VIX data
    - Fundamental data
    - Analyst recommendations
    - Institutional holdings
    """

    def __init__(self):
        """Initialize yfinance client"""
        logger.info("✓ yfinance client initialized")

    def get_vix(self) -> Optional[Dict[str, float]]:
        """
        Get current VIX data

        Returns:
            Dictionary with VIX metrics or None
        """
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="5d")

            if hist.empty:
                logger.warning("No VIX data available")
                return None

            current_vix = hist['Close'].iloc[-1]
            avg_vix_5d = hist['Close'].mean()

            result = {
                "vix": current_vix,
                "vix_5d_avg": avg_vix_5d,
                "timestamp": datetime.now()
            }

            logger.info(f"✓ VIX: {current_vix:.2f} (5d avg: {avg_vix_5d:.2f})")
            return result

        except Exception as e:
            logger.error(f"Failed to get VIX data: {e}")
            return None

    def get_fundamentals(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get fundamental data for a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with fundamental metrics or None
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info:
                logger.warning(f"No fundamental data for {ticker}")
                return None

            result = {
                "ticker": ticker,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "price_to_book": info.get("priceToBook"),
                "profit_margin": info.get("profitMargins"),
                "operating_margin": info.get("operatingMargins"),
                "return_on_equity": info.get("returnOnEquity"),
                "return_on_assets": info.get("returnOnAssets"),
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "total_cash": info.get("totalCash"),
                "total_debt": info.get("totalDebt"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "target_price": info.get("targetMeanPrice"),
                "recommendation": info.get("recommendationKey"),
                "num_analysts": info.get("numberOfAnalystOpinions"),
                "timestamp": datetime.now()
            }

            logger.info(f"✓ Retrieved fundamentals for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Failed to get fundamentals for {ticker}: {e}")
            return None

    def get_institutional_holders(self, ticker: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get institutional holders for a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            List of institutional holders or None
        """
        try:
            stock = yf.Ticker(ticker)
            holders = stock.institutional_holders

            if holders is None or holders.empty:
                logger.warning(f"No institutional holder data for {ticker}")
                return None

            result = []
            for _, row in holders.iterrows():
                result.append({
                    "holder": row.get("Holder"),
                    "shares": row.get("Shares"),
                    "date_reported": row.get("Date Reported"),
                    "percent_out": row.get("% Out"),
                    "value": row.get("Value")
                })

            logger.info(f"✓ Retrieved {len(result)} institutional holders for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Failed to get institutional holders for {ticker}: {e}")
            return None
