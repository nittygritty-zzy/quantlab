# Quick Start Guide

## 🚀 Run Complete Analysis

```bash
cd example/profitable_smallcap_ai
uv run python main.py
```

This runs the complete pipeline:
1. ✅ **Screens** 120+ AI tickers for profitable small-caps
2. ✅ **Analyzes sentiment** from 30 days of news
3. ✅ **Performs technical analysis** with 5 strategy types
4. ✅ **Generates comprehensive report** with top opportunities

## 📊 What You Get

### Output Files

```
data/
├── screened_stocks_20250117.csv          # Filtered stocks
├── sentiment_analysis_20250117.csv        # News sentiment
├── tickers_for_analysis_20250117.json    # Ticker metadata
└── comprehensive_report_20250117.json     # Final report

analysis/
└── technical_analysis_20250117.json      # Technical data

strategies/
└── strategy_report_20250117.txt          # Trading strategies
```

### Top Opportunities Report

The pipeline automatically scores stocks (0-10) based on:
- **Fundamentals** (profit margin, growth, valuation)
- **Sentiment** (news analysis)
- **Technicals** (trend, RSI, signals)

## 💡 Example Output

```
🎯 TOP TRADING OPPORTUNITIES

Top 5 Opportunities (by combined score):

1. QLYS - Qualys, Inc.
   Score: 8/10
   Market Cap: $4.60B | Price: $127.36
   Profit Margin: 29.0% | Rev Growth: 10.3%
   Sentiment: Bullish | Trend: Uptrend
   RSI: 45.2 | 3 strategies available

Strategy 1: Trend Following - Long
├─ Entry: On pullback to 20-day SMA ($125.50)
├─ Stop Loss: $120.30
├─ Take Profit 1: $132.50
├─ Take Profit 2: $138.20
├─ Position Size: Based on ATR risk (2%)
├─ Rationale: Strong Uptrend with bullish momentum
└─ Risk/Reward: 1:2 to 1:3
```

## 🎯 Next Steps

1. **Review the comprehensive report** for top-scored opportunities
2. **Check individual strategies** in the strategy report
3. **Monitor sentiment changes** daily
4. **Execute trades** with proper risk management

## ⚙️ Customization

**Change market cap range:**
```python
# Edit main.py
pipeline = AnalysisPipeline(
    min_cap=500_000_000,     # $500M
    max_cap=10_000_000_000   # $10B
)
```

**Change analysis period:**
```python
# For sentiment: days_back=30
# For technical: period="1y", "6mo", "3mo"
```

## 📈 Trading Workflow

### Daily Routine

**Morning:**
- Run `python main.py`
- Review top 5 opportunities
- Check for new buy/sell signals

**During Market:**
- Monitor watchlist stocks
- Execute trades per strategy recommendations
- Use defined stop losses

**Evening:**
- Review open positions
- Adjust trailing stops
- Update watchlist

## 🔍 Individual Module Usage

**Screen only:**
```bash
python screener.py
```

**Sentiment only:**
```bash
python sentiment_analysis.py
```

**Technical only:**
```bash
python technical_analysis.py
```

---

**Ready to start? Run `uv run python main.py` now!** 🚀
