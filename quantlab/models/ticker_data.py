"""
Ticker and options data models
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class TickerSnapshot:
    """Stock snapshot data"""
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    change_percent: Optional[float] = None
    data_source: Optional[str] = None  # 'polygon', 'parquet', etc.
    fetched_at: Optional[datetime] = None


@dataclass
class OptionContract:
    """Options contract data with Greeks"""
    contract_ticker: str
    underlying_ticker: str
    strike_price: float
    expiration_date: date
    option_type: str  # 'call' or 'put'

    # Pricing
    bid: Optional[float] = None
    ask: Optional[float] = None
    last_price: Optional[float] = None
    mark: Optional[float] = None

    # Volume and interest
    volume: Optional[int] = None
    open_interest: Optional[int] = None

    # Volatility
    implied_volatility: Optional[float] = None

    # First-order Greeks
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None

    # Advanced Greeks
    vanna: Optional[float] = None
    charm: Optional[float] = None
    vomma: Optional[float] = None

    # Moneyness
    itm_percentage: Optional[float] = None  # % in-the-money

    # Metadata
    data_source: Optional[str] = None
    fetched_at: Optional[datetime] = None


@dataclass
class FundamentalData:
    """Fundamental data for a ticker"""
    ticker: str
    date: date

    # Financial metrics
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None

    # Profitability
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None

    # Growth
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None

    # Balance sheet
    total_cash: Optional[float] = None
    total_debt: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None

    # Analyst data
    target_price: Optional[float] = None
    recommendation: Optional[str] = None  # 'buy', 'hold', 'sell'
    num_analysts: Optional[int] = None

    # Institutional
    institutional_ownership: Optional[float] = None  # Percentage
    insider_ownership: Optional[float] = None

    # Metadata
    data_source: Optional[str] = None
    fetched_at: Optional[datetime] = None


@dataclass
class SentimentData:
    """News sentiment data"""
    ticker: str
    date: date

    # Sentiment scores
    sentiment_score: Optional[float] = None  # -1.0 to +1.0
    sentiment_label: Optional[str] = None  # 'bearish', 'neutral', 'bullish'

    # Article metrics
    articles_analyzed: Optional[int] = None
    positive_articles: Optional[int] = None
    negative_articles: Optional[int] = None
    neutral_articles: Optional[int] = None

    # Aggregated scores
    average_relevance: Optional[float] = None
    buzz_score: Optional[float] = None  # Volume of mentions

    # Metadata
    data_source: Optional[str] = None
    fetched_at: Optional[datetime] = None
