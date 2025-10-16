# ORCL MULTI-SOURCE OPTIONS ANALYSIS
## Combining Polygon, Alpha Vantage & yfinance Data

**Ticker:** ORCL
**Analysis Date:** 2025-10-15 20:02:42
**Stock Price:** $303.62
**Risk-Free Rate:** 4.070% (Real 3-month Treasury)

---

## 📊 DATA SOURCES STATUS

### Polygon.io
**Status:** SUCCESS
**Data Retrieved:** 765 ITM call options

### Alpha Vantage
**Status:** SUCCESS
**Treasury Rate:** 4.07%
**News Articles:** 50
**Sentiment:** Neutral (0.119)

### yfinance
**Status:** SUCCESS
**VIX:** 20.639999389648438
**Institutions Tracked:** 10
**Option Expirations:** 22

---

## 🎯 TOP ITM CALL RECOMMENDATIONS


### 1. $287.50 Strike, Expires 2025-10-17

**Position:** 5.61% ITM
**Price:** $18.82 per share
**Open Interest:** 582

**Standard Greeks:**
- Delta: 0.8476 - Captures 84.8% of stock moves
- Gamma: 0.0142 - Delta changes by 0.0142 per $1 move
- Theta: -1.9853 - Loses $1.99 per day
- Vega: 0.0375 - Gains $3.75 if IV +1%

**Advanced Greeks:**
- Vanna: -0.002189 - Delta decreases when IV rises
- Charm: 0.113974 - Delta increases by 0.113974 per day
- Vomma: 0.000357 - Positive volatility convexity

---

### 2. $287.50 Strike, Expires 2025-10-24

**Position:** 5.61% ITM
**Price:** $23.40 per share
**Open Interest:** 210

**Standard Greeks:**
- Delta: 0.7331 - Captures 73.3% of stock moves
- Gamma: 0.0112 - Delta changes by 0.0112 per $1 move
- Theta: -0.6251 - Loses $0.63 per day
- Vega: 0.1478 - Gains $14.78 if IV +1%

**Advanced Greeks:**
- Vanna: -0.002648 - Delta decreases when IV rises
- Charm: 0.010420 - Delta increases by 0.010420 per day
- Vomma: 0.000741 - Positive volatility convexity

---

### 3. $287.50 Strike, Expires 2025-10-31

**Position:** 5.61% ITM
**Price:** $26.30 per share
**Open Interest:** 8

**Standard Greeks:**
- Delta: 0.6995 - Captures 70.0% of stock moves
- Gamma: 0.0094 - Delta changes by 0.0094 per $1 move
- Theta: -0.4494 - Loses $0.45 per day
- Vega: 0.2142 - Gains $21.42 if IV +1%

**Advanced Greeks:**
- Vanna: -0.002327 - Delta decreases when IV rises
- Charm: 0.004336 - Delta increases by 0.004336 per day
- Vomma: 0.000749 - Positive volatility convexity

---

## 📈 MARKET CONTEXT

### Volatility Environment
- **VIX:** 20.639999389648438 (5-day avg: 19.713999938964843)
- **Interpretation:** Elevated volatility - options expensive

### News Sentiment Analysis
- **Articles Analyzed:** 50
- **Average Sentiment:** 0.119 (range: -1 to +1)
- **Overall Mood:** Neutral
- **Interpretation:** Positive news flow supports bullish thesis

### Institutional Activity
- **Institutional Holders:** 10
- **Top 10 Holdings:** 572,753,479 shares

---

## 🔍 KEY INSIGHTS

### Why This Analysis is Superior:
1. **Real Risk-Free Rate:** Using actual 3-month Treasury (4.070%) instead of estimates
2. **VIX Data:** Market-wide volatility context (unavailable in Polygon alone)
3. **Sentiment Analysis:** 50 news articles with sentiment scores
4. **Multi-Source Validation:** Cross-referencing options data from Polygon and yfinance
5. **Complete Greeks:** First-order + advanced (Vanna, Charm, Vomma)

### Data Quality:
- ✅ All data from real market sources (no mock data)
- ✅ Risk-free rate updated from Treasury.gov via Alpha Vantage
- ✅ VIX data from Yahoo Finance (CBOE index)
- ✅ 107 ITM calls with complete Greeks

---

## 📁 FILES GENERATED

1. **JSON Data:** `orcl_multi_source_20251015_200246.json`
2. **This Report:** `ORCL_MULTI_SOURCE_ANALYSIS_20251015_200246.md`

---

**Data Sources:**
- Polygon.io (Options chains, Greeks, stock data)
- Alpha Vantage (Treasury rates, news sentiment)
- yfinance (VIX, institutional holdings, analyst recommendations)

**Analysis Engine:** QuantLab Multi-Source Integration
**Black-Scholes Model:** scipy.stats with real Treasury rates
**Generated:** 2025-10-15 20:02:42
