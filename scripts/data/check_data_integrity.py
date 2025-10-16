#!/usr/bin/env python3
"""
Data Integrity Check Script
Checks stock and option data integrity for QuantLab project
"""
import os
from pathlib import Path
import json
from datetime import datetime, timedelta
import pandas as pd

# Change to project root
os.chdir(Path(__file__).parent.parent.parent)

def check_qlib_stock_data():
    """Check qlib binary stock data integrity"""
    print("=" * 80)
    print("QLIB STOCK DATA INTEGRITY CHECK")
    print("=" * 80)

    qlib_path = Path("/Volumes/sandisk/quantmini-data/data/qlib/stocks_daily")

    # Check if qlib data exists
    if not qlib_path.exists():
        print("❌ ERROR: Qlib data directory not found!")
        print(f"   Expected path: {qlib_path}")
        return {}

    print("✅ Qlib data directory exists")
    print(f"   Location: {qlib_path}")
    print()

    # Check calendars
    calendar_file = qlib_path / "calendars" / "day.txt"
    if calendar_file.exists():
        with open(calendar_file, 'r') as f:
            trading_days = [line.strip() for line in f.readlines()]
        print(f"✅ Trading calendar found: {len(trading_days)} trading days")
        print(f"   First date: {trading_days[0]}")
        print(f"   Last date: {trading_days[-1]}")
    else:
        print("❌ Trading calendar not found")
        trading_days = []
    print()

    # Check instruments
    all_instruments = qlib_path / "instruments" / "all.txt"
    liquid_instruments = qlib_path / "instruments" / "liquid_stocks.txt"

    all_stocks = []
    liquid_stocks = []

    if all_instruments.exists():
        with open(all_instruments, 'r') as f:
            all_stocks = [line.strip().split('\t')[0] for line in f.readlines()]
        print(f"✅ All instruments file found: {len(all_stocks)} instruments")
    else:
        print("❌ All instruments file not found")

    if liquid_instruments.exists():
        with open(liquid_instruments, 'r') as f:
            liquid_stocks = [line.strip().split('\t')[0] for line in f.readlines()]
        print(f"✅ Liquid stocks file found: {len(liquid_stocks)} instruments")
    else:
        print("⚠️  Liquid stocks file not found")
    print()

    # Check features directory
    features_path = qlib_path / "features"
    if features_path.exists():
        # Count feature files
        feature_files = list(features_path.glob("*.bin"))
        print(f"✅ Features directory exists: {len(feature_files)} feature bin files")
    else:
        print("❌ Features directory not found")
        feature_files = []
    print()

    return {
        'qlib_exists': qlib_path.exists(),
        'trading_days': len(trading_days),
        'date_range': (trading_days[0], trading_days[-1]) if trading_days else None,
        'total_instruments': len(all_stocks),
        'liquid_instruments': len(liquid_stocks),
        'feature_files': len(feature_files),
    }

def check_parquet_stock_data():
    """Check local parquet stock data"""
    print("=" * 80)
    print("LOCAL PARQUET STOCK DATA CHECK")
    print("=" * 80)

    parquet_path = Path("data/parquet")

    if not parquet_path.exists():
        print("❌ Parquet directory not found")
        return {}

    # List all parquet files
    parquet_files = list(parquet_path.glob("*.parquet"))
    print(f"✅ Found {len(parquet_files)} parquet files")
    print()

    # Sample a few files to check data quality
    issues = []
    sample_files = parquet_files[:5] if len(parquet_files) > 5 else parquet_files

    print(f"Sampling {len(sample_files)} files for quality check:")
    for pf in sample_files:
        try:
            df = pd.read_parquet(pf)
            symbol = pf.stem

            # Check for required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                print(f"  ⚠️  {symbol}: Missing columns {missing_cols}")
                issues.append(f"{symbol}: Missing columns {missing_cols}")
            else:
                # Check for nulls
                null_counts = df[required_cols].isnull().sum()
                total_nulls = null_counts.sum()

                if total_nulls > 0:
                    print(f"  ⚠️  {symbol}: {len(df)} rows, {total_nulls} null values")
                    issues.append(f"{symbol}: {total_nulls} null values")
                else:
                    print(f"  ✅ {symbol}: {len(df)} rows, no issues")

        except Exception as e:
            print(f"  ❌ {symbol}: Error reading file - {e}")
            issues.append(f"{symbol}: Error - {e}")

    print()
    if issues:
        print(f"⚠️  Found {len(issues)} issues in sampled files")
    else:
        print("✅ No issues found in sampled files")
    print()

    return {
        'parquet_files': len(parquet_files),
        'issues': issues,
    }

def check_metadata():
    """Check metadata files"""
    print("=" * 80)
    print("METADATA CHECK")
    print("=" * 80)

    metadata_path = Path("data/metadata")

    if not metadata_path.exists():
        print("❌ Metadata directory not found")
        return {}

    # Check stocks_daily metadata
    stocks_daily_path = metadata_path / "stocks_daily"
    stocks_metadata = []
    errors = []

    if stocks_daily_path.exists():
        json_files = list(stocks_daily_path.glob("**/*.json"))
        print(f"✅ Found {len(json_files)} stock daily metadata files")

        for jf in json_files:
            try:
                with open(jf, 'r') as f:
                    meta = json.load(f)
                    stocks_metadata.append(meta)

                    if meta.get('status') == 'failed':
                        error_msg = f"{meta.get('date')}: {meta.get('error', 'Unknown error')}"
                        errors.append(error_msg)
                        print(f"  ❌ {error_msg}")
                    else:
                        stats = meta.get('statistics', {})
                        print(f"  ✅ {meta.get('date')}: {stats.get('records', 0)} records")
            except Exception as e:
                print(f"  ⚠️  Error reading {jf.name}: {e}")
    print()

    # Check options_daily metadata
    options_daily_path = metadata_path / "options_daily"
    options_metadata = []

    if options_daily_path.exists():
        json_files = list(options_daily_path.glob("**/*.json"))
        print(f"✅ Found {len(json_files)} option daily metadata files")

        for jf in json_files:
            try:
                with open(jf, 'r') as f:
                    meta = json.load(f)
                    options_metadata.append(meta)

                    if meta.get('status') == 'failed':
                        print(f"  ❌ {meta.get('date')}: {meta.get('error', 'Unknown error')}")
                    else:
                        stats = meta.get('statistics', {})
                        print(f"  ✅ {meta.get('date')}: {stats.get('records', 0)} option contracts")
            except Exception as e:
                print(f"  ⚠️  Error reading {jf.name}: {e}")
    else:
        print("⚠️  No options daily metadata found")
    print()

    # Check options_minute metadata
    options_minute_path = metadata_path / "options_minute"
    if options_minute_path.exists():
        json_files = list(options_minute_path.glob("**/*.json"))
        print(f"✅ Found {len(json_files)} option minute metadata files")
    else:
        print("⚠️  No options minute metadata found")
    print()

    return {
        'stocks_metadata_files': len(stocks_metadata),
        'options_metadata_files': len(options_metadata),
        'metadata_errors': errors,
    }

def check_option_data():
    """Check option data availability"""
    print("=" * 80)
    print("OPTION DATA CHECK")
    print("=" * 80)

    # Check for option parquet files (option symbols typically contain "O:")
    parquet_path = Path("data/parquet")

    if parquet_path.exists():
        # Look for files that might be options
        all_files = list(parquet_path.glob("*.parquet"))
        option_files = [f for f in all_files if "O:" in f.name or f.name.startswith("O_")]

        print(f"Searching for option data in parquet directory...")
        print(f"  Total parquet files: {len(all_files)}")
        print(f"  Option files found: {len(option_files)}")

        if option_files:
            print(f"\n✅ Found {len(option_files)} option files:")
            for of in option_files[:10]:  # Show first 10
                print(f"     - {of.name}")
            if len(option_files) > 10:
                print(f"     ... and {len(option_files) - 10} more")
        else:
            print("\n⚠️  No option parquet files found")
            print("   Note: Option metadata exists but no parquet data files")
    else:
        print("❌ Parquet directory not found")
    print()

    # Check if there's a separate options qlib binary
    qlib_options_path = Path("/Volumes/sandisk/quantmini-data/data/qlib/options_daily")
    if qlib_options_path.exists():
        print(f"✅ Found qlib options binary directory: {qlib_options_path}")
    else:
        print("⚠️  No qlib options binary directory found")
    print()

    return {
        'option_parquet_files': len(option_files) if parquet_path.exists() else 0,
        'option_qlib_exists': qlib_options_path.exists(),
    }

def generate_summary(stock_qlib, stock_parquet, metadata_info, option_info):
    """Generate summary report"""
    print("=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    print()

    print("📊 STOCK DATA:")
    print(f"  • Qlib binary: {stock_qlib.get('total_instruments', 0):,} instruments")
    print(f"  • Date range: {stock_qlib.get('date_range', ('N/A', 'N/A'))[0]} to {stock_qlib.get('date_range', ('N/A', 'N/A'))[1]}")
    print(f"  • Trading days: {stock_qlib.get('trading_days', 0)}")
    print(f"  • Liquid stocks: {stock_qlib.get('liquid_instruments', 0):,}")
    print(f"  • Local parquet files: {stock_parquet.get('parquet_files', 0)}")
    print()

    print("📊 OPTION DATA:")
    print(f"  • Option parquet files: {option_info.get('option_parquet_files', 0)}")
    print(f"  • Option metadata files: {metadata_info.get('options_metadata_files', 0)}")
    print(f"  • Qlib option binary: {'Yes' if option_info.get('option_qlib_exists') else 'No'}")
    print()

    print("⚠️  ISSUES FOUND:")

    total_issues = 0

    # Metadata errors
    if metadata_info.get('metadata_errors'):
        print(f"  • Metadata errors: {len(metadata_info['metadata_errors'])}")
        for err in metadata_info['metadata_errors']:
            print(f"      - {err}")
        total_issues += len(metadata_info['metadata_errors'])

    # Parquet issues
    if stock_parquet.get('issues'):
        print(f"  • Parquet data issues: {len(stock_parquet['issues'])}")
        for issue in stock_parquet['issues'][:5]:  # Show first 5
            print(f"      - {issue}")
        total_issues += len(stock_parquet['issues'])

    # Option data status
    if metadata_info.get('options_metadata_files', 0) > 0 and option_info.get('option_parquet_files', 0) == 0:
        print(f"  • Option data incomplete: Metadata exists but no parquet files")
        total_issues += 1

    if total_issues == 0:
        print("  ✅ No critical issues found!")
    else:
        print(f"\n  Total issues: {total_issues}")

    print()
    print("=" * 80)

def main():
    """Main execution"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "DATA INTEGRITY CHECK" + " " * 38 + "║")
    print("║" + " " * 20 + f"QuantLab - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Run all checks
    stock_qlib = check_qlib_stock_data()
    stock_parquet = check_parquet_stock_data()
    metadata_info = check_metadata()
    option_info = check_option_data()

    # Generate summary
    generate_summary(stock_qlib, stock_parquet, metadata_info, option_info)

if __name__ == "__main__":
    main()
