# Git Repository Setup Guide

**Date**: October 15, 2025
**Status**: Ready for Professional Git Hosting ✅

---

## 🎯 Overview

This guide explains how QuantLab is configured as a professional git repository with proper security measures to protect sensitive data, API keys, and personal information.

---

## 🔒 Security Features

### What's Protected by .gitignore

1. **API Keys & Credentials** 🔐
   - Environment files (`.env`, `.env.*`)
   - Credential JSON files
   - API token configurations
   - All files matching: `*credentials.json`, `*secrets.json`, `*api_keys.json`

2. **Personal Data** 👤
   - External data mount point (`/Volumes/sandisk/`)
   - Local data directories
   - DuckDB databases
   - Parquet files with market data

3. **Large Files** 📦
   - Qlib repository (828MB)
   - MLflow experiment data
   - Model artifacts (`.pkl`, `.joblib`, `.h5`)
   - Cache directories (indicators, sentiment, fundamentals)

4. **Generated Files** ⚙️
   - Python bytecode (`__pycache__/`, `*.pyc`)
   - Log files (`*.log`)
   - Temporary files
   - Build artifacts

---

## 📋 What IS Tracked in Git

### ✅ Source Code
- `quantlab/` - Python package source code
- `scripts/` - Data processing and analysis scripts
- `configs/` - YAML configuration files (without API keys)

### ✅ Documentation
- `docs/` - All markdown documentation
- `README.md`, `QUICKSTART.md` - Project guides
- `.claude/PROJECT_MEMORY.md` - Project knowledge base

### ✅ Configuration Templates
- `.env.example` - Environment variable template
- `configs/*.yaml` - Backtest configurations
- `pyproject.toml` - Python dependencies

### ✅ Git Configuration
- `.gitignore` - Comprehensive ignore rules
- This guide (`docs/GIT_SETUP_GUIDE.md`)

---

## 🚀 Initial Git Setup

### Step 1: Initialize Repository

```bash
cd /Users/zheyuanzhao/workspace/quantlab
git init
```

### Step 2: Review What Will Be Committed

```bash
# Dry run - see what would be added
git add --dry-run -A

# Check ignored files
git status --ignored
```

### Step 3: Create Initial Commit

```bash
# Add all files (respecting .gitignore)
git add .

# Check what's staged
git status

# Create initial commit
git commit -m "Initial commit: QuantLab quantitative trading platform

- Complete backtest integration with Microsoft Qlib
- Sentiment + Momentum strategy implementation
- Multi-source data pipeline (Polygon, Alpha Vantage, yfinance)
- Comprehensive documentation and optimization guides
- Pre-computation infrastructure for performance
- Professional project structure with archived legacy files

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 4: Add Remote Repository (Optional)

```bash
# GitHub
git remote add origin https://github.com/yourusername/quantlab.git

# Or GitLab
git remote add origin https://gitlab.com/yourusername/quantlab.git

# Verify remote
git remote -v
```

### Step 5: Push to Remote (Optional)

```bash
# Push to main branch
git branch -M main
git push -u origin main
```

---

## 🔍 Verification Checklist

Before pushing to a public repository, verify:

- [ ] `.env` file is NOT staged (should be in .gitignore)
- [ ] No API keys in any committed files
- [ ] No personal data paths in configs (use environment variables)
- [ ] No large data files (parquet, duckdb) staged
- [ ] `qlib_repo/` directory is ignored
- [ ] MLflow experiment data (`results/mlruns/`) is ignored
- [ ] All credentials files are ignored

### Quick Verification Commands

```bash
# Check for potential secrets in staged files
git diff --cached | grep -i "api_key\|secret\|password\|token"

# List all files that would be committed
git ls-files

# Check total repository size (should be < 50MB for clean repo)
du -sh .git
```

---

## 📝 Environment Setup for New Users

When someone clones your repository, they need to:

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Fill in API Keys

Edit `.env` and add:
- Polygon.io API key
- Alpha Vantage API key
- Data storage paths

### 3. Set Up Data Directory

```bash
# Create local data directory
mkdir -p data/qlib

# Or mount external drive
# Point QLIB_DATA_PATH in .env to your data location
```

### 4. Install Dependencies

```bash
# Using UV (recommended)
uv sync

# Or pip
pip install -e .
```

### 5. Clone Qlib Repository

**Important**: The qlib_repo (~828MB) is not in git. Clone it separately:

```bash
# Clone and install Qlib in one command
uv run python scripts/setup_qlib_repo.py
```

**What this does**:
- Clones Microsoft Qlib from GitHub (~828 MB)
- Installs it in development mode
- Verifies the installation
- Takes 5-10 minutes

See `docs/QLIB_SETUP.md` for detailed instructions and troubleshooting.

### 6. Run Setup Scripts

```bash
# Initialize qlib data (if needed)
uv run python scripts/data/setup_quantlab.py

# Pre-compute indicators (optional but recommended)
uv run python scripts/data/precompute_indicators.py
```

---

## 🛡️ Security Best Practices

### For Repository Maintainers

1. **Never commit credentials**
   - Always use environment variables
   - Keep `.env` in `.gitignore`
   - Provide `.env.example` template

2. **Rotate exposed keys immediately**
   - If you accidentally commit a key, rotate it ASAP
   - Use `git filter-branch` or BFG Repo-Cleaner to remove from history

3. **Use GitHub Secrets for CI/CD**
   - Store API keys as repository secrets
   - Reference them in workflows: `${{ secrets.POLYGON_API_KEY }}`

4. **Review before pushing**
   ```bash
   # Check what will be pushed
   git diff origin/main..HEAD

   # Look for sensitive patterns
   git grep -i "api_key\|secret\|password"
   ```

### For Contributors

1. **Don't commit personal configs**
   - Use `*_local.yaml` for personal settings (ignored by git)
   - Keep API keys in `.env` only

2. **Clean up test files**
   - Remove scratch files before committing
   - Use `scratch/` directory for temporary work (ignored)

3. **Follow commit message conventions**
   - Use descriptive messages
   - Reference issues when applicable

---

## 📂 .gitignore Organization

Our `.gitignore` is organized into sections:

1. **Sensitive Data** - API keys, credentials, tokens
2. **Large Data** - Datasets, caches, external drives
3. **Qlib Repo** - 828MB Microsoft Qlib installation
4. **Python** - Bytecode, distribution files
5. **Virtual Environments** - .venv, venv, etc.
6. **Jupyter** - Checkpoint files
7. **MLflow** - Experiment tracking data
8. **IDEs** - VSCode, PyCharm, Vim
9. **Operating Systems** - macOS, Windows, Linux files
10. **Logs** - All log files
11. **Generated Reports** - Backtest outputs
12. **Keep Rules** - Explicit inclusions

---

## 🔧 Common Git Operations

### Add New Files

```bash
# Add specific file
git add path/to/file.py

# Add all Python files in directory
git add quantlab/backtest/*.py

# Check what was staged
git status
```

### Commit Changes

```bash
git commit -m "Add sentiment momentum strategy optimization

- Reduced stock universe from 50 to 30
- Simplified model parameters for 2x speedup
- Created dev config for fast iteration

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Create Branches

```bash
# Create feature branch
git checkout -b feature/new-strategy

# Create optimization branch
git checkout -b optimize/backtest-performance

# Switch back to main
git checkout main
```

### Merge Changes

```bash
# Merge feature branch into main
git checkout main
git merge feature/new-strategy

# Delete merged branch
git branch -d feature/new-strategy
```

---

## 🐛 Troubleshooting

### "I accidentally committed .env!"

```bash
# Remove from staging (if not yet pushed)
git reset HEAD .env

# Remove from commit (if already committed)
git reset --soft HEAD^
git restore --staged .env
git commit -c ORIG_HEAD

# If already pushed - ROTATE YOUR API KEYS!
```

### "My repo is too large"

```bash
# Check large files
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  sed -n 's/^blob //p' | \
  sort --numeric-sort --key=2 | \
  tail -20

# Remove large file from history
git filter-branch --tree-filter 'rm -f path/to/large/file' HEAD
```

### "I want to ignore an already-tracked file"

```bash
# Remove from tracking but keep local file
git rm --cached path/to/file

# Add to .gitignore
echo "path/to/file" >> .gitignore

# Commit the change
git add .gitignore
git commit -m "Stop tracking file"
```

---

## 📊 Repository Statistics

After initial setup, your repository should have:

```
Tracked Files:
- ~60-80 Python files (quantlab package + scripts)
- ~15-20 YAML configs
- ~15-20 markdown documentation files
- ~10 project metadata files

Total Size: < 10 MB (without data/models)

Ignored Files:
- ~50 indicator cache parquet files
- qlib_repo/ (828 MB)
- MLflow experiments
- Personal .env file
- All data directories
```

---

## ✅ Final Checklist

Before considering the repo "production ready":

- [ ] .gitignore is comprehensive and tested
- [ ] .env.example provides clear template
- [ ] README.md has setup instructions
- [ ] No sensitive data in tracked files
- [ ] Repository size < 50 MB
- [ ] All scripts use environment variables for paths
- [ ] Documentation is complete
- [ ] LICENSE file added (if open-sourcing)
- [ ] CONTRIBUTING.md added (if accepting contributions)

---

## 🎓 Additional Resources

### Git Best Practices
- [GitHub Git Handbook](https://guides.github.com/introduction/git-handbook/)
- [Atlassian Git Tutorials](https://www.atlassian.com/git/tutorials)
- [Pro Git Book](https://git-scm.com/book/en/v2)

### Security
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) - Remove sensitive data from history

### Python Project Structure
- [Python Packaging Guide](https://packaging.python.org/)
- [PyPA Sample Project](https://github.com/pypa/sampleproject)

---

## 📞 Support

If you encounter issues:

1. Check this guide first
2. Review `.gitignore` patterns
3. Use `git status --ignored` to debug
4. Consult official Git documentation

---

**Last Updated**: October 15, 2025
**Maintained By**: QuantLab Team
**Status**: ✅ Production Ready

---

*Remember: Security first! Never commit credentials, always rotate exposed keys immediately.*
