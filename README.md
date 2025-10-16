# QuantLab - Quantitative Trading Research Platform

[![PyPI version](https://img.shields.io/pypi/v/quantlabs.svg)](https://pypi.org/project/quantlabs/)
[![Documentation Status](https://readthedocs.org/projects/quantlabs/badge/?version=latest)](https://quantlabs.readthedocs.io/en/latest/?badge=latest)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/nittygritty-zzy/quantlab)](https://github.com/nittygritty-zzy/quantlab/releases)

A quantitative trading research platform powered by Microsoft's Qlib, designed for systematic alpha generation and backtesting.

📚 **[Full Documentation](https://quantlabs.readthedocs.io)** | 🚀 **[Quick Start Guide](https://quantlabs.readthedocs.io/en/latest/quickstart.html)** | 📖 **[API Reference](https://quantlabs.readthedocs.io/en/latest/api/core.html)**

## 📁 Project Structure

```
quantlab/
├── README.md                       # This file
├── .gitignore                      # Git ignore rules
├── .venv/                          # Python virtual environment (uv)
│
├── docs/                           # Documentation
│   ├── BACKTEST_SUMMARY.md         # Backtest results analysis
│   ├── ALPHA158_SUMMARY.md         # Alpha158 features documentation
│   ├── ALPHA158_CORRECTED.md       # Alpha158 corrections
│   ├── USE_QLIB_ALPHA158.md        # Guide for using Alpha158
│   └── QUANTMINI_README.md         # QuantMini data setup
│
├── scripts/                        # Utility scripts
│   ├── data/                       # Data processing
│   │   ├── convert_to_qlib.py      # Convert data to qlib format
│   │   ├── refresh_today_data.py   # Update latest data
│   │   └── quantmini_setup.py      # QuantMini data setup
│   ├── analysis/                   # Analysis tools
│   │   └── visualize_results.py    # Backtest visualization
│   └── tests/                      # Test scripts
│       ├── test_qlib_alpha158.py   # Test Alpha158 features
│       ├── test_stocks_minute_fix.py
│       └── enable_alpha158.py
│
├── configs/                        # Qlib workflow configurations
│   ├── lightgbm_external_data.yaml # Full universe (all stocks)
│   ├── lightgbm_fixed_dates.yaml   # 2024 only (date filter)
│   └── lightgbm_liquid_universe.yaml # Filtered liquid stocks
│
├── results/                        # Backtest outputs
│   ├── visualizations/             # Charts and plots
│   │   └── backtest_visualization.png
│   └── mlruns/                     # MLflow experiment tracking
│       └── 489214785307856385/     # Experiment runs
│
├── data/                           # Local data storage
│   ├── parquet/                    # Raw parquet files
│   └── metadata/                   # Metadata files
│
├── notebooks/                      # Jupyter notebooks
│   └── workflow_by_code.ipynb      # Qlib workflow examples
│
├── config/                         # System configuration
│   └── system_profile.yaml         # System settings
│
└── qlib_repo/                      # Qlib source (gitignored, 828MB)
    └── (Microsoft qlib clone)
```

## 🚀 Quick Start

### Installation from PyPI

```bash
# Install from PyPI
pip install quantlabs

# Or using uv (recommended)
uv pip install quantlabs

# Verify installation
quantlab --version
quantlab --help
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/nittygritty-zzy/quantlab.git
cd quantlab

# Using uv (recommended)
uv venv
source .venv/bin/activate
uv sync

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Prepare Data

```bash
# Option A: Use external data (QuantMini on /Volumes/sandisk)
# Data is already at: /Volumes/sandisk/quantmini-data/data/qlib/stocks_daily

# Option B: Download community data
wget https://github.com/chenditc/investment_data/releases/latest/download/qlib_bin.tar.gz
mkdir -p ~/.qlib/qlib_data/cn_data
tar -zxvf qlib_bin.tar.gz -C ~/.qlib/qlib_data/cn_data --strip-components=1
```

### 3. Run a Backtest

```bash
# Navigate to qlib examples (if using qlib_repo)
cd qlib_repo/examples

# Run workflow with external data
uv run qrun ../../configs/lightgbm_liquid_universe.yaml
```

### 4. Visualize Results

```bash
# Update the experiment ID in visualize_results.py, then:
uv run python scripts/analysis/visualize_results.py
```

Results will be saved to `results/visualizations/backtest_visualization.png`

## 💼 QuantLab CLI - Real-World Use Cases

QuantLab includes a powerful CLI for portfolio management, market analysis, and data queries.

### 🎬 Use Case 1: Building a Tech Portfolio

**Scenario**: Create and manage a diversified tech portfolio with FAANG+ stocks.

```bash
# Initialize QuantLab
quantlab init

# Create a tech portfolio
quantlab portfolio create tech_giants --name "FAANG+ Portfolio" \
    --description "Large-cap tech companies"

# Add positions with target weights
quantlab portfolio add tech_giants AAPL GOOGL MSFT --weight 0.20
quantlab portfolio add tech_giants META AMZN --weight 0.15
quantlab portfolio add tech_giants NVDA --weight 0.10

# View your portfolio
quantlab portfolio show tech_giants

# Expected output:
# 📊 Portfolio: FAANG+ Portfolio
# 📈 Positions: 6
# ├─ AAPL    │ Weight: 20.00% │ Shares: -   │ Cost Basis: -
# ├─ GOOGL   │ Weight: 20.00% │ Shares: -   │ Cost Basis: -
# ├─ MSFT    │ Weight: 20.00% │ Shares: -   │ Cost Basis: -
# ├─ META    │ Weight: 15.00% │ Shares: -   │ Cost Basis: -
# ├─ AMZN    │ Weight: 15.00% │ Shares: -   │ Cost Basis: -
# └─ NVDA    │ Weight: 10.00% │ Shares: -   │ Cost Basis: -
# Total Weight: 100.00%
```

### 📊 Use Case 2: Real Position Tracking

**Scenario**: Track actual shares purchased at specific cost basis.

```bash
# Update positions with real trade data
quantlab portfolio update tech_giants AAPL \
    --shares 50 \
    --cost-basis 178.25 \
    --notes "Bought on Q4 dip"

quantlab portfolio update tech_giants GOOGL \
    --shares 30 \
    --cost-basis 142.50 \
    --notes "Post-earnings entry"

quantlab portfolio update tech_giants NVDA \
    --shares 20 \
    --cost-basis 485.00 \
    --notes "AI boom position"

# View updated portfolio
quantlab portfolio show tech_giants

# Expected output:
# 📊 Portfolio: FAANG+ Portfolio
# 📈 Positions: 6
# ├─ AAPL    │ Weight: 20.00% │ Shares: 50  │ Cost: $178.25 │ "Bought on Q4 dip"
# ├─ GOOGL   │ Weight: 20.00% │ Shares: 30  │ Cost: $142.50 │ "Post-earnings entry"
# ├─ NVDA    │ Weight: 10.00% │ Shares: 20  │ Cost: $485.00 │ "AI boom position"
# Total Investment: $22,812.50
```

### 🔍 Use Case 3: Analyzing a Stock Before Purchase

**Scenario**: Deep-dive analysis on ORCL before adding to portfolio.

```bash
# Comprehensive analysis with all data sources
quantlab analyze ticker ORCL \
    --include-fundamentals \
    --include-options \
    --include-sentiment \
    --include-technicals \
    --output results/orcl_analysis.json

# Expected output:
# 🔍 Analyzing ORCL (Oracle Corporation)
#
# 📈 Price Information:
#    Current: $145.50
#    Change: +2.3% ($3.25)
#    Volume: 5,234,567
#
# 💰 Fundamentals:
#    Market Cap: $401.2B
#    P/E Ratio: 28.5
#    Forward P/E: 21.2
#    Revenue Growth: 7.2%
#    Profit Margin: 21.5%
#    Debt/Equity: 2.84
#
# 📊 Options Activity:
#    Put/Call Ratio: 0.78 (Bullish)
#    Implied Volatility: 22.5%
#    Next Earnings: 2025-03-15 (30 days)
#
# 📰 Sentiment Analysis:
#    Score: 0.72 (Positive)
#    Articles: 45 (7 days)
#    Buzz: High
#
# 🎯 Analyst Consensus:
#    Rating: Buy (12) / Hold (8) / Sell (2)
#    Target Price: $165.00 (+13.4%)
#
# ✅ Analysis complete → results/orcl_analysis.json

# Visualize price action
quantlab visualize price ORCL --period 90d --chart-type candlestick
quantlab visualize price ORCL --period 1year --chart-type line

# Quick decision check
quantlab lookup get company ORCL
quantlab lookup get ratings ORCL
```

### 📈 Use Case 4: Portfolio-Wide Analysis

**Scenario**: Analyze all positions in your tech portfolio.

```bash
# Analyze entire portfolio
quantlab analyze portfolio tech_giants \
    --include-options \
    --aggregate-metrics \
    --output results/tech_giants_analysis.json

# Expected output:
# 📊 Analyzing Portfolio: FAANG+ Portfolio (6 positions)
#
# Processing: [████████████████████] 6/6
#
# Individual Analyses:
# ✓ AAPL  │ Score: 82/100 │ Sentiment: Positive │ Analysts: 85% Buy
# ✓ GOOGL │ Score: 78/100 │ Sentiment: Positive │ Analysts: 80% Buy
# ✓ MSFT  │ Score: 88/100 │ Sentiment: Very Positive │ Analysts: 90% Buy
# ✓ META  │ Score: 75/100 │ Sentiment: Neutral │ Analysts: 75% Buy
# ✓ AMZN  │ Score: 81/100 │ Sentiment: Positive │ Analysts: 82% Buy
# ⚠ NVDA  │ Score: 68/100 │ Sentiment: Mixed │ Analysts: 70% Buy
#
# Portfolio Metrics:
# Total Value: $52,450
# Avg P/E: 32.5
# Avg Sentiment: 0.68 (Positive)
# Portfolio Beta: 1.15
# Weighted Analyst Rating: 80% Buy
#
# ⚠️ Alerts:
# - NVDA showing weakness (consider reducing position)
# - MSFT strongest performer (98% of analysts bullish)

# Visualize portfolio performance comparison
quantlab visualize compare AAPL GOOGL MSFT META AMZN NVDA \
    --period 90d \
    --normalize \
    --output results/tech_giants_comparison.html
```

### 🔎 Use Case 5: Querying Historical Data

**Scenario**: Research historical price patterns for backtesting.

```bash
# Query daily stock data
quantlab data query AAPL GOOGL MSFT \
    --start 2024-01-01 \
    --end 2025-01-15 \
    --type stocks_daily \
    --limit 100

# Expected output:
# 📊 Querying data for 3 tickers...
#
# AAPL (Apple Inc.)
# Date Range: 2024-01-01 to 2025-01-15 (252 trading days)
#
# Recent Data (last 5 days):
# Date       │ Open    │ High    │ Low     │ Close   │ Volume
# 2025-01-15 │ $180.25 │ $182.50 │ $179.80 │ $181.75 │ 52.3M
# 2025-01-14 │ $179.50 │ $181.25 │ $178.90 │ $180.25 │ 48.7M
# ...
#
# Performance: +15.3% YTD
# Volatility: 18.5% (annualized)

# Visualize historical price patterns
quantlab visualize price AAPL --period 2year --chart-type candlestick
quantlab visualize price AAPL --interval 5min --period 5d --chart-type line

# Check available data coverage
quantlab data check

# Expected output:
# 📁 Parquet Data Availability
# ✓ stocks_daily    │ 13,187 tickers │ 2024-09-01 to 2025-10-15 (442 days)
# ✓ stocks_minute   │ 8,523 tickers  │ Last 90 days
# ✓ options_daily   │ 3,245 tickers  │ 2024-09-01 to 2025-10-15
# ✗ options_minute  │ Not available
```

### 🏦 Use Case 6: Maintaining Reference Data

**Scenario**: Keep company info and analyst ratings up-to-date.

```bash
# Initialize lookup tables
quantlab lookup init

# Refresh data for your portfolio
quantlab lookup refresh portfolio tech_giants

# Expected output:
# 🔄 Refreshing data for 6 tickers in tech_giants...
#
# Company Info:
# ✓ AAPL  - Apple Inc. (Technology - Consumer Electronics)
# ✓ GOOGL - Alphabet Inc. (Technology - Internet Services)
# ✓ MSFT  - Microsoft Corporation (Technology - Software)
# ✓ META  - Meta Platforms Inc. (Technology - Social Media)
# ✓ AMZN  - Amazon.com Inc. (Consumer Cyclical - Internet Retail)
# ✓ NVDA  - NVIDIA Corporation (Technology - Semiconductors)
#
# Analyst Ratings:
# ✓ AAPL  - 35 analysts (Buy: 28, Hold: 6, Sell: 1) Target: $210
# ✓ GOOGL - 42 analysts (Buy: 35, Hold: 6, Sell: 1) Target: $165
# ✓ MSFT  - 48 analysts (Buy: 43, Hold: 4, Sell: 1) Target: $450
# ✓ META  - 38 analysts (Buy: 28, Hold: 8, Sell: 2) Target: $520
# ✓ AMZN  - 45 analysts (Buy: 38, Hold: 6, Sell: 1) Target: $215
# ✓ NVDA  - 40 analysts (Buy: 32, Hold: 7, Sell: 1) Target: $850
#
# ✅ Refresh complete (6/6 successful)

# View stored data
quantlab lookup stats

# Expected output:
# 📊 Lookup Tables Statistics
#
# Company Information: 6 companies
# Analyst Ratings: 6 tickers (248 total analysts)
# Treasury Rates: Current (updated: 2025-10-15)
# Last Updated: 2025-10-15 14:32:15
```

### 🎯 Use Case 7: Multi-Portfolio Strategy

**Scenario**: Manage multiple portfolios for different strategies.

```bash
# Create portfolios for different strategies
quantlab portfolio create growth --name "High Growth" \
    --description "Growth stocks with P/E > 30"

quantlab portfolio create value --name "Value Plays" \
    --description "Undervalued stocks with P/E < 15"

quantlab portfolio create dividend --name "Dividend Income" \
    --description "High dividend yield stocks"

# Add different stocks to each
quantlab portfolio add growth NVDA TSLA SNOW --weight 0.33
quantlab portfolio add value BAC JPM WFC --weight 0.33
quantlab portfolio add dividend T VZ SO --weight 0.33

# View all portfolios
quantlab portfolio list

# Expected output:
# 📊 Your Portfolios
#
# Portfolio ID    │ Name              │ Positions │ Total Weight │ Last Updated
# ────────────────┼───────────────────┼───────────┼──────────────┼─────────────
# tech_giants     │ FAANG+ Portfolio  │ 6         │ 100.00%      │ 2025-10-15
# growth          │ High Growth       │ 3         │ 99.00%       │ 2025-10-15
# value           │ Value Plays       │ 3         │ 99.00%       │ 2025-10-15
# dividend        │ Dividend Income   │ 3         │ 99.00%       │ 2025-10-15
#
# Total Portfolios: 4
# Total Unique Positions: 15
```

### 🔬 Use Case 8: Options Strategy Research

**Scenario**: Research options opportunities for covered calls.

```bash
# Analyze ticker specifically for options
quantlab analyze ticker AAPL \
    --include-options \
    --no-fundamentals \
    --no-sentiment \
    --output results/aapl_options.json

# Expected output:
# 🔍 Options Analysis: AAPL
#
# Current Price: $181.75
#
# Near-Term Expiration (30 days):
# Call Options (Covered Call Candidates):
# Strike │ Premium │ IV    │ Delta │ Break-even │ Return
# ───────┼─────────┼───────┼───────┼────────────┼────────
# $185   │ $3.85   │ 21.2% │ 0.45  │ $185.00    │ 2.1%
# $190   │ $2.15   │ 19.8% │ 0.28  │ $190.00    │ 4.6%
# $195   │ $0.95   │ 18.5% │ 0.15  │ $195.00    │ 7.3%
#
# Put Options (Cash-Secured Put Candidates):
# Strike │ Premium │ IV    │ Delta │ Net Cost   │ Yield
# ───────┼─────────┼───────┼───────┼────────────┼────────
# $175   │ $2.80   │ 22.5% │ -0.35 │ $172.20    │ 1.6%
# $170   │ $1.45   │ 20.1% │ -0.20 │ $168.55    │ 0.9%
#
# Volatility Metrics:
# Current IV: 21.2%
# Historical Vol (30d): 18.5%
# IV Percentile: 62% (Elevated)
#
# 💡 Suggestion: Good conditions for selling premium
#    IV elevated vs historical - consider covered calls at $190 strike

# Visualize options payoff diagrams
quantlab visualize options long_call --current-price 181.75 --strike 190 --premium 2.15
quantlab visualize options bull_call_spread \
    --current-price 181.75 --strike1 185 --strike2 195 --premium 1.70
```

### 📅 Use Case 9: Regular Portfolio Review

**Scenario**: Monthly portfolio review workflow.

```bash
# Step 1: Refresh all market data
quantlab lookup refresh portfolio tech_giants

# Step 2: Get comprehensive analysis
quantlab analyze portfolio tech_giants --aggregate-metrics

# Step 3: Visualize portfolio performance
quantlab visualize compare AAPL GOOGL MSFT META AMZN NVDA --period 30d --normalize

# Step 4: Review individual positions
quantlab visualize price AAPL --period 90d --chart-type candlestick
quantlab visualize price NVDA --period 90d --chart-type candlestick

# Step 5: Check for rebalancing needs
quantlab portfolio show tech_giants

# Step 6: Look for new opportunities
quantlab data tickers --type stocks_daily | grep -E "^[A-Z]{1,4}$" | head -20
quantlab analyze ticker CRM --include-fundamentals
quantlab visualize price CRM --period 90d --chart-type candlestick

# Step 7: Update positions based on analysis
quantlab portfolio update tech_giants NVDA --weight 0.05 --notes "Reduced - valuation concerns"
quantlab portfolio add tech_giants CRM --weight 0.05 --notes "New position - cloud growth"

# Step 8: Export for records
quantlab analyze portfolio tech_giants --output results/monthly_review_2025_10.json
```

### 🚨 Use Case 10: Risk Monitoring

**Scenario**: Monitor portfolio risk daily.

```bash
# Create a monitoring script
cat > scripts/daily_monitor.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y-%m-%d)

echo "🔍 Daily Portfolio Monitor - $DATE"
echo "=================================="

# Analyze each portfolio
for portfolio in tech_giants growth value dividend; do
    echo ""
    echo "📊 Portfolio: $portfolio"
    quantlab analyze portfolio $portfolio \
        --include-options \
        --output "results/monitoring/${portfolio}_${DATE}.json" 2>&1 | \
        grep -E "(Score:|Sentiment:|Analysts:|⚠|❌)"
done

# Check treasury rates for risk-free rate
echo ""
echo "📈 Current Treasury Rates:"
quantlab lookup get treasury 10y

echo ""
echo "✅ Monitoring complete"
EOF

chmod +x scripts/daily_monitor.sh

# Run daily monitoring
./scripts/daily_monitor.sh

# Expected output:
# 🔍 Daily Portfolio Monitor - 2025-10-15
# ==================================
#
# 📊 Portfolio: tech_giants
# ✓ AAPL  │ Score: 82/100 │ Sentiment: Positive
# ✓ GOOGL │ Score: 78/100 │ Sentiment: Positive
# ⚠ NVDA  │ Score: 68/100 │ Sentiment: Mixed
#
# 📈 Current Treasury Rates:
# 10-Year Treasury: 4.25% (as of 2025-10-15)
#
# ✅ Monitoring complete
```

## 📊 Available Configurations

### 1. **Liquid Universe** (Recommended)
- **File**: `configs/lightgbm_liquid_universe.yaml`
- **Universe**: 13,187 stocks (filtered - no warrants, units)
- **Period**: Sept 2024 - Sept 2025
- **Best for**: Realistic backtesting with tradable stocks

### 2. **Fixed Dates**
- **File**: `configs/lightgbm_fixed_dates.yaml`
- **Universe**: All stocks
- **Period**: July 2024 - Dec 2024
- **Best for**: Testing on stable period

### 3. **Full Universe**
- **File**: `configs/lightgbm_external_data.yaml`
- **Universe**: All 14,310 instruments (includes warrants, penny stocks)
- **Period**: Sept 2024 - Sept 2025
- **Best for**: Maximum alpha discovery (but risky)

## 🎯 Key Metrics from Latest Runs

| Configuration | IC | Rank IC | Sharpe | Max DD | Universe Size |
|--------------|-----|---------|--------|--------|---------------|
| Liquid Universe | 0.066 | -0.006 | 3.94 | -39.2% | 13,187 |
| Fixed Dates | 0.079 | -0.008 | 4.54 | -35.3% | 14,310 |
| Full Universe | 0.080 | -0.004 | 2.98 | -41.7% | 14,310 |

**IC (Information Coefficient)**: 0.06-0.08 is good - shows predictive power
**Rank IC**: Near zero - model struggles with relative ranking
**Sharpe Ratio**: 2.98-4.54 - excellent risk-adjusted returns

## 📊 Visualization Capabilities

QuantLab includes comprehensive interactive visualization tools powered by Plotly.

### Price Charts

```bash
# Candlestick charts (daily data)
quantlab visualize price AAPL --period 90d --chart-type candlestick

# Line charts with volume
quantlab visualize price AAPL --period 1year --chart-type line

# Intraday charts (5min, 15min, 1hour intervals)
quantlab visualize price AAPL --interval 5min --period 5d --chart-type candlestick
quantlab visualize price NVDA --interval 1hour --period 30d --chart-type line
```

**Features:**
- Multiple timeframes: 1d, 5d, 30d, 90d, 1year, 2year
- Intraday intervals: 1min, 5min, 15min, 1hour
- Categorical x-axis for gap-free intraday charts
- Timezone-aware (US Eastern Time)
- Regular market hours filtering (9:30 AM - 4:00 PM ET)

**Example Charts:**
- [Daily Candlestick (90d)](docs/images/price_candlestick_90d.html)
- [Intraday 5-minute Line](docs/images/price_intraday_5min.html)

### Multi-Ticker Comparison

```bash
# Compare normalized performance
quantlab visualize compare AAPL GOOGL MSFT --period 90d --normalize

# Absolute price comparison
quantlab visualize compare AAPL GOOGL MSFT --period 1year
```

**Example Chart:**
- [Normalized Comparison (90d)](docs/images/comparison_normalized.html)

### Options Payoff Diagrams

```bash
# Single leg strategies
quantlab visualize options long_call --current-price 180 --strike 190 --premium 2.15
quantlab visualize options long_put --current-price 180 --strike 175 --premium 2.80

# Spread strategies
quantlab visualize options bull_call_spread \
    --current-price 180 --strike1 185 --strike2 195 --premium 1.70

quantlab visualize options iron_condor \
    --current-price 180 --strike1 170 --strike2 175 --strike3 195 --strike4 200
```

**Available Strategies:**
- Single: `long_call`, `long_put`, `short_call`, `short_put`
- Spreads: `bull_call_spread`, `bear_put_spread`, `iron_condor`, `butterfly`
- Volatility: `long_straddle`, `short_straddle`, `long_strangle`, `short_strangle`

**Example Chart:**
- [Bull Call Spread Payoff](docs/images/options_bull_call_spread.html)

### Backtest Results

```bash
# Visualize backtest performance
quantlab visualize backtest results/mlruns/[experiment_id]
```

**Metrics Displayed:**
- Cumulative returns vs benchmark
- Drawdown analysis
- Rolling Sharpe ratio
- Win/loss distribution
- Monthly returns heatmap

## 📚 Documentation

- **[BACKTEST_SUMMARY.md](docs/BACKTEST_SUMMARY.md)** - Comprehensive analysis of backtest results, root cause analysis, and recommendations
- **[ALPHA158_SUMMARY.md](docs/ALPHA158_SUMMARY.md)** - Overview of Alpha158 features used
- **[USE_QLIB_ALPHA158.md](docs/USE_QLIB_ALPHA158.md)** - How to use Alpha158 in your strategies
- **[CLI_VISUALIZATION_GUIDE.md](docs/CLI_VISUALIZATION_GUIDE.md)** - Complete guide to visualization features

## 🔧 Data Setup

### External Data Location
```
/Volumes/sandisk/quantmini-data/data/qlib/stocks_daily/
├── calendars/day.txt           # Trading calendar (442 days)
├── instruments/
│   ├── all.txt                 # All 14,310 instruments
│   └── liquid_stocks.txt       # Filtered 13,187 instruments
└── features/                   # Stock price data (OHLCV)
```

### Creating Custom Universe Filters

```python
# See scripts/data/ for examples
# Filter by:
# - Market cap
# - Average volume
# - Exclude warrants/units
# - Sector/industry
```

## 🧪 Testing

```bash
# Test Alpha158 features
python scripts/tests/test_qlib_alpha158.py

# Test data conversion
python scripts/data/convert_to_qlib.py

# Refresh latest data
python scripts/data/refresh_today_data.py
```

## 🔍 Next Steps

### Improve Model Performance
1. **Fix Rank IC** - Try ensemble models (XGBoost, TabNet, LSTM)
2. **Better features** - Add momentum, volatility, cross-sectional features
3. **Risk controls** - Add position limits, volatility weighting

### Data Quality
1. Validate corporate actions (splits, dividends)
2. Check for survivorship bias
3. Add liquidity filters (min volume, market cap)

### Alternative Strategies
1. Market-neutral long-short
2. Factor-based weighting
3. Multi-timeframe approaches

## 📝 Notes

- **Data Source**: External data from QuantMini (US stocks, daily, 2024-2025)
- **ML Framework**: Qlib by Microsoft Research
- **Models Tested**: LightGBM with Alpha158 features
- **Tracking**: MLflow for experiment management

## ⚠️ Known Issues

1. **Unrealistic backtest returns** - Investigating data quality and backtest engine
2. **Rank IC near zero** - Model can predict returns but not rank stocks well
3. **High volatility** - Some instruments show extreme price movements
4. See [BACKTEST_SUMMARY.md](docs/BACKTEST_SUMMARY.md) for detailed analysis

## 🤝 Contributing

This is a research project. Key areas for improvement:
- Better universe filters
- Alternative features
- Improved ranking models
- Risk management strategies

## 📄 License

Research and educational purposes.

## 🔗 Resources

- [Qlib Documentation](https://qlib.readthedocs.io/)
- [Qlib GitHub](https://github.com/microsoft/qlib)
- [Alpha158 Paper](https://arxiv.org/abs/2107.08321)
