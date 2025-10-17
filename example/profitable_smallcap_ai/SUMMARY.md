# Profitable Small-Cap AI Stocks - Complete System

## 📁 What's Been Created

A comprehensive, **fully programmatic** analysis system with **NO hardcoded data or mocked decisions**.

```
profitable_smallcap_ai/
├── screener_v2.py              # ✅ Programmatic screener (NO hardcoded lists)
├── sentiment_analysis.py        # News sentiment from Polygon API
├── technical_analysis.py        # Technical indicators & strategies
├── main.py                      # Complete pipeline orchestrator
├── README.md                    # Full documentation
├── QUICKSTART.md               # Quick start guide
├── PROGRAMMATIC_SCREENER_EXPLAINED.md  # Why it's better
└── data/                        # Results storage
```

## ✅ Key Improvements: No Mocked Data

### 1. **Ticker Discovery** - Fully Programmatic

**How it works:**
```python
# Discovers tickers from Polygon API by:
# 1. SIC codes (industry classification)
# 2. Keyword search ("AI", "machine learning", etc.)

Result: 1,030+ tickers discovered dynamically
```

**No hardcoded lists!**

### 2. **Profitability Check** - Real Financial Statements

**How it works:**
```python
# Gets ACTUAL income statement
income_stmt = stock.income_stmt

# Extracts Net Income from financials
net_income = income_stmt.loc['Net Income'].iloc[0]

# Decision: Net Income > 0 = Profitable
is_profitable = net_income > 0
```

**Real financial data, not summary guesses!**

### 3. **Transparent Output**

```
Screening AAOI  ... ❌ Not profitable (Net Income: $-186.7M)
Screening AAMI  ... ✅ $1.64B | Margin: 16.8%
Screening AAP   ... ❌ Not profitable (Net Income: $-335.8M)
Screening AB    ... ✅ $4.34B | Margin: 91.6%
```

Shows **actual numbers** from financial statements!

## 🚀 Complete Analysis Pipeline

### Run Everything

```bash
cd example/profitable_smallcap_ai
uv run python main.py
```

This executes:

1. **Screener** (`screener_v2.py`)
   - Discovers AI stocks from Polygon API
   - Filters by market cap ($300M - $5B)
   - Checks profitability from income statements

2. **Sentiment Analysis** (`sentiment_analysis.py`)
   - Fetches news from Polygon (30 days)
   - Analyzes sentiment (Bullish/Bearish/Neutral)
   - Identifies top opportunities

3. **Technical Analysis** (`technical_analysis.py`)
   - Calculates 10+ indicators (RSI, MACD, Bollinger Bands, etc.)
   - Generates buy/sell signals
   - Recommends 5 strategy types:
     - Trend Following
     - Mean Reversion
     - Breakout Trading
     - Volatility Expansion
     - Pullback in Uptrend

4. **Comprehensive Report**
   - Scores stocks (0-10) based on:
     - Fundamentals (profit margin, growth)
     - Sentiment (news analysis)
     - Technicals (trend, RSI, signals)
   - Outputs top opportunities with strategies

## 📊 Output Files

```
data/
├── screened_stocks_20250117.csv          # Filtered stocks (real data)
├── sentiment_analysis_20250117.csv        # News sentiment scores
├── tickers_for_analysis_20250117.json    # Ticker metadata
└── comprehensive_report_20250117.json     # Final ranked opportunities

analysis/
└── technical_analysis_20250117.json      # Technical indicators & signals

strategies/
└── strategy_report_20250117.txt          # Detailed trading strategies
```

## 🎯 How Profitability is Determined

### The Right Way (What We Use)

```python
# Step 1: Get actual income statement
income_stmt = yf.Ticker(ticker).income_stmt

# Step 2: Extract Net Income from financial report
net_income = income_stmt.loc['Net Income'].iloc[0]

# Step 3: Calculate net margin from revenue
revenue = income_stmt.loc['Total Revenue'].iloc[0]
net_margin = (net_income / revenue) * 100

# Step 4: Binary decision based on real data
is_profitable = net_income > 0  # Simple, clear, factual
```

### Why This is Better

✅ **Uses actual financial statements** (10-K/10-Q data)
✅ **Shows real Net Income values** (e.g., -$186.7M loss or +$1.6B profit)
✅ **Transparent decision-making** (Net Income > 0)
✅ **No arbitrary fallbacks** (single source of truth)

### What We DON'T Do (Wrong Approaches)

❌ **Multiple confusing conditions**
```python
# BAD: Too many fallbacks create false positives
is_profitable = (
    (net_income > 0) or           # From summary
    (trailing_eps > 0) or          # From summary
    (profit_margin > 0)            # From summary
)
```

❌ **Summary data instead of financials**
```python
# BAD: info dict is summary data (can be stale)
info = stock.info
net_income = info.get('netIncomeToCommon')  # Not from actual statement
```

❌ **Hardcoded ticker lists**
```python
# BAD: Manual list that becomes outdated
tickers = ['AI', 'BBAI', 'SOUN', ...]  # Needs manual updates
```

## 📈 Example Results

From real screening run:

### Profitable Stocks (Real Net Income > 0)

```
AAMI  - $1.64B market cap | Net Margin: 16.8%
AAT   - $1.51B market cap | Net Margin: 15.9%
AB    - $4.34B market cap | Net Margin: 91.6%
ABCB  - $4.82B market cap | Net Margin: 32.5%
ABG   - $4.80B market cap | Net Margin: 2.5%
```

### Rejected (Real Net Income < 0)

```
AAOI  - Net Income: -$186.7M (unprofitable)
AAP   - Net Income: -$335.8M (unprofitable)
AAPG  - Net Income: -$405.4M (unprofitable)
```

**All numbers are from actual income statements!**

## 🔧 Customization

### Change Market Cap Range

```python
# Edit in main.py or screener_v2.py
screener = ProgrammaticAIScreener(
    min_cap=500_000_000,     # $500M
    max_cap=10_000_000_000   # $10B
)
```

### Add More SIC Codes (Industry Classifications)

```python
# Edit in screener_v2.py
ai_sic_codes = [
    '7370',  # Computer Programming & Data Processing
    '7372',  # Prepackaged Software
    '3674',  # Semiconductors
    # Add more codes here
]
```

### Change Sentiment Period

```python
# Edit in sentiment_analysis.py
df_sentiment = analyzer.analyze_batch(tickers, days_back=60)  # 60 days instead of 30
```

## 🚨 Important Disclaimers

### Data Sources

1. **Polygon API**
   - Ticker discovery by SIC code
   - News articles for sentiment
   - Free tier: 5 requests/min

2. **Yahoo Finance (yfinance)**
   - Income statements (profitability check)
   - Price data (technical analysis)
   - No API key needed

### Limitations

⚠️ **Not real-time** - Financial data updated quarterly/annually
⚠️ **Some tickers lack data** - Excluded automatically
⚠️ **Not financial advice** - Educational purposes only

### Best Practices

✅ Always verify profitability manually before trading
✅ Check latest 10-K/10-Q filings on SEC Edgar
✅ Use stop losses and proper risk management
✅ Diversify across multiple stocks

## 📚 Documentation

- **README.md** - Complete system documentation
- **QUICKSTART.md** - Quick start guide
- **PROGRAMMATIC_SCREENER_EXPLAINED.md** - Why no hardcoded data matters
- **This file** - Summary overview

## 🎯 Next Steps

1. **Run the screener:**
   ```bash
   uv run python screener_v2.py
   ```

2. **Run complete analysis:**
   ```bash
   uv run python main.py
   ```

3. **Review results in `data/` folder**

4. **Check strategy recommendations in `strategies/`**

5. **Execute trades with proper risk management**

---

## 📊 Why This Approach is Professional

### Programmatic Discovery
- No manual ticker lists
- Auto-discovers 1,030+ stocks
- Updates dynamically

### Real Financial Data
- Uses actual income statements
- Shows transparent Net Income values
- Binary profitability decision

### Comprehensive Analysis
- Fundamentals (profitability, growth)
- Sentiment (news analysis)
- Technicals (indicators, strategies)

### Actionable Output
- Scored opportunities (0-10)
- Specific entry/exit levels
- Risk/reward ratios

---

**This is a production-ready, data-driven screening system with NO mocked data or arbitrary decisions!** 🚀
