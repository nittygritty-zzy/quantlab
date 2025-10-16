#!/usr/bin/env python3
"""
Benchmark backtest performance and identify bottlenecks

Usage:
    cd qlib_repo
    uv run python ../scripts/analysis/benchmark_backtest.py
"""

import time
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quantlab.data.data_manager import DataManager
from quantlab.data.database import DatabaseManager
from quantlab.data.parquet_reader import ParquetReader
from quantlab.utils.config import load_config
from quantlab.backtest.realtime_features import RealtimeIndicatorFetcher


def benchmark_data_loading():
    """Benchmark data loading performance"""
    print("=" * 60)
    print("BENCHMARK: Data Loading Performance")
    print("=" * 60)

    # Initialize data manager
    config = load_config()
    db = DatabaseManager(db_path=config.database_path)
    parquet = ParquetReader(parquet_root=config.parquet_root)
    data_manager = DataManager(config, db, parquet)

    # Test configuration
    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "META", "TSLA", "JPM", "V", "UNH"
    ]
    start_date = "2024-01-01"
    end_date = "2024-12-31"

    feature_names = [
        "polygon_rsi_14",
        "polygon_macd_hist",
        "polygon_sma_20",
        "polygon_sma_50"
    ]

    # 1. Benchmark raw parquet loading
    print("\n1. Raw Parquet Loading (10 stocks, 1 year)")
    print("-" * 60)
    start = time.time()

    for ticker in tickers:
        df = parquet.get_stock_daily(
            tickers=[ticker],
            start_date=start_date,
            end_date=end_date
        )

    parquet_time = time.time() - start
    print(f"   Time: {parquet_time:.2f}s ({parquet_time/len(tickers):.3f}s per stock)")

    # 2. Benchmark indicator calculation
    print("\n2. Technical Indicator Calculation")
    print("-" * 60)
    start = time.time()

    fetcher = RealtimeIndicatorFetcher(data_manager)
    df_features = fetcher.fetch_features(
        instruments=tickers,
        start_time=start_date,
        end_time=end_date,
        feature_names=feature_names
    )

    indicator_time = time.time() - start
    print(f"   Time: {indicator_time:.2f}s ({indicator_time/len(tickers):.3f}s per stock)")
    print(f"   Rows: {len(df_features)}")
    print(f"   Columns: {len(df_features.columns)}")

    # 3. Benchmark external API calls (yfinance)
    print("\n3. External API Calls (yfinance fundamentals)")
    print("-" * 60)

    yf_features = ["yf_pe_ratio", "yf_revenue_growth"]
    start = time.time()

    df_fundamentals = fetcher.fetch_features(
        instruments=tickers[:3],  # Only 3 stocks to avoid rate limits
        start_time=start_date,
        end_time=end_date,
        feature_names=yf_features
    )

    api_time = time.time() - start
    print(f"   Time: {api_time:.2f}s ({api_time/3:.3f}s per stock)")
    print(f"   Note: This is SLOW - pre-caching recommended for production")

    # Summary
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"Parquet loading:      {parquet_time:.2f}s")
    print(f"Indicator calculation: {indicator_time:.2f}s")
    print(f"API calls (3 stocks):  {api_time:.2f}s")
    print(f"\nEstimated time for 50 stocks (all features):")
    print(f"  Technical only:  {(parquet_time + indicator_time) * 5:.1f}s")
    print(f"  With APIs:       {(parquet_time + indicator_time) * 5 + api_time * 16.7:.1f}s")
    print("\nRECOMMENDATIONS:")
    print("  1. Pre-cache technical indicators → Save ~{:.1f}s per run".format(indicator_time * 5))
    print("  2. Parallelize data fetching → 4-8x speedup possible")
    print("  3. Pre-fetch API data → Save ~{:.1f}s per run".format(api_time * 16.7))


def benchmark_model_training():
    """Benchmark model training performance"""
    print("\n" + "=" * 60)
    print("BENCHMARK: Model Training Performance")
    print("=" * 60)
    print("\nTo benchmark model training, run:")
    print("  cd qlib_repo")
    print("  time uv run qrun ../configs/backtest_demo_small.yaml")
    print("\nLook for these timing metrics:")
    print("  - Dataset preparation time")
    print("  - Model training time")
    print("  - Backtest execution time")


if __name__ == "__main__":
    benchmark_data_loading()
    benchmark_model_training()

    print("\n" + "=" * 60)
    print("Next steps: Review results and apply optimizations")
    print("=" * 60)
