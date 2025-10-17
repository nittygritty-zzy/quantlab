# QuantLab CLI Structure & Capabilities Exploration

**Date:** October 16, 2025
**Version:** QuantLab 0.2.1
**Status:** Complete Architecture Exploration

---

## EXECUTIVE SUMMARY

QuantLab is a **production-ready quantitative trading platform** combining portfolio management, multi-source data integration, and professional visualization. The architecture is modular and well-organized, making it ideal as a foundation for building a stock screener.

**Key Finding:** While comprehensive data querying and analysis capabilities exist, **NO dedicated screener/filter CLI command currently exists** - this is the perfect opportunity for enhancement.

---

## 1. CLI COMMANDS STRUCTURE

### Current Command Hierarchy

```
quantlab/
├── init                      # Initialize database and config
├── portfolio                 # Portfolio management
│   ├── create              # Create portfolio
│   ├── list                # List all portfolios
│   ├── show                # Show portfolio details
│   ├── add                 # Add positions
│   ├── remove              # Remove positions
│   ├── update              # Update position attributes
│   └── delete              # Delete portfolio
├── data                     # Historical data queries
│   ├── check               # Check Parquet data availability
│   ├── tickers             # List available tickers
│   ├── query               # Query OHLCV data with charts
│   ├── range               # Show date range
│   └── options-minute      # Query minute-level options (1-day delayed)
├── analyze                  # Multi-source analysis
│   ├── ticker              # Analyze single ticker (price, options, technicals)
│   └── portfolio           # Analyze all portfolio positions
├── strategy                 # Options trading strategies
│   ├── list                # List available strategies
│   ├── build               # Build specific strategy
│   ├── analyze             # Analyze saved strategy
│   └── compare             # Compare multiple strategies
├── lookup                   # Lookup table management
│   ├── init                # Initialize tables
│   ├── stats               # View statistics
│   ├── refresh             # Refresh cached data
│   ├── get                 # Get cached data
│   └── refresh-portfolio   # Refresh portfolio data
└── visualize               # Interactive charts
    ├── backtest            # Backtest performance charts
    ├── price               # Price and candlestick charts
    ├── compare             # Multi-ticker comparison
    ├── portfolio           # Portfolio allocation charts
    └── options             # Options payoff diagrams
```

**Total: 27 CLI commands across 7 subcommand groups**

---

## 2. DATA LAYER CAPABILITIES

### 2.1 Data Sources

| Source | Type | Purpose | API | Status |
|--------|------|---------|-----|--------|
| **Parquet Files** | Daily OHLCV + Options | Historical data (2020-present) | DuckDB | Active |
| **Polygon API** | Real-time, Intraday | Current prices, options chains | polygon-api-client | Integrated |
| **Alpha Vantage** | News Sentiment | Market sentiment analysis | requests | Integrated |
| **yfinance** | Fundamentals, VIX | P/E, revenue, analyst ratings | yfinance | Integrated |

### 2.2 ParquetReader (`quantlab/data/parquet_reader.py`)

**Capabilities:**
- Query stock daily data by ticker, date range
- Query options daily data (call/put filtering)
- Query minute-level options (August 2025+)
- List available tickers and date ranges
- DuckDB-powered: sub-second queries on 19,382 stocks

**Methods:**
```python
get_stock_daily(tickers, start_date, end_date, limit)
get_options_daily(underlying_tickers, start_date, end_date, option_type, limit)
get_options_minute(underlying_tickers, start_datetime, end_datetime, option_type, limit)
get_available_tickers(data_type)  # Returns 19,382+ tickers
get_date_range(data_type)         # 2020-10-16 to 2025-10-14
check_data_availability()
```

### 2.3 DataManager (`quantlab/data/data_manager.py`)

**Smart Routing Strategy:**
```
Real-time request (no date specified)
    └─→ Polygon API (current prices)

Historical request (with date)
    └─→ Parquet files (cached local data)

Fallback for missing data
    └─→ API retry with rate limiting
```

**Key Methods:**
```python
get_stock_price(ticker, date=None)           # Price data
get_intraday_prices(ticker, interval, from_date, to_date)  # 1m-1h bars
get_options_chain(ticker, expiration_date)   # Full options chain
get_fundamentals(ticker)                     # P/E, revenue, margins, etc.
get_sentiment(tickers)                       # News sentiment scores
get_vix()                                    # Market volatility index
get_technical_indicators(ticker, days=200)   # 10+ indicators
```

### 2.4 Database Layer (`quantlab/data/database.py`)

**DuckDB-backed persistent storage:**

Tables designed for screening:
- `portfolios` - Portfolio definitions
- `portfolio_positions` - Holdings with weights, cost basis, entry dates
- `ticker_snapshots` - Cached price data
- `options_analysis` - Options chain analysis with Greeks
- `fundamental_data` - **15 fundamental metrics** (P/E, ROE, debt/equity, etc.)
- `sentiment_data` - News sentiment scores
- `analysis_cache` - Cached analysis results

**Indexing for fast queries:**
- idx_positions_portfolio
- idx_snapshots_ticker
- idx_fundamental_ticker
- idx_sentiment_ticker

---

## 3. ANALYSIS CAPABILITIES

### 3.1 Analyzer (`quantlab/core/analyzer.py`)

**Multi-source Analysis Methods:**

```python
analyze_ticker(
    ticker,
    include_options=True,        # Options chain analysis
    include_fundamentals=True,   # P/E, revenue, margins
    include_sentiment=True,      # News sentiment
    include_technicals=True      # RSI, MACD, Bollinger Bands, etc.
)

analyze_portfolio(
    portfolio_id,
    include_options=False
)
```

**Returns comprehensive dictionary:**
- Price: current, open, high, low, volume, % change
- Options: ITM calls/puts with Greeks (delta, gamma, theta, vega, vanna, charm, vomma)
- Fundamentals: 10+ metrics (P/E, P/B, margins, ROE, revenue growth, debt/equity)
- Sentiment: score, label, article counts, relevance
- Technical indicators: 10+ indicators with signals
- Market context: VIX, 5-day VIX average

### 3.2 Technical Indicators (`quantlab/analysis/technical_indicators.py`)

**Implemented Indicators:**

**Trend:**
- SMA (20, 50, 200)
- EMA (12, 26)

**Momentum:**
- RSI (14)
- MACD (12/26/9)
- Stochastic K/D
- ADX (Trend strength)

**Volatility:**
- Bollinger Bands (upper/middle/lower)
- ATR (Average True Range)

**Volume:**
- OBV (On-Balance Volume)

**All support signal interpretation** (overbought/oversold/neutral)

### 3.3 Options Analysis (`quantlab/analysis/options_analyzer.py`)

**Methods:**
```python
analyze_itm_calls(ticker, min_itm_pct, max_itm_pct, top_n)
analyze_itm_puts(ticker, min_itm_pct, max_itm_pct, top_n)
```

**Scoring System:**
- Liquidity score (volume + open interest)
- Greeks score (delta, gamma, theta optimization)
- Combined recommendation score

---

## 4. EXISTING FILTERING/SCREENING CAPABILITIES

### 4.1 Current Filtering

| Feature | Location | Capability |
|---------|----------|------------|
| **Data Type Filter** | ParquetReader | Stocks vs Options |
| **Date Range Filter** | ParquetReader | Configurable start/end |
| **Ticker Filter** | ParquetReader | Single or multi-ticker |
| **Options Type Filter** | ParquetReader | Call/Put filtering |
| **ITM Percentage Filter** | OptionsAnalyzer | 5-20% ITM range |
| **Technical Signals** | TechnicalIndicators | RSI 30/70, MACD, Bollinger |
| **Fundamental Filters** | DataManager | Via getter methods (no built-in filtering) |

### 4.2 What's Missing: Stock Screener Functionality

**Currently, there is NO dedicated CLI command for:**
- ✗ Multi-criteria stock screening
- ✗ Fundamental filtering (P/E, revenue growth, debt/equity ranges)
- ✗ Technical signal screening (RSI < 30, SMA crossovers, etc.)
- ✗ Sentiment-based filtering
- ✗ Custom rule combinations
- ✗ Batch processing (screen entire universe at once)
- ✗ Results persistence and tracking

---

## 5. VISUALIZATION CAPABILITIES

### 5.1 Available Charts (16 total)

**Backtest Performance (5 charts):**
- Cumulative returns
- Drawdown chart
- Monthly returns heatmap
- Rolling Sharpe ratio
- Comprehensive dashboard

**Price & Candlesticks (3 charts):**
- Candlestick chart with volume
- Price line with moving averages
- Multi-ticker comparison

**Options (5 charts):**
- Payoff diagrams
- Greeks heatmaps
- Greeks 3D surfaces
- Greeks timelines
- Strategy comparison

**Portfolio Management (3 charts):**
- Portfolio pie chart
- Position P&L bars
- 4-panel dashboard

### 5.2 Visualization Integration

All charts:
- Interactive Plotly-based
- Export to HTML
- Hover tooltips with data
- Date range selectors
- Zoom/pan controls
- Professional styling

---

## 6. QUICK START: KEY COMMANDS

### Portfolio Management
```bash
quantlab portfolio create tech --name "Tech Portfolio"
quantlab portfolio add tech AAPL MSFT GOOGL --weight 0.33
quantlab portfolio show tech
```

### Data Queries
```bash
quantlab data query AAPL --start 2025-10-01 --end 2025-10-16
quantlab data query AAPL MSFT --chart results/aapl_msft.html --chart-type comparison
quantlab data options-minute NVDA --start "2025-10-14 09:30" --end "2025-10-14 16:00"
```

### Analysis
```bash
quantlab analyze ticker AAPL
quantlab analyze ticker MSFT --no-options --output analysis.json
quantlab analyze portfolio tech --with-options
```

### Visualizations
```bash
quantlab visualize price AAPL --period 30d
quantlab visualize compare AAPL MSFT GOOGL --period 90d
quantlab visualize options long_call --current-price 100 --strike 100 --premium 5
```

---

## 7. ARCHITECTURE STRENGTHS

### Data Architecture
✓ **Multi-source integration** - 4 APIs + local Parquet
✓ **Smart routing** - Uses Parquet for speed, APIs for real-time
✓ **DuckDB integration** - Sub-second queries on 19,382 stocks
✓ **Efficient indexing** - Indexed on common queries
✓ **Caching layer** - Reduces API calls (TTL: 15min-24hr)

### Analysis Architecture
✓ **Modular design** - Each analysis type is separate
✓ **Extensible** - Easy to add new indicators/analyzers
✓ **Comprehensive Greeks** - Vanna, charm, vomma included
✓ **Signal interpretation** - Automatic trading signal generation
✓ **Error handling** - Graceful fallbacks and logging

### CLI Architecture
✓ **Professional** - Click-based with help text
✓ **Composable** - Subcommands organized logically
✓ **Flexible** - Many options and configurations
✓ **User-friendly** - Rich output with tables and emoji

### Visualization Architecture
✓ **Interactive** - Plotly-based responsive charts
✓ **Diverse** - 16 different chart types
✓ **Professional** - Consistent theming
✓ **Integrated** - Works with all other modules

---

## 8. KEY FILES FOR STOCK SCREENER DEVELOPMENT

### Data Access Foundation
- `quantlab/data/parquet_reader.py` - Query 19,382 stocks
- `quantlab/data/data_manager.py` - Smart data routing
- `quantlab/data/database.py` - Persistent storage for screening results

### Analysis Foundation
- `quantlab/analysis/technical_indicators.py` - 10+ indicators
- `quantlab/core/analyzer.py` - Multi-source analysis
- `quantlab/analysis/options_analyzer.py` - Options screening

### CLI Framework
- `quantlab/cli/main.py` - Main CLI entry point
- `quantlab/cli/data.py` - Data command template
- `quantlab/cli/analyze.py` - Analysis command template

### Visualization
- `quantlab/visualization/` - All chart types available
- `quantlab/cli/visualize.py` - CLI visualization commands

---

## 9. SCREENING USE CASES ENABLED

### Possible Stock Screener Features

1. **Technical Screener**
   - RSI < 30 (oversold)
   - SMA 20 < SMA 50 (downtrend)
   - MACD histogram > 0 (bullish)
   - Bollinger Bands squeeze

2. **Fundamental Screener**
   - P/E < 15 (value)
   - Revenue growth > 10% (growth)
   - Debt/Equity < 0.5 (safe)
   - ROE > 15% (profitable)

3. **Sentiment Screener**
   - Positive sentiment > 0.5
   - Articles analyzed > 10
   - Recent positive articles

4. **Hybrid Screener**
   - Combine multiple criteria
   - Weight by importance
   - Score and rank results

5. **Options-Based Screener**
   - High IV percentile
   - Liquidity filters
   - Spread/strategy opportunities
   - Greeks optimization

---

## 10. DATA AVAILABILITY

### Stock Data
- **19,382 stocks** available daily
- **Daily data:** 2020-10-16 to 2025-10-14 (1,740+ trading days)
- **Minute data:** Also available for major stocks
- **Location:** `/Volumes/sandisk/quantmini-data/data/parquet/`

### Options Data
- **Daily options:** 2024-present
- **Minute options:** August 2025+ (1-day delayed from S3)
- **Underlyings:** Full US equity universe

### Fundamentals
- **yfinance source:** Current P/E, revenue, margins, recommendations
- **Caching:** 24-hour TTL reduces API calls

### Sentiment
- **Alpha Vantage:** News sentiment scores
- **Caching:** 1-hour TTL

---

## 11. DEPENDENCIES FOR SCREENER

### Already Installed
- `click>=8.0.0` - CLI framework
- `duckdb>=0.9.0` - Database queries
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical operations
- `plotly>=5.18.0` - Visualization
- `polygon-api-client>=1.12.0` - Options/price data
- `yfinance>=0.2.0` - Fundamentals

### Utility Functions Available
- Signal interpretation (technical_indicators.py)
- Advanced Greeks calculation (greeks_calculator.py)
- Database operations (database.py)
- JSON serialization for results
- Rich CLI output formatting (tabulate)

---

## 12. IMPLEMENTATION ROADMAP FOR SCREENER

### Phase 1: Core Filtering Engine
1. Create `quantlab/analysis/screener.py` - Core filtering logic
2. Create database schema for screening results
3. Implement filter combinations and scoring

### Phase 2: CLI Integration
1. Create `quantlab/cli/screen.py` - CLI commands
2. Add `quantlab screen` command group
3. Implement predefined filters (technical, fundamental, sentiment)

### Phase 3: Results Management
1. Persist screening results to database
2. Track screening history
3. Compare results over time

### Phase 4: Visualization
1. Create screener results charts
2. Show filter contribution to scores
3. Compare sectors/industries

### Phase 5: Advanced Features
1. Custom rule engine
2. Backtesting screener rules
3. Real-time monitoring
4. Email/webhook alerts

---

## 13. EXAMPLE: QUERYING FOUNDATION

### Current Capability
```python
# Get technical indicators for a stock
analyzer = Analyzer(config, db, data_manager)
result = analyzer.analyze_ticker("AAPL")

# Filter by technical signals
rsi = result['technical_indicators']['momentum']['rsi_14']
if rsi < 30:
    # Stock is oversold
```

### What's Needed for Screener
```python
# Apply multi-criteria filter to universe
screener = StockScreener(data_manager, analyzer)
results = screener.screen(
    universe='all_stocks',  # or 'sp500', 'nasdaq100'
    criteria={
        'rsi': {'min': 0, 'max': 30},
        'pe_ratio': {'max': 20},
        'revenue_growth': {'min': 0.10},
    },
    limit=50,  # Top 50 matches
    sort_by='rsi'  # Sort by RSI ascending
)
```

---

## CONCLUSION

QuantLab provides **excellent foundational infrastructure** for a stock screener:

✓ **Data Layer:** 19,382 stocks, multi-source, well-indexed
✓ **Analysis Layer:** 10+ technical indicators, fundamentals, sentiment, options
✓ **CLI Framework:** Professional Click-based interface
✓ **Visualization:** 16 chart types ready to use
✓ **Database:** DuckDB with screening-friendly schema

**Missing:** Dedicated screening/filtering CLI command and batch processing logic

**Recommendation:** Implement stock screener as new `quantlab screen` command group with:
1. Predefined technical filters (RSI, MACD, SMA crosses)
2. Fundamental filters (P/E, growth, margins)
3. Sentiment filters
4. Custom criteria combinations
5. Results visualization and tracking

This would create a **complete quantitative trading suite** covering research, backtesting, portfolio management, and real-time screening.

---

*Generated: October 16, 2025*
*QuantLab Version: 0.2.1*
