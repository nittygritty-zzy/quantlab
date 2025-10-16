"""
Comprehensive Analysis Engine

Integrates all data sources and analysis modules to provide
complete ticker and portfolio analysis.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ..data.data_manager import DataManager
from ..data.database import DatabaseManager
from ..analysis.options_analyzer import OptionsAnalyzer
from ..utils.logger import setup_logger
from ..utils.config import Config

logger = setup_logger(__name__)


class Analyzer:
    """
    Multi-source analysis engine

    Integrates:
    - Polygon API (real-time prices, options)
    - Alpha Vantage API (sentiment, treasury rates)
    - yfinance API (fundamentals, analyst data)
    - Historical Parquet data
    - Advanced Greeks calculation
    - Options chain analysis
    """

    def __init__(self, config: Config, db_manager: DatabaseManager, data_manager: DataManager):
        """
        Initialize analyzer

        Args:
            config: Configuration object
            db_manager: Database manager
            data_manager: Data manager with API access
        """
        self.config = config
        self.db = db_manager
        self.data = data_manager
        self.options_analyzer = OptionsAnalyzer(data_manager)

        logger.info("✓ Analyzer initialized with all data sources")

    def analyze_ticker(
        self,
        ticker: str,
        include_options: bool = True,
        include_fundamentals: bool = True,
        include_sentiment: bool = True,
        include_technicals: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a single ticker

        Args:
            ticker: Stock ticker symbol
            include_options: Whether to include options analysis
            include_fundamentals: Whether to include fundamental data
            include_sentiment: Whether to include sentiment analysis
            include_technicals: Whether to include technical indicators

        Returns:
            Dictionary with complete analysis
        """
        try:
            logger.info(f"🔍 Analyzing {ticker}...")

            analysis = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }

            # 1. Get current price
            price_data = self.data.get_stock_price(ticker)
            if price_data:
                analysis["price"] = {
                    "current": price_data.close,
                    "open": price_data.open,
                    "high": price_data.high,
                    "low": price_data.low,
                    "volume": price_data.volume,
                    "change_percent": price_data.change_percent,
                    "date": price_data.date.isoformat()
                }
            else:
                analysis["price"] = None
                logger.warning(f"No price data for {ticker}")

            # 2. Options analysis
            if include_options and price_data:
                logger.info(f"  Analyzing options chain...")

                call_recommendations = self.options_analyzer.analyze_itm_calls(
                    ticker=ticker,
                    min_itm_pct=5.0,
                    max_itm_pct=20.0,
                    top_n=5
                )

                put_recommendations = self.options_analyzer.analyze_itm_puts(
                    ticker=ticker,
                    min_itm_pct=5.0,
                    max_itm_pct=20.0,
                    top_n=5
                )

                analysis["options"] = {
                    "top_itm_calls": [
                        {
                            "contract_ticker": rec["contract"].contract_ticker,
                            "strike": rec["contract"].strike_price,
                            "expiration": rec["contract"].expiration_date if isinstance(rec["contract"].expiration_date, str) else rec["contract"].expiration_date.isoformat(),
                            "itm_pct": rec["contract"].itm_percentage,
                            "price": rec["contract"].last_price,
                            "open_interest": rec["contract"].open_interest,
                            "delta": rec["contract"].delta,
                            "gamma": rec["contract"].gamma,
                            "theta": rec["contract"].theta,
                            "vega": rec["contract"].vega,
                            "vanna": rec["contract"].vanna,
                            "charm": rec["contract"].charm,
                            "vomma": rec["contract"].vomma,
                            "score": rec["score"],
                            "analysis": rec["analysis"]
                        }
                        for rec in call_recommendations
                    ],
                    "top_itm_puts": [
                        {
                            "contract_ticker": rec["contract"].contract_ticker,
                            "strike": rec["contract"].strike_price,
                            "expiration": rec["contract"].expiration_date if isinstance(rec["contract"].expiration_date, str) else rec["contract"].expiration_date.isoformat(),
                            "itm_pct": rec["contract"].itm_percentage,
                            "price": rec["contract"].last_price,
                            "open_interest": rec["contract"].open_interest,
                            "delta": rec["contract"].delta,
                            "gamma": rec["contract"].gamma,
                            "theta": rec["contract"].theta,
                            "vega": rec["contract"].vega,
                            "vanna": rec["contract"].vanna,
                            "charm": rec["contract"].charm,
                            "vomma": rec["contract"].vomma,
                            "score": rec["score"],
                            "analysis": rec["analysis"]
                        }
                        for rec in put_recommendations
                    ]
                }

                logger.info(f"  ✓ Found {len(call_recommendations)} call and {len(put_recommendations)} put recommendations")
            else:
                analysis["options"] = None

            # 3. Fundamentals
            if include_fundamentals:
                logger.info(f"  Fetching fundamentals...")
                fundamentals = self.data.get_fundamentals(ticker)
                if fundamentals:
                    analysis["fundamentals"] = {
                        "market_cap": fundamentals.market_cap,
                        "pe_ratio": fundamentals.pe_ratio,
                        "forward_pe": fundamentals.forward_pe,
                        "peg_ratio": fundamentals.peg_ratio,
                        "profit_margin": fundamentals.profit_margin,
                        "return_on_equity": fundamentals.return_on_equity,
                        "revenue_growth": fundamentals.revenue_growth,
                        "debt_to_equity": fundamentals.debt_to_equity,
                        "recommendation": fundamentals.recommendation,
                        "target_price": fundamentals.target_price
                    }
                    logger.info(f"  ✓ Fundamentals retrieved")
                else:
                    analysis["fundamentals"] = None

            # 4. Sentiment
            if include_sentiment:
                logger.info(f"  Fetching news sentiment...")
                sentiment = self.data.get_sentiment([ticker])
                if sentiment:
                    analysis["sentiment"] = {
                        "score": sentiment.sentiment_score,
                        "label": sentiment.sentiment_label,
                        "articles_analyzed": sentiment.articles_analyzed,
                        "positive_articles": sentiment.positive_articles,
                        "negative_articles": sentiment.negative_articles,
                        "neutral_articles": sentiment.neutral_articles
                    }
                    logger.info(f"  ✓ Sentiment: {sentiment.sentiment_label} ({sentiment.sentiment_score:.3f})")
                else:
                    analysis["sentiment"] = None

            # 5. Market context
            logger.info(f"  Fetching market context...")
            vix_data = self.data.get_vix()
            if vix_data:
                analysis["market_context"] = {
                    "vix": vix_data["vix"],
                    "vix_5d_avg": vix_data["vix_5d_avg"]
                }
                logger.info(f"  ✓ VIX: {vix_data['vix']:.2f}")
            else:
                analysis["market_context"] = None

            # 6. Technical indicators
            if include_technicals:
                logger.info(f"  Calculating technical indicators...")
                technicals = self.data.get_technical_indicators(ticker, days=200)
                if technicals:
                    analysis["technical_indicators"] = technicals
                    logger.info(f"  ✓ Technical indicators calculated")
                else:
                    analysis["technical_indicators"] = None
            else:
                analysis["technical_indicators"] = None

            logger.info(f"✅ Analysis complete for {ticker}")
            return analysis

        except Exception as e:
            logger.error(f"Analysis failed for {ticker}: {e}")
            return {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    def analyze_portfolio(
        self,
        portfolio_id: str,
        include_options: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze all tickers in a portfolio

        Args:
            portfolio_id: Portfolio identifier
            include_options: Whether to include options analysis (can be slow)

        Returns:
            Dictionary with portfolio-wide analysis
        """
        try:
            logger.info(f"📊 Analyzing portfolio: {portfolio_id}...")

            # Get portfolio from database
            from ..core.portfolio_manager import PortfolioManager
            portfolio_mgr = PortfolioManager(self.db)

            summary = portfolio_mgr.get_portfolio_summary(portfolio_id)
            if not summary:
                return {
                    "portfolio_id": portfolio_id,
                    "status": "error",
                    "error": "Portfolio not found"
                }

            positions = summary["positions"]
            tickers = [p.ticker for p in positions]

            logger.info(f"  Analyzing {len(tickers)} positions...")

            # Analyze each ticker
            ticker_analyses = {}
            for ticker in tickers:
                logger.info(f"  → {ticker}")
                ticker_analyses[ticker] = self.analyze_ticker(
                    ticker=ticker,
                    include_options=include_options,
                    include_fundamentals=True,
                    include_sentiment=False  # Too slow for multiple tickers
                )

            # Aggregate portfolio-level metrics
            portfolio_analysis = {
                "portfolio_id": portfolio_id,
                "portfolio_name": summary["name"],
                "num_positions": len(positions),
                "tickers": tickers,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "ticker_analyses": ticker_analyses,
                "aggregate_metrics": self._calculate_portfolio_metrics(ticker_analyses, positions)
            }

            logger.info(f"✅ Portfolio analysis complete for {portfolio_id}")
            return portfolio_analysis

        except Exception as e:
            logger.error(f"Portfolio analysis failed for {portfolio_id}: {e}")
            return {
                "portfolio_id": portfolio_id,
                "status": "error",
                "error": str(e)
            }

    def _calculate_portfolio_metrics(
        self,
        ticker_analyses: Dict[str, Dict[str, Any]],
        positions: List
    ) -> Dict[str, Any]:
        """Calculate aggregate portfolio metrics"""
        try:
            # Calculate weighted average P/E
            total_weight = 0.0
            weighted_pe = 0.0
            num_with_pe = 0

            for position in positions:
                ticker = position.ticker
                if ticker in ticker_analyses:
                    analysis = ticker_analyses[ticker]
                    if analysis.get("fundamentals") and analysis["fundamentals"].get("pe_ratio"):
                        weight = position.weight if position.weight else (1.0 / len(positions))
                        weighted_pe += analysis["fundamentals"]["pe_ratio"] * weight
                        total_weight += weight
                        num_with_pe += 1

            avg_pe = weighted_pe / total_weight if total_weight > 0 else None

            # Count recommendations
            buy_count = 0
            hold_count = 0
            sell_count = 0

            for analysis in ticker_analyses.values():
                if analysis.get("fundamentals") and analysis["fundamentals"].get("recommendation"):
                    rec = analysis["fundamentals"]["recommendation"]
                    if rec in ["buy", "strong_buy"]:
                        buy_count += 1
                    elif rec in ["hold"]:
                        hold_count += 1
                    elif rec in ["sell", "strong_sell"]:
                        sell_count += 1

            return {
                "average_pe": avg_pe,
                "tickers_with_pe": num_with_pe,
                "analyst_recommendations": {
                    "buy": buy_count,
                    "hold": hold_count,
                    "sell": sell_count
                }
            }

        except Exception as e:
            logger.error(f"Failed to calculate portfolio metrics: {e}")
            return {}
