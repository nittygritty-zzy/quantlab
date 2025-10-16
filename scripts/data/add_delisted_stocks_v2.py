#!/usr/bin/env python3
"""
Add Delisted Stocks to Qlib Dataset (Optimized)

Uses list_tickers to get delisted stocks directly (no need for get_ticker_details).
Much faster than v1 since we avoid the second API call per ticker.

Requirements:
    - polygon-api-client
    - POLYGON_API_KEY environment variable

Usage:
    export POLYGON_API_KEY=your_key
    cd /path/to/quantlab
    uv run python scripts/data/add_delisted_stocks_v2.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from polygon import RESTClient
import time

# Change to project root
os.chdir(Path(__file__).parent.parent.parent)

# Configuration
QLIB_DATA_PATH = Path("/Volumes/sandisk/quantmini-data/data/qlib/stocks_daily")
PARQUET_DATA_PATH = Path("data/parquet")
BACKTEST_START = "2024-01-02"
BACKTEST_END = "2025-10-06"

print("=" * 80)
print("ADD DELISTED STOCKS TO QLIB DATASET (OPTIMIZED V2)")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Backtest period: {BACKTEST_START} to {BACKTEST_END}")
print("Strategy: Query all delisted stocks, filter by delisting date")
print("=" * 80)

# Initialize Polygon client
try:
    client = RESTClient()
    print("\n✓ Polygon API client initialized")
except Exception as e:
    print(f"\n❌ Error initializing Polygon client: {e}")
    print("Make sure POLYGON_API_KEY environment variable is set")
    sys.exit(1)

# ==============================================================================
# STEP 1: Query Delisted Stocks and Filter by Date
# ==============================================================================
print("\n" + "=" * 80)
print("STEP 1: QUERY AND FILTER DELISTED STOCKS")
print("=" * 80)

print("\nQuerying delisted stocks from Polygon...")
print("Note: list_tickers includes delisted_utc directly - no need for extra API calls!")

backtest_start_dt = datetime.fromisoformat(BACKTEST_START + 'T00:00:00+00:00')
backtest_end_dt = datetime.fromisoformat(BACKTEST_END + 'T23:59:59+00:00')

all_delisted = []
in_period = []
total_checked = 0
start_time = time.time()

try:
    print("Fetching delisted tickers...")

    for ticker_obj in client.list_tickers(
        market="stocks",
        type="CS",  # Common stock only
        active=False,  # Delisted only
        limit=1000  # Max allowed by Polygon API
    ):
        total_checked += 1

        # Progress update every 100
        if total_checked % 100 == 0:
            elapsed = time.time() - start_time
            print(f"  Checked: {total_checked}, Found in period: {len(in_period)} ({elapsed:.1f}s)")

        # Check if has delisting date
        if not hasattr(ticker_obj, 'delisted_utc') or not ticker_obj.delisted_utc:
            continue

        # Parse delisting date
        try:
            delisted_date_str = ticker_obj.delisted_utc.replace('Z', '+00:00')
            delisted_date = datetime.fromisoformat(delisted_date_str)

            # Check if in our backtest period
            if backtest_start_dt <= delisted_date <= backtest_end_dt:
                in_period.append({
                    'ticker': ticker_obj.ticker,
                    'name': ticker_obj.name if hasattr(ticker_obj, 'name') else ticker_obj.ticker,
                    'delisted_date': delisted_date.strftime('%Y-%m-%d'),
                    'exchange': ticker_obj.primary_exchange if hasattr(ticker_obj, 'primary_exchange') else 'N/A',
                })

        except Exception as e:
            # Skip if can't parse date
            continue

except KeyboardInterrupt:
    print("\n\n⚠️  Interrupted by user")

except Exception as e:
    print(f"\n❌ Error querying tickers: {e}")
    import traceback
    traceback.print_exc()

elapsed_time = time.time() - start_time

print(f"\n{'=' * 80}")
print("QUERY RESULTS")
print(f"{'=' * 80}")
print(f"Time elapsed: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
print(f"Total delisted tickers checked: {total_checked}")
print(f"Delisted during backtest period ({BACKTEST_START} to {BACKTEST_END}): {len(in_period)}")

if len(in_period) == 0:
    print("\n⚠️  WARNING: No stocks delisted during backtest period!")
    print("\nThis could mean:")
    print("  1. Very few delistings occurred in 2024-2025")
    print("  2. Need to check a larger sample of delisted stocks")
    print("\nSuggestion: The backtest period might have had unusually few delistings.")
    print("Consider extending the date range or checking historical delisting rates.")

    sys.exit(0)

# Save the list
delisted_df = pd.DataFrame(in_period).sort_values('delisted_date')

print("\n" + "-" * 80)
print("DELISTED STOCKS IN BACKTEST PERIOD:")
print("-" * 80)
print(delisted_df.to_string(index=False, max_rows=50))

if len(delisted_df) > 50:
    print(f"... and {len(delisted_df) - 50} more")

# Save to CSV
output_path = Path("data") / "delisted_stocks_2024_2025.csv"
output_path.parent.mkdir(exist_ok=True, parents=True)
delisted_df.to_csv(output_path, index=False)
print(f"\n✓ Saved to: {output_path}")

# ==============================================================================
# STEP 2: Download Historical Data
# ==============================================================================
print("\n" + "=" * 80)
print("STEP 2: DOWNLOAD HISTORICAL OHLCV DATA")
print("=" * 80)

print(f"\nDownloading daily data for {len(in_period)} delisted stocks...")
print("Estimated time: ~{} minutes".format(len(in_period) / 4))  # ~4 per minute with rate limiting

PARQUET_DATA_PATH.mkdir(exist_ok=True, parents=True)

download_stats = {
    'success': 0,
    'no_data': 0,
    'errors': 0
}

start_download = time.time()

for i, stock in enumerate(in_period, 1):
    ticker = stock['ticker']
    delisted_date = stock['delisted_date']

    # Progress update every 10 or at end
    if i % 10 == 0 or i == len(in_period):
        elapsed = time.time() - start_download
        rate = i / elapsed if elapsed > 0 else 0
        remaining = len(in_period) - i
        eta_min = (remaining / rate / 60) if rate > 0 else 0
        print(f"  [{i}/{len(in_period)}] {ticker} (Rate: {rate:.1f}/sec, ETA: {eta_min:.1f}min)")

    try:
        # Download from backtest start to delisting date
        bars = []
        for bar in client.list_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=BACKTEST_START,
            to=delisted_date,
            limit=50000
        ):
            bars.append({
                'date': datetime.fromtimestamp(bar.timestamp / 1000).strftime('%Y-%m-%d'),
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'vwap': bar.vwap if hasattr(bar, 'vwap') else (bar.high + bar.low + bar.close) / 3,
            })

        # Rate limiting (5 calls/sec max, be conservative at 4)
        time.sleep(0.25)

        if len(bars) == 0:
            download_stats['no_data'] += 1
            continue

        # Save to parquet
        df = pd.DataFrame(bars)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        parquet_file = PARQUET_DATA_PATH / f"{ticker}.parquet"
        df.to_parquet(parquet_file, index=False)

        download_stats['success'] += 1

    except Exception as e:
        download_stats['errors'] += 1
        if download_stats['errors'] <= 5:  # Print first 5 errors
            print(f"  ⚠️  {ticker}: {str(e)[:60]}")
        continue

download_time = time.time() - start_download

print(f"\n{'=' * 80}")
print("DOWNLOAD SUMMARY")
print(f"{'=' * 80}")
print(f"Time elapsed: {download_time/60:.1f} minutes")
print(f"Success: {download_stats['success']}")
print(f"No data: {download_stats['no_data']}")
print(f"Errors: {download_stats['errors']}")
print(f"Total: {len(in_period)}")
print(f"Success rate: {download_stats['success']/len(in_period)*100:.1f}%")

# ==============================================================================
# STEP 3: Update Instruments File (Reference Only)
# ==============================================================================
print("\n" + "=" * 80)
print("STEP 3: NEXT STEPS")
print("=" * 80)

print(f"""
✓ Successfully downloaded {download_stats['success']} delisted stocks

To complete the integration:

1. Convert parquet files to qlib binary format:
   cd /path/to/quantlab
   uv run python scripts/data/convert_to_qlib.py

2. Update instruments file:
   Add the following tickers with end dates:
   {", ".join([s['ticker'] for s in in_period[:10]])}{"..." if len(in_period) > 10 else ""}

3. Re-run backtest:
   cd qlib_repo/examples
   uv run qrun ../../configs/xgboost_liquid_universe.yaml

Expected Impact:
  Current (with survivorship bias):
    - Annualized Return: ~188%
    - Sharpe: ~3.93
    - Universe: 13,187 stocks (0 delistings)

  After adding {download_stats['success']} delisted stocks:
    - Annualized Return: ~120-150% (more realistic)
    - Sharpe: ~2.5-3.0
    - Universe: 13,187 + {download_stats['success']} stocks

Files Created:
  - data/delisted_stocks_2024_2025.csv (reference list)
  - data/parquet/[TICKER].parquet ({download_stats['success']} new files)
""")

print("=" * 80)
print("COMPLETE - Ready for qlib conversion")
print("=" * 80)
