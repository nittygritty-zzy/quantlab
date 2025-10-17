# QuantLab CLI Visualization Guide

**Date:** October 16, 2025
**Status:** ✅ Complete
**Module:** `quantlab.cli.visualize`

---

## Overview

The QuantLab CLI provides powerful visualization commands to create interactive Plotly charts directly from the command line. All commands generate standalone HTML files that can be opened in any browser.

### Available Commands

```bash
quantlab visualize --help
```

**5 Visualization Commands:**
1. `backtest` - Visualize backtest performance from MLflow runs
2. `price` - Create price charts for individual tickers
3. `compare` - Compare multiple tickers on one chart
4. `portfolio` - Visualize portfolio allocation and P&L
5. `options` - Generate options strategy payoff diagrams

---

## 1. Backtest Visualization

Visualize backtest results from MLflow experiment runs with comprehensive performance metrics.

### Basic Usage

```bash
# View comprehensive dashboard
quantlab visualize backtest <run_id>

# Specific chart types
quantlab visualize backtest <run_id> --chart-type returns
quantlab visualize backtest <run_id> --chart-type drawdown
quantlab visualize backtest <run_id> --chart-type heatmap
quantlab visualize backtest <run_id> --chart-type sharpe

# Custom names and output
quantlab visualize backtest <run_id> \
  --strategy-name "My Strategy" \
  --benchmark-name "SPY" \
  --output results/my_backtest.html
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `run_id` | argument | required | MLflow run ID (from results/mlruns) |
| `--output` | path | auto | Output HTML file path |
| `--strategy-name` | text | "Strategy" | Strategy display name |
| `--benchmark-name` | text | "Benchmark" | Benchmark display name |
| `--chart-type` | choice | "dashboard" | Chart type: dashboard, returns, drawdown, heatmap, sharpe |

### Chart Types

**Dashboard (default):**
- 3-panel comprehensive view
- Cumulative returns (portfolio vs benchmark)
- Drawdown underwater plot
- Rolling 60-day Sharpe ratio

**Returns:**
- Cumulative returns over time
- Portfolio vs benchmark comparison
- Date range selectors (1M, 3M, 6M, YTD, 1Y, ALL)

**Drawdown:**
- Underwater plot showing drawdown percentage
- Maximum drawdown annotation
- Recovery periods highlighted

**Heatmap:**
- Monthly returns calendar view
- Color-coded performance (red/yellow/green)
- Easy to spot seasonality patterns

**Sharpe:**
- Rolling Sharpe ratio (60-day window)
- Risk-adjusted returns timeline
- Zero reference line

### Performance Metrics Displayed

```
📈 Performance Metrics:
   Total Return: X.XX%
   Annual Return: X.XX%
   Sharpe Ratio: X.XX
   Max Drawdown: X.XX%
   Win Rate: X.XX%
```

### Examples

```bash
# View latest backtest results
quantlab visualize backtest 94521661f21b4c2b8ab01337684d983f

# Create returns chart with custom names
quantlab visualize backtest abc123def456 \
  --chart-type returns \
  --strategy-name "Tech Fundamental Strategy" \
  --benchmark-name "QQQ"

# Generate all chart types
for type in dashboard returns drawdown heatmap sharpe; do
  quantlab visualize backtest abc123 --chart-type $type \
    --output results/backtest_$type.html
done
```

### Finding Run IDs

```bash
# List recent runs
ls -lt results/mlruns/*/

# Or use MLflow UI
cd results && mlflow ui
# Open http://localhost:5000
```

---

## 2. Price Charts

Create interactive price charts for individual tickers with volume and moving averages.

### Basic Usage

```bash
# Candlestick chart (default)
quantlab visualize price AAPL

# With custom period
quantlab visualize price MSFT --period 180d

# Line chart with moving averages
quantlab visualize price GOOGL --chart-type line

# Technical analysis dashboard
quantlab visualize price TSLA --chart-type technical --period 90d
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ticker` | argument | required | Stock ticker symbol |
| `--period` | text | "90d" | Time period (30d, 90d, 180d, 1y, etc.) |
| `--chart-type` | choice | "candlestick" | Chart type: candlestick, line, technical |
| `--output` | path | auto | Output HTML file path |

### Chart Types

**Candlestick (default):**
- OHLC bars with volume subplot
- Volume bars colored by price direction
- Interactive zoom and pan
- Hover tooltips with OHLCV data

**Line:**
- Simple line chart with close prices
- Moving averages: 20-day, 50-day, 200-day
- Volume subplot
- Clean and minimal design

**Technical:**
- 4-panel dashboard
- Price with Bollinger Bands
- RSI (14-day)
- MACD with signal and histogram
- Volume

### Period Format

- Days: `30d`, `60d`, `90d`
- Weeks: `1w`, `2w`, `4w`
- Months: `1m`, `3m`, `6m`
- Years: `1y`, `2y`

### Examples

```bash
# Quick AAPL candlestick
quantlab visualize price AAPL

# Deep analysis with technical indicators
quantlab visualize price TSLA --chart-type technical --period 180d

# Create all chart types for MSFT
for type in candlestick line technical; do
  quantlab visualize price MSFT --chart-type $type \
    --output results/msft_$type.html
done
```

---

## 3. Multi-Ticker Comparison

Compare performance of multiple tickers on a single normalized or absolute chart.

### Basic Usage

```bash
# Compare 3 tech stocks (normalized % change)
quantlab visualize compare AAPL MSFT GOOGL

# Compare with custom period
quantlab visualize compare AAPL MSFT GOOGL --period 180d

# Absolute price comparison (not normalized)
quantlab visualize compare TSLA NIO RIVN --absolute

# Custom output path
quantlab visualize compare SPY QQQ DIA IWM \
  --period 1y \
  --output results/etf_comparison.html
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `tickers` | arguments | required | 2+ ticker symbols to compare |
| `--period` | text | "90d" | Time period |
| `--normalize/--absolute` | flag | normalize | Normalize to % change or show absolute prices |
| `--output` | path | auto | Output HTML file path |

### Normalized vs Absolute

**Normalized (default):**
- All tickers start at 0%
- Shows relative performance
- Best for comparing returns across different price levels
- Example: AAPL $200 vs GOOGL $150 both start at 0%

**Absolute:**
- Shows actual price levels
- Useful for price level comparison
- Can see absolute price differences
- Example: AAPL at $230, GOOGL at $170

### Examples

```bash
# Compare FAANG stocks (normalized)
quantlab visualize compare META AAPL AMZN NFLX GOOGL --period 1y

# Compare similar-priced stocks (absolute)
quantlab visualize compare JPM BAC WFC --absolute --period 90d

# Compare against benchmark
quantlab visualize compare AAPL MSFT SPY --period 180d

# Maximum 5 tickers recommended for readability
quantlab visualize compare AAPL MSFT GOOGL AMZN META
```

### Tips

- **2-5 tickers:** Optimal readability
- **6+ tickers:** Chart may become cluttered
- Use normalized mode for different price ranges
- Use absolute mode for similar-priced stocks

---

## 4. Portfolio Visualization

Visualize portfolio allocation, P&L, and position breakdown.

### Basic Usage

```bash
# Portfolio dashboard (allocation + P&L + winners/losers)
quantlab visualize portfolio tech

# Just allocation pie chart
quantlab visualize portfolio growth --chart-type allocation

# Just P&L bar chart
quantlab visualize portfolio value --chart-type pnl

# Custom output
quantlab visualize portfolio income \
  --output results/income_portfolio_dashboard.html
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `portfolio_id` | argument | required | Portfolio name/ID |
| `--chart-type` | choice | "dashboard" | Chart type: dashboard, allocation, pnl |
| `--output` | path | auto | Output HTML file path |

### Chart Types

**Dashboard (default):**
- 4-panel comprehensive view
- Top left: Allocation pie chart
- Top right: P&L bar chart
- Bottom left: Top winners (top 5)
- Bottom right: Top losers (bottom 5)

**Allocation:**
- Donut pie chart showing position weights
- Percentage labels for each position
- Hover for detailed values
- Center annotation with total value

**P&L:**
- Horizontal bar chart of position P&L
- Green bars for profits
- Red bars for losses
- Sorted by P&L amount

### Portfolio Metrics Displayed

```
💼 Loading portfolio: tech...

✓ Loaded portfolio: 7 positions
   Total Value: $150,000.00
   Total P&L: $12,000.00 (8.00%)
```

### Examples

```bash
# View all portfolios
quantlab portfolio list

# Visualize specific portfolio
quantlab visualize portfolio tech_growth

# Compare multiple portfolios (create separate charts)
for portfolio in tech growth value income; do
  quantlab visualize portfolio $portfolio \
    --output results/${portfolio}_dashboard.html
done
```

### Requirements

- Portfolio must exist in QuantLab database
- Use `quantlab portfolio list` to see available portfolios
- Use `quantlab portfolio create` to create new portfolios

---

## 5. Options Strategy Payoff

Generate interactive payoff diagrams for options strategies.

### Basic Usage

```bash
# Single leg strategies
quantlab visualize options long_call \
  --current-price 100 --strike 100 --premium 5

quantlab visualize options long_put \
  --current-price 100 --strike 100 --premium 4

# Two-leg spread strategies
quantlab visualize options bull_call_spread \
  --current-price 100 --strike1 95 --strike2 105

# Four-leg strategies
quantlab visualize options iron_condor \
  --current-price 100 \
  --strike1 90 --strike2 95 --strike3 105 --strike4 110 \
  --premium 6
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `strategy_type` | argument | yes | Strategy name (see list below) |
| `--current-price` | float | yes | Current underlying price |
| `--strike` | float | depends | Strike price (single leg) |
| `--strike1` | float | depends | First strike (multi-leg) |
| `--strike2` | float | depends | Second strike (multi-leg) |
| `--strike3` | float | depends | Third strike (4-leg) |
| `--strike4` | float | depends | Fourth strike (4-leg) |
| `--premium` | float | depends | Premium paid/received |
| `--output` | path | no | Output HTML file path |

### Available Strategies

**Single Leg (--strike, --premium required):**
- `long_call` - Bullish, unlimited profit
- `long_put` - Bearish, limited profit

**Two-Leg Spreads (--strike1, --strike2 required):**
- `bull_call_spread` - Moderately bullish, defined risk
- `bear_put_spread` - Moderately bearish, defined risk

**Volatility Plays (--strike, --premium required):**
- `long_straddle` - High volatility expected, long ATM call + put
- `short_straddle` - Low volatility expected, short ATM call + put
- `long_strangle` - High volatility, long OTM call + OTM put (--strike1, --strike2)
- `short_strangle` - Low volatility, short OTM call + OTM put (--strike1, --strike2)

**Four-Leg Strategies (--strike1/2/3/4 required):**
- `iron_condor` - Range-bound, sell put spread + call spread

### Payoff Diagram Features

- **Breakeven points:** Marked with vertical dashed lines
- **Current price:** Highlighted reference line
- **Max profit:** Horizontal green line (if defined)
- **Max loss:** Horizontal red line (if defined)
- **Profit zone:** Green shaded region
- **Loss zone:** Red shaded region
- **P&L curve:** Interactive line with hover tooltips

### Strategy Summary Display

```
✓ Strategy: Long Call
   Current Price: $100.00
   Breakeven: $105.00
   Max Profit: Unlimited
   Max Loss: $-5.00
```

### Examples

```bash
# Long call (bullish)
quantlab visualize options long_call \
  --current-price 100 --strike 100 --premium 5

# Bull call spread (moderately bullish, defined risk)
quantlab visualize options bull_call_spread \
  --current-price 100 --strike1 95 --strike2 105

# Iron condor (range-bound, neutral)
quantlab visualize options iron_condor \
  --current-price 100 \
  --strike1 90 --strike2 95 --strike3 105 --strike4 110 \
  --premium 6

# Long straddle (high volatility expected)
quantlab visualize options long_straddle \
  --current-price 100 --strike 100 --premium 10

# Create multiple strategies for comparison
for strategy in long_call long_put long_straddle; do
  quantlab visualize options $strategy \
    --current-price 100 --strike 100 --premium 5 \
    --output results/${strategy}_payoff.html
done
```

---

## Common Workflows

### 1. Complete Ticker Analysis

```bash
TICKER="AAPL"
PERIOD="180d"

# Price analysis
quantlab visualize price $TICKER --period $PERIOD
quantlab visualize price $TICKER --chart-type technical --period $PERIOD

# Compare to benchmark
quantlab visualize compare $TICKER SPY QQQ --period $PERIOD

# Options strategy analysis
quantlab visualize options long_call \
  --current-price 230 --strike 230 --premium 10
```

### 2. Portfolio Review

```bash
PORTFOLIO="tech_growth"

# Visualize current state
quantlab visualize portfolio $PORTFOLIO

# Compare performance to benchmark
quantlab portfolio show $PORTFOLIO | grep -E "^[A-Z]+" | \
  xargs quantlab visualize compare --period 90d

# Individual position deep dives
for ticker in AAPL MSFT GOOGL; do
  quantlab visualize price $ticker --chart-type technical
done
```

### 3. Backtest Analysis

```bash
RUN_ID="abc123def456"

# Create all backtest charts
for type in dashboard returns drawdown heatmap sharpe; do
  quantlab visualize backtest $RUN_ID \
    --chart-type $type \
    --strategy-name "My Strategy" \
    --benchmark-name "SPY" \
    --output results/backtest_$type.html
done

# Compare strategy stocks to benchmark
quantlab visualize compare AAPL MSFT GOOGL SPY --period 1y
```

### 4. Options Strategy Comparison

```bash
PRICE=100

# Create multiple strategies
strategies=(
  "long_call --strike 100 --premium 5"
  "bull_call_spread --strike1 95 --strike2 105"
  "long_straddle --strike 100 --premium 10"
  "iron_condor --strike1 90 --strike2 95 --strike3 105 --strike4 110 --premium 6"
)

for strategy in "${strategies[@]}"; do
  strategy_name=$(echo $strategy | awk '{print $1}')
  quantlab visualize options $strategy --current-price $PRICE \
    --output results/options_${strategy_name}.html
done
```

---

## Output Files

### Default Naming Convention

| Command | Default Output Path |
|---------|---------------------|
| `backtest <run_id>` | `results/backtest_<type>_<run_id_prefix>.html` |
| `price <ticker>` | `results/<ticker>_<chart_type>_<period>.html` |
| `compare <tickers...>` | `results/compare_<ticker1>_<ticker2>_..._<period>.html` |
| `portfolio <id>` | `results/portfolio_<id>_<chart_type>.html` |
| `options <strategy>` | `results/options_<strategy>.html` |

### Custom Output Paths

All commands support `--output` flag:

```bash
# Specific file
quantlab visualize price AAPL --output ~/Desktop/aapl_chart.html

# Organized by date
DATE=$(date +%Y%m%d)
quantlab visualize backtest abc123 --output results/backtest_${DATE}.html

# Organized by category
mkdir -p results/{backtest,price,portfolio}
quantlab visualize price AAPL --output results/price/aapl_90d.html
```

---

## Interactive Features

All generated charts support:

### Navigation
- **Zoom:** Click and drag to select region
- **Pan:** Shift + click and drag
- **Reset:** Double-click chart
- **Box select:** Click box select icon in toolbar
- **Lasso select:** Click lasso icon in toolbar

### Tooltips
- **Hover:** Move mouse over data points for details
- **Compare:** Hover shows all series at same x-position

### Controls
- **Legend:** Click to toggle series visibility
- **Download:** Click camera icon to save as PNG
- **Zoom in/out:** Click +/- buttons
- **Autoscale:** Click autoscale icon to reset axes

### Range Selectors (where available)
- **1M, 3M, 6M:** Quick time range selection
- **YTD:** Year to date
- **1Y:** One year
- **ALL:** Full data range

---

## Tips and Best Practices

### Performance
- **Large datasets:** Use shorter periods for faster loading
- **Multiple tickers:** Limit to 5 tickers for clarity
- **Technical charts:** May take longer due to indicator calculations

### Data Availability
- **Price data:** Requires Parquet data in configured location
- **Backtest data:** Requires completed MLflow run with results
- **Portfolio data:** Requires portfolio created in QuantLab

### Troubleshooting

**"No data available":**
```bash
# Check data availability
quantlab init

# Verify ticker exists
quantlab lookup ticker <TICKER>

# Check date range
quantlab data info
```

**"Portfolio not found":**
```bash
# List available portfolios
quantlab portfolio list

# Create portfolio if needed
quantlab portfolio create <name>
```

**"Run not found":**
```bash
# Browse runs with MLflow UI
cd results && mlflow ui

# Or list runs
ls results/mlruns/*/
```

### Output Management

```bash
# Clean old results
rm results/*.html

# Organize by date
mkdir -p results/$(date +%Y%m%d)
quantlab visualize price AAPL --output results/$(date +%Y%m%d)/aapl.html

# Batch processing
for ticker in AAPL MSFT GOOGL; do
  quantlab visualize price $ticker --output results/${ticker}.html &
done
wait
```

---

## Integration with Other Tools

### Jupyter Notebooks

```python
from IPython.display import IFrame

# Display chart inline
IFrame('results/aapl_candlestick_90d.html', width=1000, height=600)
```

### Streamlit

```python
import streamlit as st
from pathlib import Path

# Read and display HTML
html_file = Path("results/backtest_dashboard.html").read_text()
st.components.v1.html(html_file, height=800)
```

### Email Reports

```bash
# Generate charts
quantlab visualize portfolio tech --output /tmp/portfolio.html
quantlab visualize price AAPL --output /tmp/aapl.html

# Email with attachments
echo "Daily Report" | mail -s "Portfolio Update" \
  -a /tmp/portfolio.html -a /tmp/aapl.html user@example.com
```

---

## Command Reference Summary

```bash
# General format
quantlab visualize <command> [arguments] [options]

# Commands
backtest <run_id>              # Backtest performance analysis
price <ticker>                 # Price charts
compare <ticker1> <ticker2>... # Multi-ticker comparison
portfolio <portfolio_id>       # Portfolio visualization
options <strategy>             # Options payoff diagrams

# Common options
--output <path>                # Custom output file
--period <time>                # Time period (30d, 90d, 1y)
--chart-type <type>            # Chart type (varies by command)

# Help
quantlab visualize --help
quantlab visualize <command> --help
```

---

## Future Enhancements

Potential additions in future versions:

1. **Real-time updates:** WebSocket integration for live charts
2. **PDF export:** Direct PDF generation without browser
3. **Annotations:** Add custom notes and markers
4. **Themes:** Dark mode and custom color schemes
5. **Mobile views:** Responsive mobile-optimized charts
6. **Batch mode:** Generate multiple charts in one command
7. **Templates:** Customizable chart templates
8. **API mode:** HTTP API for remote chart generation

---

## Related Documentation

- **Visualization Functions:** `docs/VISUALIZATION_COMPLETE_SUMMARY.md`
- **Backtest Charts:** `docs/BACKTEST_VISUALIZATION_SUMMARY.md`
- **Price Charts:** `docs/PRICE_CHARTS_SUMMARY.md`
- **Options Charts:** `docs/OPTIONS_CHARTS_SUMMARY.md`
- **CLI Overview:** `QUICKSTART.md`

---

**Document Version:** 1.0
**Last Updated:** October 16, 2025
**Author:** Claude Code
**Status:** Complete ✅
