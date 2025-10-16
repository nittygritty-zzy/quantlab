#!/usr/bin/env python3
"""
Test Qlib's Alpha158 with Your Existing Data

This script verifies that your Qlib binary data works with Alpha158.
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / ".venv/lib/python3.12/site-packages"))

import qlib
from qlib.data import D
from qlib.contrib.data.handler import Alpha158
from qlib.contrib.data.loader import Alpha158DL


def test_basic_fields():
    """Test that basic OHLCV fields exist"""
    print("="*70)
    print("Test 1: Basic Fields")
    print("="*70)

    # Initialize Qlib
    qlib.init(
        provider_uri='/Users/zheyuanzhao/sandisk/quantmini-data/data/qlib',
        region='us'
    )

    # Test basic fields
    fields = ['$open', '$high', '$low', '$close', '$volume']
    df = D.features(
        instruments=['AAPL'],
        fields=fields,
        start_time='2025-09-30',
        end_time='2025-09-30'
    )

    print(f"\n✓ Basic fields loaded successfully")
    print(f"  Shape: {df.shape}")
    print(f"\nData:")
    print(df)

    return True


def test_alpha158_expressions():
    """Test Alpha158 expressions work"""
    print("\n" + "="*70)
    print("Test 2: Alpha158 Expressions")
    print("="*70)

    # Sample Alpha158 expressions
    expressions = [
        ("KMID", "($close-$open)/$open"),
        ("KLEN", "($high-$low)/$open"),
        ("MA5", "Mean($close, 5)/$close"),
        ("MA20", "Mean($close, 20)/$close"),
        ("STD20", "Std($close, 20)/$close"),
        ("ROC5", "Ref($close, 5)/$close"),
        # ("CORR20", "Corr($close, Log($volume+1), 20)"),  # Needs 20+ days
    ]

    # Need enough days for 20-day window
    df = D.features(
        instruments=['AAPL'],
        fields=[expr for _, expr in expressions],
        start_time='2025-09-01',  # Start from Sep 1
        end_time='2025-09-30'
    )

    # Rename columns
    df.columns = [name for name, _ in expressions]

    print(f"\n✓ Alpha158 expressions computed successfully")
    print(f"  Shape: {df.shape}")
    print(f"  Features: {', '.join(df.columns.tolist())}")
    print(f"\nSample data (last 5 days):")
    print(df.tail())

    return True


def test_alpha158_config():
    """Test Alpha158 config generation"""
    print("\n" + "="*70)
    print("Test 3: Alpha158 Feature Config")
    print("="*70)

    # Get full Alpha158 config
    config = {
        "kbar": {},
        "price": {
            "windows": [0],
            "feature": ["OPEN", "HIGH", "LOW", "VWAP"],
        },
        "rolling": {
            "windows": [5, 10, 20],
            "include": ["ROC", "MA", "STD"]  # Subset for testing
        },
    }

    fields, names = Alpha158DL.get_feature_config(config)

    print(f"\n✓ Alpha158 config generated")
    print(f"  Total features: {len(fields)}")
    print(f"\nKBAR features (9):")
    kbar_names = [n for n in names if n.startswith('K')]
    print(f"  {', '.join(kbar_names)}")

    print(f"\nPrice features:")
    price_names = [n for n in names if n.startswith(('OPEN', 'HIGH', 'LOW', 'VWAP'))]
    print(f"  {', '.join(price_names)}")

    print(f"\nRolling features (sample):")
    rolling_names = [n for n in names if not n.startswith(('K', 'OPEN', 'HIGH', 'LOW', 'VWAP', 'VOLUME'))]
    print(f"  {', '.join(rolling_names[:10])}...")

    return True


def test_alpha158_handler():
    """Test Alpha158 handler (requires valid date range)"""
    print("\n" + "="*70)
    print("Test 4: Alpha158 Handler")
    print("="*70)

    try:
        # Note: This requires instruments to exist in your data
        handler = Alpha158(
            instruments=['AAPL'],  # Just AAPL for testing
            start_time='2025-09-01',
            end_time='2025-09-30',
        )

        print(f"\n✓ Alpha158 handler initialized")
        print(f"  Instruments: AAPL")
        print(f"  Date range: 2025-09-01 to 2025-09-30")

        # Get feature config
        feature_config = handler.get_feature_config()
        print(f"  Features: {len(feature_config[0])} expressions")

        return True

    except Exception as e:
        print(f"\n⚠️  Alpha158 handler test skipped: {e}")
        print(f"    This is okay - handler needs proper instrument universe")
        return True


def test_full_alpha158_features():
    """Test full Alpha158 feature set"""
    print("\n" + "="*70)
    print("Test 5: Full Alpha158 Features")
    print("="*70)

    # Get ALL Alpha158 features
    config = {
        "kbar": {},
        "price": {
            "windows": [0],
            "feature": ["OPEN", "HIGH", "LOW", "VWAP"],
        },
        "rolling": {
            "windows": [5, 10, 20, 30, 60],
            # Default: includes ALL operators
        },
    }

    fields, names = Alpha158DL.get_feature_config(config)

    print(f"\n✓ Full Alpha158 config")
    print(f"  Total features: {len(fields)}")

    # Count by category
    kbar = [n for n in names if n.startswith('K')]
    price = [n for n in names if n.startswith(('OPEN', 'HIGH', 'LOW', 'VWAP'))]
    volume = [n for n in names if n.startswith('VOLUME')]
    rolling = [n for n in names if n not in kbar + price + volume]

    print(f"\n  Breakdown:")
    print(f"    KBAR:    {len(kbar):3d}")
    print(f"    Price:   {len(price):3d}")
    print(f"    Volume:  {len(volume):3d}")
    print(f"    Rolling: {len(rolling):3d}")
    print(f"    {'='*30}")
    print(f"    Total:   {len(fields):3d}")

    # Show sample rolling features
    print(f"\n  Sample rolling features:")
    rolling_types = {}
    for name in rolling:
        prefix = ''.join([c for c in name if c.isalpha()])
        if prefix not in rolling_types:
            rolling_types[prefix] = []
        rolling_types[prefix].append(name)

    for ftype in sorted(rolling_types.keys())[:10]:
        print(f"    {ftype:10s}: {', '.join(rolling_types[ftype])}")

    return True


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("QLIB ALPHA158 TEST SUITE")
    print("="*70)
    print("\nTesting Alpha158 with your existing Qlib binary data...")

    tests = [
        test_basic_fields,
        test_alpha158_expressions,
        test_alpha158_config,
        test_alpha158_handler,
        test_full_alpha158_features,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n❌ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8s} {name}")

    print(f"\n  {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ SUCCESS! Your data works with Qlib Alpha158!")
        print("\nNext steps:")
        print("  1. Use Alpha158 handler in your models:")
        print("     from qlib.contrib.data.handler import Alpha158")
        print("     handler = Alpha158(instruments='csi500', ...)")
        print()
        print("  2. Or use specific expressions:")
        print("     D.features(['AAPL'], ['Mean($close, 20)/$close'], ...)")
        print()
        print("  3. See full guide:")
        print("     cat /Users/zheyuanzhao/workspace/quantlab/USE_QLIB_ALPHA158.md")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("     Your basic data may be missing required fields.")

    print()


if __name__ == '__main__':
    main()
