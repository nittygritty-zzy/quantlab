# QuantLab Stock Screener Guide

**Status:** Phase 1-5 Complete ✅
**Date:** October 16, 2025
**Version:** 3.0.0 (includes Phase 4 Advanced Features + Phase 5 Visualizations)

## Overview

The QuantLab stock screener enables multi-criteria filtering across 19,000+ stocks using technical indicators, fundamental data, sentiment analysis, and custom combinations.

## Quick Start

### Basic Usage

```bash
# Find oversold stocks (simple preset)
quantlab screen preset oversold --limit 20

# Custom technical screen
quantlab screen custom \
    --universe AAPL --universe MSFT --universe GOOGL \
    --rsi-max 40 \
    --limit 10

# Find value stocks
quantlab screen preset value-stocks --limit 30

# Technical screen with specific criteria
quantlab screen technical \
    --rsi-max 30 \
    --volume-min 1000000 \
    --limit 50 \
    --output results/oversold_stocks.json
```

## Available Commands

### 1. `quantlab screen technical`

Screen by technical indicators only (fastest - no API calls).

**Options:**
- `--rsi-min`, `--rsi-max` - RSI range (0-100)
- `--macd-signal` - `bullish` or `bearish`
- `--sma-crossover` - `golden` or `death` cross
- `--price-above-sma20` - Price above 20-day SMA
- `--price-above-sma50` - Price above 50-day SMA
- `--bb-position` - Bollinger Bands position (`above_upper`, `below_lower`, `middle`)
- `--adx-min` - Minimum ADX (25+ = strong trend)
- `--volume-min` - Minimum daily volume
- `--price-min`, `--price-max` - Price range

**Example:**
```bash
# Find stocks with bullish MACD and strong trend
quantlab screen technical \
    --macd-signal bullish \
    --adx-min 25 \
    --volume-min 1000000 \
    --limit 20
```

### 2. `quantlab screen fundamental`

Screen by fundamental data (requires API calls - slower).

**Options:**
- `--pe-min`, `--pe-max` - P/E ratio range
- `--forward-pe-max` - Maximum forward P/E
- `--peg-ratio-max` - Maximum PEG ratio (<1 is good)
- `--revenue-growth-min` - Minimum revenue growth %
- `--profit-margin-min` - Minimum profit margin %
- `--roe-min` - Minimum return on equity %
- `--debt-equity-max` - Maximum debt/equity ratio
- `--market-cap-min`, `--market-cap-max` - Market cap in billions
- `--min-analysts` - Minimum analyst coverage
- `--recommendation` - Analyst recommendation (`buy`, `hold`, `sell`)

**Example:**
```bash
# Find high-quality growth stocks
quantlab screen fundamental \
    --revenue-growth-min 20 \
    --profit-margin-min 15 \
    --debt-equity-max 1.0 \
    --limit 30
```

### 3. `quantlab screen combined`

Combine technical, fundamental, and sentiment criteria (slowest - comprehensive).

**Example:**
```bash
# Find undervalued stocks with positive momentum
quantlab screen combined \
    --rsi-max 35 \
    --pe-max 20 \
    --revenue-growth-min 10 \
    --sentiment-min 0.6 \
    --limit 25
```

### 4. `quantlab screen preset`

Run predefined screening strategies.

**Available Presets:**

| Preset | Description | Criteria |
|--------|-------------|----------|
| `value-stocks` | Low P/E, good fundamentals | P/E < 15, debt/equity < 1.5, revenue growth > 5%, profit margin > 10% |
| `growth-stocks` | High revenue growth, strong margins | Revenue growth > 20%, profit margin > 15%, market cap > $1B |
| `oversold` | RSI < 30, high volume | RSI < 30, volume > 1M, price > $5 |
| `overbought` | RSI > 70, potential reversal | RSI > 70, volume > 1M, price > $5 |
| `momentum` | Bullish MACD, strong trend | MACD bullish, ADX > 25, volume > 1M, price > SMA50 |
| `quality` | High margins, low debt, good growth | Profit margin > 20%, debt/equity < 1.0, revenue growth > 10%, ROE > 15% |

**Example:**
```bash
# Run value stocks preset
quantlab screen preset value-stocks --limit 20

# Run oversold preset with output
quantlab screen preset oversold \
    --limit 50 \
    --output results/oversold_$(date +%Y%m%d).json
```

### 5. `quantlab screen custom`

Maximum flexibility with custom universe and criteria.

**Options:**
- `--universe` - Specific ticker (can specify multiple times)
- `--universe-file` - File with tickers (one per line)
- `--workers` - Number of parallel workers (default: 4)
- All technical and fundamental options

**Example:**
```bash
# Screen custom watchlist
quantlab screen custom \
    --universe-file my_watchlist.txt \
    --rsi-max 40 \
    --pe-max 25 \
    --limit 20

# Screen specific tickers
quantlab screen custom \
    --universe AAPL --universe MSFT --universe GOOGL \
    --rsi-max 50 \
    --volume-min 500000
```

## Output Format

### Terminal Display

Results are displayed as formatted tables:

```
✅ Found 3 matching stocks

📊 Technical Screen Results:

ticker    price      rsi    macd_histogram    score
--------  -------  -----  ----------------  -------
AAON      $78.69    42.2            -0.297     60.0
AAPL      $182.50   55.3             0.125     72.5
MSFT      $415.20   48.9            -0.082     68.3
```

### JSON Output

Use `--output <file.json>` to save results:

```json
{
  "screen_name": "Technical Screen",
  "num_results": 3,
  "results": [
    {
      "ticker": "AAON",
      "price": 78.69,
      "rsi": 42.2,
      "macd_histogram": -0.297,
      "score": 60.0
    }
  ]
}
```

## Scoring System

When `include_score=True` (default for combined screens), stocks receive a 0-100 score:

**Technical (30 points):**
- RSI 40-60: +10 points
- Bullish MACD: +10 points
- Strong trend (ADX > 25): +10 points

**Fundamental (40 points):**
- P/E 10-25: +10 points
- Revenue growth > 20%: +15 points
- Profit margin > 20%: +10 points
- Debt/equity < 1.0: +5 points

**Sentiment (30 points):**
- Based on sentiment score (0-1 scale × 30)

**Total:** Capped at 100 points

## Performance Notes

### Speed Estimates

| Screen Type | Universe Size | Time Estimate |
|-------------|---------------|---------------|
| Technical (custom, 10 tickers) | 10 | <5 seconds |
| Technical (custom, 100 tickers) | 100 | 10-20 seconds |
| Technical (full universe) | 19,382 | 5-10 minutes |
| Fundamental (custom, 10 tickers) | 10 | 30-60 seconds |
| Fundamental (full universe) | 19,382 | 3-6 hours |
| Combined (custom, 50 tickers) | 50 | 2-5 minutes |

### Performance Tips

1. **Use Custom Universe** - Screen specific tickers for faster results:
   ```bash
   quantlab screen custom --universe-file sp500.txt --rsi-max 30
   ```

2. **Technical-Only First** - Run technical screens first, then fundamental on results:
   ```bash
   # Step 1: Technical screen (fast)
   quantlab screen technical --rsi-max 30 --output step1.json

   # Step 2: Extract tickers and run fundamental (slow but targeted)
   quantlab screen custom --universe-file step1_tickers.txt --pe-max 20
   ```

3. **Increase Workers** - Use more parallel workers for large screens:
   ```bash
   quantlab screen custom --workers 8 --rsi-max 40
   ```

4. **Save Results** - Always save results to avoid re-running:
   ```bash
   quantlab screen preset oversold \
       --output results/oversold_$(date +%Y%m%d).json
   ```

## Data Requirements

### Historical Price Data

- **Source:** Parquet files (stocks_daily)
- **Tickers:** 19,382 available
- **Date Range:** 2020-10-16 to 2025-10-14
- **Lookback:** 90 days for technical indicators

### API Data (Optional)

- **Fundamentals:** yfinance API (no key required)
- **Sentiment:** Alpha Vantage API (key in config)
- **Rate Limits:** Respected automatically

## Common Workflows

### 1. Daily Oversold Scanner

```bash
#!/bin/bash
# daily_scanner.sh

DATE=$(date +%Y%m%d)

# Find oversold stocks
quantlab screen preset oversold \
    --limit 50 \
    --output results/oversold_$DATE.json

# Analyze top candidates
for ticker in $(jq -r '.results[0:5].ticker' results/oversold_$DATE.json); do
    echo "Analyzing $ticker..."
    quantlab analyze ticker $ticker --include-fundamentals
done
```

### 2. Value Stock Research

```bash
# Step 1: Find value stocks
quantlab screen preset value-stocks \
    --limit 100 \
    --output results/value_candidates.json

# Step 2: Visualize top picks
quantlab visualize compare AAPL MSFT GOOGL --period 90d
```

### 3. Portfolio Screening

```bash
# Create portfolio from screen results
quantlab screen preset quality --limit 20 --output quality.json

# Import to portfolio
quantlab portfolio create quality_picks \
    --name "Quality Stocks" \
    --description "From quality preset screen"

# Add positions
quantlab portfolio add quality_picks AAPL MSFT GOOGL
```

## Troubleshooting

### "No stocks matched criteria"

- **Solution 1:** Relax filters (increase max values, decrease min values)
- **Solution 2:** Check universe has recent data
- **Solution 3:** Try a different preset

### "Retrieved 0 rows of stock data"

- **Cause:** Ticker not available in parquet data
- **Solution:** Check available tickers with `quantlab data tickers`
- **Note:** Only stocks with data in the last 90 days are screened

### Slow Performance

- **Solution 1:** Use smaller custom universe
- **Solution 2:** Use technical-only screens first
- **Solution 3:** Increase `--workers` parameter
- **Solution 4:** Screen during off-peak hours for API calls

## Advanced Features (Phase 4) ✅

### 6. `quantlab screen saved` - Template Management

Save and reuse screening criteria as named templates.

**Actions:**
- `save` - Save screening criteria
- `list` - List all saved screens
- `load` - Show screen details
- `run` - Execute saved screen
- `delete` - Delete saved screen
- `export` - Export to JSON file
- `import` - Import from JSON file

**Examples:**
```bash
# Save a custom screen
quantlab screen saved save --id my_oversold \
    --name "My Oversold Strategy" \
    --description "RSI < 30 with high volume" \
    --rsi-max 30 --volume-min 1000000 \
    --tags oversold --tags technical

# List all saved screens
quantlab screen saved list

# Run saved screen
quantlab screen saved run --id my_oversold --limit 20

# Export for sharing
quantlab screen saved export --id my_oversold --file my_screen.json

# Import from colleague
quantlab screen saved import --file colleague_screen.json
```

**Use Cases:**
- Reuse frequently-used screens without recreating criteria
- Share successful strategies with team members
- Track which screens you run most often
- Build a library of proven screening strategies

---

### 7. `quantlab screen backtest` - Historical Validation

Test screening criteria over historical periods to validate effectiveness.

**Options:**
- `--saved-id` - ID of saved screen to backtest
- `--start-date` - Start date (YYYY-MM-DD)
- `--end-date` - End date (YYYY-MM-DD)
- `--frequency` - Rebalance frequency (daily/weekly/monthly)
- `--output` - Save backtest report to JSON

**Examples:**
```bash
# Backtest saved screen
quantlab screen backtest --saved-id my_oversold \
    --start-date 2025-01-01 \
    --end-date 2025-10-01 \
    --frequency weekly

# Backtest custom criteria
quantlab screen backtest --rsi-max 30 --volume-min 1000000 \
    --start-date 2025-04-01 --end-date 2025-10-01 \
    --output backtest_results.json
```

**Output Metrics:**
- **Total Return** - Cumulative return over period
- **Annualized Return** - Return normalized to annual rate
- **Sharpe Ratio** - Risk-adjusted return metric
- **Max Drawdown** - Largest peak-to-trough decline
- **Win Rate** - Percentage of periods with positive returns
- **Alpha** - Excess return vs benchmark (SPY)

**Use Cases:**
- Validate screening strategies before live trading
- Compare multiple strategies historically
- Optimize parameters (find best RSI threshold, etc.)
- Build confidence in screening criteria

---

### 8. `quantlab screen compare-multi` - Multi-Strategy Analysis

Compare multiple screening strategies side-by-side to find consensus picks.

**Options:**
- `--saved` - Saved screen ID (can specify multiple)
- `--preset` - Preset strategy (can specify multiple)
- `--limit` - Max results per screen
- `--output` - Save report to Excel/JSON
- `--format` - Output format (excel/json)

**Examples:**
```bash
# Compare multiple saved screens
quantlab screen compare-multi \
    --saved my_oversold \
    --saved my_momentum \
    --saved my_value \
    --output comparison.xlsx

# Compare preset strategies
quantlab screen compare-multi \
    --preset value-stocks \
    --preset growth-stocks \
    --preset quality

# Mix saved and presets
quantlab screen compare-multi \
    --saved my_custom \
    --preset oversold \
    --preset momentum \
    --output comparison.xlsx
```

**Output Includes:**
- **Overlap Analysis** - How many stocks in each screen, unique vs shared
- **Consensus Picks** - Stocks found by multiple strategies (high conviction)
- **Comparison Metrics** - Avg price, volume, market cap, sector diversity
- **Individual Results** - Full results for each screen

**Use Cases:**
- Find high-conviction picks (consensus stocks)
- Compare strategy effectiveness side-by-side
- Understand strategy overlap and diversification
- Validate strategies against each other

---

### 9. `quantlab screen watch-monitor` - Real-Time Monitoring

Monitor saved screens with scheduled checking and real-time alerts.

**Actions:**
- `start` - Start monitoring session
- `stop` - Stop monitoring session
- `list` - List active sessions
- `run-cycle` - Manually run one check
- `alerts` - View alert history

**Options:**
- `--screen-id` - Saved screen to monitor
- `--interval` - Check interval (15m, 1h, 4h, 1d)
- `--alert-on` - Alert types (entry, exit, price_change, volume_spike)
- `--since-hours` - Show alerts from last N hours
- `--unack-only` - Show only unacknowledged alerts

**Examples:**
```bash
# Start monitoring oversold screen
quantlab screen watch-monitor start --screen-id my_oversold \
    --interval 1h \
    --alert-on entry --alert-on exit

# List active sessions
quantlab screen watch-monitor list

# Run one check manually
quantlab screen watch-monitor run-cycle

# View recent alerts
quantlab screen watch-monitor alerts --since-hours 24

# Stop monitoring
quantlab screen watch-monitor stop --session-id my_oversold_20251016_120000
```

**Alert Types:**
- **Entry** - Stock newly qualifies for screen
- **Exit** - Stock no longer qualifies
- **Price Change** - Significant price movement (>5%)
- **Volume Spike** - Volume > 2x previous (abnormal activity)

**Use Cases:**
- Monitor oversold conditions for entry opportunities
- Track when stocks exit profitable screens
- Alert on unusual activity (volume spikes)
- Automate repetitive screening tasks

---

## Phase 4 Complete Workflows

### 1. Build and Validate a Strategy

```bash
# Step 1: Create and save a custom screen
quantlab screen saved save --id momentum_quality \
    --name "Momentum + Quality" \
    --description "Bullish MACD with strong margins" \
    --macd-signal bullish \
    --adx-min 20 \
    --profit-margin-min 15 \
    --debt-equity-max 1.5

# Step 2: Backtest the strategy
quantlab screen backtest --saved-id momentum_quality \
    --start-date 2024-01-01 \
    --end-date 2025-10-01 \
    --frequency weekly \
    --output backtest/momentum_quality.json

# Step 3: If backtest looks good, start monitoring
quantlab screen watch-monitor start \
    --screen-id momentum_quality \
    --interval 1h \
    --alert-on entry --alert-on exit
```

### 2. Find Consensus Opportunities

```bash
# Compare 3 different strategies
quantlab screen compare-multi \
    --preset oversold \
    --preset value-stocks \
    --preset quality \
    --output consensus/multi_strategy.xlsx

# The consensus picks (stocks in 2+ screens) are high-conviction opportunities
```

### 3. Daily Trading Routine

```bash
#!/bin/bash
# trading_routine.sh

DATE=$(date +%Y%m%d)

# 1. Run watch cycle to check all monitored screens
echo "Checking monitored screens..."
quantlab screen watch-monitor run-cycle

# 2. View new alerts
echo "New alerts:"
quantlab screen watch-monitor alerts --since-hours 24 --unack-only

# 3. Run saved screens for fresh ideas
quantlab screen saved run --id my_breakout \
    --output results/breakout_$DATE.json

quantlab screen saved run --id my_value \
    --output results/value_$DATE.json

# 4. Compare results
quantlab screen compare-multi \
    --saved my_breakout \
    --saved my_value \
    --output results/daily_comparison_$DATE.xlsx
```

---

## Complete Command Reference

### Basic Screening Commands

| Command | Purpose | Speed |
|---------|---------|-------|
| `screen technical` | Technical indicators only | Fast (no API) |
| `screen fundamental` | Fundamental data only | Slow (API calls) |
| `screen combined` | Technical + Fundamental + Sentiment | Slowest (comprehensive) |
| `screen preset` | Predefined strategies | Varies |
| `screen custom` | Maximum flexibility | Depends on criteria |

### Advanced Commands (Phase 4)

| Command | Purpose | Requirements |
|---------|---------|--------------|
| `screen saved` | Template management | None |
| `screen backtest` | Historical validation | Historical data |
| `screen compare-multi` | Multi-strategy analysis | None |
| `screen watch-monitor` | Real-time monitoring | Saved screens |

### Phase 3 Commands

| Command | Purpose | Requirements |
|---------|---------|--------------|
| `screen export` | Export to Excel/CSV | Screen results JSON |
| `screen watch` | Watchlist management | None |
| `screen compare` | Compare two screens | 2 result files |

---

## Visualizations (Phase 5) ✅

### 10. `quantlab visualize screen-backtest` - Backtest Visualization

Generate interactive HTML reports from screen backtest results with 6 key charts.

**Charts Included:**
- Cumulative returns (strategy vs benchmark)
- Drawdown chart
- Rolling Sharpe ratio (30-period window)
- Performance metrics dashboard
- Returns distribution histogram
- Win rate bar chart

**Example:**
```bash
# Step 1: Run backtest
quantlab screen backtest --saved-id my_oversold \
    --start-date 2025-01-01 --end-date 2025-10-01 \
    --output backtest.json

# Step 2: Visualize
quantlab visualize screen-backtest --input backtest.json \
    --output backtest_report.html

# Step 3: Open in browser
open backtest_report.html
```

**Features:**
- Interactive zoom/pan on all charts
- Hover tooltips with detailed data
- Benchmark comparison (SPY)
- Self-contained HTML (shareable)

---

### 11. `quantlab visualize screen-comparison` - Comparison Visualization

Visualize screen comparison results with overlap and consensus analysis.

**Charts Included:**
- Screen size comparison bar chart
- Overlap analysis (stocks in multiple screens)
- Sector distribution comparison (grouped bars)
- Consensus picks interactive table

**Example:**
```bash
# Step 1: Compare screens
quantlab screen compare-multi \
    --saved oversold --saved momentum --saved value \
    --output comparison.json

# Step 2: Visualize
quantlab visualize screen-comparison --input comparison.json \
    --output comparison_report.html

# Step 3: Review
open comparison_report.html
```

**Use Cases:**
- Identify consensus picks visually
- Compare sector allocations
- Understand strategy overlap

---

### 12. `quantlab visualize screen-results` - Screening Results Visualization

Create distribution analysis charts for screening results.

**Charts Included:**
- Sector distribution pie chart
- Industry breakdown (top 15)
- Price vs volume scatter plot (colored by RSI)
- Metric distribution histograms (P/E, RSI, volume, etc.)

**Example:**
```bash
# Step 1: Run screen
quantlab screen run --rsi-max 30 --volume-min 1000000 \
    --output screening.json

# Step 2: Visualize
quantlab visualize screen-results --input screening.json \
    --output screening_report.html

# Step 3: Explore
open screening_report.html
```

**Use Cases:**
- Understand sector/industry distribution
- Identify outliers in price/volume
- Analyze metric distributions

---

### 13. `quantlab visualize screen-alerts` - Watch Alerts Visualization

Visualize watch mode alert patterns with time-series analysis.

**Charts Included:**
- Alert timeline (Gantt-style)
- Alert type breakdown pie chart
- Ticker frequency heatmap (top 20 most active)
- Daily alert count line chart

**Example:**
```bash
# Step 1: Export alerts (manual JSON creation currently needed)
# Create alerts.json with alert data

# Step 2: Visualize
quantlab visualize screen-alerts --input alerts.json \
    --output alerts_report.html

# Step 3: Analyze patterns
open alerts_report.html
```

**Use Cases:**
- Identify temporal alert patterns
- Find most active tickers
- Analyze alert frequency trends

---

## Phase 5 Complete Workflows

### 1. Backtest and Visualize Strategy

```bash
# Complete workflow from screen creation to visualization
quantlab screen saved save --id trend_quality \
    --name "Trend + Quality" \
    --macd-signal bullish --adx-min 25 \
    --profit-margin-min 15 --roe-min 12

quantlab screen backtest --saved-id trend_quality \
    --start-date 2024-01-01 --end-date 2025-10-01 \
    --output backtest.json

quantlab visualize screen-backtest --input backtest.json \
    --output trend_quality_report.html

open trend_quality_report.html
```

### 2. Compare Strategies with Visual Analysis

```bash
# Compare multiple strategies and visualize overlap
quantlab screen compare-multi \
    --saved oversold --saved momentum --saved value \
    --output comparison.json

quantlab visualize screen-comparison --input comparison.json \
    --output strategy_comparison.html

open strategy_comparison.html
```

### 3. Screen and Analyze Distributions

```bash
# Daily screening with distribution analysis
DATE=$(date +%Y%m%d)

quantlab screen preset oversold --limit 50 \
    --output results/oversold_$DATE.json

quantlab visualize screen-results \
    --input results/oversold_$DATE.json \
    --output results/oversold_analysis_$DATE.html

open results/oversold_analysis_$DATE.html
```

---

## Future Enhancements (Phase 6+)

Potential next features:

1. **Real-Time Dashboards** - Auto-refreshing web dashboard for live monitoring
2. **PDF Export** - Generate PDF reports automatically
3. **Email Notifications** - Automated email alerts for watch mode
4. **Options Screeners** - Screen options by Greeks, volume, OI
5. **Sector Rotation** - Identify trending sectors over time
6. **Machine Learning** - Predict screen effectiveness
7. **Portfolio Optimization** - Build optimal portfolios from screens

## Examples

### Find Tech Stocks with Strong Momentum

```bash
# Create tech watchlist
cat > tech_stocks.txt << EOF
AAPL
MSFT
GOOGL
AMZN
META
NVDA
AMD
INTC
TSLA
EOF

# Screen for momentum
quantlab screen custom \
    --universe-file tech_stocks.txt \
    --macd-signal bullish \
    --adx-min 20 \
    --rsi-min 40 --rsi-max 65 \
    --limit 5
```

### Find Undervalued Small Caps

```bash
quantlab screen combined \
    --market-cap-min 0.3 \
    --market-cap-max 5.0 \
    --pe-max 15 \
    --debt-equity-max 1.0 \
    --revenue-growth-min 10 \
    --volume-min 500000 \
    --limit 30 \
    --output results/small_cap_value.json
```

## Support

For issues or feature requests:
1. Check this guide
2. Review `quantlab screen --help`
3. Check individual command help: `quantlab screen technical --help`
4. Report issues at GitHub

---

**Happy Screening!** 📊🔍
