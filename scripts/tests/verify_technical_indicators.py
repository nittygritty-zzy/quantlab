#!/usr/bin/env python
"""
Test verification of calculated vs Polygon API technical indicators

This script compares our calculated indicators with Polygon's API values
to ensure accuracy within acceptable tolerance.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from quantlab.data.data_manager import DataManager
from quantlab.data.database import DatabaseManager
from quantlab.data.parquet_reader import ParquetReader
from quantlab.utils.config import load_config

def main():
    # Load config
    config = load_config()

    # Initialize
    db = DatabaseManager(db_path=config.database_path)
    parquet = ParquetReader(parquet_root=config.parquet_root)
    data_mgr = DataManager(config, db, parquet)

    # Test with AAPL
    ticker = "AAPL"
    print(f"\n{'='*70}")
    print(f"Testing {ticker} - Polygon API vs Calculated Indicators")
    print(f"{'='*70}\n")

    # Get indicators with verification enabled
    indicators = data_mgr.get_technical_indicators(ticker, verify_calculations=True)

    if not indicators:
        print("❌ Failed to get technical indicators")
        return

    # Display verification results
    if "verification" in indicators:
        verification = indicators["verification"]

        print(f"Verification Status: {verification['status'].upper()}")
        print(f"Tolerance: ±{verification['tolerance_pct']}%\n")

        print("Indicator Comparisons:")
        print(f"{'='*70}")
        print(f"{'Indicator':<15} {'Polygon':>12} {'Calculated':>12} {'Diff %':>10} {'Status':>8}")
        print(f"{'-'*70}")

        for indicator, result in verification["differences"].items():
            polygon_val = result["polygon"]
            calc_val = result["calculated"]
            diff_pct = result["diff_pct"]
            status = "✓ PASS" if result["within_tolerance"] else "✗ FAIL"

            print(f"{indicator:<15} {polygon_val:>12.4f} {calc_val:>12.4f} {diff_pct:>9.2f}% {status:>8}")

        print(f"{'='*70}\n")

        # Summary
        passed = sum(1 for r in verification["differences"].values() if r["within_tolerance"])
        total = len(verification["differences"])
        print(f"Summary: {passed}/{total} indicators within tolerance")

        if verification["status"] == "pass":
            print("✅ All indicators verified successfully!")
        else:
            print("⚠️  Some indicators exceeded tolerance")
    else:
        print("ℹ️  Verification not available (using Polygon API only)")

    # Display data source tracking
    print(f"\n{'='*70}")
    print("Data Source Tracking:")
    print(f"{'='*70}")
    for indicator, source in indicators.get("data_source", {}).items():
        emoji = "🔴" if source == "polygon" else "🔵"
        print(f"{emoji} {indicator:<20}: {source}")

    print(f"\n{'='*70}")
    print("Legend:")
    print("  🔴 polygon    = From Polygon API (primary)")
    print("  🔵 calculated = From historical data (fallback)")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
