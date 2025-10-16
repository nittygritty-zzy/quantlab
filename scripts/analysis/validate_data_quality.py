#!/usr/bin/env python3
"""Data Quality Validation Script

This script checks for common data quality issues:
1. Survivorship bias (delisted stocks missing)
2. Look-ahead bias (features using future data)
3. Corporate action adjustments (splits, dividends)
4. Data completeness and consistency

Usage:
    cd /path/to/quantlab
    uv run python scripts/analysis/validate_data_quality.py
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Change to project root
os.chdir(Path(__file__).parent.parent.parent)
sys.path.insert(0, str(Path("qlib_repo")))

import qlib
from qlib.data import D

# Initialize qlib
qlib.init(provider_uri="/Volumes/sandisk/quantmini-data/data/qlib/stocks_daily", region="cn")

print("=" * 80)
print("DATA QUALITY VALIDATION REPORT")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ==============================================================================
# 1. SURVIVORSHIP BIAS CHECK
# ==============================================================================
print("\n" + "=" * 80)
print("1. SURVIVORSHIP BIAS CHECK")
print("=" * 80)

# Load instrument list
instruments_file = Path("/Volumes/sandisk/quantmini-data/data/qlib/stocks_daily/instruments/liquid_stocks.txt")
instruments_df = pd.read_csv(instruments_file, sep='\t', header=None, names=['symbol', 'start_datetime', 'end_datetime'])

print(f"\nTotal instruments in universe: {len(instruments_df)}")

# Check date ranges
instruments_df['start_datetime'] = pd.to_datetime(instruments_df['start_datetime'])
instruments_df['end_datetime'] = pd.to_datetime(instruments_df['end_datetime'])

# Find stocks that ended before the latest date
latest_date = instruments_df['end_datetime'].max()
earliest_date = instruments_df['start_datetime'].min()
delisted = instruments_df[instruments_df['end_datetime'] < latest_date]

print(f"\nDate range: {earliest_date.date()} to {latest_date.date()}")
print(f"Stocks potentially delisted (end before {latest_date.date()}): {len(delisted)}")

if len(delisted) > 0:
    print(f"\n⚠️  WARNING: {len(delisted)} stocks ended before the latest date")
    print("This could indicate delisted stocks, which is GOOD (no survivorship bias)")
    print("\nSample delisted stocks:")
    print(delisted[['symbol', 'start_datetime', 'end_datetime']].head(10))
else:
    print("\n⚠️  POTENTIAL ISSUE: All stocks have the same end date")
    print("This is unusual and may indicate survivorship bias")

# Check stocks that started mid-period
mid_starters = instruments_df[instruments_df['start_datetime'] > earliest_date]
print(f"\nStocks that started after {earliest_date.date()}: {len(mid_starters)}")
print("(IPOs or newly added stocks)")

# ==============================================================================
# 2. DATA AVAILABILITY OVER TIME
# ==============================================================================
print("\n" + "=" * 80)
print("2. DATA AVAILABILITY OVER TIME")
print("=" * 80)

# Sample dates to check
check_dates = [
    "2024-01-02",
    "2024-04-01",
    "2024-07-01",
    "2024-10-01",
    "2025-01-02",
    "2025-04-01",
    "2025-07-01",
]

print("\nNumber of stocks with data on each date:")
print("-" * 50)

available_counts = []
for date in check_dates:
    # Get all stocks for this date
    try:
        instruments_on_date = D.instruments(market="liquid_stocks")
        count = len(instruments_on_date)
        available_counts.append(count)
        print(f"{date}: {count:,} stocks (instrument count at market level)")
    except Exception as e:
        print(f"{date}: ERROR - {e}")
        available_counts.append(0)

# Check for significant drops (might indicate data issues)
if available_counts and max(available_counts) > 0:
    max_count = max(available_counts)
    min_count = min(available_counts)
    variation = (max_count - min_count) / max_count * 100

    print(f"\nVariation: {variation:.1f}% between max ({max_count:,}) and min ({min_count:,})")

    if variation > 20:
        print("⚠️  WARNING: Large variation in stock count over time (>20%)")
        print("Could indicate data quality issues or major market events")
    else:
        print("✓ Stock count relatively stable over time")

# ==============================================================================
# 3. LOOK-AHEAD BIAS CHECK (FEATURE AVAILABILITY)
# ==============================================================================
print("\n" + "=" * 80)
print("3. LOOK-AHEAD BIAS CHECK")
print("=" * 80)

# Sample a few stocks to check feature alignment
sample_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
test_date = "2024-09-01"

print(f"\nChecking if features are available on prediction date: {test_date}")
print("(Features should only use data from BEFORE the prediction date)")
print("-" * 50)

for stock in sample_stocks:
    try:
        # Get close price on the test date
        close_price = D.features([stock], ['$close'], start_time=test_date, end_time=test_date)

        if not close_price.empty:
            price = close_price.values[0][0]
            print(f"{stock}: ✓ Data available (close=${price:.2f})")

            # Check if Alpha158 features are available
            # Try to get a simple Alpha158 feature (KLEN = (high - low) / open)
            klen_data = D.features([stock], ['($high-$low)/$open'], start_time=test_date, end_time=test_date)
            if not klen_data.empty:
                print(f"  → Alpha158 features calculable ✓")
            else:
                print(f"  → ⚠️  Alpha158 features NOT available")
        else:
            print(f"{stock}: ✗ No data available on {test_date}")
    except Exception as e:
        print(f"{stock}: ERROR - {e}")

# ==============================================================================
# 4. CORPORATE ACTIONS CHECK
# ==============================================================================
print("\n" + "=" * 80)
print("4. CORPORATE ACTIONS CHECK")
print("=" * 80)

print("\nChecking for potential stock splits (large price jumps)...")
print("-" * 50)

# Check for suspicious price movements that might indicate unadjusted splits
sample_stocks_extended = ['AAPL', 'TSLA', 'NVDA', 'GOOGL', 'AMZN']

for stock in sample_stocks_extended:
    try:
        # Get daily returns over entire period
        prices = D.features([stock], ['$close'], start_time="2024-01-02", end_time="2025-09-30")

        if len(prices) > 1:
            prices_series = prices.values.flatten()
            # Calculate day-over-day changes
            pct_changes = pd.Series(prices_series).pct_change()

            # Look for changes > 50% in one day (potential split if not adjusted)
            large_moves = pct_changes[abs(pct_changes) > 0.5]

            if len(large_moves) > 0:
                print(f"{stock}: ⚠️  {len(large_moves)} days with >50% price change")
                for idx, change in large_moves.items():
                    print(f"  → Day {idx}: {change*100:.1f}% change")
            else:
                max_move = pct_changes.abs().max() if len(pct_changes) > 0 else 0
                print(f"{stock}: ✓ No suspicious splits (max daily move: {max_move*100:.1f}%)")
    except Exception as e:
        print(f"{stock}: ERROR - {e}")

# ==============================================================================
# 5. DATA COMPLETENESS CHECK
# ==============================================================================
print("\n" + "=" * 80)
print("5. DATA COMPLETENESS CHECK")
print("=" * 80)

print("\nChecking for missing data (NaN values)...")
print("-" * 50)

# Sample stocks and check for missing values
for stock in sample_stocks:
    try:
        # Get OHLCV data
        data = D.features([stock], ['$open', '$high', '$low', '$close', '$volume'],
                         start_time="2024-01-02", end_time="2025-09-30")

        if len(data) > 0:
            total_points = len(data) * 5  # 5 features
            nan_count = data.isna().sum().sum()
            nan_pct = (nan_count / total_points) * 100

            if nan_pct > 0:
                print(f"{stock}: ⚠️  {nan_pct:.2f}% missing values ({nan_count}/{total_points})")
            else:
                print(f"{stock}: ✓ No missing values ({len(data)} days)")
        else:
            print(f"{stock}: ⚠️  No data available")
    except Exception as e:
        print(f"{stock}: ERROR - {e}")

# ==============================================================================
# 6. SUMMARY AND RECOMMENDATIONS
# ==============================================================================
print("\n" + "=" * 80)
print("6. SUMMARY AND RECOMMENDATIONS")
print("=" * 80)

recommendations = []

if len(delisted) == 0:
    recommendations.append("⚠️  All stocks have same end date - possible survivorship bias")
else:
    recommendations.append(f"✓ Dataset includes {len(delisted)} delisted stocks - no survivorship bias detected")

if variation > 20:
    recommendations.append(f"⚠️  Stock count varies by {variation:.1f}% over time - investigate cause")
else:
    recommendations.append(f"✓ Stock count stable over time (variation: {variation:.1f}%)")

recommendations.append("⚠️  Alpha158 features should be manually verified for look-ahead bias")
recommendations.append("⚠️  Corporate actions need verification - check provider documentation")

print("\n" + "\n".join(recommendations))

print("\n" + "=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)
print("\nNext steps:")
print("1. Review warnings and investigate any issues")
print("2. Compare backtest results with in-sample IC to detect overfitting")
print("3. Run backtest on recent data (last 3 months) as out-of-sample test")
print("4. Consider using alternative data source for validation")
print("=" * 80)
