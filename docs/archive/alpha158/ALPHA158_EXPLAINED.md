# Alpha158 Dataset Explained

## What is Alpha158?

**Alpha158** = 158 hand-crafted **technical indicators** (features), NOT trading alphas/signals.

These are feature engineering inputs that machine learning models use to learn predictive patterns.

---

## The 158 Features Breakdown

### 1. Candlestick Patterns (9 features)
- **KMID**: (close - open) / open - body ratio
- **KLEN**: (high - low) / open - total range
- **KUP**: (high - max(open, close)) / open - upper shadow
- **KLOW**: (min(open, close) - low) / open - lower shadow
- And 5 more variations

### 2. Current Prices (4 features)
- **OPEN0**: open / close
- **HIGH0**: high / close
- **LOW0**: low / close
- **VWAP0**: vwap / close

### 3. Rolling Momentum Indicators (75 features = 15 types × 5 windows)

**Windows**: [5, 10, 20, 30, 60] days

**15 Indicator types**:
- **ROC** (Rate of Change): `close_t / close_{t-N}` - momentum
- **MA** (Moving Average): `mean(close, N)` - trend direction
- **STD** (Standard Deviation): `std(close, N)` - volatility
- **BETA** (Slope): Linear trend strength
- **RSQR** (R-squared): How linear the trend is (0-1)
- **RESI** (Residual): Deviation from linear trend
- **MAX**: Highest high in N days - resistance level
- **MIN**: Lowest low in N days - support level
- **QTLU** (Upper Quantile 80%): Price distribution
- **QTLD** (Lower Quantile 20%): Price distribution
- **RANK**: Current price percentile rank vs past N days
- **RSV**: (close - min) / (max - min) - RSI-like
- **IMAX**: Days since highest high (Aroon indicator)
- **IMIN**: Days since lowest low
- **IMXD**: Difference between IMAX and IMIN

### 4. Volume Indicators (60 features = 12 types × 5 windows)

**12 Volume types**:
- **CORR**: Price-volume correlation
- **CORD**: Price-volume correlation (delta version)
- **CNTP/CNTN/CNTD**: Count of positive/negative/delta days
- **SUMP/SUMN/SUMD**: Sum of positive/negative/delta returns
- **VMA**: Volume moving average
- **VSTD**: Volume standard deviation
- **WVMA**: Volume-weighted moving average
- **VSUMP/VSUMN/VSUMD**: Volume-weighted sums

### 5. Additional Features (10 features)
- Cross-instrument correlations
- Sector momentum
- Market regime indicators

---

## How Machine Learning Uses These Features

### XGBoost Example

```
Training data: 158 features → Model learns which matter
                    ↓
            Decision Tree Ensemble
                    ↓
         Feature Importance Scores
```

**XGBoost does NOT filter out features**. Instead, it:

1. **Assigns importance** through tree splits
2. **Learns automatically** which features are predictive
3. **Combines features** in non-linear ways

### Typical Feature Importance Distribution

Based on XGBoost benchmarks:

```
Top 20 features: ~60-70% of predictive power
Top 50 features: ~85-90% of predictive power
Remaining 108 features: ~10-15% (long tail)
```

**Most important feature categories** (typically):
1. **Short-term momentum (ROC5, MA5, STD5)**: 20-30%
2. **Candlestick patterns (KMID, KLEN)**: 15-20%
3. **Volume trends (VMA, CORR)**: 10-15%
4. **Price extremes (MAX, MIN, RANK)**: 10-15%
5. **Long-term trends (MA60, ROC60)**: 5-10%
6. **Everything else**: 20-30%

---

## Why 158 Features Instead of Manual Selection?

### Advantages of Feature-Rich Dataset

1. **Diversification**: Different features capture different market regimes
   - Bull market: MA, ROC matter
   - Volatile market: STD, RSV matter
   - Ranging market: RANK, RSV matter

2. **Model Flexibility**: Let the model decide what's important
   - XGBoost can use different features for different stocks
   - Ensemble effect: Multiple weak predictors → Strong predictor

3. **Time-varying importance**: Feature importance changes over time
   - 2024 may favor momentum (ROC)
   - 2025 may favor mean reversion (RANK)

4. **Non-linear combinations**: ML finds feature interactions
   - Example: `if STD > threshold AND ROC > 0 → strong buy`
   - Impossible to code manually

### Trade-offs

**Pros**:
- Comprehensive coverage of technical patterns
- No need for manual feature selection
- Model adapts to market conditions

**Cons**:
- **Overfitting risk** (especially with limited data!)
- Slower training
- Harder to interpret

---

## Connection to Your Rank IC Problem

### Why Limited Data Hurts Feature-Rich Models

With only **120 training days** and **158 features**:

```
Samples per feature: ~120 / 158 ≈ 0.76 samples per feature
```

This is **severely underfitted** for learning ranking patterns!

### What Models Need to Learn

**For IC (directional prediction)**:
- Need: ~10-20 samples per feature
- Our data: 120 days × ~3000 stocks = 360K samples ✅
- **Sufficient for IC!**

**For Rank IC (relative ranking)**:
- Need: Cross-sectional patterns (comparing stocks on SAME day)
- Requires: More days to learn stable ranking relationships
- Our data: Only 120 days of cross-sections ❌
- **Insufficient for Rank IC!**

### Why Qlib Benchmark Works

```
Qlib: 7 years × 252 days = 1,764 days
  → 1,764 cross-sections to learn ranking patterns
  → 11 samples per feature per cross-section

Ours: 6 months × 21 days = 120 days
  → 120 cross-sections
  → 0.76 samples per feature per cross-section
```

**This is why we have good IC but zero Rank IC!**

---

## Solutions

### Option 1: Get More Training Data ⭐
Extend to 2020-2024 (4 years):
- 4 years × 252 = ~1000 days
- 6x more cross-sections for learning ranking

### Option 2: Feature Selection
Reduce to top 30-50 features:
- Improves samples-per-feature ratio
- Reduces overfitting risk
- Trade-off: May miss important patterns

### Option 3: Different Model Architecture
Use models designed for limited data:
- **LightGBM**: More efficient with limited data
- **HIST**: Has attention mechanism for ranking
- **Linear models**: Ridge regression with regularization

---

## Summary

**Alpha158 ≠ 158 Alphas**
- It's 158 **technical indicators** (features)
- Machine learning models **learn** which ones matter
- Not filtered manually - model assigns importance

**Why we have zero Rank IC**:
- 158 features × 120 days = Insufficient cross-sections
- IC can be learned from temporal patterns (works with less data)
- Rank IC needs cross-sectional stability (requires more days)

**Next steps**: Get more training data OR reduce features OR try different model
