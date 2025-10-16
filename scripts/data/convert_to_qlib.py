"""
Convert parquet data to Qlib binary format.

This script uses the quantmini QlibBinaryWriter to convert downloaded parquet data
to Qlib's binary format for use in ML/backtesting.

Usage: python convert_to_qlib.py [YYYY-MM-DD]
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add quantmini to path
sys.path.insert(0, str(Path(__file__).parent / ".venv/lib/python3.12/site-packages"))

from src.transform.qlib_binary_writer import QlibBinaryWriter
from src.core.config_loader import ConfigLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_to_qlib(target_date=None, data_types=None):
    """
    Convert parquet data to Qlib binary format.

    Args:
        target_date: Date to convert (default: yesterday)
        data_types: List of data types to convert (default: all except options_minute)
    """
    # Get target date
    if target_date:
        date_str = target_date
    else:
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")

    # Default data types (exclude options_minute as requested)
    if data_types is None:
        data_types = ['stocks_daily', 'stocks_minute', 'options_daily']

    print(f"🔄 Converting data to Qlib binary format")
    print(f"📅 Date: {date_str}")
    print(f"📊 Data types: {', '.join(data_types)}")
    print("-" * 70)

    # Initialize configuration
    config_loader = ConfigLoader(config_dir=Path("/Users/zheyuanzhao/workspace/quantmini/config"))

    # Setup paths
    # Use parquet directory as enriched input (already has the data we need)
    enriched_root = Path("data/parquet")
    qlib_root = Path("/Users/zheyuanzhao/sandisk/quantmini-data/data/qlib")

    print(f"\n📂 Paths:")
    print(f"   Input (parquet): {enriched_root.absolute()}")
    print(f"   Output (qlib):   {qlib_root.absolute()}")

    # Initialize writer
    try:
        writer = QlibBinaryWriter(
            enriched_root=enriched_root,
            qlib_root=qlib_root,
            config=config_loader
        )
        print(f"\n✅ QlibBinaryWriter initialized (mode: {writer.mode})")
    except Exception as e:
        print(f"\n❌ Failed to initialize writer: {e}")
        import traceback
        traceback.print_exc()
        return

    # Convert each data type
    results = {}
    total_symbols = 0
    total_features = 0
    total_size_mb = 0

    for data_type in data_types:
        print(f"\n{'='*70}")
        print(f"🔧 Converting {data_type}...")
        print(f"{'='*70}")

        try:
            result = writer.convert_data_type(
                data_type=data_type,
                start_date=date_str,
                end_date=date_str,
                incremental=False
            )

            results[data_type] = result
            total_symbols += result.get('symbols_converted', 0)
            total_features += result.get('features_written', 0)
            total_size_mb += result.get('bytes_written', 0) / 1024 / 1024

            print(f"\n   ✓ {data_type}:")
            print(f"      Symbols: {result.get('symbols_converted', 0):,}")
            print(f"      Features: {result.get('features_written', 0):,}")
            print(f"      Size: {result.get('bytes_written', 0) / 1024 / 1024:.1f} MB")

        except Exception as e:
            print(f"\n   ✗ Failed to convert {data_type}: {e}")
            if '--verbose' in sys.argv:
                import traceback
                traceback.print_exc()
            results[data_type] = {'error': str(e)}

    # Print final summary
    print(f"\n{'='*70}")
    print(f"📋 Conversion Summary")
    print(f"{'='*70}")

    success_count = sum(1 for r in results.values() if 'error' not in r)

    print(f"✓ Successful: {success_count}/{len(data_types)}")
    print(f"📊 Total symbols: {total_symbols:,}")
    print(f"📈 Total features: {total_features:,}")
    print(f"💾 Total size: {total_size_mb:.1f} MB")
    print(f"📅 Date: {date_str}")
    print(f"📂 Output location: {qlib_root}")

    return results


if __name__ == "__main__":
    # Parse command line arguments
    target_date = None
    if len(sys.argv) > 1 and sys.argv[1] not in ['--verbose']:
        target_date = sys.argv[1]
        print(f"Using specified date: {target_date}\n")

    convert_to_qlib(target_date)
