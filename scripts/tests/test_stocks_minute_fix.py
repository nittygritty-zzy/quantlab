"""Test that stocks_minute conversion works with the fix."""

import sys
from pathlib import Path

# Add quantmini to path
sys.path.insert(0, str(Path(__file__).parent / ".venv/lib/python3.12/site-packages"))

# Update the source with the fix
import shutil
src_file = Path("/Users/zheyuanzhao/workspace/quantmini/src/transform/qlib_binary_writer.py")
dst_file = Path(".venv/lib/python3.12/site-packages/src/transform/qlib_binary_writer.py")

print(f"Copying fixed file from {src_file}")
print(f"                     to {dst_file}")
shutil.copy2(src_file, dst_file)
print("✓ File updated\n")

# Now test
from src.transform.qlib_binary_writer import QlibBinaryWriter
from src.core.config_loader import ConfigLoader

config_loader = ConfigLoader(config_dir=Path("/Users/zheyuanzhao/workspace/quantmini/config"))

enriched_root = Path("data/parquet")
qlib_root = Path("/Users/zheyuanzhao/sandisk/quantmini-data/data/qlib")

writer = QlibBinaryWriter(
    enriched_root=enriched_root,
    qlib_root=qlib_root,
    config=config_loader
)

print("🔄 Testing stocks_minute conversion...")
print("-" * 70)

try:
    result = writer.convert_data_type(
        data_type='stocks_minute',
        start_date='2025-09-30',
        end_date='2025-09-30',
        incremental=False
    )

    print("\n✅ SUCCESS!")
    print(f"   Symbols: {result['symbols_converted']:,}")
    print(f"   Features: {result['features_written']:,}")
    print(f"   Trading days: {result['trading_days']}")
    print(f"   Size: {result['bytes_written'] / 1024 / 1024:.1f} MB")

except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
