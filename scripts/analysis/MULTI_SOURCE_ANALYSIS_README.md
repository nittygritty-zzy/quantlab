# Multi-Source Options Analysis Tool

**Comprehensive options analysis integrating Polygon, Alpha Vantage, and yfinance**

## Overview

This tool provides the most comprehensive options analysis by combining data from three different sources:

| Data Source | Provides |
|-------------|----------|
| **Polygon.io** | Options chains, Greeks (Delta, Gamma, Theta, Vega), stock prices, open interest |
| **Alpha Vantage** | Real 3-month Treasury rates, news sentiment analysis |
| **yfinance** | VIX data, institutional holdings, analyst recommendations |

## Features

✅ **Real Risk-Free Rate** - Uses actual 3-month Treasury rates (not estimates)
✅ **VIX Context** - Market-wide volatility data unavailable in Polygon
✅ **News Sentiment** - Analyzes 50+ recent news articles with sentiment scores
✅ **Advanced Greeks** - Calculates Vanna, Charm, and Vomma using Black-Scholes
✅ **Multi-Source Validation** - Cross-references options data across sources
✅ **Institutional Holdings** - Track what big institutions are holding

## Usage

### Basic Usage

```bash
# Analyze AAPL (default output directories)
uv run python scripts/analysis/multi_source_options_analysis.py --ticker AAPL

# Analyze GOOG (default ticker)
uv run python scripts/analysis/multi_source_options_analysis.py

# Analyze MSFT with custom output directory
uv run python scripts/analysis/multi_source_options_analysis.py --ticker MSFT --output-dir /path/to/output
```

### Get Help

```bash
uv run python scripts/analysis/multi_source_options_analysis.py --help
```

## Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--ticker` | string | `GOOG` | Stock ticker symbol to analyze |
| `--output-dir` | string | `results/` & `docs/` | Custom output directory for reports |

## Output Files

The tool generates two files for each analysis:

1. **JSON Data File**: `{ticker}_multi_source_{timestamp}.json`
   - Complete raw data from all sources
   - All calculated Greeks
   - Structured for programmatic access

2. **Markdown Report**: `{ticker}_MULTI_SOURCE_ANALYSIS_{timestamp}.md`
   - Human-readable comprehensive report
   - Top 3 ITM call recommendations
   - Market context and sentiment analysis
   - Data source status

## Report Contents

Each report includes:

### 📊 Data Sources Status
- Success/error status for each API
- Number of options analyzed
- Treasury rate and news sentiment summary

### 🎯 Top ITM Call Recommendations
- Best ITM calls in the 5-20% range
- Complete first-order Greeks (Delta, Gamma, Theta, Vega)
- Advanced Greeks (Vanna, Charm, Vomma)
- Open interest and liquidity metrics

### 📈 Market Context
- **VIX Level**: Current volatility environment
- **News Sentiment**: Bullish/Bearish/Neutral with score
- **Institutional Activity**: Top holdings data

### 🔍 Key Insights
- Why multi-source analysis is superior
- Data quality verification
- Interpretation of findings

## Example Output

```
$ uv run python scripts/analysis/multi_source_options_analysis.py --ticker AAPL

========================================================
AAPL MULTI-SOURCE OPTIONS ANALYSIS
========================================================

✓ Current Price: $249.34
✓ Found 731 ITM call options from Polygon
✓ VIX: 20.64
✓ News Sentiment: Bullish (0.187)
✓ Calculated advanced Greeks for 727 options
✓ Selected 112 ITM calls for detailed analysis

Reports Generated:
  - Markdown: docs/AAPL_MULTI_SOURCE_ANALYSIS_20251015_190442.md
  - JSON: results/aapl_multi_source_20251015_190442.json
```

## Requirements

- Python 3.8+
- uv package manager
- API Keys (see below)

### Required Packages

Already installed in quantlab environment:
- `polygon-api-client` - Polygon.io API
- `yfinance` - Yahoo Finance data
- `requests` - HTTP requests for Alpha Vantage
- `numpy`, `scipy` - Black-Scholes calculations

### API Keys Required

| API | Where to Set | Notes |
|-----|--------------|-------|
| **Polygon** | `POLYGON_API_KEY` env var or hardcoded | Required for options data |
| **Alpha Vantage** | Hardcoded in script | Free tier: 5 req/min, 100/day |
| **yfinance** | No key required | Free, no authentication needed |

## How It Works

1. **Fetch from Polygon**: Gets options chain, stock price, and market Greeks
2. **Fetch from yfinance**: Gets VIX, institutional holdings, analyst data
3. **Fetch from Alpha Vantage**: Gets real Treasury rate and news sentiment
4. **Calculate Advanced Greeks**: Uses Black-Scholes with real risk-free rate
5. **Filter ITM Calls**: Focuses on 5-20% ITM range for best risk/reward
6. **Generate Reports**: Creates JSON and Markdown with comprehensive analysis

## Advanced Greeks Explained

### Vanna (∂Delta/∂σ)
- How delta changes when implied volatility changes
- **Positive**: Delta increases when IV rises (good for long calls)
- **Negative**: Delta decreases when IV rises (bad for long calls)

### Charm (∂Delta/∂t)
- How delta changes over time (delta decay)
- **Positive**: Delta increases toward 1.0 as time passes (good for ITM calls)
- **Negative**: Delta decreases as time passes

### Vomma (∂Vega/∂σ)
- How vega changes when implied volatility changes
- **Positive**: Benefit more from volatility increases
- **Negative**: Exposed to volatility crush

## Tips for Using This Tool

1. **Run before market hours** - Get fresh overnight news sentiment
2. **Compare multiple tickers** - Run for AAPL, MSFT, GOOG to compare opportunities
3. **Check VIX** - High VIX (>20) = expensive options, consider waiting
4. **Read sentiment** - Bullish news supports bullish options thesis
5. **Focus on high OI** - Options with high open interest = better liquidity

## Comparison with Single-Source Analysis

| Feature | Polygon Only | Multi-Source |
|---------|--------------|--------------|
| Risk-Free Rate | Hardcoded 4.5% | ✅ Real 4.070% from Treasury |
| VIX Data | ❌ Not available | ✅ Current VIX: 20.64 |
| News Sentiment | ❌ Not available | ✅ 50 articles analyzed |
| Institutional Data | ❌ Not available | ✅ 1.56B shares tracked |
| Greeks Accuracy | Good | ✅ Better (real rates) |

## Troubleshooting

### "Must specify POLYGON_API_KEY"
- Set environment variable: `export POLYGON_API_KEY=your_key_here`
- Or API key is hardcoded in script as fallback

### "Invalid ticker format"
- Ticker must be 1-5 letters only (no numbers, special characters)
- Examples: AAPL, GOOG, MSFT (not AAPL123, GO-OG)

### "Alpha Vantage rate limit"
- Free tier: 5 requests/minute, 100/day
- Wait 60 seconds and try again
- Consider upgrading Alpha Vantage plan

### "No options data found"
- Ticker may not have options (ETFs, small caps)
- Check ticker symbol is correct
- Try a large-cap stock like AAPL, MSFT, GOOG

## File Location

**Script**: `/Users/zheyuanzhao/workspace/quantlab/scripts/analysis/multi_source_options_analysis.py`

**Default Output**:
- JSON: `/Users/zheyuanzhao/workspace/quantlab/results/`
- Markdown: `/Users/zheyuanzhao/workspace/quantlab/docs/`

## Related Files

- `advanced_greeks_calculator.py` - Black-Scholes Greeks calculation engine
- `goog_complete_with_advanced_greeks.py` - Original GOOG-only analysis (deprecated)
- `goog_advanced_indicators.py` - Additional indicators calculator

## Version History

- **v2.0** (2025-10-15): Refactored to accept any ticker with CLI interface
- **v1.0** (2025-10-15): Initial GOOG-specific multi-source analysis

## Credits

**Data Sources:**
- [Polygon.io](https://polygon.io) - Options and stock data
- [Alpha Vantage](https://www.alphavantage.co) - Treasury rates and news
- [yfinance](https://github.com/ranaroussi/yfinance) - VIX and institutional data

**Analysis Engine:** QuantLab Multi-Source Integration
**Black-Scholes Model:** scipy.stats with real Treasury rates
