# Qlib Repository Setup Guide

**Purpose**: Clone and set up the Microsoft Qlib repository for QuantLab
**Why**: The qlib_repo is ~828MB and excluded from git to keep the repository small
**Status**: Automated setup script available ✅

---

## 🚀 Quick Start

### One Command Setup

```bash
# Clone and install Qlib in one step
uv run python scripts/setup_qlib_repo.py
```

That's it! The script will:
1. ✅ Clone Microsoft Qlib from GitHub
2. ✅ Install it in development mode
3. ✅ Verify the installation
4. ✅ Show next steps

**Expected time**: 5-10 minutes (depending on internet speed)

---

## 📋 Usage Options

### Basic Usage

```bash
# Clone latest version and install
uv run python scripts/setup_qlib_repo.py
```

### Advanced Options

```bash
# Clone specific version/tag
uv run python scripts/setup_qlib_repo.py --branch v0.9.1

# Force re-clone (removes existing directory)
uv run python scripts/setup_qlib_repo.py --force

# Clone only, skip installation
uv run python scripts/setup_qlib_repo.py --no-install

# Custom location
uv run python scripts/setup_qlib_repo.py --repo-path /path/to/qlib

# Combine options
uv run python scripts/setup_qlib_repo.py --branch v0.9.1 --force
```

### Get Help

```bash
python scripts/setup_qlib_repo.py --help
```

---

## 📂 What Gets Created

After running the setup script:

```
quantlab/
├── qlib_repo/                    # 🆕 Microsoft Qlib repository (~828 MB)
│   ├── .git/                     # Git repository
│   ├── qlib/                     # Qlib Python package
│   ├── scripts/                  # Qlib scripts
│   ├── examples/                 # Example notebooks
│   ├── setup.py                  # Installation file
│   └── README.md                 # Qlib documentation
│
└── .gitignore                    # Already configured to ignore qlib_repo/
```

**Note**: The `qlib_repo/` directory is in `.gitignore` and will NOT be tracked by git.

---

## ✅ Verification

The script automatically verifies:

1. ✅ Repository cloned successfully
2. ✅ Valid git repository
3. ✅ Qlib can be imported in Python
4. ✅ `qrun` command available

### Manual Verification

```bash
# Check Qlib version
python -c "import qlib; print(qlib.__version__)"

# Check qrun command
which qrun

# Check repository
ls -lh qlib_repo/
```

---

## 🔄 Updating Qlib

To update Qlib to the latest version:

```bash
# Pull latest changes
cd qlib_repo
git pull

# Reinstall
pip install -e .

# Or use the setup script with --force
cd ..
uv run python scripts/setup_qlib_repo.py --force
```

---

## 🛠️ Troubleshooting

### Issue: "git: command not found"

**Solution**: Install git first

```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git

# CentOS/RHEL
sudo yum install git
```

### Issue: "Directory already exists"

**Solution**: Use `--force` to re-clone

```bash
uv run python scripts/setup_qlib_repo.py --force
```

Or remove manually:

```bash
rm -rf qlib_repo
uv run python scripts/setup_qlib_repo.py
```

### Issue: Installation fails

**Solution**: Try manual installation

```bash
cd qlib_repo
pip install -e .
```

Or install without dev dependencies:

```bash
cd qlib_repo
pip install -e . --no-deps
pip install -r requirements.txt
```

### Issue: "Cannot import qlib"

**Solution**: Check if installation completed

```bash
# Reinstall
cd qlib_repo
pip install -e .

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Try importing
python -c "import qlib; print(qlib.__file__)"
```

### Issue: "qrun command not found"

**Solution**: Restart your shell or add to PATH

```bash
# Restart shell
exec $SHELL

# Or find qrun location
find .venv -name qrun

# Or use full path
.venv/bin/qrun ../configs/backtest_dev.yaml
```

---

## 🎓 Understanding the Setup

### Why Clone Qlib?

1. **Development mode**: We install Qlib in editable mode (`-e`) so changes in qlib_repo are immediately available
2. **Custom modifications**: We can modify Qlib code if needed
3. **Version control**: We can pin to specific Qlib versions
4. **Size**: Qlib is ~828MB, too large to commit to git

### What About pip install qlib?

You can also install Qlib from PyPI:

```bash
pip install qlib
```

However, we use the git repository because:
- ✅ Latest features and bug fixes
- ✅ Can modify Qlib code if needed
- ✅ Better for development and debugging
- ✅ Access to examples and documentation

### Repository Structure

```
qlib_repo/
├── qlib/                         # Core Qlib package
│   ├── backtest/                 # Backtest engine
│   ├── contrib/                  # Contributed models
│   ├── data/                     # Data handlers
│   ├── model/                    # Model interfaces
│   ├── strategy/                 # Trading strategies
│   ├── utils/                    # Utilities
│   └── workflow/                 # Workflow management
│
├── examples/                     # Example notebooks and scripts
├── scripts/                      # Utility scripts
├── tests/                        # Test suite
├── setup.py                      # Installation configuration
├── requirements.txt              # Dependencies
└── README.md                     # Documentation
```

---

## 🔗 Integration with QuantLab

After setup, QuantLab uses Qlib through:

1. **Backtest Configs**: YAML files in `configs/` reference Qlib classes
2. **Custom Handlers**: `quantlab/backtest/handlers.py` extends Qlib handlers
3. **Trading Strategies**: `quantlab/backtest/strategies/` implement Qlib strategy interface
4. **qrun Command**: Execute backtests from `qlib_repo/` directory

### Running Backtests

```bash
# Navigate to qlib_repo
cd qlib_repo

# Run backtest with QuantLab config
uv run qrun ../configs/backtest_dev.yaml

# Run production config
uv run qrun ../configs/backtest_sentiment_momentum.yaml
```

---

## 📚 Additional Resources

### Microsoft Qlib

- **GitHub**: https://github.com/microsoft/qlib
- **Documentation**: https://qlib.readthedocs.io/
- **Paper**: https://arxiv.org/abs/2009.11189

### QuantLab Documentation

- **Backtest Guide**: `docs/BACKTEST_INTEGRATION_COMPLETE.md`
- **Quick Start**: `QUICKSTART.md`
- **Architecture**: `docs/COMPREHENSIVE_SYSTEM_ARCHITECTURE.md`

---

## 🎯 Next Steps After Setup

1. **Verify installation**
   ```bash
   python -c "import qlib; print(qlib.__version__)"
   ```

2. **Initialize Qlib data** (if needed)
   ```bash
   uv run python scripts/data/setup_quantlab.py
   ```

3. **Pre-compute indicators** (recommended)
   ```bash
   uv run python scripts/data/precompute_indicators.py
   ```

4. **Run your first backtest**
   ```bash
   cd qlib_repo
   uv run qrun ../configs/backtest_dev.yaml
   ```

---

## 💡 Pro Tips

### Tip 1: Pin Qlib Version

To ensure reproducibility, pin to a specific Qlib version:

```bash
# Check available tags
cd qlib_repo
git tag

# Checkout specific version
git checkout v0.9.1

# Or use the setup script
cd ..
uv run python scripts/setup_qlib_repo.py --branch v0.9.1
```

### Tip 2: Shallow Clone

To save disk space and clone faster:

```bash
# Manual shallow clone (not in script)
git clone --depth 1 https://github.com/microsoft/qlib.git qlib_repo
```

### Tip 3: Update Safely

Before updating, create a backup:

```bash
# Backup current setup
cp -r qlib_repo qlib_repo.backup

# Update
cd qlib_repo
git pull
pip install -e .

# If issues occur, restore backup
cd ..
rm -rf qlib_repo
mv qlib_repo.backup qlib_repo
```

---

## 📊 Setup Script Details

The `scripts/setup_qlib_repo.py` script:

**What it does**:
1. Checks if git is installed
2. Clones Microsoft Qlib from GitHub
3. Optionally checks out specific branch/tag
4. Installs Qlib in development mode (`pip install -e .`)
5. Verifies the installation
6. Shows next steps

**Features**:
- ✅ Colored terminal output
- ✅ Progress indicators
- ✅ Error handling
- ✅ Verification checks
- ✅ Helpful error messages
- ✅ Force re-clone option
- ✅ Custom branch/tag support
- ✅ Skip installation option

**Script size**: ~400 lines of Python
**Dependencies**: None (uses stdlib only)

---

## ✅ Checklist

After running the setup script:

- [ ] qlib_repo/ directory exists
- [ ] Can import qlib in Python
- [ ] qrun command available (or accessible via .venv/bin/qrun)
- [ ] Qlib version displayed correctly
- [ ] No errors in verification step

---

**Last Updated**: October 15, 2025
**Script Location**: `scripts/setup_qlib_repo.py`
**Qlib Size**: ~828 MB
**Setup Time**: 5-10 minutes
**Status**: ✅ Ready to Use

---

*Remember: The qlib_repo/ directory is in .gitignore and safe to delete. You can always re-clone it using the setup script!*
