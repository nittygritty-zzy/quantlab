# GOOG ADVANCED INDICATORS ANALYSIS
## Comprehensive Options & Market Metrics
**Analysis Date:** October 15, 2025  
**Stock:** GOOG (Alphabet Inc. Class C)  
**Current Price:** $251.71

---

## ✅ INDICATORS SUCCESSFULLY CALCULATED

### 1. OPTIONS GREEKS (from Polygon API)
**Status:** ✅ **COMPLETE - 1,966/2,010 contracts have full Greeks**

| Greek | Value | Description |
|-------|-------|-------------|
| **Delta** | 0.573 (ATM calls) | Directional exposure - how much option price changes per $1 stock move |
| **Gamma** | Available | Rate of change of delta |
| **Theta** | Available | Time decay - how much option loses per day |
| **Vega** | Available | Sensitivity to volatility changes |

**Data Source:** Polygon `get_snapshot_option()` API  
**Coverage:** Near-the-money and ATM options have complete Greeks  
**Note:** Deep ITM options may not have Greeks calculated by market makers

---

### 2. OPTIONS FLOW METRICS
**Status:** ✅ **COMPLETE**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Put/Call Ratio (Volume)** | 0.495 | **Bullish** - More call volume than puts |
| **Put/Call Ratio (OI)** | 0.709 | Moderate bullish bias |
| **Total Call Volume** | 159,347 | High activity in calls |
| **Total Put Volume** | 78,908 | Lower put activity |
| **Total Call OI** | 987,153 | Strong call interest |
| **Total Put OI** | 699,693 | Moderate put interest |

**Max Pain Analysis:**
- **Max Pain Price:** $225.00 (Oct 17 expiry)
- **Current vs Max Pain:** +10.61% above
- **Interpretation:** Market makers would profit most if stock closes at $225. Stock trading $26.71 above max pain suggests strong bullish pressure.

---

### 3. VOLATILITY INDICATORS
**Status:** ✅ **COMPLETE**

| Indicator | Value | Analysis |
|-----------|-------|----------|
| **30-Day Realized Vol** | 23.12% | Actual historical volatility |
| **20-Day Realized Vol** | 21.42% | Recent volatility lower |
| **10-Day Realized Vol** | 26.06% | Short-term vol elevated |
| **ATM Implied Vol** | 39.99% | Market expects 40% annualized vol |
| **IV vs Realized** | +16.87% | **Options are expensive!** |

**Key Insight:** Implied volatility (39.99%) is significantly higher than realized volatility (23.12%). This means:
- Options are trading at a premium
- Market expects more volatility than recently experienced
- **Selling premium strategies favored** (if you disagree with high IV)
- **Buying options is expensive** (paying 173% of realized vol)

**VIX Data:** ❌ Not available (ticker format issue - will fix)

---

### 4. SENTIMENT INDICATORS
**Status:** ✅ **COMPLETE**

| Indicator | Value | Signal |
|-----------|-------|--------|
| **IV Skew** | -0.0291 (-7.27%) | **BULLISH** |
| **ATM Call IV** | 39.99% | Calls trading at higher IV |
| **ATM Put IV** | 37.08% | Puts cheaper than calls |

**Interpretation of Negative Skew:**
- Calls are MORE expensive than puts (unusual)
- Typically, puts have higher IV (protective demand)
- Negative skew suggests strong bullish positioning
- Market participants willing to pay premium for upside exposure

---

### 5. TECHNICAL INDICATORS
**Status:** ✅ **COMPLETE**

#### Bollinger Bands (20-period, 2σ)
| Band | Price | Status |
|------|-------|--------|
| Upper Band | $255.65 | 1.56% away |
| Middle Band (SMA) | $247.35 | Current reference |
| Lower Band | $239.06 | Support level |
| **Current Price** | **$251.71** | **76.3% position** |
| Bandwidth | 6.71% | Moderate volatility |

**Interpretation:** Stock at 76.3% position means it's in upper portion of bands but not overbought. Approaching upper band but has room to move higher.

#### Volume Profile (20-day)
| Level | Price | Analysis |
|-------|-------|----------|
| **Point of Control** | $245.52 | Highest volume traded here |
| Value Area High | $245.52 | Top of 70% volume zone |
| Value Area Low | $241.59 | Bottom of 70% volume zone |
| **Current Price** | **$251.71** | **Above value area** ✅ |

**Interpretation:** Trading above the value area is bullish. Stock has broken out of the zone where 70% of recent volume traded, suggesting buyers in control.

---

### 6. RSI & MACD (from previous analysis)
**Status:** ✅ **COMPLETE**

| Indicator | Value | Signal |
|-----------|-------|--------|
| **RSI (14-period)** | 53.21 | Neutral - room for upside |
| **MACD Line** | 5.18 | Positive momentum |
| **MACD Signal** | 7.35 | Above signal (bearish cross) |
| **MACD Histogram** | -2.17 | Slightly negative |

---

## ❌ INDICATORS NOT AVAILABLE (Require Market-Wide Data)

### 7. ADVANCED GREEKS
**Status:** ⚠️ **REQUIRES CALCULATION - Not provided by Polygon**

These higher-order Greeks require:
- **Vanna**: ∂Delta/∂IV - sensitivity of delta to volatility changes
- **Charm**: ∂Delta/∂Time - rate of delta decay
- **Vomma**: ∂Vega/∂IV - sensitivity of vega to volatility
  
**Why not available:** Polygon provides first-order Greeks (Delta, Gamma, Theta, Vega) but not second-order derivatives. These would need to be calculated using Black-Scholes model with finite difference methods.

**Can calculate if needed:** Yes, with additional code using scipy and option pricing models.

---

### 8. MARKET BREADTH INDICATORS
**Status:** ❌ **NOT AVAILABLE - Requires Market-Wide Data**

These indicators require data across all stocks:

| Indicator | Why Not Available |
|-----------|-------------------|
| **Advance-Decline Line** | Needs all NYSE/NASDAQ stocks' daily moves |
| **New Highs/New Lows** | Needs 52-week data for entire market |
| **McClellan Oscillator** | Needs breadth data (advancing vs declining issues) |

**Workaround:** Could fetch these from market summary APIs or specialized breadth data providers.

---

### 9. VIX TERM STRUCTURE
**Status:** ⚠️ **PARTIALLY AVAILABLE**

- VIX current level: ❌ Failed (ticker format issue)
- VVIX: ❌ Not attempted yet
- VIX futures term structure: ❌ Would need VIX futures data

**Can fix:** Yes, need to use correct Polygon ticker format for indices.

---

### 10. FEAR & GREED INDEX
**Status:** ❌ **NOT AVAILABLE from Polygon**

- This is a CNN Business composite index
- Not available via Polygon API
- Would need to scrape from CNN or use alternative data provider

---

## 📊 SUMMARY OF AVAILABLE vs REQUIRED DATA

### ✅ What We Have (100% Complete):
1. ✅ First-order Greeks (Delta, Gamma, Theta, Vega) - 1,966 contracts
2. ✅ Implied Volatility - 1,966 contracts  
3. ✅ Put/Call Ratios (Volume & OI)
4. ✅ Max Pain calculation
5. ✅ Open Interest data
6. ✅ IV Skew (Put/Call)
7. ✅ Realized Volatility (10/20/30 day)
8. ✅ IV vs Realized comparison
9. ✅ RSI, MACD, SMA, EMA
10. ✅ Bollinger Bands
11. ✅ Volume Profile

### ⚠️ Can Calculate (Need Additional Code):
1. ⚠️ Vanna, Charm, Vomma (using Black-Scholes)
2. ⚠️ IV Rank/Percentile (need historical IV database)
3. ⚠️ VIX (fix ticker format)

### ❌ Not Available via Polygon for Single Stock:
1. ❌ Market breadth indicators (Advance-Decline, New Highs/Lows, McClellan)
2. ❌ Fear & Greed Index (proprietary CNN indicator)
3. ❌ VVIX (would need separate data source)

---

## 🎯 KEY INSIGHTS FROM AVAILABLE DATA

### BULLISH SIGNALS:
1. ✅ Put/Call Ratio 0.495 - More calls than puts
2. ✅ Negative IV Skew (-7.27%) - Calls more expensive than puts
3. ✅ Trading 10.61% above Max Pain
4. ✅ Price above Volume Profile value area
5. ✅ RSI at 53 - Room for upside

### CAUTION SIGNALS:
1. ⚠️ IV 73% above realized volatility - Options expensive
2. ⚠️ Approaching Bollinger Band upper limit (76.3% position)
3. ⚠️ MACD histogram negative (momentum weakening)

### OPTIONS TRADING IMPLICATIONS:
- **For Buyers:** Options are expensive (IV elevated). Consider waiting for IV crush or buying further OTM.
- **For Sellers:** Good environment for selling premium (high IV vs realized). Consider credit spreads or covered calls.
- **For ITM Calls:** Delta ~0.57 means good leverage, but time premium is elevated due to high IV.

---

## 📁 DATA FILES GENERATED

1. **Advanced Indicators:** `results/goog_advanced_indicators_20251015_171449.json`
2. **Full Analysis:** `results/goog_analysis_20251015_170749.json`
3. **Research Report:** `docs/GOOG_ITM_CALLS_RESEARCH_20251015_170805.md`
4. **Recommendations:** `docs/GOOG_ITM_CALLS_RECOMMENDATIONS.md`

---

**Generated by:** QuantLab Analysis System  
**Data Source:** Polygon.io API (Real market data)  
**Analysis Type:** Comprehensive Options & Technical Analysis
