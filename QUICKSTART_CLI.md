# QuantLab CLI Quick Start

**Portfolio Management & Market Data Analysis Platform**

---

## Installation

```bash
cd /Users/zheyuanzhao/workspace/quantlab
uv pip install -e .
```

---

## First Time Setup

Initialize the database and configuration:

```bash
uv run quantlab init
```

This creates:
- `~/.quantlab/quantlab.duckdb` - Database
- `~/.quantlab/config.yaml` - Configuration file

**Edit the config** to add your API keys:
```bash
nano ~/.quantlab/config.yaml
```

---

## Quick Reference

### Check Available Data

```bash
# Check what data is available
uv run quantlab data check

# List available tickers
uv run quantlab data tickers

# See date range
uv run quantlab data range
```

### Query Historical Data

```bash
# Get recent data for AAPL, MSFT, GOOGL
uv run quantlab data query AAPL MSFT GOOGL --start 2025-10-01 --limit 20

# Query with date range
uv run quantlab data query AAPL --start 2025-01-01 --end 2025-10-15 --limit 100
```

**Currently Available:**
- 📊 **19,382 stocks** with daily data (2020-10-16 to 2025-10-14)
- ⚡ **14,270 stocks** with minute data
- 📈 **Options data** (daily & minute, 2024-present)

### Portfolio Management

```bash
# Create a portfolio
uv run quantlab portfolio create tech --name "Tech Portfolio" --description "Large cap tech stocks"

# Add tickers with equal weights
uv run quantlab portfolio add tech AAPL MSFT GOOGL NVDA --weight 0.25

# View portfolio
uv run quantlab portfolio show tech

# Update a position
uv run quantlab portfolio update tech AAPL --shares 100 --cost-basis 247.77

# List all portfolios
uv run quantlab portfolio list

# Remove a ticker
uv run quantlab portfolio remove tech NVDA

# Delete portfolio
uv run quantlab portfolio delete tech
```

---

## Common Workflows

### Create and Track a Portfolio

```bash
# 1. Create portfolio
uv run quantlab portfolio create growth --name "Growth Stocks"

# 2. Add positions
uv run quantlab portfolio add growth AAPL MSFT GOOGL AMZN TSLA

# 3. Update with position details
uv run quantlab portfolio update growth AAPL --shares 100 --cost-basis 247.77 --notes "Q4 2025 entry"
uv run quantlab portfolio update growth MSFT --shares 50 --cost-basis 513.57

# 4. View portfolio
uv run quantlab portfolio show growth
```

### Analyze Historical Performance

```bash
# Get historical prices
uv run quantlab data query AAPL MSFT --start 2024-01-01 --end 2024-12-31 --limit 500

# Check recent performance
uv run quantlab data query AAPL MSFT GOOGL NVDA --start 2025-10-01
```

---

## Data Sources

**Historical Data (Local Parquet Files):**
- Location: `/Volumes/sandisk/quantmini-data/data/parquet/`
- Format: Partitioned by year/month/date
- Access: Direct DuckDB queries (no import needed!)
- Performance: Sub-second queries on 5 years of data

**Real-Time Data (Coming in Phase 2):**
- Polygon.io API - Real-time quotes, options chains
- Alpha Vantage API - News sentiment, economic indicators
- yfinance API - Fundamentals, analyst ratings

---

## Help

```bash
# Main help
uv run quantlab --help

# Portfolio commands help
uv run quantlab portfolio --help

# Data commands help
uv run quantlab data --help

# Specific command help
uv run quantlab portfolio create --help
```

---

## Configuration

**Config file:** `~/.quantlab/config.yaml`

```yaml
api_keys:
  polygon: "your_polygon_api_key_here"
  alphavantage: "your_alphavantage_api_key_here"

database:
  path: "~/.quantlab/quantlab.duckdb"

data_paths:
  parquet_root: "/Volumes/sandisk/quantmini-data/data/parquet"
  qlib_root: "/Volumes/sandisk/quantmini-data/data/qlib"

cache:
  cache_ttl_prices: 900          # 15 minutes
  cache_ttl_fundamentals: 86400  # 24 hours
  cache_ttl_news: 3600           # 1 hour

rate_limits:
  polygon: 5      # requests/minute
  alphavantage: 5 # requests/minute
```

---

## Examples

### Example 1: Tech Portfolio

```bash
# Create tech portfolio
uv run quantlab portfolio create tech --name "FAANG+ Portfolio" --description "Top tech companies"

# Add FAANG stocks with equal weight
uv run quantlab portfolio add tech AAPL AMZN GOOGL META NFLX --weight 0.20

# View it
uv run quantlab portfolio show tech
```

### Example 2: Value Portfolio

```bash
# Create value portfolio
uv run quantlab portfolio create value --name "Value Stocks" --description "Undervalued large caps"

# Add positions
uv run quantlab portfolio add value BRK.B JPM JNJ PG KO --weight 0.20

# Update with actual holdings
uv run quantlab portfolio update value BRK.B --shares 25 --cost-basis 450.00
uv run quantlab portfolio update value JPM --shares 100 --cost-basis 180.50

# View it
uv run quantlab portfolio show value
```

### Example 3: Query Historical Data

```bash
# Get October 2025 data for mega-caps
uv run quantlab data query AAPL MSFT GOOGL AMZN NVDA --start 2025-10-01 --limit 100

# Check data availability for specific ticker
uv run quantlab data query TSLA --start 2024-01-01 --limit 10
```

---

## Current Features (Phase 1)

✅ Portfolio management (create, update, delete)
✅ Position tracking (tickers, weights, shares, cost basis)
✅ Historical data queries (5 years of daily data)
✅ DuckDB integration (fast analytical queries)
✅ Parquet file queries (no import needed)
✅ CLI interface with rich output

## Coming Soon (Phase 2)

⏳ Real-time price fetching (Polygon API)
⏳ Options chain analysis
⏳ Advanced Greeks (Vanna, Charm, Vomma)
⏳ News sentiment analysis (Alpha Vantage)
⏳ Fundamental data (yfinance)
⏳ Portfolio valuation
⏳ Analysis reports (markdown)

---

## Troubleshooting

**Command not found: quantlab**
```bash
# Use uv run instead
uv run quantlab <command>
```

**Database initialization fails**
```bash
# Remove old database and reinitialize
rm ~/.quantlab/quantlab.duckdb
uv run quantlab init
```

**No data found for ticker**
```bash
# Check if ticker exists in data
uv run quantlab data tickers | grep AAPL

# Check date range
uv run quantlab data range
```

**Permission denied on config**
```bash
# Fix permissions
chmod 644 ~/.quantlab/config.yaml
```

---

## Documentation

- **Full Architecture:** `docs/COMPREHENSIVE_SYSTEM_ARCHITECTURE.md`
- **Implementation Plan:** `docs/IMPLEMENTATION_PLAN_V1.md`
- **Phase 1 Summary:** `docs/PHASE_1_COMPLETION_SUMMARY.md`
- **Multi-Source Analysis:** `scripts/analysis/MULTI_SOURCE_ANALYSIS_README.md`

---

## Support

For issues or questions:
1. Check the documentation in `docs/`
2. Review existing analysis scripts in `scripts/analysis/`
3. Check the project memory: `.claude/PROJECT_MEMORY.md`

---

**Last Updated:** October 15, 2025
**Version:** 0.1.0 (Phase 1 Complete)
