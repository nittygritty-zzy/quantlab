# Can Minute Data Solve the Rank IC Problem?

**TL;DR: No. Minute data gives more observations per day, but Rank IC needs more DAYS, not more minutes per day.**

---

## The Question

> "We have zero Rank IC with 120 days of daily data. Would minute data (390 minutes/day × 120 days = 46,800 data points) solve this?"

---

## Answer: No, Because of Cross-Sectional Independence

### What Rank IC Measures

**Rank IC** = Spearman correlation between predicted stock ranks and actual future returns **on each day separately**.

```
Daily Rank IC calculation:

Day 1: Rank all stocks by predicted return → Compare with actual returns
Day 2: Rank all stocks by predicted return → Compare with actual returns
...
Day N: Rank all stocks by predicted return → Compare with actual returns

→ Average correlation across N days = Rank IC
```

### The Data Requirement

To learn ranking patterns, model needs:
- **Independent cross-sections** (different days with different market conditions)
- Not **more observations of the same cross-section** (more minutes on same day)

### Daily Data vs Minute Data

**Daily data (120 days)**:
```
Training: 120 independent cross-sections
Each cross-section: "Which stocks will outperform TOMORROW?"

Day 1: [AAPL, GOOGL, MSFT, ...] → Learn relative ranking
Day 2: [AAPL, GOOGL, MSFT, ...] → Learn relative ranking (independent sample)
...
Day 120: [AAPL, GOOGL, MSFT, ...] → Learn relative ranking (independent sample)

Cross-sectional samples: 120 ✓
```

**Minute data (120 days × 390 minutes/day)**:
```
Training: Still only 120 independent cross-sections!

Day 1:
  09:30: [AAPL, GOOGL, MSFT, ...] → Same day, highly correlated
  09:31: [AAPL, GOOGL, MSFT, ...] → Same day, highly correlated
  ...
  16:00: [AAPL, GOOGL, MSFT, ...] → Same day, highly correlated

Day 2:
  09:30: [AAPL, GOOGL, MSFT, ...] → New independent sample
  ...

Cross-sectional samples: 120 (NOT 46,800!)
Observations per sample: 390 (mostly noise)
```

**Key insight**: Minute data gives you 390 noisy observations of the SAME cross-section, not 390 new cross-sections.

---

## Why More Minutes Don't Help

### Analogy: Grading Students

**Goal**: Learn which students consistently rank higher than others across different exams.

**Scenario A (Daily data)**:
- 120 different exams
- Each exam: Rank all students
- Can learn: "Alice usually beats Bob across different topics"

**Scenario B (Minute data)**:
- 120 exams, but you watch students take EACH exam minute-by-minute
- Exam 1: 390 minutes of watching → Still just 1 exam ranking
- Exam 2: 390 minutes of watching → Still just 1 exam ranking
- ...
- Total: 46,800 minutes of observation, but still only 120 exam rankings

**Result**: Watching students more carefully during each exam doesn't tell you who performs better across DIFFERENT exams.

---

## Mathematical Explanation

### Degrees of Freedom for Rank Learning

**Daily data**:
```
N_days = 120
N_stocks = 3000
N_features = 158

Cross-sectional samples: N_days = 120
Temporal samples per stock: N_days × N_features = 120 × 158 = 18,960

For ranking, effective DOF = N_days = 120 (too low!)
```

**Minute data**:
```
N_days = 120
N_minutes_per_day = 390
N_stocks = 3000
N_features = 158 (or minute-equivalent)

Total observations: 120 × 390 × 3000 × 158 = 22B (huge!)
BUT cross-sectional samples: N_days = 120 (same as daily!)

For ranking, effective DOF = N_days = 120 (no improvement!)
```

### Why Minutes Are Not Independent Samples

**Cross-sectional correlation within same day**:
```
Corr(Stock_ranks_09:30, Stock_ranks_09:31) ≈ 0.95+
Corr(Stock_ranks_09:30, Stock_ranks_16:00) ≈ 0.85+

→ Minutes are NOT independent cross-sectional samples
→ They're noisy observations of the SAME ranking
```

**Cross-sectional correlation across days**:
```
Corr(Stock_ranks_Day1, Stock_ranks_Day2) ≈ 0.3-0.5

→ Different days ARE independent samples
→ This is what we need more of!
```

---

## Additional Problems with Minute Data

### 1. Alpha158 Features Don't Translate

Alpha158 features are designed for **daily frequency**:

```python
# Daily features (economically meaningful)
MA5 = mean(close, past 5 DAYS)           # 5-day trend
ROC20 = close / close_20DAYS_ago - 1     # 20-day momentum
STD60 = std(close, past 60 DAYS)         # 60-day volatility
```

Minute equivalents lose meaning:
```python
# Minute features (mixing scales inappropriately)
MA_1950min = mean(close, past 1950 MINUTES)  # 5 days = mixing intraday + overnight
ROC_7800min = close / close_7800min_ago - 1  # 20 days = weird mix
STD_23400min = std(close, past 23400 MIN)    # 60 days = what does this mean?
```

**Problems**:
- Mix intraday noise with overnight gaps
- Lose economic interpretation (earnings, macro events happen daily, not per-minute)
- Most quant research is based on daily patterns

### 2. Intraday vs Inter-day Dynamics

**Daily data captures**:
- Overnight information absorption
- Fundamental news impact
- Macro regime changes
- Long-term trends and momentum
- **Cross-sectional ranking persistence**

**Minute data captures**:
- Microstructure noise (bid-ask bounce)
- Liquidity fluctuations
- Intraday mean reversion (NOT ranking persistence!)
- Order flow imbalances
- High-frequency patterns (decay in milliseconds)

**For TopK strategy based on daily rebalancing**:
- You care about: "Which stocks will be best TOMORROW?"
- Minute data answers: "Which stocks are best in NEXT MINUTE?"
- These are DIFFERENT questions with DIFFERENT patterns!

### 3. Data Quality Issues

**Minute data challenges**:
```
Liquid stocks (AAPL, MSFT): Clean minute data ✓
Mid-cap stocks: Sparse minute data, wider spreads ⚠️
Small-cap stocks: Very sparse, many zero-volume minutes ❌

→ Alpha158 indicators become unreliable for 50-70% of liquid_stocks universe
→ Many NaN/Inf values from division by zero volume
→ Feature quality degrades severely
```

### 4. Computational Cost

**Training time comparison**:
```
Daily data:
- Samples: 120 days × 3000 stocks = 360K
- Training time: ~5 minutes

Minute data:
- Samples: 120 days × 390 min × 3000 stocks = 140M
- Training time: ~30+ hours (390x slower!)
- Memory usage: ~100x higher
```

For potentially ZERO improvement in Rank IC!

---

## What WOULD Work

### Option 1: More Daily Data ⭐⭐⭐ (Best)

```
Extend training period: 2020-2024 (4 years)

Training days: 4 years × 252 days = ~1000 days
Cross-sectional samples: 1000 (8.3x improvement!)

Expected Rank IC: 0 → 0.03-0.05 ✓
```

### Option 2: Intraday Features on Daily Frequency ⭐⭐

Use minute data to **engineer better DAILY features**:

```python
# Daily aggregates from minute data
Daily_high_low_ratio = intraday_high / intraday_low
Daily_vwap = volume_weighted_avg_price (better than close)
Open_to_close_volume_profile = first_30min_vol / last_30min_vol
Intraday_volatility = std(minute_returns)
Number_of_large_moves = count(|minute_return| > 1%)

→ Still predict daily returns
→ But use richer daily features
→ Keep 120 cross-sectional samples
```

**This COULD help!** But only marginally (Rank IC might improve from 0 to 0.01-0.02).

### Option 3: High-Frequency Strategy (Different Problem)

If you want to use minute data properly:

```
Goal: Intraday trading (hold for minutes/hours)
Frequency: Minute bars
Prediction: Next-minute or next-hour returns
Strategy: High-frequency TopK with intraday rebalancing

→ Completely different problem!
→ Need different features (order flow, spread, liquidity)
→ Need different models (online learning, recurrent networks)
→ Need different infrastructure (low-latency execution)
```

This is a **different research project**, not a solution to current Rank IC problem.

---

## Summary Table

| Approach | Cross-sections | Will Fix Rank IC? | Cost | Recommended? |
|----------|----------------|-------------------|------|--------------|
| **Current (120 daily)** | 120 | ❌ (baseline) | Low | Need more data |
| **Minute data (naive)** | 120 | ❌ | Very High | **NO** |
| **More daily data (1000 days)** | 1000 | ✅ | Low | **YES** ⭐⭐⭐ |
| **Minute-derived daily features** | 120 | Maybe (0→0.02) | Medium | Worth trying ⭐ |
| **Different model (HIST)** | 120 | Maybe (0→0.03) | Low | **YES** ⭐⭐ |

---

## Recommended Action

**Do NOT pursue minute data for fixing Rank IC.**

Instead:

1. **Get more daily data** (2020-2024) - highest priority ⭐⭐⭐
2. **Try HIST or DoubleEnsemble** - proven to work with limited data ⭐⭐
3. **Consider minute-derived daily features** - as an enhancement ⭐

---

## Final Explanation

**Why your intuition was reasonable but wrong**:

✓ Correct intuition: "More data points should help"
✗ Wrong assumption: "More minutes = more cross-sectional samples"

**The truth**:
- Rank IC requires learning **which stocks beat other stocks across different days**
- This requires **more days**, not more observations per day
- Minute data gives you 390 noisy measurements of each day's ranking
- But the ranking itself is still just 1 sample per day

**Analogy**:
- Taking 390 photos of a person doesn't give you 390 people
- It gives you 390 views of the same person
- To learn patterns across people, you need photos of MORE people, not more photos of same people

For Rank IC, you need more DAYS (people), not more MINUTES per day (photos per person).
