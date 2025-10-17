"""
Stock Screener Module

Provides multi-criteria stock screening capabilities:
- Technical indicators (RSI, MACD, SMA, Bollinger Bands, etc.)
- Fundamental data (P/E, revenue growth, margins, debt ratios)
- Sentiment analysis (news sentiment scores)
- Combined scoring and ranking
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..data.parquet_reader import ParquetReader
from ..data.data_manager import DataManager
from ..data.lookup_tables import LookupTableManager
from ..analysis.technical_indicators import TechnicalIndicators
from ..utils.logger import setup_logger
from ..utils.config import Config
from ..data.database import DatabaseManager

logger = setup_logger(__name__)


@dataclass
class ScreenCriteria:
    """
    Screening criteria for multi-factor stock screening

    All criteria are optional - use only what you need.
    Criteria with _min or _max are range filters.
    Criteria with specific values are exact matches.
    """

    # === TECHNICAL INDICATORS ===
    # RSI (Relative Strength Index) - momentum oscillator (0-100)
    rsi_min: Optional[float] = None        # Find oversold (e.g., 30)
    rsi_max: Optional[float] = None        # Find overbought (e.g., 70)

    # MACD signals
    macd_signal: Optional[str] = None      # 'bullish' or 'bearish'

    # Moving averages
    sma_crossover: Optional[str] = None    # 'golden' (SMA20 > SMA50), 'death' (SMA20 < SMA50)
    price_above_sma20: Optional[bool] = None   # True = price > SMA20
    price_above_sma50: Optional[bool] = None   # True = price > SMA50

    # Bollinger Bands
    bb_position: Optional[str] = None      # 'above_upper', 'below_lower', 'middle'

    # Trend strength (ADX)
    adx_min: Optional[float] = None        # Strong trend if > 25
    adx_max: Optional[float] = None

    # === FUNDAMENTAL DATA ===
    # Valuation
    pe_min: Optional[float] = None
    pe_max: Optional[float] = None
    forward_pe_min: Optional[float] = None
    forward_pe_max: Optional[float] = None
    peg_ratio_max: Optional[float] = None   # Good if < 1.0

    # Growth
    revenue_growth_min: Optional[float] = None   # As percentage (e.g., 10.0 for 10%)
    revenue_growth_max: Optional[float] = None
    earnings_growth_min: Optional[float] = None
    earnings_growth_max: Optional[float] = None

    # Profitability
    profit_margin_min: Optional[float] = None    # As percentage
    profit_margin_max: Optional[float] = None
    roe_min: Optional[float] = None              # Return on Equity
    roe_max: Optional[float] = None

    # Financial health
    debt_equity_min: Optional[float] = None
    debt_equity_max: Optional[float] = None
    current_ratio_min: Optional[float] = None    # Liquidity (> 1.0 is good)

    # Market cap
    market_cap_min: Optional[float] = None       # In billions
    market_cap_max: Optional[float] = None

    # === SENTIMENT ===
    sentiment_min: Optional[float] = None        # -1 to 1 (or 0 to 1 depending on source)
    sentiment_max: Optional[float] = None
    articles_min: Optional[int] = None           # Minimum news coverage

    # === VOLUME & LIQUIDITY ===
    volume_min: Optional[int] = None             # Daily volume
    volume_max: Optional[int] = None
    avg_volume_min: Optional[int] = None         # 20-day average volume

    # === PRICE ===
    price_min: Optional[float] = None
    price_max: Optional[float] = None

    # === ANALYST RATINGS ===
    min_analysts: Optional[int] = None           # Minimum analyst coverage
    recommendation: Optional[str] = None         # 'buy', 'hold', 'sell'

    # === SECTOR/INDUSTRY FILTERS ===
    sectors: Optional[List[str]] = None          # Filter by sectors (e.g., ['Technology', 'Healthcare'])
    industries: Optional[List[str]] = None       # Filter by industries (e.g., ['Software', 'Biotech'])
    exclude_sectors: Optional[List[str]] = None  # Exclude these sectors
    exclude_industries: Optional[List[str]] = None  # Exclude these industries


class StockScreener:
    """
    Multi-criteria stock screening engine

    Features:
    - Screen 19,000+ stocks across multiple criteria
    - Technical, fundamental, and sentiment filters
    - Parallel processing for speed
    - Scoring and ranking
    - Result persistence

    Example:
        >>> criteria = ScreenCriteria(
        ...     rsi_min=None, rsi_max=30,  # Oversold
        ...     pe_max=20,                   # Reasonable valuation
        ...     volume_min=1000000           # Liquid stocks
        ... )
        >>> screener = StockScreener(config, db, data_manager)
        >>> results = screener.screen(criteria, limit=50)
    """

    def __init__(
        self,
        config: Config,
        db: DatabaseManager,
        data_manager: DataManager,
        parquet_reader: ParquetReader
    ):
        """
        Initialize stock screener

        Args:
            config: Configuration object
            db: Database manager
            data_manager: Data manager with API access
            parquet_reader: Parquet reader for historical data
        """
        self.config = config
        self.db = db
        self.data = data_manager
        self.parquet = parquet_reader
        self.lookup = LookupTableManager(db)

        logger.info("✓ Stock screener initialized")

    def screen(
        self,
        criteria: ScreenCriteria,
        universe: Optional[List[str]] = None,
        limit: int = 100,
        workers: int = 4,
        include_score: bool = True
    ) -> pd.DataFrame:
        """
        Screen stocks based on criteria

        Args:
            criteria: Screening criteria
            universe: Optional list of tickers to screen (default: all available)
            limit: Maximum results to return
            workers: Number of parallel workers
            include_score: Whether to calculate composite scores

        Returns:
            DataFrame with columns: ticker, price, rsi, pe_ratio, sentiment, score, etc.
        """
        try:
            logger.info("🔍 Starting stock screening...")

            # Step 1: Get universe
            if universe is None:
                universe = self._get_default_universe()
                logger.info(f"  Using full universe: {len(universe)} tickers")
            else:
                logger.info(f"  Custom universe: {len(universe)} tickers")

            # Step 2: Process tickers in parallel
            results = []
            processed = 0
            skipped = 0

            logger.info(f"  Processing with {workers} workers...")

            with ThreadPoolExecutor(max_workers=workers) as executor:
                # Submit all tickers
                future_to_ticker = {
                    executor.submit(self._evaluate_ticker, ticker, criteria): ticker
                    for ticker in universe
                }

                # Collect results as they complete
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        result = future.result()
                        if result is not None:
                            results.append(result)
                            processed += 1

                            # Progress update every 100 tickers
                            if processed % 100 == 0:
                                logger.info(f"  Progress: {processed}/{len(universe)} processed, {len(results)} passed")
                        else:
                            skipped += 1
                    except Exception as e:
                        logger.debug(f"  Error processing {ticker}: {e}")
                        skipped += 1

            logger.info(f"  Completed: {processed} processed, {len(results)} passed filters, {skipped} skipped")

            # Step 3: Convert to DataFrame
            if not results:
                logger.warning("⚠️  No stocks matched criteria")
                return pd.DataFrame()

            df = pd.DataFrame(results)

            # Step 4: Calculate composite score if requested
            if include_score:
                df['score'] = self._calculate_score(df, criteria)
                df = df.sort_values('score', ascending=False)

            # Step 5: Limit results
            df = df.head(limit)

            logger.info(f"✅ Screening complete: {len(df)} results")
            return df

        except Exception as e:
            logger.error(f"Screening failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()

    def _get_default_universe(self) -> List[str]:
        """Get default screening universe (only stocks with recent data)"""
        try:
            # Get only tickers with recent data (much faster than all tickers)
            # Requires at least 50 rows in the last 90 days for technical indicators
            tickers = self.parquet.get_tickers_with_recent_data(days_back=90, min_rows=50)

            if not tickers:
                logger.warning("Could not load tickers with recent data, using fallback list")
                tickers = self._get_fallback_universe()

            return tickers

        except Exception as e:
            logger.error(f"Failed to get universe: {e}")
            return self._get_fallback_universe()

    def _get_fallback_universe(self) -> List[str]:
        """Fallback list of top liquid US stocks"""
        return [
            # Tech
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC", "NFLX",
            "CRM", "ADBE", "ORCL", "CSCO", "AVGO", "TXN", "QCOM", "NOW", "INTU", "IBM",
            # Finance
            "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "USB",
            # Healthcare
            "JNJ", "UNH", "PFE", "ABBV", "TMO", "LLY", "MRK", "ABT", "DHR", "BMY",
            # Consumer
            "WMT", "HD", "MCD", "DIS", "NKE", "SBUX", "TGT", "LOW", "COST", "PG",
            # Energy
            "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL",
            # Industrial
            "BA", "CAT", "GE", "MMM", "HON", "UPS", "RTX", "LMT", "DE", "UNP"
        ]

    def _evaluate_ticker(
        self,
        ticker: str,
        criteria: ScreenCriteria
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate a single ticker against criteria

        Returns:
            Dictionary with ticker data if passes filters, None otherwise
        """
        try:
            # Get recent historical data for technical indicators
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)  # 90 days for indicators

            df = self.parquet.get_stock_daily(
                tickers=[ticker],
                start_date=start_date,
                end_date=end_date
            )

            if df is None or df.empty or len(df) < 50:
                # Not enough data for technical indicators
                return None

            # Initialize result
            result = {'ticker': ticker}

            # === SECTOR/INDUSTRY FILTERING (early exit for performance) ===
            if self._has_sector_industry_criteria(criteria):
                company_info = self.lookup.get_company_info(ticker)
                if company_info:
                    sector = company_info.get('sector')
                    industry = company_info.get('industry')

                    # Check sector filters
                    if criteria.sectors and sector not in criteria.sectors:
                        return None
                    if criteria.exclude_sectors and sector in criteria.exclude_sectors:
                        return None

                    # Check industry filters
                    if criteria.industries and industry not in criteria.industries:
                        return None
                    if criteria.exclude_industries and industry in criteria.exclude_industries:
                        return None
                else:
                    # If sector/industry required but not available, skip
                    if criteria.sectors or criteria.industries:
                        return None

            # === PRICE DATA ===
            current_price = float(df['close'].iloc[-1])
            result['price'] = current_price
            result['volume'] = int(df['volume'].iloc[-1])

            # Price filter
            if criteria.price_min and current_price < criteria.price_min:
                return None
            if criteria.price_max and current_price > criteria.price_max:
                return None

            # Volume filter
            if criteria.volume_min and result['volume'] < criteria.volume_min:
                return None
            if criteria.volume_max and result['volume'] > criteria.volume_max:
                return None

            # === TECHNICAL INDICATORS ===
            if self._has_technical_criteria(criteria):
                tech_data = self._calculate_technicals(df, current_price)

                # Apply technical filters
                if not self._check_technical_filters(tech_data, criteria):
                    return None

                # Add technical data to result
                result.update(tech_data)

            # === FUNDAMENTALS ===
            if self._has_fundamental_criteria(criteria):
                fundamentals = self.data.get_fundamentals(ticker)

                if fundamentals:
                    fund_data = self._extract_fundamental_data(fundamentals)

                    # Apply fundamental filters
                    if not self._check_fundamental_filters(fund_data, criteria):
                        return None

                    # Add fundamental data to result
                    result.update(fund_data)
                else:
                    # If fundamentals required but not available, skip
                    if self._requires_fundamentals(criteria):
                        return None

            # === SENTIMENT ===
            if self._has_sentiment_criteria(criteria):
                sentiment = self.data.get_sentiment([ticker])

                if sentiment:
                    sent_data = {
                        'sentiment_score': sentiment.sentiment_score,
                        'sentiment_label': sentiment.sentiment_label,
                        'articles_count': sentiment.articles_analyzed
                    }

                    # Apply sentiment filters
                    if not self._check_sentiment_filters(sent_data, criteria):
                        return None

                    result.update(sent_data)
                else:
                    # If sentiment required but not available, skip
                    if criteria.sentiment_min or criteria.articles_min:
                        return None

            return result

        except Exception as e:
            logger.debug(f"Error evaluating {ticker}: {e}")
            return None

    def _has_sector_industry_criteria(self, criteria: ScreenCriteria) -> bool:
        """Check if any sector/industry criteria are specified"""
        return any([
            criteria.sectors, criteria.industries,
            criteria.exclude_sectors, criteria.exclude_industries
        ])

    def _has_technical_criteria(self, criteria: ScreenCriteria) -> bool:
        """Check if any technical criteria are specified"""
        return any([
            criteria.rsi_min, criteria.rsi_max,
            criteria.macd_signal,
            criteria.sma_crossover,
            criteria.price_above_sma20, criteria.price_above_sma50,
            criteria.bb_position,
            criteria.adx_min, criteria.adx_max
        ])

    def _has_fundamental_criteria(self, criteria: ScreenCriteria) -> bool:
        """Check if any fundamental criteria are specified"""
        return any([
            criteria.pe_min, criteria.pe_max,
            criteria.forward_pe_min, criteria.forward_pe_max,
            criteria.peg_ratio_max,
            criteria.revenue_growth_min, criteria.revenue_growth_max,
            criteria.profit_margin_min, criteria.profit_margin_max,
            criteria.roe_min, criteria.roe_max,
            criteria.debt_equity_min, criteria.debt_equity_max,
            criteria.market_cap_min, criteria.market_cap_max,
            criteria.min_analysts, criteria.recommendation
        ])

    def _has_sentiment_criteria(self, criteria: ScreenCriteria) -> bool:
        """Check if any sentiment criteria are specified"""
        return any([
            criteria.sentiment_min, criteria.sentiment_max,
            criteria.articles_min
        ])

    def _requires_fundamentals(self, criteria: ScreenCriteria) -> bool:
        """Check if fundamentals are strictly required (not just optional)"""
        # If min values are set, they're required
        return any([
            criteria.pe_min, criteria.revenue_growth_min,
            criteria.profit_margin_min, criteria.roe_min,
            criteria.market_cap_min, criteria.min_analysts
        ])

    def _calculate_technicals(self, df: pd.DataFrame, current_price: float) -> Dict[str, Any]:
        """Calculate technical indicators"""
        result = {}

        try:
            # RSI
            rsi = TechnicalIndicators.rsi(df['close'], 14)
            result['rsi'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None

            # MACD
            macd_line, signal_line, histogram = TechnicalIndicators.macd(df['close'])
            result['macd_line'] = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
            result['macd_signal'] = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
            result['macd_histogram'] = float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None

            # Moving averages
            sma_20 = TechnicalIndicators.sma(df['close'], 20)
            sma_50 = TechnicalIndicators.sma(df['close'], 50)
            result['sma_20'] = float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None
            result['sma_50'] = float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else None

            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(df['close'], 20, 2.0)
            result['bb_upper'] = float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None
            result['bb_lower'] = float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None

            # ADX
            adx = TechnicalIndicators.adx(df, 14)
            result['adx'] = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else None

            return result

        except Exception as e:
            logger.debug(f"Error calculating technicals: {e}")
            return result

    def _check_technical_filters(self, tech_data: Dict[str, Any], criteria: ScreenCriteria) -> bool:
        """Check if technical data passes filters"""
        # RSI
        if criteria.rsi_min and (tech_data.get('rsi') is None or tech_data['rsi'] < criteria.rsi_min):
            return False
        if criteria.rsi_max and (tech_data.get('rsi') is None or tech_data['rsi'] > criteria.rsi_max):
            return False

        # MACD signal
        if criteria.macd_signal:
            macd_hist = tech_data.get('macd_histogram')
            if macd_hist is None:
                return False
            if criteria.macd_signal == 'bullish' and macd_hist <= 0:
                return False
            if criteria.macd_signal == 'bearish' and macd_hist >= 0:
                return False

        # SMA crossover
        if criteria.sma_crossover:
            sma_20 = tech_data.get('sma_20')
            sma_50 = tech_data.get('sma_50')
            if sma_20 is None or sma_50 is None:
                return False
            if criteria.sma_crossover == 'golden' and sma_20 <= sma_50:
                return False
            if criteria.sma_crossover == 'death' and sma_20 >= sma_50:
                return False

        # Price vs SMA
        if criteria.price_above_sma20:
            sma_20 = tech_data.get('sma_20')
            price = tech_data.get('price')
            if sma_20 is None or price is None or price <= sma_20:
                return False

        if criteria.price_above_sma50:
            sma_50 = tech_data.get('sma_50')
            price = tech_data.get('price')
            if sma_50 is None or price is None or price <= sma_50:
                return False

        # Bollinger Bands position
        if criteria.bb_position:
            bb_upper = tech_data.get('bb_upper')
            bb_lower = tech_data.get('bb_lower')
            price = tech_data.get('price')
            if bb_upper is None or bb_lower is None or price is None:
                return False
            if criteria.bb_position == 'above_upper' and price <= bb_upper:
                return False
            if criteria.bb_position == 'below_lower' and price >= bb_lower:
                return False
            if criteria.bb_position == 'middle' and (price >= bb_upper or price <= bb_lower):
                return False

        # ADX
        if criteria.adx_min and (tech_data.get('adx') is None or tech_data['adx'] < criteria.adx_min):
            return False
        if criteria.adx_max and (tech_data.get('adx') is None or tech_data['adx'] > criteria.adx_max):
            return False

        return True

    def _extract_fundamental_data(self, fundamentals) -> Dict[str, Any]:
        """Extract fundamental data into dictionary"""
        return {
            'market_cap': float(fundamentals.market_cap) / 1e9 if fundamentals.market_cap else None,  # Convert to billions
            'pe_ratio': float(fundamentals.pe_ratio) if fundamentals.pe_ratio else None,
            'forward_pe': float(fundamentals.forward_pe) if fundamentals.forward_pe else None,
            'peg_ratio': float(fundamentals.peg_ratio) if fundamentals.peg_ratio else None,
            'profit_margin': float(fundamentals.profit_margin) * 100 if fundamentals.profit_margin else None,  # As percentage
            'roe': float(fundamentals.return_on_equity) * 100 if fundamentals.return_on_equity else None,
            'revenue_growth': float(fundamentals.revenue_growth) * 100 if fundamentals.revenue_growth else None,
            'earnings_growth': float(fundamentals.earnings_growth) * 100 if fundamentals.earnings_growth else None,
            'debt_equity': float(fundamentals.debt_to_equity) if fundamentals.debt_to_equity else None,
            'current_ratio': float(fundamentals.current_ratio) if fundamentals.current_ratio else None,
            'recommendation': fundamentals.recommendation,
            'num_analysts': fundamentals.num_analysts,
            'target_price': float(fundamentals.target_price) if fundamentals.target_price else None
        }

    def _check_fundamental_filters(self, fund_data: Dict[str, Any], criteria: ScreenCriteria) -> bool:
        """Check if fundamental data passes filters"""
        # P/E ratio
        if criteria.pe_min and (fund_data.get('pe_ratio') is None or fund_data['pe_ratio'] < criteria.pe_min):
            return False
        if criteria.pe_max and (fund_data.get('pe_ratio') is None or fund_data['pe_ratio'] > criteria.pe_max):
            return False

        # Forward P/E
        if criteria.forward_pe_min and (fund_data.get('forward_pe') is None or fund_data['forward_pe'] < criteria.forward_pe_min):
            return False
        if criteria.forward_pe_max and (fund_data.get('forward_pe') is None or fund_data['forward_pe'] > criteria.forward_pe_max):
            return False

        # PEG ratio
        if criteria.peg_ratio_max and (fund_data.get('peg_ratio') is None or fund_data['peg_ratio'] > criteria.peg_ratio_max):
            return False

        # Revenue growth
        if criteria.revenue_growth_min and (fund_data.get('revenue_growth') is None or fund_data['revenue_growth'] < criteria.revenue_growth_min):
            return False
        if criteria.revenue_growth_max and (fund_data.get('revenue_growth') is None or fund_data['revenue_growth'] > criteria.revenue_growth_max):
            return False

        # Profit margin
        if criteria.profit_margin_min and (fund_data.get('profit_margin') is None or fund_data['profit_margin'] < criteria.profit_margin_min):
            return False
        if criteria.profit_margin_max and (fund_data.get('profit_margin') is None or fund_data['profit_margin'] > criteria.profit_margin_max):
            return False

        # ROE
        if criteria.roe_min and (fund_data.get('roe') is None or fund_data['roe'] < criteria.roe_min):
            return False
        if criteria.roe_max and (fund_data.get('roe') is None or fund_data['roe'] > criteria.roe_max):
            return False

        # Debt/Equity
        if criteria.debt_equity_min and (fund_data.get('debt_equity') is None or fund_data['debt_equity'] < criteria.debt_equity_min):
            return False
        if criteria.debt_equity_max and (fund_data.get('debt_equity') is None or fund_data['debt_equity'] > criteria.debt_equity_max):
            return False

        # Market cap
        if criteria.market_cap_min and (fund_data.get('market_cap') is None or fund_data['market_cap'] < criteria.market_cap_min):
            return False
        if criteria.market_cap_max and (fund_data.get('market_cap') is None or fund_data['market_cap'] > criteria.market_cap_max):
            return False

        # Analyst coverage
        if criteria.min_analysts and (fund_data.get('num_analysts') is None or fund_data['num_analysts'] < criteria.min_analysts):
            return False

        # Recommendation
        if criteria.recommendation:
            rec = fund_data.get('recommendation')
            if rec is None or rec != criteria.recommendation:
                return False

        return True

    def _check_sentiment_filters(self, sent_data: Dict[str, Any], criteria: ScreenCriteria) -> bool:
        """Check if sentiment data passes filters"""
        # Sentiment score
        if criteria.sentiment_min and (sent_data.get('sentiment_score') is None or sent_data['sentiment_score'] < criteria.sentiment_min):
            return False
        if criteria.sentiment_max and (sent_data.get('sentiment_score') is None or sent_data['sentiment_score'] > criteria.sentiment_max):
            return False

        # Article count
        if criteria.articles_min and (sent_data.get('articles_count') is None or sent_data['articles_count'] < criteria.articles_min):
            return False

        return True

    def _calculate_score(self, df: pd.DataFrame, criteria: ScreenCriteria) -> pd.Series:
        """
        Calculate composite score for each stock

        Score is 0-100 based on:
        - Technical strength (30%)
        - Fundamental quality (40%)
        - Sentiment (30%)
        """
        scores = pd.Series(index=df.index, dtype=float)

        for idx in df.index:
            row = df.loc[idx]
            score = 50.0  # Base score

            # Technical score (0-30 points)
            tech_score = 0.0
            if 'rsi' in row and pd.notna(row['rsi']):
                # Ideal RSI is 40-60
                if 40 <= row['rsi'] <= 60:
                    tech_score += 10
                elif 30 <= row['rsi'] < 40 or 60 < row['rsi'] <= 70:
                    tech_score += 5

            if 'macd_histogram' in row and pd.notna(row['macd_histogram']):
                if row['macd_histogram'] > 0:
                    tech_score += 10

            if 'adx' in row and pd.notna(row['adx']):
                if row['adx'] > 25:
                    tech_score += 10

            # Fundamental score (0-40 points)
            fund_score = 0.0
            if 'pe_ratio' in row and pd.notna(row['pe_ratio']):
                if 10 <= row['pe_ratio'] <= 25:
                    fund_score += 10
                elif 5 <= row['pe_ratio'] < 10 or 25 < row['pe_ratio'] <= 35:
                    fund_score += 5

            if 'revenue_growth' in row and pd.notna(row['revenue_growth']):
                if row['revenue_growth'] > 20:
                    fund_score += 15
                elif row['revenue_growth'] > 10:
                    fund_score += 10
                elif row['revenue_growth'] > 5:
                    fund_score += 5

            if 'profit_margin' in row and pd.notna(row['profit_margin']):
                if row['profit_margin'] > 20:
                    fund_score += 10
                elif row['profit_margin'] > 10:
                    fund_score += 5

            if 'debt_equity' in row and pd.notna(row['debt_equity']):
                if row['debt_equity'] < 1.0:
                    fund_score += 5

            # Sentiment score (0-30 points)
            sent_score = 0.0
            if 'sentiment_score' in row and pd.notna(row['sentiment_score']):
                # Normalize sentiment (assume 0-1 scale)
                sent_score = row['sentiment_score'] * 30

            # Combine scores
            total_score = score + tech_score + fund_score + sent_score
            scores.loc[idx] = min(100.0, total_score)  # Cap at 100

        return scores

    # ===== PHASE 2: ADVANCED FEATURES =====

    def screen_with_weights(
        self,
        criteria: ScreenCriteria,
        weight_technical: float = 0.3,
        weight_fundamental: float = 0.4,
        weight_sentiment: float = 0.3,
        **kwargs
    ) -> pd.DataFrame:
        """
        Screen with custom scoring weights

        Args:
            criteria: Screening criteria
            weight_technical: Weight for technical score (0-1)
            weight_fundamental: Weight for fundamental score (0-1)
            weight_sentiment: Weight for sentiment score (0-1)
            **kwargs: Additional arguments passed to screen()

        Returns:
            DataFrame with weighted scores

        Example:
            >>> # Prioritize fundamentals
            >>> screener.screen_with_weights(
            ...     criteria,
            ...     weight_technical=0.2,
            ...     weight_fundamental=0.6,
            ...     weight_sentiment=0.2
            ... )
        """
        # Normalize weights
        total_weight = weight_technical + weight_fundamental + weight_sentiment
        weight_technical /= total_weight
        weight_fundamental /= total_weight
        weight_sentiment /= total_weight

        logger.info(f"Weighted screening: tech={weight_technical:.2f}, fund={weight_fundamental:.2f}, sent={weight_sentiment:.2f}")

        # Run standard screen
        results = self.screen(criteria, include_score=False, **kwargs)

        if results.empty:
            return results

        # Calculate weighted scores
        results['score'] = self._calculate_weighted_score(
            results,
            weight_technical,
            weight_fundamental,
            weight_sentiment
        )

        # Sort by score
        results = results.sort_values('score', ascending=False)

        return results

    def _calculate_weighted_score(
        self,
        df: pd.DataFrame,
        weight_tech: float,
        weight_fund: float,
        weight_sent: float
    ) -> pd.Series:
        """Calculate weighted composite score"""
        scores = pd.Series(index=df.index, dtype=float)

        for idx in df.index:
            row = df.loc[idx]

            # Technical component (0-100)
            tech_score = 0.0
            tech_count = 0

            if 'rsi' in row and pd.notna(row['rsi']):
                if 40 <= row['rsi'] <= 60:
                    tech_score += 100
                elif 30 <= row['rsi'] < 40 or 60 < row['rsi'] <= 70:
                    tech_score += 50
                tech_count += 1

            if 'macd_histogram' in row and pd.notna(row['macd_histogram']):
                if row['macd_histogram'] > 0:
                    tech_score += 100
                tech_count += 1

            if 'adx' in row and pd.notna(row['adx']):
                if row['adx'] > 25:
                    tech_score += 100
                elif row['adx'] > 20:
                    tech_score += 50
                tech_count += 1

            tech_final = (tech_score / max(tech_count, 1)) if tech_count > 0 else 50

            # Fundamental component (0-100)
            fund_score = 0.0
            fund_count = 0

            if 'pe_ratio' in row and pd.notna(row['pe_ratio']):
                if 10 <= row['pe_ratio'] <= 25:
                    fund_score += 100
                elif 5 <= row['pe_ratio'] < 10 or 25 < row['pe_ratio'] <= 35:
                    fund_score += 50
                fund_count += 1

            if 'revenue_growth' in row and pd.notna(row['revenue_growth']):
                if row['revenue_growth'] > 20:
                    fund_score += 100
                elif row['revenue_growth'] > 10:
                    fund_score += 66
                elif row['revenue_growth'] > 5:
                    fund_score += 33
                fund_count += 1

            if 'profit_margin' in row and pd.notna(row['profit_margin']):
                if row['profit_margin'] > 20:
                    fund_score += 100
                elif row['profit_margin'] > 10:
                    fund_score += 50
                fund_count += 1

            if 'debt_equity' in row and pd.notna(row['debt_equity']):
                if row['debt_equity'] < 0.5:
                    fund_score += 100
                elif row['debt_equity'] < 1.0:
                    fund_score += 66
                elif row['debt_equity'] < 2.0:
                    fund_score += 33
                fund_count += 1

            fund_final = (fund_score / max(fund_count, 1)) if fund_count > 0 else 50

            # Sentiment component (0-100)
            sent_final = 50.0
            if 'sentiment_score' in row and pd.notna(row['sentiment_score']):
                # Assume sentiment is 0-1 scale
                sent_final = row['sentiment_score'] * 100

            # Weighted combination
            total_score = (
                tech_final * weight_tech +
                fund_final * weight_fund +
                sent_final * weight_sent
            )

            scores.loc[idx] = total_score

        return scores

    def find_similar_to_portfolio(
        self,
        portfolio_id: str,
        limit: int = 20,
        min_score: float = 60.0
    ) -> pd.DataFrame:
        """
        Find stocks similar to an existing portfolio

        Args:
            portfolio_id: Portfolio identifier
            limit: Maximum results
            min_score: Minimum similarity score (0-100)

        Returns:
            DataFrame with similar stocks and similarity scores

        Example:
            >>> screener.find_similar_to_portfolio("tech_giants", limit=10)
        """
        try:
            logger.info(f"Finding stocks similar to portfolio: {portfolio_id}")

            # Get portfolio tickers
            from ..core.portfolio_manager import PortfolioManager
            portfolio_mgr = PortfolioManager(self.db)

            summary = portfolio_mgr.get_portfolio_summary(portfolio_id)
            if not summary:
                logger.error(f"Portfolio not found: {portfolio_id}")
                return pd.DataFrame()

            portfolio_tickers = [p.ticker for p in summary["positions"]]
            logger.info(f"  Portfolio has {len(portfolio_tickers)} stocks")

            # Get characteristics of portfolio stocks
            portfolio_chars = self._get_portfolio_characteristics(portfolio_tickers)

            # Screen for similar stocks (excluding portfolio stocks)
            criteria = self._create_similarity_criteria(portfolio_chars)

            # Get full universe and exclude portfolio stocks
            universe = self._get_default_universe()
            universe = [t for t in universe if t not in portfolio_tickers]

            logger.info(f"  Screening {len(universe)} candidates...")

            results = self.screen(criteria, universe=universe, limit=limit * 2, include_score=False)

            if results.empty:
                return results

            # Calculate similarity scores
            results['similarity_score'] = self._calculate_similarity_scores(results, portfolio_chars)

            # Filter by minimum score
            results = results[results['similarity_score'] >= min_score]

            # Sort and limit
            results = results.sort_values('similarity_score', ascending=False).head(limit)

            logger.info(f"✅ Found {len(results)} similar stocks")

            return results

        except Exception as e:
            logger.error(f"Failed to find similar stocks: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()

    def _get_portfolio_characteristics(self, tickers: List[str]) -> Dict[str, Any]:
        """Get average characteristics of portfolio stocks"""
        chars = {
            'avg_rsi': [],
            'avg_pe': [],
            'avg_revenue_growth': [],
            'avg_profit_margin': [],
            'avg_market_cap': []
        }

        for ticker in tickers:
            # Get technical data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)

            df = self.parquet.get_stock_daily([ticker], start_date, end_date)

            if df is not None and not df.empty and len(df) >= 50:
                rsi = TechnicalIndicators.rsi(df['close'], 14)
                if not pd.isna(rsi.iloc[-1]):
                    chars['avg_rsi'].append(float(rsi.iloc[-1]))

            # Get fundamentals
            fundamentals = self.data.get_fundamentals(ticker)
            if fundamentals:
                if fundamentals.pe_ratio:
                    chars['avg_pe'].append(float(fundamentals.pe_ratio))
                if fundamentals.revenue_growth:
                    chars['avg_revenue_growth'].append(float(fundamentals.revenue_growth) * 100)
                if fundamentals.profit_margin:
                    chars['avg_profit_margin'].append(float(fundamentals.profit_margin) * 100)
                if fundamentals.market_cap:
                    chars['avg_market_cap'].append(float(fundamentals.market_cap) / 1e9)

        # Calculate averages
        return {
            'avg_rsi': np.mean(chars['avg_rsi']) if chars['avg_rsi'] else None,
            'avg_pe': np.mean(chars['avg_pe']) if chars['avg_pe'] else None,
            'avg_revenue_growth': np.mean(chars['avg_revenue_growth']) if chars['avg_revenue_growth'] else None,
            'avg_profit_margin': np.mean(chars['avg_profit_margin']) if chars['avg_profit_margin'] else None,
            'avg_market_cap': np.mean(chars['avg_market_cap']) if chars['avg_market_cap'] else None
        }

    def _create_similarity_criteria(self, portfolio_chars: Dict[str, Any]) -> ScreenCriteria:
        """Create screening criteria based on portfolio characteristics"""
        criteria = ScreenCriteria()

        # Set ranges (±20% of portfolio average)
        if portfolio_chars['avg_rsi']:
            criteria.rsi_min = max(0, portfolio_chars['avg_rsi'] * 0.8)
            criteria.rsi_max = min(100, portfolio_chars['avg_rsi'] * 1.2)

        if portfolio_chars['avg_pe']:
            criteria.pe_min = max(0, portfolio_chars['avg_pe'] * 0.7)
            criteria.pe_max = portfolio_chars['avg_pe'] * 1.3

        if portfolio_chars['avg_revenue_growth']:
            criteria.revenue_growth_min = max(0, portfolio_chars['avg_revenue_growth'] * 0.5)

        if portfolio_chars['avg_profit_margin']:
            criteria.profit_margin_min = max(0, portfolio_chars['avg_profit_margin'] * 0.7)

        if portfolio_chars['avg_market_cap']:
            criteria.market_cap_min = portfolio_chars['avg_market_cap'] * 0.3
            criteria.market_cap_max = portfolio_chars['avg_market_cap'] * 3.0

        return criteria

    def _calculate_similarity_scores(
        self,
        df: pd.DataFrame,
        portfolio_chars: Dict[str, Any]
    ) -> pd.Series:
        """Calculate similarity score (0-100) compared to portfolio"""
        scores = pd.Series(index=df.index, dtype=float)

        for idx in df.index:
            row = df.loc[idx]
            similarity = 0.0
            count = 0

            # RSI similarity
            if 'rsi' in row and pd.notna(row['rsi']) and portfolio_chars['avg_rsi']:
                diff = abs(row['rsi'] - portfolio_chars['avg_rsi'])
                score = max(0, 100 - (diff * 2))  # 2% RSI diff = 2 points off
                similarity += score
                count += 1

            # P/E similarity
            if 'pe_ratio' in row and pd.notna(row['pe_ratio']) and portfolio_chars['avg_pe']:
                diff_pct = abs(row['pe_ratio'] - portfolio_chars['avg_pe']) / portfolio_chars['avg_pe']
                score = max(0, 100 - (diff_pct * 100))
                similarity += score
                count += 1

            # Revenue growth similarity
            if 'revenue_growth' in row and pd.notna(row['revenue_growth']) and portfolio_chars['avg_revenue_growth']:
                diff = abs(row['revenue_growth'] - portfolio_chars['avg_revenue_growth'])
                score = max(0, 100 - diff)
                similarity += score
                count += 1

            # Profit margin similarity
            if 'profit_margin' in row and pd.notna(row['profit_margin']) and portfolio_chars['avg_profit_margin']:
                diff = abs(row['profit_margin'] - portfolio_chars['avg_profit_margin'])
                score = max(0, 100 - diff)
                similarity += score
                count += 1

            # Market cap similarity (log scale)
            if 'market_cap' in row and pd.notna(row['market_cap']) and portfolio_chars['avg_market_cap']:
                if row['market_cap'] > 0:
                    ratio = row['market_cap'] / portfolio_chars['avg_market_cap']
                    log_diff = abs(np.log10(ratio))
                    score = max(0, 100 - (log_diff * 50))
                    similarity += score
                    count += 1

            scores.loc[idx] = (similarity / count) if count > 0 else 0

        return scores

    def compare_screens(
        self,
        screen1_results: pd.DataFrame,
        screen2_results: pd.DataFrame,
        screen1_name: str = "Screen 1",
        screen2_name: str = "Screen 2"
    ) -> Dict[str, Any]:
        """
        Compare two screening results

        Args:
            screen1_results: First screen results
            screen2_results: Second screen results
            screen1_name: Name for first screen
            screen2_name: Name for second screen

        Returns:
            Dictionary with comparison statistics

        Example:
            >>> results1 = screener.screen(criteria1)
            >>> results2 = screener.screen(criteria2)
            >>> comparison = screener.compare_screens(results1, results2)
        """
        tickers1 = set(screen1_results['ticker'].tolist()) if not screen1_results.empty else set()
        tickers2 = set(screen2_results['ticker'].tolist()) if not screen2_results.empty else set()

        overlap = tickers1 & tickers2
        only_in_1 = tickers1 - tickers2
        only_in_2 = tickers2 - tickers1

        comparison = {
            'screen1': {
                'name': screen1_name,
                'count': len(tickers1),
                'tickers': sorted(list(tickers1))
            },
            'screen2': {
                'name': screen2_name,
                'count': len(tickers2),
                'tickers': sorted(list(tickers2))
            },
            'overlap': {
                'count': len(overlap),
                'tickers': sorted(list(overlap)),
                'percentage': (len(overlap) / min(len(tickers1), len(tickers2)) * 100) if tickers1 and tickers2 else 0
            },
            'only_in_screen1': {
                'count': len(only_in_1),
                'tickers': sorted(list(only_in_1))
            },
            'only_in_screen2': {
                'count': len(only_in_2),
                'tickers': sorted(list(only_in_2))
            }
        }

        logger.info(f"Screen comparison:")
        logger.info(f"  {screen1_name}: {len(tickers1)} stocks")
        logger.info(f"  {screen2_name}: {len(tickers2)} stocks")
        logger.info(f"  Overlap: {len(overlap)} stocks ({comparison['overlap']['percentage']:.1f}%)")

        return comparison
