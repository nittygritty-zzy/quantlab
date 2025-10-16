# QuantLab CLI - Complete Analysis Capabilities Guide

**Last Updated**: 2025-10-15
**Performance**: Optimized for unlimited Polygon API access (125+ contracts/sec)

---

## 📊 Core Analysis Features

### 1. **Multi-Source Ticker Analysis**

Complete analysis combining **3 real-time APIs** + **advanced Greeks calculations**:

```bash
quantlab analyze ticker <TICKER> [OPTIONS]
```

**Data Sources Integrated**:
- 🔴 **Polygon.io**: Real-time prices, options chains (unlimited API calls)
- 🟢 **Alpha Vantage**: News sentiment, treasury rates
- 🔵 **yfinance**: Fundamentals, analyst recommendations, VIX data

**Analysis Components**:

| Component | Data Included | Source |
|-----------|---------------|--------|
| **Price** | Current, Open, High, Low, Volume, VWAP, Change % | Polygon |
| **Options** | Top 5 ITM calls/puts with advanced Greeks | Polygon + Calculated |
| **Greeks** | Delta, Gamma, Theta, Vega, **Vanna, Charm, Vomma** | Black-Scholes Model |
| **Fundamentals** | P/E, Forward P/E, Margins, ROE, Debt, Growth | yfinance |
| **Sentiment** | News analysis (50 articles), Bullish/Bearish/Neutral | Alpha Vantage |
| **Market Context** | VIX, 5-day VIX average | yfinance |
| **Technical Indicators** | RSI, MACD, Bollinger Bands, SMA, EMA, ATR, Stochastic, OBV, ADX | Parquet Historical Data |

---

## 🎯 Analysis Commands

### **Basic Ticker Analysis**
```bash
# Full analysis (options + fundamentals + sentiment + technicals)
quantlab analyze ticker AAPL

# Skip options (faster, fundamentals only)
quantlab analyze ticker MSFT --no-options

# Skip sentiment (faster)
quantlab analyze ticker GOOGL --no-sentiment

# Skip fundamentals
quantlab analyze ticker TSLA --no-fundamentals

# Skip technical indicators
quantlab analyze ticker META --no-technicals

# Quick analysis (skip slow components)
quantlab analyze ticker NVDA --no-options --no-sentiment

# Save to JSON file
quantlab analyze ticker NVDA --output results/nvda_analysis.json
```

**Example Output**:
```
🔍 Analyzing AAPL...

💰 Price: $249.34
   Volume: 45,234,567

📈 Market Context:
   VIX: 20.64 (5d avg: 19.71)

📊 Fundamentals:
   P/E Ratio: 28.45
   Forward P/E: 26.12
   Recommendation: BUY
   Target Price: $265.00 (+6.3% upside)

📰 News Sentiment:
   Label: BULLISH
   Score: 0.187
   Articles: 50 (35 positive, 3 negative)

📉 Technical Indicators:
   Price: $222.13
   SMA(20): $201.16
   SMA(50): $202.93
   RSI(14): 62.60
   MACD: 2.4301 / Signal: -1.1268
   Bollinger Bands: $174.82 - $227.51
   Signals:
      RSI: Neutral (30-70)
      MACD: Bullish (histogram > 0)
      Trend: Moderate trend (ADX 20-25)

📞 Top ITM Call Recommendations:
   1. $240.00 strike, expires 2025-12-19
      ITM: 15.2% | OI: 5,234
      Delta: 0.856 | Theta: -0.145
      Vanna: -0.004521 | Charm: 0.003214
      Score: 85.0/100
```

---

### **Portfolio Analysis**
```bash
# Analyze all tickers in a portfolio
quantlab analyze portfolio tech

# Include options analysis (slower but comprehensive)
quantlab analyze portfolio growth --with-options

# Save to JSON
quantlab analyze portfolio value --output results/portfolio_analysis.json
```

**Output Includes**:
- Individual ticker analyses
- Portfolio-wide metrics (weighted avg P/E, recommendations summary)
- Aggregate performance indicators

---

## 📁 Portfolio Management

### **Create & Manage Portfolios**

```bash
# Create new portfolio
quantlab portfolio create tech "Tech Giants Portfolio"

# Add positions
quantlab portfolio add tech AAPL MSFT GOOGL NVDA

# Show portfolio details
quantlab portfolio show tech

# List all portfolios
quantlab portfolio list

# Remove positions
quantlab portfolio remove tech AAPL

# Update position attributes
quantlab portfolio update tech MSFT --weight 0.25 --notes "Core holding"

# Delete portfolio
quantlab portfolio delete tech
```

---

## 📈 Historical Data Queries

### **Parquet Data Access**

```bash
# Check available data
quantlab data check

# List all available tickers
quantlab data tickers

# Show date range
quantlab data range

# Query specific tickers
quantlab data query AAPL MSFT --start 2024-01-01 --end 2024-12-31
quantlab data query GOOGL --limit 100
```

**Data Source**: `/Volumes/sandisk/quantmini-data/data/parquet`

---

## 🔍 Lookup Tables (Performance Cache)

### **Slowly-Changing Data Cache**

Automatically caches data that changes infrequently (daily updates):

```bash
# Initialize lookup tables
quantlab lookup init

# View cache statistics
quantlab lookup stats

# Refresh specific data types
quantlab lookup refresh company AAPL MSFT
quantlab lookup refresh ratings AAPL
quantlab lookup refresh treasury

# Refresh entire portfolio
quantlab lookup refresh-portfolio tech

# Get cached data
quantlab lookup get company AAPL
quantlab lookup get ratings MSFT
quantlab lookup get treasury 3month
```

**Lookup Tables**:
1. **Company Info**: Name, sector, industry, description
2. **Analyst Ratings**: Strong Buy/Buy/Hold/Sell/Strong Sell counts
3. **Treasury Rates**: 3-month, 2-year, 5-year, 10-year, 30-year
4. **Financial Statements**: Balance sheet, income, cash flow (planned)
5. **Corporate Actions**: Dividends, splits, earnings dates (planned)

---

## 🚀 Advanced Options Analysis

### **What Gets Analyzed**

**Options Chain Filtering**:
- ITM Range: 5% to 20% in-the-money
- Liquidity scoring (based on open interest)
- Expiration filtering (short-term vs LEAP)

**Advanced Greeks Calculated**:

| Greek | Measures | Formula |
|-------|----------|---------|
| **Delta (Δ)** | Price sensitivity | ∂Option/∂Stock |
| **Gamma (Γ)** | Delta change rate | ∂²Option/∂Stock² |
| **Theta (Θ)** | Time decay | ∂Option/∂Time |
| **Vega (ν)** | IV sensitivity | ∂Option/∂σ |
| **Vanna** | Delta-IV cross | ∂²Option/∂Stock∂σ |
| **Charm** | Delta time decay | ∂²Option/∂Stock∂Time |
| **Vomma** | Vega-IV cross | ∂²Option/∂σ² |

**Scoring Algorithm**:
```python
score = (
    liquidity_score * 0.3 +     # Open interest based
    greek_score * 0.4 +          # Delta, theta, vega optimality
    itm_score * 0.3              # Proximity to optimal ITM %
)
```

---

## 📉 Technical Indicators

### **Available Indicators**

**Trend Indicators**:
- **SMA** (Simple Moving Average): 20, 50, 200-day periods
- **EMA** (Exponential Moving Average): 12, 26-day periods

**Momentum Indicators**:
- **RSI** (Relative Strength Index): 14-day period
  - Overbought: >70 | Oversold: <30
- **MACD** (Moving Average Convergence Divergence)
  - Fast: 12-day EMA | Slow: 26-day EMA | Signal: 9-day EMA
- **Stochastic Oscillator**: %K and %D
  - Overbought: >80 | Oversold: <20

**Volatility Indicators**:
- **Bollinger Bands**: 20-day SMA ± 2 standard deviations
- **ATR** (Average True Range): 14-day period

**Volume Indicators**:
- **OBV** (On-Balance Volume): Cumulative volume-weighted price momentum

**Trend Strength**:
- **ADX** (Average Directional Index): 14-day period
  - Strong trend: >25 | Moderate: 20-25 | Weak: <20

### **Signal Interpretation**

Automatic signal generation for:
- **RSI**: Overbought/Oversold/Neutral
- **MACD**: Bullish/Bearish based on histogram
- **Bollinger Bands**: Price position relative to bands
- **Stochastic**: Overbought/Oversold/Neutral
- **ADX**: Trend strength classification
- **Moving Averages**: Price position relative to SMA trends

### **Data Requirements**

- Uses 200 days of historical OHLCV data from Parquet warehouse
- Automatically handles missing data with NaN values
- Real-time calculation on each analysis request

---

## 📊 Analysis Output Formats

### **Terminal Display**
- Formatted tables with color-coded metrics
- Real-time progress indicators
- Summary statistics

### **JSON Export**
Complete machine-readable data with all metrics:

```json
{
  "ticker": "AAPL",
  "timestamp": "2025-10-15T20:00:00",
  "status": "success",
  "price": { "current": 249.34, ... },
  "options": {
    "top_itm_calls": [
      {
        "contract_ticker": "O:AAPL251219C00240000",
        "strike": 240.0,
        "expiration": "2025-12-19",
        "delta": 0.856,
        "vanna": -0.004521,
        "charm": 0.003214,
        "score": 85.0,
        ...
      }
    ]
  },
  "fundamentals": { ... },
  "sentiment": { ... },
  "technical_indicators": {
    "timestamp": "2025-10-15T21:00:53",
    "current_price": 222.13,
    "trend": {
      "sma_20": 201.16,
      "sma_50": 202.93,
      "ema_12": 205.47,
      "ema_26": 203.04
    },
    "momentum": {
      "rsi_14": 62.60,
      "macd_line": 2.43,
      "macd_signal": -1.13,
      "macd_histogram": 3.56,
      "stochastic_k": 95.97,
      "stochastic_d": 86.55
    },
    "volatility": {
      "bb_upper": 227.51,
      "bb_middle": 201.16,
      "bb_lower": 174.82,
      "atr_14": 15.76
    },
    "volume": {
      "obv": -545837156.0
    },
    "trend_strength": {
      "adx_14": 21.59
    },
    "signals": {
      "rsi": "Neutral (30-70)",
      "macd": "Bullish (histogram > 0)",
      "bollinger": "Normal range",
      "stochastic": "Overbought (>80)",
      "trend_strength": "Moderate trend (ADX 20-25)",
      "ma_trend": "Mixed signals"
    }
  }
}
```

---

## ⚡ Performance Characteristics

**With Optimized Polygon API**:

| Operation | Time | Details |
|-----------|------|---------|
| Stock Price | ~0.3s | Single snapshot |
| Technical Indicators | ~0.5s | 200 days historical data |
| Options Chain (100) | ~0.8s | Parallel fetch (50 workers) |
| Options Chain (1000) | ~7-8s | Full LEAP analysis |
| Full Ticker Analysis | ~10-15s | All components |
| Full Ticker (no options) | ~2-3s | Price + fundamentals + technicals |
| Portfolio (5 tickers) | ~60s | Without options |
| Portfolio (5 tickers) | ~5 min | With options |

---

## 🎓 Real-World Use Cases

### **1. LEAP Call Analysis**
```bash
# Analyze GOOG for long-term call options
quantlab analyze ticker GOOG --output results/goog_leap.json
```
**Result**: Top 5 ITM calls with 457-day expiration, advanced Greeks, scoring

### **2. Portfolio Rebalancing**
```bash
# Create portfolio
quantlab portfolio create tech "Tech Portfolio"
quantlab portfolio add tech AAPL MSFT GOOGL NVDA META

# Analyze all positions
quantlab analyze portfolio tech --output results/tech_analysis.json

# Review recommendations and adjust weights
quantlab portfolio update tech AAPL --weight 0.30
```

### **3. Sentiment-Driven Trading**
```bash
# Quick sentiment check on multiple tickers
for ticker in AAPL MSFT GOOGL; do
  quantlab analyze ticker $ticker --no-options --no-fundamentals
done
```

### **4. Options Strategy Screening**
```bash
# Find best ITM calls across portfolio
quantlab analyze portfolio tech --with-options --output results/options_screen.json
```

---

## 🔧 Configuration

**Config Location**: `~/.quantlab/config.yaml`

```yaml
api_keys:
  polygon: your_key_here        # Unlimited API calls
  alphavantage: your_key_here   # 5 req/min (free tier)

rate_limits:
  polygon: 10000    # Effectively unlimited
  alphavantage: 5   # Free tier limit

cache:
  cache_ttl_prices: 900         # 15 minutes
  cache_ttl_fundamentals: 86400 # 24 hours
  cache_ttl_news: 3600          # 1 hour
```

---

## 📚 Additional Resources

- **Options Theory**: See `docs/GOOG_LEAP_CALL_ANALYSIS.md`
- **Performance**: See `docs/POLYGON_API_OPTIMIZATION.md`
- **Project Structure**: See `PROJECT_STRUCTURE.md`
- **Quick Start**: See `QUICKSTART.md`

---

## 💡 Tips & Best Practices

### **Speed Optimization**
```bash
# Fast analysis (skip slow components)
quantlab analyze ticker AAPL --no-options --no-sentiment

# Batch analysis (use --output and process offline)
quantlab analyze ticker AAPL --output aapl.json
quantlab analyze ticker MSFT --output msft.json
```

### **Data Freshness**
```bash
# Refresh lookup tables before analysis
quantlab lookup refresh company AAPL
quantlab analyze ticker AAPL
```

### **Error Handling**
- **No options data**: Some tickers don't have active options
- **Sentiment unavailable**: Alpha Vantage rate limit (wait 60s)
- **Fundamentals missing**: Small-cap stocks may have limited data

---

## 🆕 Recent Additions

**October 2025**:
- ✅ **Technical indicators**: RSI, MACD, Bollinger Bands, SMA, EMA, ATR, Stochastic, OBV, ADX
  - Automatic signal interpretation (Bullish/Bearish/Neutral)
  - Based on 200 days of historical data from Parquet warehouse
  - CLI flag: `--no-technicals` to skip

## 🔮 Coming Soon

Potential future enhancements:
- [ ] Backtesting framework integration
- [ ] Custom options strategies (spreads, straddles)
- [ ] Real-time alerts and notifications
- [ ] Correlation analysis between portfolio holdings
- [ ] Historical options data analysis

---

**Status**: ✅ Production-ready with optimized performance
**Last Tested**: 2025-10-15 (Technical indicators + GOOG LEAP analysis)
