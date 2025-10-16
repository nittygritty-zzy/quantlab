"""
QuantMini setup script for quantlab project.

This script initializes quantmini with the correct configuration paths.
"""

import os
import sys
from pathlib import Path

# Configuration paths
CONFIG_DIR = Path("/Users/zheyuanzhao/workspace/quantmini/config")
DATA_ROOT = Path("/Users/zheyuanzhao/sandisk/quantmini-data/data")

# Add quantmini to path (installed via uv)
sys.path.insert(0, str(Path(__file__).parent / ".venv/lib/python3.12/site-packages"))

from src.core.config_loader import ConfigLoader


def initialize_quantmini():
    """Initialize quantmini with project-specific configurations."""
    # Set environment variable for data root
    os.environ['DATA_ROOT'] = str(DATA_ROOT)

    # Verify paths exist
    pipeline_config = CONFIG_DIR / "pipeline_config.yaml"
    system_profile = CONFIG_DIR / "system_profile.yaml"

    assert pipeline_config.exists(), f"Pipeline config not found: {pipeline_config}"
    assert system_profile.exists(), f"System profile not found: {system_profile}"
    assert DATA_ROOT.exists(), f"Data root not found: {DATA_ROOT}"

    print(f"✓ Configuration directory: {CONFIG_DIR}")
    print(f"✓ Data root: {DATA_ROOT}")
    print(f"✓ Pipeline config: {pipeline_config}")
    print(f"✓ System profile: {system_profile}")

    # Initialize ConfigLoader with the config directory
    config_loader = ConfigLoader(config_dir=CONFIG_DIR)

    print(f"\n✓ QuantMini initialized successfully!")
    print(f"  - Mode: {config_loader.get('pipeline.mode', 'adaptive')}")
    print(f"  - Data root: {config_loader.get('data_root')}")
    print(f"  - Available data types: {config_loader.get('pipeline.data_types', [])}")

    return config_loader


if __name__ == "__main__":
    config = initialize_quantmini()
