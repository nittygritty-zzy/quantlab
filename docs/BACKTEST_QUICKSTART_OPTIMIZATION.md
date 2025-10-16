# Backtest Performance Optimization - Quick Start

**Date**: October 15, 2025
**Goal**: Get 3-5x faster backtests in 30 minutes

## Current Performance

- **Demo (10 stocks)**: ~2-3 minutes
- **Full (50 stocks)**: ~8-12 minutes

## Target Performance (After Optimization)

- **Dev (5 stocks)**: ~30-60 seconds ⚡
- **Full (50 stocks, cached)**: ~2-3 minutes ⚡⚡⚡

---

## 🚀 30-Minute Optimization Sprint

### Step 1: Use Development Config (5 min)

**Current**: Running full backtests with 50 stocks during development is slow.
**Solution**: Use optimized dev config for fast iteration.

```bash
cd qlib_repo

# Before: Slow (10+ minutes)
# uv run qrun ../configs/backtest_tech_fundamental.yaml

# After: Fast (30-60 seconds)
uv run qrun ../configs/backtest_dev.yaml
```

**What changed**:
- ✅ 5 stocks instead of 50 (10x less data)
- ✅ Simpler model (4 depth vs 6, 100 rounds vs 1000)
- ✅ Technical indicators only (no slow API calls)
- ✅ Shorter training period (3 months vs 6 months)

**Expected speedup**: 5-10x faster

---

### Step 2: Pre-compute Technical Indicators (15 min)

**Current**: Every backtest recalculates RSI, MACD, SMA from scratch.
**Solution**: Calculate once, cache forever.

```bash
# Run precomputation (takes ~2-3 minutes)
uv run python scripts/data/precompute_indicators.py
```

**Output**:
```
[1/50] Processing AAPL... ✓ 252 valid rows, saved to cache
[2/50] Processing MSFT... ✓ 252 valid rows, saved to cache
...
✓ Indicators pre-computed successfully!
```

**Cache location**: `/Volumes/sandisk/quantmini-data/data/indicators_cache/`

**Expected speedup**: 2-3x faster data loading

---

### Step 3: Pre-fetch Fundamentals (Optional, 10 min)

**Current**: yfinance API calls during backtest are SLOW (~2s per stock).
**Solution**: Fetch once per day, cache results.

```bash
# Run precomputation (takes ~30-60 seconds with rate limiting)
uv run python scripts/data/precompute_fundamentals.py
```

**Output**:
```
[1/50] Fetching AAPL... ✓ 28/30 metrics
[2/50] Fetching MSFT... ✓ 27/30 metrics
...
✓ Fundamentals pre-fetched successfully!
```

**Cache location**: `/Volumes/sandisk/quantmini-data/data/fundamentals_cache/`

**Expected speedup**: Eliminates 50-100 seconds of API calls

---

## 📊 Benchmark Your System

Before and after optimization, measure actual performance:

```bash
cd qlib_repo

# Benchmark data loading
uv run python ../scripts/analysis/benchmark_backtest.py

# Benchmark full backtest (with timing)
time uv run qrun ../configs/backtest_dev.yaml
```

**Look for these metrics**:
- Data loading time
- Model training time
- Total execution time

---

## 🎯 Recommended Workflow

### During Development (Fast Iteration)

```bash
# 1. Use dev config
cd qlib_repo
uv run qrun ../configs/backtest_dev.yaml

# Expected time: 30-60 seconds
# Perfect for: Testing strategies, debugging, feature experiments
```

**Features**:
- 5 stocks (AAPL, MSFT, GOOGL, AMZN, NVDA)
- Technical indicators only
- Simpler model (100 boost rounds)
- 4-month backtest period

### Before Production (Full Validation)

```bash
# 2. Run full backtest with all features
cd qlib_repo
uv run qrun ../configs/backtest_tech_fundamental.yaml

# Expected time: 2-3 minutes (with caching)
# Use for: Final validation, performance reporting
```

**Features**:
- 50 stocks (top liquid US stocks)
- All features (technical + fundamental)
- Production model (1000 boost rounds)
- Full year backtest

---

## 📁 New Files Created

### Configuration Files
- **`configs/backtest_dev.yaml`** - Fast development config (5 stocks, simple model)

### Data Preprocessing Scripts
- **`scripts/data/precompute_indicators.py`** - Cache technical indicators
- **`scripts/data/precompute_fundamentals.py`** - Cache fundamental data

### Benchmarking Tools
- **`scripts/analysis/benchmark_backtest.py`** - Measure performance bottlenecks

### Documentation
- **`docs/BACKTEST_PERFORMANCE_OPTIMIZATION.md`** - Comprehensive optimization guide
- **`docs/BACKTEST_QUICKSTART_OPTIMIZATION.md`** - This quick-start guide

---

## 🔧 Next Steps (Optional)

### Phase 2: Implement Caching in Code (1-2 hours)

Modify `quantlab/backtest/realtime_features.py` to load from cache:

```python
def _fetch_ticker_features(self, ticker, start_date, end_date, feature_names):
    """Fetch features - use cache if available"""

    cache_file = Path(f"/Volumes/sandisk/quantmini-data/data/indicators_cache/{ticker}_indicators.parquet")

    if cache_file.exists():
        # Load from cache (FAST!)
        df = pd.read_parquet(cache_file)
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

        # Select requested features
        cols_to_keep = ['date'] + [f for f in feature_names if f.startswith('polygon_')]
        # Map feature names to cache columns: polygon_rsi_14 -> rsi_14
        cache_col_map = {
            'polygon_rsi_14': 'rsi_14',
            'polygon_macd_hist': 'macd_hist',
            'polygon_sma_20': 'sma_20',
            'polygon_sma_50': 'sma_50',
        }
        # ... return filtered data
    else:
        # Fallback to on-demand calculation
        # ... existing code
```

### Phase 3: Parallel Processing (2-3 hours)

Add ThreadPoolExecutor to `fetch_features()`:

```python
from concurrent.futures import ThreadPoolExecutor

def fetch_features(self, instruments, start_time, end_time, feature_names):
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Process 8 stocks at once
        futures = {executor.submit(...): ticker for ticker in instruments}
        # ... collect results
```

**Expected speedup**: 4-8x faster with parallelization

---

## 📈 Performance Summary

| Optimization | Time Saved | Effort | Priority |
|--------------|------------|--------|----------|
| Use dev config | 80-90% | 5 min | ⭐⭐⭐ HIGH |
| Pre-compute indicators | 50-60% | 15 min | ⭐⭐⭐ HIGH |
| Pre-fetch fundamentals | 30-40% | 10 min | ⭐⭐ MEDIUM |
| Implement caching in code | 70-80% | 1-2 hours | ⭐⭐ MEDIUM |
| Parallel processing | 75-85% | 2-3 hours | ⭐ LOW |

**Cumulative impact**: Starting from 10 minutes → Down to 1-2 minutes with all optimizations

---

## ✅ Checklist

Quick implementation checklist:

- [ ] Run benchmark to establish baseline: `uv run python scripts/analysis/benchmark_backtest.py`
- [ ] Test dev config: `cd qlib_repo && uv run qrun ../configs/backtest_dev.yaml`
- [ ] Pre-compute indicators: `uv run python scripts/data/precompute_indicators.py`
- [ ] (Optional) Pre-fetch fundamentals: `uv run python scripts/data/precompute_fundamentals.py`
- [ ] Run benchmark again to measure improvement
- [ ] Update `.claude/PROJECT_MEMORY.md` with optimization notes

---

## 🎓 Key Takeaways

1. **Use the right tool for the job**: Dev config for iteration, full config for validation
2. **Cache expensive computations**: Pre-compute indicators and fundamentals
3. **Measure before optimizing**: Run benchmarks to identify real bottlenecks
4. **Iterate quickly**: Fast feedback loop = better strategies

**Remember**: Faster backtests = more experiments = better strategies! 🚀
