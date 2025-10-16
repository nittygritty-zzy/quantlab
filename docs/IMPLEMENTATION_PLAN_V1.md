# QUANTLAB V1.0 IMPLEMENTATION PLAN
## Portfolio Analysis System with Multi-Source Data Integration

**Version:** 1.0
**Date:** October 15, 2025
**Target:** CLI-based portfolio management with DuckDB

---

## 1. PROJECT SPECIFICATIONS

### 1.1 Requirements (from user)

✅ **Database:** DuckDB (not SQLite/PostgreSQL)
✅ **Interface:** CLI only (no web dashboard)
✅ **Scope:** Portfolio management (not just single ticker)
✅ **Data:** Use existing production data at `/Volumes/sandisk/quantmini-data/`
   - 2 years of stock/option data from Polygon
   - No backfilling required

### 1.2 Existing Data Assets

**Location:** `/Volumes/sandisk/quantmini-data/data/`

**Available Data:**
```
parquet/
├── stocks_daily/      # Daily stock OHLCV
├── stocks_minute/     # Minute-level stock data
├── options_daily/     # Daily options data
└── options_minute/    # Minute-level options data

qlib/stocks_daily/
├── calendars/         # Trading calendars
├── features/          # Calculated features
└── instruments/       # Stock universe metadata
```

**Data Coverage:** 2 years of production Polygon data (2023-2025)

### 1.3 Goals

**Primary Goal:**
Build a CLI tool for comprehensive portfolio analysis that:
1. Manages multiple tickers (portfolios)
2. Integrates existing Polygon data with real-time APIs
3. Provides comprehensive analysis (options, fundamentals, sentiment)
4. Uses DuckDB for fast analytical queries
5. Generates actionable insights and reports

**Success Metrics:**
- ✅ Analyze entire portfolio in <10 seconds
- ✅ Generate comprehensive reports
- ✅ Support 50+ tickers per portfolio
- ✅ CLI commands intuitive and fast

---

## 2. SYSTEM ARCHITECTURE (REVISED)

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI INTERFACE                             │
│  quantlab portfolio add AAPL MSFT GOOG                      │
│  quantlab analyze --portfolio tech                          │
│  quantlab report --portfolio tech --format markdown         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│              PORTFOLIO ANALYSIS ENGINE                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  PortfolioManager                                     │  │
│  │  • Load/save portfolios                              │  │
│  │  • Batch analysis orchestration                      │  │
│  │  • Result aggregation                                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  TickerAnalysisEngine                                │  │
│  │  • Single ticker comprehensive analysis              │  │
│  │  • Multi-source data integration                     │  │
│  │  • Greeks calculation                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                  DATA LAYER (DuckDB)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DuckDB Database: quantlab.duckdb                    │  │
│  │                                                        │  │
│  │  Tables:                                              │  │
│  │  • portfolios          (portfolio definitions)        │  │
│  │  • portfolio_positions (ticker allocations)          │  │
│  │  • ticker_snapshots    (cached real-time data)       │  │
│  │  • options_analysis    (options Greeks, IV)          │  │
│  │  • fundamental_data    (financials, ratios)          │  │
│  │  • sentiment_data      (news sentiment)              │  │
│  │  • analysis_cache      (cached analysis results)     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                DATA SOURCES (4 Sources)                      │
│  ┌─────────────┐  ┌───────────┐  ┌──────────┐  ┌─────────┐│
│  │ Existing    │  │ Polygon   │  │  Alpha   │  │yfinance ││
│  │ Parquet     │  │ Real-time │  │ Vantage  │  │   API   ││
│  │ Files       │  │    API    │  │   API    │  │         ││
│  │ (2yr data)  │  │ (current) │  │ (news)   │  │ (fund.) ││
│  └─────────────┘  └───────────┘  └──────────┘  └─────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Why DuckDB?

**Advantages over SQLite/PostgreSQL:**

1. **Analytical Performance** 🚀
   - Column-oriented storage (perfect for financial data)
   - Vectorized query execution (10-100x faster than SQLite)
   - Efficient aggregations on millions of rows

2. **Native Parquet Support** 📊
   - Read existing parquet files directly
   - No data migration needed
   - Zero-copy data access

3. **Python Integration** 🐍
   - Excellent Python API
   - Pandas/Arrow integration
   - In-process execution (no server)

4. **SQL Analytics** 📈
   - Full SQL support
   - Window functions (for technical indicators)
   - CTEs and complex queries

**Example: Query existing data directly:**
```python
import duckdb

# Query parquet files directly (no import needed!)
result = duckdb.sql("""
    SELECT symbol, date, close, volume
    FROM '/Volumes/sandisk/quantmini-data/data/parquet/stocks_daily/*.parquet'
    WHERE symbol IN ('AAPL', 'MSFT', 'GOOGL')
    AND date >= '2024-01-01'
    ORDER BY date DESC
""").df()
```

---

## 3. DATABASE SCHEMA (DuckDB)

### 3.1 Core Tables

```sql
-- ==========================================
-- PORTFOLIO MANAGEMENT
-- ==========================================

CREATE TABLE portfolios (
    portfolio_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE portfolio_positions (
    id BIGINT PRIMARY KEY,
    portfolio_id VARCHAR REFERENCES portfolios(portfolio_id),
    ticker VARCHAR(20) NOT NULL,
    weight DECIMAL(5,4),  -- Portfolio weight (e.g., 0.25 = 25%)
    shares INTEGER,
    cost_basis DECIMAL(18,6),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(portfolio_id, ticker)
);

-- ==========================================
-- REAL-TIME DATA CACHE
-- ==========================================

CREATE TABLE ticker_snapshots (
    ticker VARCHAR(20) PRIMARY KEY,

    -- Price data
    current_price DECIMAL(18,6),
    open DECIMAL(18,6),
    high DECIMAL(18,6),
    low DECIMAL(18,6),
    volume BIGINT,
    vwap DECIMAL(18,6),

    -- Change metrics
    change DECIMAL(18,6),
    change_percent DECIMAL(10,4),

    -- Market data
    market_cap BIGINT,
    pe_ratio DECIMAL(10,4),

    -- Metadata
    snapshot_date TIMESTAMP,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- OPTIONS ANALYSIS
-- ==========================================

CREATE TABLE options_analysis (
    id BIGINT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    analysis_date DATE NOT NULL,

    -- Top ITM call recommendation
    best_strike DECIMAL(18,6),
    best_expiry DATE,
    best_delta DECIMAL(10,8),
    best_price DECIMAL(18,6),

    -- Greeks summary
    avg_iv DECIMAL(10,8),
    iv_skew DECIMAL(10,8),
    put_call_ratio DECIMAL(10,4),

    -- Advanced Greeks (for best option)
    vanna DECIMAL(10,8),
    charm DECIMAL(10,8),
    vomma DECIMAL(10,8),

    -- Recommendation
    recommendation TEXT,  -- JSON with top 3 options

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(ticker, analysis_date)
);

-- ==========================================
-- FUNDAMENTAL DATA
-- ==========================================

CREATE TABLE fundamental_data (
    ticker VARCHAR(20) PRIMARY KEY,

    -- Company info
    company_name VARCHAR(200),
    sector VARCHAR(100),
    industry VARCHAR(200),

    -- Valuation
    market_cap BIGINT,
    enterprise_value BIGINT,
    pe_ratio DECIMAL(10,4),
    forward_pe DECIMAL(10,4),
    peg_ratio DECIMAL(10,4),
    price_to_book DECIMAL(10,4),
    price_to_sales DECIMAL(10,4),

    -- Profitability
    profit_margin DECIMAL(10,6),
    operating_margin DECIMAL(10,6),
    roe DECIMAL(10,6),
    roa DECIMAL(10,6),

    -- Growth
    revenue_growth DECIMAL(10,6),
    earnings_growth DECIMAL(10,6),

    -- Financial health
    current_ratio DECIMAL(10,4),
    debt_to_equity DECIMAL(10,4),
    free_cash_flow BIGINT,

    -- Dividends
    dividend_rate DECIMAL(18,6),
    dividend_yield DECIMAL(10,6),
    payout_ratio DECIMAL(10,4),

    -- Analyst data
    analyst_rating VARCHAR(50),  -- Buy/Hold/Sell
    price_target_mean DECIMAL(18,6),
    price_target_high DECIMAL(18,6),
    price_target_low DECIMAL(18,6),
    num_analysts INTEGER,

    -- Metadata
    last_updated TIMESTAMP,
    source VARCHAR(50)
);

-- ==========================================
-- SENTIMENT DATA
-- ==========================================

CREATE TABLE sentiment_data (
    ticker VARCHAR(20) PRIMARY KEY,

    -- News sentiment (from Alpha Vantage)
    news_sentiment_score DECIMAL(6,4),  -- -1 to +1
    news_sentiment_label VARCHAR(50),   -- Bearish/Neutral/Bullish
    articles_analyzed INTEGER,

    -- Analyst sentiment
    analyst_consensus VARCHAR(50),  -- Strong Buy/Buy/Hold/Sell
    recent_upgrades INTEGER,
    recent_downgrades INTEGER,

    -- Insider activity
    insider_purchases_30d INTEGER,
    insider_sales_30d INTEGER,
    insider_net_activity DECIMAL(20,2),

    -- Social sentiment (placeholder for future)
    social_sentiment_score DECIMAL(6,4),

    -- Metadata
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- ANALYSIS CACHE
-- ==========================================

CREATE TABLE analysis_cache (
    cache_key VARCHAR(500) PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    analysis_type VARCHAR(100) NOT NULL,  -- 'comprehensive', 'options', 'fundamentals', etc.

    -- Cached data (JSON)
    result_json TEXT,

    -- Cache metadata
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    hit_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,

    INDEX idx_ticker_type (ticker, analysis_type),
    INDEX idx_expires (expires_at)
);
```

### 3.2 External Parquet Files (Read-Only)

DuckDB can query existing parquet files directly without importing:

**Historical Stock Data:**
```sql
-- Query 2 years of stock data directly
SELECT * FROM '/Volumes/sandisk/quantmini-data/data/parquet/stocks_daily/*.parquet'
WHERE symbol = 'AAPL';
```

**Historical Options Data:**
```sql
-- Query historical options
SELECT * FROM '/Volumes/sandisk/quantmini-data/data/parquet/options_daily/*.parquet'
WHERE underlying_symbol = 'AAPL'
AND expiration_date >= CURRENT_DATE;
```

**Benefits:**
- ✅ No data duplication
- ✅ Zero import time
- ✅ Always uses latest parquet data
- ✅ Can join with DuckDB tables

---

## 4. CLI INTERFACE DESIGN

### 4.1 Command Structure

```bash
quantlab [command] [subcommand] [options]
```

### 4.2 Core Commands

#### Portfolio Management

```bash
# Create portfolio
quantlab portfolio create tech --name "Tech Portfolio"

# Add tickers to portfolio
quantlab portfolio add tech AAPL MSFT GOOGL NVDA

# Remove ticker
quantlab portfolio remove tech NVDA

# List portfolios
quantlab portfolio list

# Show portfolio details
quantlab portfolio show tech

# Delete portfolio
quantlab portfolio delete tech
```

#### Analysis Commands

```bash
# Analyze entire portfolio
quantlab analyze tech

# Analyze specific ticker
quantlab analyze AAPL

# Options-focused analysis
quantlab analyze tech --options

# Include sentiment analysis
quantlab analyze tech --sentiment

# Force refresh (bypass cache)
quantlab analyze tech --force-refresh

# Specific time period
quantlab analyze tech --period 30d
```

#### Report Generation

```bash
# Generate comprehensive report
quantlab report tech

# Specific report format
quantlab report tech --format markdown
quantlab report tech --format json
quantlab report tech --format pdf

# Report sections
quantlab report tech --sections options,fundamentals,sentiment

# Save to file
quantlab report tech --output tech_analysis_2025-10-15.md
```

#### Data Management

```bash
# Show data status
quantlab data status

# Refresh data from APIs
quantlab data refresh --ticker AAPL
quantlab data refresh --portfolio tech

# Cache management
quantlab data cache-stats
quantlab data clear-cache
```

#### Configuration

```bash
# Show current configuration
quantlab config show

# Set API keys
quantlab config set polygon_api_key YOUR_KEY
quantlab config set alphavantage_api_key YOUR_KEY

# Configure cache TTL
quantlab config set cache_ttl_price 900  # 15 minutes
quantlab config set cache_ttl_fundamentals 86400  # 24 hours
```

### 4.3 Example Workflows

**Workflow 1: Create and analyze new portfolio**
```bash
# Create portfolio
quantlab portfolio create long_term --name "Long-term Holdings"

# Add stocks
quantlab portfolio add long_term AAPL MSFT GOOGL AMZN META

# Run analysis
quantlab analyze long_term --options --sentiment

# Generate report
quantlab report long_term --format markdown --output reports/long_term_$(date +%Y%m%d).md
```

**Workflow 2: Daily portfolio check**
```bash
# Quick analysis (uses cache)
quantlab analyze tech

# Get latest news sentiment
quantlab analyze tech --sentiment --force-refresh

# Check options opportunities
quantlab analyze tech --options
```

**Workflow 3: Single ticker deep dive**
```bash
# Comprehensive single ticker analysis
quantlab analyze AAPL --options --fundamentals --sentiment --technical

# Generate detailed report
quantlab report AAPL --format markdown
```

---

## 5. DATA INTEGRATION STRATEGY

### 5.1 Four-Source Integration

| Data Source | What It Provides | Update Frequency | Cost |
|-------------|------------------|------------------|------|
| **Existing Parquet** | 2 years historical stock/options | Static | $0 |
| **Polygon Real-time** | Current prices, live Greeks | 15-min delay | $58/mo |
| **Alpha Vantage** | News sentiment, Treasury rates | Daily | $0 (free tier) |
| **yfinance** | Financials, analyst data, ownership | Daily | $0 (free) |

### 5.2 Data Flow

```
User Command: quantlab analyze tech
        │
        ▼
┌───────────────────────────┐
│ Portfolio Manager         │
│ Load portfolio "tech"     │
│ Tickers: AAPL,MSFT,GOOGL │
└───────────┬───────────────┘
            │
            ▼ (For each ticker)
┌───────────────────────────────────────────────────┐
│ Check cache (DuckDB analysis_cache table)        │
│ If fresh: return cached result                   │
│ If stale: proceed to fetch                       │
└────────────┬──────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│ Fetch current price (Polygon API)                 │
│ • Cache for 15 minutes                            │
│ • Store in ticker_snapshots table                │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ Fetch historical data (Existing Parquet)          │
│ • DuckDB query on parquet files                   │
│ • No caching needed (direct query)                │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ Fetch options (Polygon API)                       │
│ • Calculate advanced Greeks                        │
│ • Cache for 15 minutes                            │
│ • Store in options_analysis table                 │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ Fetch fundamentals (yfinance API)                 │
│ • Financial statements, ratios                     │
│ • Cache for 24 hours                              │
│ • Store in fundamental_data table                 │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ Fetch sentiment (Alpha Vantage API)               │
│ • News sentiment analysis                          │
│ • Cache for 1 hour                                │
│ • Store in sentiment_data table                   │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ Run analysis modules                               │
│ • Price analysis                                   │
│ • Options analysis                                 │
│ • Fundamental analysis                             │
│ • Sentiment analysis                               │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ Aggregate results                                  │
│ • Combine all analysis                            │
│ • Generate recommendations                         │
│ • Cache complete result                           │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ Return to Portfolio Manager                        │
│ Repeat for next ticker                            │
└────────────────────────────────────────────────────┘
```

---

## 6. PROJECT STRUCTURE

```
quantlab/
├── quantlab/                       # Main package
│   ├── __init__.py
│   ├── cli/                        # CLI interface
│   │   ├── __init__.py
│   │   ├── main.py                # Click CLI entry point
│   │   ├── portfolio_commands.py  # Portfolio management commands
│   │   ├── analyze_commands.py    # Analysis commands
│   │   ├── report_commands.py     # Report generation commands
│   │   └── data_commands.py       # Data management commands
│   │
│   ├── core/                       # Core business logic
│   │   ├── __init__.py
│   │   ├── portfolio_manager.py   # Portfolio CRUD operations
│   │   ├── ticker_analyzer.py     # Single ticker analysis
│   │   ├── batch_analyzer.py      # Batch portfolio analysis
│   │   └── report_generator.py    # Report generation
│   │
│   ├── data/                       # Data layer
│   │   ├── __init__.py
│   │   ├── duckdb_manager.py      # DuckDB operations
│   │   ├── cache_manager.py       # Caching logic
│   │   ├── polygon_client.py      # Polygon API wrapper
│   │   ├── alphavantage_client.py # Alpha Vantage API wrapper
│   │   ├── yfinance_client.py     # yfinance API wrapper
│   │   └── parquet_reader.py      # Read existing parquet files
│   │
│   ├── analysis/                   # Analysis modules
│   │   ├── __init__.py
│   │   ├── price_analyzer.py      # Price & volume analysis
│   │   ├── options_analyzer.py    # Options analysis
│   │   ├── greeks_calculator.py   # Advanced Greeks
│   │   ├── fundamental_analyzer.py # Fundamental analysis
│   │   ├── sentiment_analyzer.py  # Sentiment analysis
│   │   └── technical_analyzer.py  # Technical indicators
│   │
│   ├── models/                     # Data models
│   │   ├── __init__.py
│   │   ├── portfolio.py           # Portfolio models
│   │   ├── ticker_data.py         # Ticker data models
│   │   ├── options_data.py        # Options models
│   │   └── analysis_result.py     # Analysis result models
│   │
│   └── utils/                      # Utilities
│       ├── __init__.py
│       ├── config.py              # Configuration management
│       ├── rate_limiter.py        # Rate limiting
│       └── logger.py              # Logging setup
│
├── scripts/                        # Utility scripts
│   ├── setup_database.py         # Initialize DuckDB
│   └── import_portfolios.py      # Import portfolios from CSV
│
├── tests/                          # Tests
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/                           # Documentation
│   ├── COMPREHENSIVE_SYSTEM_ARCHITECTURE.md
│   ├── IMPLEMENTATION_PLAN_V1.md
│   └── CLI_USER_GUIDE.md
│
├── pyproject.toml                  # Project config (using uv)
├── README.md
└── .env.example                    # Environment variables template
```

---

## 7. IMPLEMENTATION PHASES

### Phase 1: Foundation (Week 1)

**Goal:** Core infrastructure

**Tasks:**
1. ✅ Set up project structure
2. ✅ Initialize DuckDB with schema
3. ✅ Create base CLI with Click
4. ✅ Implement portfolio CRUD operations
5. ✅ Test DuckDB with parquet file queries

**Deliverables:**
- Working CLI skeleton
- DuckDB database initialized
- Can create/list/delete portfolios
- Can query existing parquet files

**Test:**
```bash
quantlab portfolio create test
quantlab portfolio add test AAPL
quantlab portfolio list
# Should show test portfolio with AAPL
```

### Phase 2: Data Integration (Week 2)

**Goal:** Connect all data sources

**Tasks:**
1. ✅ Implement PolygonClient (real-time data)
2. ✅ Implement AlphaVantageClient (sentiment)
3. ✅ Implement YFinanceClient (fundamentals)
4. ✅ Implement ParquetReader (historical data)
5. ✅ Build CacheManager with TTL

**Deliverables:**
- All 4 data sources integrated
- Caching working
- Rate limiting in place

**Test:**
```bash
quantlab data refresh --ticker AAPL
# Should fetch and cache all data
```

### Phase 3: Analysis Engine (Week 3)

**Goal:** Build analysis modules

**Tasks:**
1. ✅ Implement TickerAnalyzer
2. ✅ Build PriceAnalyzer
3. ✅ Build OptionsAnalyzer with Greeks
4. ✅ Build FundamentalAnalyzer
5. ✅ Build SentimentAnalyzer

**Deliverables:**
- Complete analysis for single ticker
- All analysis modules working

**Test:**
```bash
quantlab analyze AAPL
# Should show comprehensive analysis
```

### Phase 4: Portfolio Analysis (Week 4)

**Goal:** Batch analysis and reporting

**Tasks:**
1. ✅ Implement BatchAnalyzer
2. ✅ Build ReportGenerator (Markdown)
3. ✅ Implement portfolio-level aggregation
4. ✅ Add comparison metrics

**Deliverables:**
- Full portfolio analysis
- Markdown reports
- Portfolio-level insights

**Test:**
```bash
quantlab analyze tech
quantlab report tech --format markdown
# Should generate portfolio report
```

### Phase 5: Polish & Documentation (Week 5)

**Goal:** Production ready

**Tasks:**
1. ✅ Add comprehensive error handling
2. ✅ Write user documentation
3. ✅ Add example portfolios
4. ✅ Performance optimization
5. ✅ Testing

**Deliverables:**
- User guide (CLI_USER_GUIDE.md)
- Example portfolios
- 90%+ test coverage
- Performance benchmarks

---

## 8. CONFIGURATION

### 8.1 Configuration File (`~/.quantlab/config.yaml`)

```yaml
# API Keys
api_keys:
  polygon: "vDr8GDaQ87Z9Mwe5IiCKzGcRP9pnO8TW"
  alphavantage: "3NHDCBRE0IKFB8XW"

# Database
database:
  path: "~/.quantlab/quantlab.duckdb"

# Data paths
data_paths:
  parquet_root: "/Volumes/sandisk/quantmini-data/data/parquet"
  qlib_root: "/Volumes/sandisk/quantmini-data/data/qlib"

# Cache TTL (seconds)
cache:
  price_snapshot: 900       # 15 minutes
  options_data: 900         # 15 minutes
  fundamental_data: 86400   # 24 hours
  sentiment_data: 3600      # 1 hour
  technical_indicators: 3600 # 1 hour

# Rate limiting
rate_limits:
  polygon:
    calls_per_second: 5
  alphavantage:
    calls_per_minute: 5
    calls_per_day: 25
  yfinance:
    calls_per_second: 1

# Analysis settings
analysis:
  default_period: "30d"
  options_itm_range: [5, 20]  # 5-20% ITM
  max_concurrent_tickers: 10

# Reports
reports:
  default_format: "markdown"
  output_dir: "~/quantlab_reports"
```

---

## 9. DEPENDENCIES

### 9.1 Python Packages (pyproject.toml)

```toml
[project]
name = "quantlab"
version = "1.0.0"
description = "Multi-source portfolio analysis system"
requires-python = ">=3.10"

dependencies = [
    "duckdb>=1.1.0",
    "click>=8.1.0",
    "pandas>=2.2.0",
    "numpy>=2.0.0",
    "pyarrow>=17.0.0",
    "polygon-api-client>=1.15.0",
    "yfinance>=0.2.66",
    "requests>=2.32.0",
    "pyyaml>=6.0.0",
    "scipy>=1.14.0",
    "rich>=13.0.0",  # For beautiful CLI output
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "black>=24.0.0",
    "ruff>=0.6.0",
]

[project.scripts]
quantlab = "quantlab.cli.main:cli"
```

---

## 10. SUCCESS CRITERIA

### 10.1 Performance Targets

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Single ticker analysis (cache hit) | <500ms | `time quantlab analyze AAPL` |
| Single ticker analysis (cache miss) | <5s | `time quantlab analyze AAPL --force-refresh` |
| Portfolio analysis (10 tickers, cache hit) | <2s | `time quantlab analyze tech` |
| Portfolio analysis (10 tickers, cache miss) | <30s | `time quantlab analyze tech --force-refresh` |
| Parquet query (2yr data, single ticker) | <100ms | Direct DuckDB query benchmark |
| Report generation | <3s | `time quantlab report tech` |

### 10.2 Functional Requirements

✅ **Must Have:**
- [ ] Portfolio CRUD operations
- [ ] Multi-ticker batch analysis
- [ ] Options analysis with advanced Greeks
- [ ] Fundamental analysis from yfinance
- [ ] Sentiment analysis from Alpha Vantage
- [ ] Markdown report generation
- [ ] Data caching with TTL
- [ ] Query existing parquet files

✅ **Nice to Have:**
- [ ] PDF report generation
- [ ] Email alerts
- [ ] Historical backtesting
- [ ] Correlation analysis

---

## 11. NEXT STEPS

### Immediate Actions (This Week):

1. **Set up project structure**
   ```bash
   cd /Users/zheyuanzhao/workspace/quantlab
   mkdir -p quantlab/{cli,core,data,analysis,models,utils}
   touch quantlab/__init__.py
   ```

2. **Initialize DuckDB**
   - Create `scripts/setup_database.py`
   - Run schema creation
   - Test parquet file queries

3. **Build CLI skeleton**
   - Install Click
   - Create basic commands
   - Test portfolio CRUD

4. **Test data integration**
   - Query existing parquet files
   - Test Polygon API connection
   - Verify yfinance works

### Questions to Confirm:

1. **Portfolio definition:** Should we track cost basis and P&L?
2. **Report frequency:** Daily cron job or on-demand only?
3. **Comparison:** Portfolio vs S&P500 benchmarking?

---

**Ready to start Phase 1 implementation?** 🚀

Let me know if you want to:
1. Start building the CLI
2. Set up the DuckDB database first
3. Create the project structure
4. Something else?
