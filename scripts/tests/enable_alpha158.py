#!/usr/bin/env python3
"""
Enable Alpha158 Features in QuantMini Pipeline

This script:
1. Computes Alpha158 features from parquet data
2. Saves enriched data with 158+ features
3. Converts to Qlib binary format
4. Verifies the feature set

Usage:
    python enable_alpha158.py --date 2025-09-30
    python enable_alpha158.py --start 2025-09-01 --end 2025-09-30
"""

import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Add quantmini to path
sys.path.insert(0, str(Path(__file__).parent / ".venv/lib/python3.12/site-packages"))

from src.core.config_loader import ConfigLoader
from src.features.alpha158 import (
    build_alpha158_sql,
    get_alpha158_feature_list,
    KBAR_FEATURES,
    PRICE_FEATURES,
    VOLUME_FEATURES
)
import duckdb
import pyarrow.parquet as pq


def compute_alpha158_features(
    parquet_root: Path,
    enriched_root: Path,
    data_type: str,
    date: str
):
    """
    Compute Alpha158 features for a specific date

    Args:
        parquet_root: Raw parquet data directory
        enriched_root: Output directory for enriched data
        data_type: 'stocks_daily', 'stocks_minute', etc.
        date: YYYY-MM-DD
    """
    print(f"\n{'='*70}")
    print(f"Computing Alpha158 features for {data_type} on {date}")
    print(f"{'='*70}\n")

    # Initialize DuckDB
    conn = duckdb.connect(':memory:', config={
        'memory_limit': '7GB',
        'threads': 4
    })

    # Read raw parquet data
    input_pattern = parquet_root / data_type / f'{date}' / '*.parquet'
    print(f"📂 Reading: {input_pattern}")

    # Load data into DuckDB
    conn.execute(f"""
        CREATE OR REPLACE VIEW raw_data AS
        SELECT * FROM read_parquet('{input_pattern}')
    """)

    # Count records
    count = conn.execute("SELECT COUNT(*) FROM raw_data").fetchone()[0]
    print(f"📊 Records: {count:,}")

    if count == 0:
        print("⚠️  No data found, skipping...")
        return

    # Build Alpha158 SQL
    print("\n🔧 Computing Alpha158 features...")
    alpha158_sql = build_alpha158_sql('raw_data')

    # Execute and get results
    print("⏳ Running SQL query (this may take a few minutes)...")
    result = conn.execute(alpha158_sql).fetch_arrow_table()

    # Count features
    feature_count = len(result.column_names) - 7  # Exclude base columns
    print(f"✅ Computed {feature_count} features")

    # Save enriched data
    output_dir = enriched_root / data_type / date
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'data.parquet'

    print(f"\n💾 Saving to: {output_file}")
    pq.write_table(result, output_file, compression='snappy')

    file_size = output_file.stat().st_size / 1024 / 1024
    print(f"✅ Saved {file_size:.1f} MB")

    # Print feature summary
    print(f"\n📋 Feature Summary:")
    print(f"   KBAR:    {len(KBAR_FEATURES)} features")
    print(f"   Price:   {len(PRICE_FEATURES)} features")
    print(f"   Volume:  {len(VOLUME_FEATURES)} features")
    print(f"   Rolling: ~124 features")
    print(f"   Total:   {feature_count} features")

    conn.close()


def verify_features(enriched_root: Path, data_type: str, date: str):
    """Verify that Alpha158 features are present"""
    print(f"\n{'='*70}")
    print("Verifying Features")
    print(f"{'='*70}\n")

    file_path = enriched_root / data_type / date / 'data.parquet'

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    # Read parquet schema
    table = pq.read_table(file_path)
    columns = table.column_names

    print(f"📁 File: {file_path}")
    print(f"📊 Columns: {len(columns)}")

    # Check for key features
    key_features = ['KMID', 'KLEN', 'ROC5', 'MA20', 'STD20', 'CORR20']
    missing = [f for f in key_features if f not in columns]

    if missing:
        print(f"\n⚠️  Missing features: {missing}")
        return False

    print(f"\n✅ All key Alpha158 features present:")
    for feat in key_features:
        print(f"   ✓ {feat}")

    # Show sample data
    print(f"\n📊 Sample data (first row):")
    sample = table.to_pandas().iloc[0]
    for feat in key_features:
        value = sample[feat]
        print(f"   {feat:8s} = {value:.6f}" if not pd.isna(value) else f"   {feat:8s} = NaN")

    return True


def convert_to_qlib(
    enriched_root: Path,
    qlib_root: Path,
    data_type: str,
    start_date: str,
    end_date: str
):
    """Convert enriched data to Qlib binary format"""
    print(f"\n{'='*70}")
    print("Converting to Qlib Binary Format")
    print(f"{'='*70}\n")

    from src.transform.qlib_binary_writer import QlibBinaryWriter

    writer = QlibBinaryWriter(
        enriched_root=enriched_root,
        qlib_root=qlib_root,
        config=ConfigLoader(config_dir=Path("/Users/zheyuanzhao/workspace/quantmini/config"))
    )

    print(f"🔄 Converting {data_type} from {start_date} to {end_date}...")

    result = writer.convert_data_type(
        data_type=data_type,
        start_date=start_date,
        end_date=end_date,
        incremental=False
    )

    print(f"\n✅ Conversion complete:")
    print(f"   Symbols:  {result['symbols_converted']:,}")
    print(f"   Features: {result['features_written']:,}")
    print(f"   Size:     {result['bytes_written'] / 1024 / 1024:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description='Enable Alpha158 features')
    parser.add_argument('--date', type=str, help='Single date to process (YYYY-MM-DD)')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--data-type', type=str, default='stocks_daily',
                       choices=['stocks_daily', 'stocks_minute'],
                       help='Data type to process')
    parser.add_argument('--skip-conversion', action='store_true',
                       help='Skip Qlib conversion step')

    args = parser.parse_args()

    # Determine date range
    if args.date:
        start_date = end_date = args.date
    elif args.start and args.end:
        start_date = args.start
        end_date = args.end
    else:
        print("Error: Provide --date or both --start and --end")
        return

    # Paths
    parquet_root = Path("data/parquet")
    enriched_root = Path("data/enriched_alpha158")
    qlib_root = Path("/Users/zheyuanzhao/sandisk/quantmini-data/data/qlib_alpha158")

    print(f"""
Alpha158 Feature Pipeline
{'='*70}

Configuration:
  Data Type:      {args.data_type}
  Date Range:     {start_date} to {end_date}
  Parquet Root:   {parquet_root}
  Enriched Root:  {enriched_root}
  Qlib Root:      {qlib_root}
    """)

    # Step 1: Compute features
    if args.date:
        compute_alpha158_features(
            parquet_root, enriched_root,
            args.data_type, args.date
        )
    else:
        # Process date range
        from datetime import timedelta
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            compute_alpha158_features(
                parquet_root, enriched_root,
                args.data_type, date_str
            )
            current += timedelta(days=1)

    # Step 2: Verify
    verify_features(enriched_root, args.data_type, end_date)

    # Step 3: Convert to Qlib
    if not args.skip_conversion:
        convert_to_qlib(
            enriched_root, qlib_root,
            args.data_type, start_date, end_date
        )
    else:
        print("\n⏭️  Skipping Qlib conversion (--skip-conversion)")

    print(f"\n{'='*70}")
    print("✅ Alpha158 Pipeline Complete!")
    print(f"{'='*70}\n")

    print(f"Next steps:")
    print(f"1. Verify features in: {enriched_root}")
    print(f"2. Check Qlib binary: {qlib_root}")
    print(f"3. Use in Qlib:")
    print(f"""
import qlib
qlib.init(provider_uri='{qlib_root}')

from qlib.data.dataset import DatasetH
from qlib.data.dataset.handler import DataHandlerLP

dataset = DatasetH(
    handler=DataHandlerLP(
        instruments='csi300',
        start_time='2025-01-01',
        end_time='2025-09-30'
    )
)
    """)


if __name__ == '__main__':
    main()
