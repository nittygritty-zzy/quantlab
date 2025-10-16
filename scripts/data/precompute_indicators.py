#!/usr/bin/env python3
"""
Pre-compute technical indicators for all stocks

This script calculates all technical indicators once and caches them to parquet files.
This eliminates the need to recalculate indicators on every backtest run.

Usage:
    uv run python scripts/data/precompute_indicators.py

Cache location: /Volumes/sandisk/quantmini-data/data/indicators_cache/

Run this:
- Once before starting backtest development
- Daily/weekly as new data arrives
- After adding new indicators
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quantlab.data.parquet_reader import ParquetReader
from quantlab.analysis.technical_indicators import TechnicalIndicators
from quantlab.utils.config import load_config
from quantlab.utils.logger import setup_logger

logger = setup_logger(__name__)


def precompute_all_indicators(
    tickers: list,
    start_date: str,
    end_date: str,
    cache_dir: str = "/Volumes/sandisk/quantmini-data/data/indicators_cache"
):
    """
    Pre-calculate all technical indicators and save to parquet

    Args:
        tickers: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        cache_dir: Directory to save cached indicators
    """
    print("=" * 70)
    print("PRECOMPUTING TECHNICAL INDICATORS")
    print("=" * 70)
    print(f"Date range: {start_date} to {end_date}")
    print(f"Tickers: {len(tickers)}")
    print(f"Cache directory: {cache_dir}")
    print()

    # Initialize parquet reader
    config = load_config()
    parquet = ParquetReader(parquet_root=config.parquet_root)

    # Create cache directory
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    successful = 0
    failed = 0
    skipped = 0

    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Processing {ticker}...", end=" ")

        try:
            # Check if already cached and recent
            cache_file = cache_path / f"{ticker}_indicators.parquet"
            if cache_file.exists():
                # Check if cache is recent (less than 1 day old)
                cache_age_hours = (datetime.now().timestamp() - cache_file.stat().st_mtime) / 3600
                if cache_age_hours < 24:
                    print(f"✓ Cached (age: {cache_age_hours:.1f}h)")
                    skipped += 1
                    continue

            # Load raw OHLCV data
            df = parquet.get_stock_daily(
                tickers=[ticker],
                start_date=start_date,
                end_date=end_date
            )

            if df is None or df.empty:
                print("✗ No data")
                failed += 1
                continue

            # Keep original OHLCV columns
            result_df = df[['date', 'open', 'high', 'low', 'close', 'volume']].copy()

            # Calculate ALL technical indicators
            # RSI
            result_df['rsi_14'] = TechnicalIndicators.rsi(df['close'], period=14)
            result_df['rsi_30'] = TechnicalIndicators.rsi(df['close'], period=30)

            # MACD
            macd_line, signal_line, macd_hist = TechnicalIndicators.macd(
                df['close'], fast_period=12, slow_period=26, signal_period=9
            )
            result_df['macd_line'] = macd_line
            result_df['macd_signal'] = signal_line
            result_df['macd_hist'] = macd_hist

            # Moving Averages
            result_df['sma_5'] = TechnicalIndicators.sma(df['close'], period=5)
            result_df['sma_10'] = TechnicalIndicators.sma(df['close'], period=10)
            result_df['sma_20'] = TechnicalIndicators.sma(df['close'], period=20)
            result_df['sma_50'] = TechnicalIndicators.sma(df['close'], period=50)
            result_df['sma_200'] = TechnicalIndicators.sma(df['close'], period=200)

            # Exponential Moving Averages
            result_df['ema_12'] = TechnicalIndicators.ema(df['close'], period=12)
            result_df['ema_26'] = TechnicalIndicators.ema(df['close'], period=26)
            result_df['ema_50'] = TechnicalIndicators.ema(df['close'], period=50)

            # Bollinger Bands
            upper_bb, middle_bb, lower_bb = TechnicalIndicators.bollinger_bands(
                df['close'], period=20, num_std=2.0
            )
            result_df['bb_upper'] = upper_bb
            result_df['bb_middle'] = middle_bb
            result_df['bb_lower'] = lower_bb
            result_df['bb_width'] = (upper_bb - lower_bb) / middle_bb

            # Volume indicators
            result_df['volume_sma_20'] = TechnicalIndicators.sma(df['volume'], period=20)
            result_df['volume_ratio'] = df['volume'] / result_df['volume_sma_20']

            # Calculate number of valid rows (after warm-up period)
            valid_rows = result_df.dropna().shape[0]

            # Save to cache (including NaN rows for alignment)
            result_df.to_parquet(cache_file, index=False)

            print(f"✓ {valid_rows} valid rows, saved to cache")
            successful += 1

        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            failed += 1
            logger.error(f"Failed to process {ticker}: {e}", exc_info=True)

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Successful: {successful}")
    print(f"Skipped (cached): {skipped}")
    print(f"Failed: {failed}")
    print(f"Total: {len(tickers)}")
    print()
    print(f"Cache location: {cache_dir}")
    print()

    if successful > 0:
        print("✓ Indicators pre-computed successfully!")
        print()
        print("Next steps:")
        print("  1. Update backtest configs to use faster settings")
        print("  2. Modify realtime_features.py to load from cache")
        print("  3. Run backtests and enjoy the speedup!")
    else:
        print("✗ No indicators were computed. Check errors above.")

    return successful, skipped, failed


if __name__ == "__main__":
    # Top 50 liquid US stocks
    TICKERS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "UNH", "XOM",
        "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "LLY", "ABBV", "MRK",
        "AVGO", "PEP", "COST", "KO", "ADBE", "WMT", "MCD", "CSCO", "CRM", "ACN",
        "TMO", "ABT", "NFLX", "DHR", "CMCSA", "VZ", "NKE", "DIS", "TXN", "INTC",
        "AMD", "QCOM", "UPS", "PM", "NEE", "RTX", "HON", "ORCL", "INTU", "AMGN"
    ]

    # Date range for backtests
    START_DATE = "2024-01-01"
    END_DATE = "2024-12-31"

    # Run precomputation
    precompute_all_indicators(
        tickers=TICKERS,
        start_date=START_DATE,
        end_date=END_DATE
    )
