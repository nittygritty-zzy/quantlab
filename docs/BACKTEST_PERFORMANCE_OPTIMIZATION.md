# Backtest Performance Optimization Guide

**Date**: October 15, 2025
**Status**: Recommendations for Production Deployment

## Current Performance Baseline

Based on the successful backtest runs:
- **Demo (10 stocks)**: ~2-3 minutes total
- **Full (50 stocks)**: ~8-12 minutes estimated
- **Bottlenecks**: External API calls (yfinance, Alpha Vantage), indicator recalculation

## Optimization Roadmap (Prioritized)

### Phase 1: Quick Wins (30 minutes implementation)

#### 1.1 Use Development Config for Iteration
**Impact**: 5x faster testing
**Effort**: 5 minutes

```yaml
# configs/backtest_dev.yaml
market: &market ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]  # 5 stocks only

task:
  model:
    kwargs:
      max_depth: 4
      num_leaves: 16
      num_boost_round: 100  # Fewer rounds
```

**When to use**: Strategy development, hyperparameter tuning
**When to skip**: Final performance evaluation

#### 1.2 Reduce Model Complexity
**Impact**: 2-3x faster training
**Effort**: 5 minutes

```yaml
# Update all configs
task:
  model:
    kwargs:
      max_depth: 4              # Was 6
      num_leaves: 32            # Was 64
      num_boost_round: 300      # Was 1000
      early_stopping_rounds: 30 # Was 50
```

**Trade-off**: Slightly lower model accuracy (~1-2% IC drop), but much faster iteration.

#### 1.3 Skip Slow Features During Development
**Impact**: 10x faster for API-heavy configs
**Effort**: 10 minutes

```yaml
# Temporarily comment out slow features
feature_names:
  - polygon_rsi_14
  - polygon_macd_hist
  # - yf_pe_ratio          # Uncomment for final run
  # - yf_revenue_growth     # Uncomment for final run
  # - av_sentiment_score    # Uncomment for final run
```

**When to use**: Feature engineering experiments, strategy logic testing
**Restore**: Before final evaluation

---

### Phase 2: Caching System (2 hours implementation)

#### 2.1 Pre-compute Technical Indicators
**Impact**: Save ~60% of computation time
**Effort**: 1 hour

**Implementation**:

```python
# scripts/data/precompute_indicators.py

import pandas as pd
from quantlab.data.parquet_reader import ParquetReader
from quantlab.analysis.technical_indicators import TechnicalIndicators
from quantlab.utils.config import load_config
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def precompute_all_indicators(
    tickers: list,
    start_date: str,
    end_date: str,
    cache_dir: str = "/Volumes/sandisk/quantmini-data/data/indicators_cache"
):
    """
    Pre-calculate all technical indicators and save to parquet

    This needs to be run ONCE before backtests, or when new data is added.

    Usage:
        uv run python scripts/data/precompute_indicators.py
    """
    config = load_config()
    parquet = ParquetReader(parquet_root=config.parquet_root)
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    for ticker in tickers:
        print(f"Processing {ticker}...")

        # Load raw OHLCV
        df = parquet.get_stock_daily(
            tickers=[ticker],
            start_date=start_date,
            end_date=end_date
        )

        if df is None or df.empty:
            logger.warning(f"No data for {ticker}")
            continue

        # Calculate ALL indicators at once
        df['rsi_14'] = TechnicalIndicators.rsi(df['close'], 14)
        df['rsi_30'] = TechnicalIndicators.rsi(df['close'], 30)

        macd_line, signal_line, macd_hist = TechnicalIndicators.macd(df['close'])
        df['macd_line'] = macd_line
        df['macd_signal'] = signal_line
        df['macd_hist'] = macd_hist

        df['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
        df['sma_50'] = TechnicalIndicators.sma(df['close'], 50)
        df['sma_200'] = TechnicalIndicators.sma(df['close'], 200)

        df['ema_12'] = TechnicalIndicators.ema(df['close'], 12)
        df['ema_26'] = TechnicalIndicators.ema(df['close'], 26)

        upper_bb, middle_bb, lower_bb = TechnicalIndicators.bollinger_bands(df['close'])
        df['bb_upper'] = upper_bb
        df['bb_middle'] = middle_bb
        df['bb_lower'] = lower_bb

        # Save to cache
        cache_file = cache_path / f"{ticker}_indicators.parquet"
        df.to_parquet(cache_file, index=False)
        print(f"  ✓ Saved to {cache_file}")

    print(f"\n✓ Pre-computed indicators for {len(tickers)} stocks")
    print(f"  Cache directory: {cache_dir}")

if __name__ == "__main__":
    # Top 50 stocks
    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "UNH", "XOM",
        "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "LLY", "ABBV", "MRK",
        "AVGO", "PEP", "COST", "KO", "ADBE", "WMT", "MCD", "CSCO", "CRM", "ACN",
        "TMO", "ABT", "NFLX", "DHR", "CMCSA", "VZ", "NKE", "DIS", "TXN", "INTC",
        "AMD", "QCOM", "UPS", "PM", "NEE", "RTX", "HON", "ORCL", "INTU", "AMGN"
    ]

    precompute_all_indicators(
        tickers=tickers,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
```

**Then modify `realtime_features.py` to use cache**:

```python
def _fetch_ticker_features(self, ticker, start_date, end_date, feature_names):
    """Fetch features - use cache if available"""

    cache_file = Path(f"/Volumes/sandisk/quantmini-data/data/indicators_cache/{ticker}_indicators.parquet")

    if cache_file.exists():
        # Load from cache (FAST!)
        df = pd.read_parquet(cache_file)
        # Filter by date range and features
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        # Select only requested features
        # ... return filtered data
    else:
        # Fallback to on-demand calculation
        # ... existing code
```

**Maintenance**: Re-run precompute script daily/weekly as new data arrives.

#### 2.2 Pre-fetch Fundamental Data
**Impact**: Eliminate 80% of API call time
**Effort**: 1 hour

```python
# scripts/data/precompute_fundamentals.py

import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def precompute_fundamentals(tickers, cache_dir="/Volumes/sandisk/quantmini-data/data/fundamentals_cache"):
    """
    Fetch fundamental data once and cache it

    Run daily/weekly to keep fresh.
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    all_fundamentals = []

    for ticker in tickers:
        print(f"Fetching {ticker}...")
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract key metrics
            fundamental_data = {
                'ticker': ticker,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'pe_ratio': info.get('forwardPE', None),
                'trailing_pe': info.get('trailingPE', None),
                'peg_ratio': info.get('pegRatio', None),
                'pb_ratio': info.get('priceToBook', None),
                'revenue_growth': info.get('revenueGrowth', None),
                'profit_margin': info.get('profitMargins', None),
                'roe': info.get('returnOnEquity', None),
                'debt_to_equity': info.get('debtToEquity', None),
                'market_cap': info.get('marketCap', None)
            }

            all_fundamentals.append(fundamental_data)

        except Exception as e:
            print(f"  Error: {e}")
            continue

    # Save to parquet
    df = pd.DataFrame(all_fundamentals)
    cache_file = cache_path / f"fundamentals_{datetime.now().strftime('%Y%m%d')}.parquet"
    df.to_parquet(cache_file, index=False)
    print(f"\n✓ Saved fundamentals to {cache_file}")

    return df

# Run this via cron daily
```

---

### Phase 3: Parallel Processing (3 hours implementation)

#### 3.1 Parallelize Ticker Processing
**Impact**: 4-8x faster data loading
**Effort**: 2 hours

**Modify `realtime_features.py`**:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

def fetch_features(
    self,
    instruments: List[str],
    start_time: str,
    end_time: str,
    feature_names: List[str] = None
) -> pd.DataFrame:
    """Fetch features with parallel processing"""

    start_date = datetime.strptime(start_time, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_time, '%Y-%m-%d').date()

    results = []

    # Determine optimal worker count (use 50-75% of CPU cores)
    num_workers = min(8, max(4, multiprocessing.cpu_count() // 2))

    logger.info(f"Processing {len(instruments)} tickers with {num_workers} workers")

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        future_to_ticker = {
            executor.submit(
                self._fetch_ticker_features,
                ticker,
                start_date,
                end_date,
                feature_names
            ): ticker
            for ticker in instruments
        }

        # Collect results as they complete
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                df = future.result(timeout=30)  # 30s timeout per ticker
                if df is not None and not df.empty:
                    results.append(df)
                    logger.debug(f"  ✓ {ticker}: {len(df)} rows")
            except Exception as e:
                logger.error(f"  ✗ {ticker}: {e}")

    if results:
        df_combined = pd.concat(results, ignore_index=False)
        logger.info(f"✓ Loaded {len(df_combined)} total rows")
        return df_combined

    return pd.DataFrame()
```

**Caution**: Be mindful of API rate limits for yfinance/Alpha Vantage calls.

#### 3.2 Use Process Pool for Heavy Computation
**Impact**: 2-3x faster for CPU-bound tasks
**Effort**: 1 hour

For very heavy indicator calculations, use `ProcessPoolExecutor` instead of threads:

```python
from concurrent.futures import ProcessPoolExecutor

# Better for CPU-bound tasks (heavy calculations)
with ProcessPoolExecutor(max_workers=4) as executor:
    # ... same pattern as ThreadPoolExecutor
```

---

### Phase 4: Production Optimizations (4+ hours)

#### 4.1 Incremental Data Updates
**Impact**: 100x faster for daily updates
**Effort**: 3 hours

Instead of recalculating everything:
```python
# Only process new data since last run
last_run_date = get_last_backtest_date()
new_data_start = last_run_date + timedelta(days=1)
new_data_end = datetime.now().date()

# Append only new rows to cached indicators
```

#### 4.2 GPU Acceleration for LightGBM
**Impact**: 5-10x faster model training
**Effort**: 1 hour (if GPU available)

```yaml
task:
  model:
    class: LGBModel
    kwargs:
      device: gpu
      gpu_platform_id: 0
      gpu_device_id: 0
```

Requires: CUDA-enabled GPU and `lightgbm` compiled with GPU support.

#### 4.3 Distributed Computing
**Impact**: Near-linear scaling with workers
**Effort**: 8+ hours

Use Qlib's distributed execution:
- Ray for parallel backtest execution
- Spark for large-scale data processing
- Multiple machines for stock universe partitioning

---

## Benchmark Your System

**Before optimizations, run benchmarks**:

```bash
cd qlib_repo

# 1. Benchmark data loading
uv run python ../scripts/analysis/benchmark_backtest.py

# 2. Benchmark full backtest
time uv run qrun ../configs/backtest_demo_small.yaml

# 3. Benchmark with 50 stocks
time uv run qrun ../configs/backtest_tech_fundamental.yaml
```

**Track these metrics**:
- Data loading time
- Indicator calculation time
- Model training time
- Backtest execution time
- Total end-to-end time

---

## Recommended Workflow

### Development Phase (Fast Iteration)
```bash
# 1. Use dev config (5-10 stocks)
configs/backtest_dev.yaml

# 2. Simpler model
max_depth: 3
num_boost_round: 50

# 3. Cache technical indicators
uv run python scripts/data/precompute_indicators.py

# 4. Skip slow API features
feature_names:
  - polygon_rsi_14      # Fast (cached)
  - polygon_macd_hist   # Fast (cached)
  # - yf_pe_ratio       # Slow (skip for dev)
```

**Expected time**: 30-60 seconds per iteration

### Production Phase (Full Backtest)
```bash
# 1. Pre-compute everything
uv run python scripts/data/precompute_indicators.py
uv run python scripts/data/precompute_fundamentals.py

# 2. Use full config (50 stocks)
configs/backtest_tech_fundamental.yaml

# 3. Optimized model settings
max_depth: 5
num_boost_round: 500

# 4. Run with all features
# (uses cached data)
```

**Expected time**: 2-3 minutes (vs 10-15 minutes without caching)

---

## Performance Targets

| Phase | Stocks | Features | Time Target | Status |
|-------|--------|----------|-------------|---------|
| **Development** | 5-10 | Technical only | <1 minute | Achievable with caching |
| **Testing** | 20-30 | All features | 2-3 minutes | Achievable with parallel + cache |
| **Production** | 50+ | All features | 3-5 minutes | Achievable with full optimization |
| **Research** | 100+ | All features | 10-15 minutes | Requires distributed computing |

---

## Quick Start: Implement Top 3 Optimizations

**30-minute optimization sprint**:

1. **Create dev config** (5 min):
```bash
cp configs/backtest_demo_small.yaml configs/backtest_dev.yaml
# Edit to use 5 stocks, simpler model
```

2. **Pre-compute indicators** (15 min):
```bash
uv run python scripts/data/precompute_indicators.py
# Modify realtime_features.py to use cache
```

3. **Reduce model complexity** (10 min):
```yaml
# Edit all configs:
max_depth: 4
num_leaves: 32
num_boost_round: 300
```

**Expected speedup**: 3-5x faster backtests

---

## Monitoring & Profiling

Add timing instrumentation:

```python
import time
import logging

logger = logging.getLogger(__name__)

def fetch_features(self, ...):
    t0 = time.time()

    # ... data loading
    t1 = time.time()
    logger.info(f"Data loading: {t1-t0:.2f}s")

    # ... indicator calculation
    t2 = time.time()
    logger.info(f"Indicators: {t2-t1:.2f}s")

    # ... API calls
    t3 = time.time()
    logger.info(f"API calls: {t3-t2:.2f}s")

    logger.info(f"Total: {t3-t0:.2f}s")
```

Use this data to identify actual bottlenecks in YOUR system.

---

## Summary

**Fastest path to 5x speedup**:
1. Use dev config with 5-10 stocks
2. Pre-compute and cache technical indicators
3. Reduce model complexity during development
4. Skip slow API features during iteration

**Production-ready optimization**:
- Implement full caching system (Phase 2)
- Add parallel processing (Phase 3)
- Use optimized configs for different use cases

**Measure first, optimize second**: Run benchmarks to identify YOUR bottlenecks before implementing all optimizations.
