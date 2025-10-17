# Profitable Small-Cap AI Stocks Analysis

A comprehensive analysis pipeline for identifying and analyzing profitable small-cap AI stocks with trading strategies.

## 📋 Overview

This project provides an end-to-end analysis system that:

1. **Screens** for profitable small-cap AI stocks ($300M - $5B market cap)
2. **Analyzes sentiment** from news articles
3. **Performs technical analysis** and generates trading strategies
4. **Creates comprehensive reports** with actionable insights

## 🏗️ Project Structure

```
profitable_smallcap_ai/
├── data/                          # Data storage
│   ├── screened_stocks_*.csv     # Screener results
│   ├── sentiment_analysis_*.csv   # Sentiment data
│   ├── tickers_for_analysis_*.json # Ticker lists
│   └── comprehensive_report_*.json # Final reports
│
├── analysis/                      # Technical analysis results
│   └── technical_analysis_*.json
│
├── strategies/                    # Trading strategies
│   └── strategy_report_*.txt
│
├── screener.py                    # Stock screening module
├── sentiment_analysis.py          # Sentiment analysis module
├── technical_analysis.py          # Technical analysis & strategies
├── main.py                        # Main orchestrator
└── README.md                      # This file
```

## 🚀 Quick Start

### Run Complete Analysis Pipeline

```bash
# From the example/profitable_smallcap_ai directory
uv run python main.py
```

This will:
- Screen for profitable small-cap AI stocks
- Analyze sentiment from recent news
- Perform technical analysis
- Generate trading strategy recommendations
- Create a comprehensive report

### Run Individual Modules

**1. Stock Screening Only:**
```bash
uv run python screener.py
```

**2. Sentiment Analysis Only:**
```bash
uv run python sentiment_analysis.py
```

**3. Technical Analysis Only:**
```bash
uv run python technical_analysis.py
```

## 📊 Module Details

### 1. Stock Screener (`screener.py`)

**Criteria:**
- Market cap: $300M - $5B (small to mid-cap)
- Profitability: Positive earnings/profit margin
- Industry: AI/ML/Data Analytics related

**Output:**
- CSV file with screened stocks
- JSON file with detailed metadata
- Summary statistics

**Key Metrics Captured:**
- Market cap, current price
- Profit margin, P/E ratio, PEG ratio
- Revenue growth, earnings growth
- Volume, beta, short ratio
- Industry classification

### 2. Sentiment Analysis (`sentiment_analysis.py`)

**Data Sources:**
- Polygon News API (30 days of news)
- Keyword-based sentiment scoring

**Analysis:**
- Positive/Negative/Neutral classification
- Sentiment score (-1 to +1)
- News coverage count
- Article summaries

**Output:**
- Sentiment scores for each stock
- Top bullish/bearish stocks
- News coverage statistics

### 3. Technical Analysis (`technical_analysis.py`)

**Indicators Calculated:**
- Moving Averages: SMA 20/50/200, EMA 12/26
- MACD (with signal line and histogram)
- RSI (14-period)
- Bollinger Bands
- ATR (Average True Range)
- Volume indicators
- Support/Resistance levels

**Signals Generated:**
- Buy/Sell/Neutral signals
- Golden/Death cross detection
- Oversold/Overbought conditions
- Breakout alerts

**Strategies Recommended:**

1. **Trend Following**
   - Entry: Pullback to moving averages in uptrend
   - Stop loss: 2x ATR below entry
   - Target: 2-3x ATR above entry

2. **Mean Reversion**
   - Entry: Oversold conditions (RSI < 30)
   - Stop loss: Recent support level
   - Target: Return to mean (20 SMA)

3. **Breakout Trading**
   - Entry: Break above resistance with volume
   - Stop loss: Below breakout level
   - Target: Measured move (range projection)

4. **Volatility Expansion**
   - Entry: Bollinger Band squeeze breakout
   - Stop loss: Opposite side of range
   - Target: ATR-based projection

5. **Pullback in Uptrend**
   - Entry: Dip to 20 SMA in strong uptrend
   - Stop loss: Below 50 SMA
   - Target: Previous resistance + extension

## 📈 Trading Strategies Explained

### Strategy Selection Criteria

Each stock is analyzed and matched with appropriate strategies based on:

- **Current trend** (uptrend, downtrend, sideways)
- **Momentum indicators** (RSI, MACD)
- **Volatility levels** (ATR, Bollinger Bands)
- **Volume patterns**
- **Price position** relative to key levels

### Risk Management Guidelines

All strategies include:

✅ **Entry conditions** - Specific price levels or signals
✅ **Stop loss levels** - Risk-defined exits
✅ **Take profit targets** - Multiple targets for scaling out
✅ **Position sizing** - Based on volatility (ATR)
✅ **Risk/Reward ratios** - Minimum 1:2, preferably 1:3

### Example Strategy Output

```
Strategy 1: Trend Following - Long
├─ Entry: On pullback to 20-day SMA
├─ Stop Loss: $42.15
├─ Take Profit 1: $46.30
├─ Take Profit 2: $48.40
├─ Position Size: Based on ATR risk
├─ Rationale: Strong Uptrend with bullish momentum
└─ Risk/Reward: 1:2 to 1:3
```

## 🎯 How to Use the Results

### 1. Review Screening Results

Check `data/screened_stocks_*.csv` for:
- List of profitable small-cap AI stocks
- Fundamental metrics
- Initial filtering

### 2. Analyze Sentiment

Review `data/sentiment_analysis_*.csv`:
- Identify stocks with bullish sentiment
- Check news coverage levels
- Avoid stocks with bearish news trends

### 3. Study Technical Setups

Review `analysis/technical_analysis_*.json`:
- Identify stocks with clear trend direction
- Look for oversold conditions in uptrends
- Find stocks near key support/resistance

### 4. Select Trading Strategies

Review `strategies/strategy_report_*.txt`:
- Match your trading style (trend/reversion/breakout)
- Choose appropriate timeframe
- Verify risk/reward aligns with your goals

### 5. Execute Trades

From comprehensive report (`data/comprehensive_report_*.json`):
- Focus on stocks with high "opportunity score"
- Combine fundamental + sentiment + technical alignment
- Start with smaller positions to test strategies

## 📊 Opportunity Scoring System

Stocks are scored (0-10 scale) based on:

### Fundamental Score (max 5 points)
- Profit margin > 10%: +2 points
- Revenue growth > 15%: +2 points
- P/E ratio < 30: +1 point

### Sentiment Score (max 3 points)
- Bullish sentiment: +3 points
- Neutral: 0 points
- Bearish: -2 points

### Technical Score (max 4 points)
- Uptrend: +2 points
- RSI 30-50 (buy zone): +2 points
- RSI < 30 (oversold): +1 point
- Downtrend: -1 point

**Interpretation:**
- **8-10**: Excellent opportunity
- **6-7**: Good opportunity
- **4-5**: Moderate opportunity
- **<4**: Wait for better setup

## 🔧 Configuration

### Market Cap Range

Edit in `main.py`:
```python
pipeline = AnalysisPipeline(
    min_cap=300_000_000,    # $300M
    max_cap=5_000_000_000   # $5B
)
```

### Sentiment Analysis Period

Edit in `sentiment_analysis.py`:
```python
df_sentiment = sentiment_analyzer.analyze_batch(tickers, days_back=30)
```

### Technical Analysis Period

Edit in `technical_analysis.py`:
```python
technical_analyses = technical_analyzer.analyze_batch(tickers, period="1y")
```

### AI Ticker Universe

Edit `_load_ai_tickers()` in `screener.py` to add/remove tickers.

## 📈 Example Workflow

### Daily Analysis Routine

**Morning (Pre-Market):**
1. Run `uv run python main.py`
2. Review top opportunities from comprehensive report
3. Check sentiment changes from previous day
4. Identify new technical setups

**During Market:**
1. Monitor stocks on watchlist
2. Wait for entry signals per strategy recommendations
3. Execute trades with defined stop losses

**Evening (Post-Market):**
1. Review open positions against strategy targets
2. Adjust stops if needed (trailing stops)
3. Research any new AI stocks to add to universe

### Weekly Review

1. Re-run complete analysis
2. Compare week-over-week changes
3. Update watchlist based on new opportunities
4. Review performance of executed strategies

## 📊 Performance Tracking

Track these metrics for each strategy:

- **Win rate**: % of profitable trades
- **Average R-multiple**: Average profit/loss in terms of risk
- **Max drawdown**: Largest peak-to-trough decline
- **Sharpe ratio**: Risk-adjusted returns

Use MLflow (integrated with QuantLab) to track:
```python
import mlflow

with mlflow.start_run():
    mlflow.log_param("strategy", "Trend Following")
    mlflow.log_metric("win_rate", 0.65)
    mlflow.log_metric("avg_r_multiple", 2.3)
```

## 🔍 Advanced Features

### Custom Screener Criteria

Add your own filters in `screener.py`:

```python
def custom_filter(self, stock_data):
    # Example: Only stocks with revenue > $100M
    if stock_data.get('revenue', 0) < 100_000_000:
        return False
    return True
```

### Custom Technical Indicators

Add new indicators in `technical_analysis.py`:

```python
# Example: Add Stochastic Oscillator
df['Stoch_K'] = ta.stoch(df['High'], df['Low'], df['Close'], window=14)
df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
```

### Integration with Other Data Sources

Extend sentiment analysis:

```python
# Add Twitter sentiment
def get_twitter_sentiment(self, ticker):
    # Your Twitter API implementation
    pass

# Add Reddit mentions
def get_reddit_mentions(self, ticker):
    # Your Reddit API implementation
    pass
```

## 🚨 Important Notes

### Risk Disclaimer

⚠️ **This is for educational purposes only. Not financial advice.**

- Always do your own research
- Never risk more than you can afford to lose
- Past performance doesn't guarantee future results
- Markets can be irrational and volatile

### API Limitations

- **Polygon Free Tier**: Limited to 5 requests/minute
- **News sentiment**: Keyword-based (not ML model)
- **Financial data**: May have delays or inaccuracies

### Best Practices

1. **Diversification**: Don't put all capital in one stock
2. **Position sizing**: Risk 1-2% of capital per trade
3. **Stop losses**: Always use protective stops
4. **Scale in/out**: Don't go all-in at once
5. **Journal trades**: Track and learn from every trade

## 📚 Resources

### Technical Analysis
- [Investopedia - Technical Indicators](https://www.investopedia.com/terms/t/technicalindicator.asp)
- [TradingView](https://www.tradingview.com/) - Charting platform

### AI Stock Research
- [CB Insights - AI Trends](https://www.cbinsights.com/research/artificial-intelligence-trends/)
- [Gartner AI Hype Cycle](https://www.gartner.com/en/research/methodologies/gartner-hype-cycle)

### Trading Education
- [Babypips](https://www.babypips.com/) - Trading basics
- [Tastytrade](https://www.tastytrade.com/tt/learn) - Options & strategies

## 🤝 Contributing

To add new features:

1. Add new screening criteria → Edit `screener.py`
2. Add new sentiment sources → Edit `sentiment_analysis.py`
3. Add new indicators → Edit `technical_analysis.py`
4. Add new strategies → Edit `_recommend_strategies()` in `technical_analysis.py`

## 📝 License

Part of the QuantLab project. See main project README for license details.

## 🔄 Updates

**Latest Version**: 1.0.0 (2025-01-17)

- ✅ Initial release
- ✅ Stock screener with fundamental filters
- ✅ News sentiment analysis
- ✅ Technical analysis with 5 strategy types
- ✅ Comprehensive reporting system

---

**Happy Trading! 📈**

*Remember: The best strategy is one that matches your risk tolerance, time horizon, and trading style.*
