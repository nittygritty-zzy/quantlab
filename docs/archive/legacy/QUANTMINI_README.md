# QuantMini Setup

## Installation Complete

QuantMini has been successfully installed in the `uv` virtual environment.

### Configuration

- **Config Directory**: `/Users/zheyuanzhao/workspace/quantmini/config`
- **Data Root**: `/Users/zheyuanzhao/sandisk/quantmini-data/data`
- **Python Version**: 3.12.11 (required for pyqlib compatibility)

### Files

- `quantmini_setup.py` - Initialization script to load quantmini configuration
- `.venv/` - Virtual environment with quantmini and all dependencies

### Usage

To use quantmini in your scripts:

```python
from quantmini_setup import initialize_quantmini

# Initialize with your configuration
config_loader = initialize_quantmini()

# Access configuration values
mode = config_loader.get('pipeline.mode')
data_root = config_loader.get('data_root')
```

Or import directly from the installed package:

```python
import sys
from pathlib import Path

# Add quantmini to path
sys.path.insert(0, str(Path('.venv/lib/python3.12/site-packages')))

from src.core.config_loader import ConfigLoader

# Initialize
config_loader = ConfigLoader(config_dir=Path('/Users/zheyuanzhao/workspace/quantmini/config'))
```

### Running Python with QuantMini

Always use the uv virtual environment:

```bash
# Activate the venv
source .venv/bin/activate

# Or run directly
.venv/bin/python your_script.py
```

### Next Steps

1. Verify your data directory structure matches the expected layout
2. Configure credentials in `/Users/zheyuanzhao/workspace/quantmini/config/credentials.yaml`
3. Review and adjust pipeline settings in `pipeline_config.yaml` as needed

For full documentation, visit: https://quantmini.readthedocs.io/en/latest/
