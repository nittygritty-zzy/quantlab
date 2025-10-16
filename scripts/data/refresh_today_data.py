"""
Refresh today's data for quantmini.

This script downloads and ingests data for today's date across all configured data types.
Usage: python refresh_today_data.py [YYYY-MM-DD]
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add quantmini to path
sys.path.insert(0, str(Path(__file__).parent / ".venv/lib/python3.12/site-packages"))

from src.orchestration.ingestion_orchestrator import IngestionOrchestrator
from src.core.config_loader import ConfigLoader


async def refresh_today_data(target_date=None):
    """Refresh data for the specified date."""
    # Get target date
    if target_date:
        date_str = target_date
    else:
        # Use yesterday by default (data is usually 1 day delayed)
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")

    print(f"🔄 Refreshing data for {date_str}")
    print("-" * 60)

    # Initialize configuration
    config_loader = ConfigLoader(config_dir=Path("/Users/zheyuanzhao/workspace/quantmini/config"))

    # Get data types from config
    data_types = config_loader.get('pipeline.data_types', [])
    print(f"📊 Data types to refresh: {', '.join(data_types)}\n")

    # Initialize orchestrator
    try:
        orchestrator = IngestionOrchestrator(config=config_loader)
    except Exception as e:
        print(f"❌ Error initializing orchestrator: {e}")
        print("\n💡 Make sure credentials are configured in:")
        print("   /Users/zheyuanzhao/workspace/quantmini/config/credentials.yaml")
        return

    # Refresh each data type
    results = {}
    for data_type in data_types:
        print(f"\n📥 Downloading {data_type}...")
        try:
            result = await orchestrator.ingest_date(
                data_type=data_type,
                date=date_str,
                use_polars=True
            )
            results[data_type] = result

            # Print summary
            if result.get('success'):
                records = result.get('records_processed', 0)
                files = result.get('files_created', 0)
                print(f"   ✓ Success: {records:,} records processed, {files} files created")
            else:
                error = result.get('error', 'Unknown error')
                print(f"   ✗ Failed: {error}")

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"   ✗ Error: {e}")
            if '--verbose' in sys.argv:
                print(f"   Details:\n{error_detail}")
            results[data_type] = {'success': False, 'error': str(e)}

    # Print final summary
    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)

    success_count = sum(1 for r in results.values() if r.get('success'))
    total_records = sum(r.get('records_processed', 0) for r in results.values())

    print(f"✓ Successful: {success_count}/{len(data_types)}")
    print(f"📊 Total records: {total_records:,}")
    print(f"📅 Date: {date_str}")

    return results


if __name__ == "__main__":
    # Parse command line arguments
    target_date = None
    if len(sys.argv) > 1 and sys.argv[1] not in ['--verbose']:
        target_date = sys.argv[1]
        print(f"Using specified date: {target_date}\n")

    asyncio.run(refresh_today_data(target_date))
