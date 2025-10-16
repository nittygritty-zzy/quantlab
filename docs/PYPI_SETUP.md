# PyPI Deployment Guide

This guide explains how to publish QuantLab to PyPI.

## Prerequisites

### 1. PyPI Account Setup

1. Create accounts on both:
   - **PyPI**: https://pypi.org/account/register/
   - **TestPyPI**: https://test.pypi.org/account/register/ (for testing)

2. Enable 2FA on both accounts (required for trusted publishing)

### 2. Configure Trusted Publishing on PyPI

**Trusted publishing** (recommended) uses GitHub OIDC to authenticate without API tokens.

#### For PyPI (Production):

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new publisher"
3. Fill in:
   - **PyPI Project Name**: `quantlab`
   - **Owner**: `nittygritty-zzy`
   - **Repository name**: `quantlab`
   - **Workflow name**: `publish-to-pypi.yml`
   - **Environment name**: `pypi`
4. Click "Add"

#### For TestPyPI (Testing):

1. Go to https://test.pypi.org/manage/account/publishing/
2. Click "Add a new publisher"
3. Fill in:
   - **PyPI Project Name**: `quantlab`
   - **Owner**: `nittygritty-zzy`
   - **Repository name**: `quantlab`
   - **Workflow name**: `publish-to-pypi.yml`
   - **Environment name**: `testpypi`
4. Click "Add"

### 3. Create GitHub Environments

1. Go to repository Settings → Environments
2. Create environment named `pypi`
   - Add protection rules if desired (require reviewers, etc.)
3. Create environment named `testpypi`

## Publishing Methods

### Method 1: Automatic Publishing (Recommended)

Publishing happens automatically when you create a GitHub release:

```bash
# 1. Update version in pyproject.toml
# version = "0.2.1"

# 2. Commit and push changes
git add pyproject.toml
git commit -m "chore: bump version to 0.2.1"
git push

# 3. Create and push a new tag
git tag v0.2.1
git push origin v0.2.1

# 4. Create a GitHub release
gh release create v0.2.1 \
  --title "v0.2.1 - Bug Fixes and Improvements" \
  --notes "Release notes here..."

# The GitHub Actions workflow will automatically:
# - Build the package
# - Publish to PyPI
```

### Method 2: Manual Publish to TestPyPI

Test your package before publishing to production:

```bash
# From GitHub Actions UI:
# 1. Go to Actions → "Publish Python Package to PyPI"
# 2. Click "Run workflow"
# 3. Check "Publish to TestPyPI instead of PyPI"
# 4. Click "Run workflow"

# Or trigger from command line:
gh workflow run publish-to-pypi.yml -f testpypi=true
```

After publishing to TestPyPI, verify installation:

```bash
# Create a clean environment
python -m venv test_env
source test_env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  quantlab

# Test the installation
quantlab --version
quantlab --help
```

### Method 3: Manual Local Build

Build and upload manually (not recommended - use trusted publishing):

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# This creates:
# dist/quantlab-0.2.0-py3-none-any.whl
# dist/quantlab-0.2.0.tar.gz

# Check the build
twine check dist/*

# Upload to TestPyPI (optional)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Version Management

QuantLab uses semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Version Bump Workflow

```bash
# For patch release (0.2.0 → 0.2.1)
# Update pyproject.toml: version = "0.2.1"
git add pyproject.toml
git commit -m "chore: bump version to 0.2.1"
git tag v0.2.1
git push && git push --tags

# For minor release (0.2.0 → 0.3.0)
# Update pyproject.toml: version = "0.3.0"
git add pyproject.toml
git commit -m "chore: bump version to 0.3.0"
git tag v0.3.0
git push && git push --tags

# Then create GitHub release to trigger publishing
gh release create v0.3.0 --generate-notes
```

## Pre-Release Checklist

Before publishing a new version:

- [ ] Update version in `pyproject.toml`
- [ ] Update `docs/source/conf.py` (release and version)
- [ ] Run all tests: `pytest`
- [ ] Build documentation locally: `cd docs && make html`
- [ ] Test build locally: `python -m build`
- [ ] Review `dist/` contents
- [ ] Update CHANGELOG (if using one)
- [ ] Test on TestPyPI first
- [ ] Create GitHub release with release notes

## Package Metadata

The package metadata is defined in `pyproject.toml`:

```toml
[project]
name = "quantlab"
version = "0.2.0"
description = "Professional quantitative trading research platform..."
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}

[project.urls]
Homepage = "https://github.com/nittygritty-zzy/quantlab"
Documentation = "https://quantlabs.readthedocs.io"
Repository = "https://github.com/nittygritty-zzy/quantlab"
"Bug Tracker" = "https://github.com/nittygritty-zzy/quantlab/issues"
```

## Package Contents

Files included in the distribution (defined in `MANIFEST.in`):

```
quantlab-0.2.0/
├── LICENSE
├── README.md
├── pyproject.toml
└── quantlab/
    ├── __init__.py
    ├── cli/
    ├── core/
    ├── data/
    ├── analysis/
    └── visualization/
```

Files **excluded** from distribution:
- Tests
- Documentation source
- Scripts
- Notebooks
- Results
- Development files

## Installation

After publishing, users can install with:

```bash
# Standard installation
pip install quantlab

# With development dependencies
pip install quantlab[dev]

# Specific version
pip install quantlab==0.2.0

# Latest pre-release
pip install --pre quantlab
```

## Troubleshooting

### Build Fails

```bash
# Clear build artifacts
rm -rf build/ dist/ *.egg-info

# Rebuild
python -m build
```

### Import Error After Install

```bash
# Check installed files
pip show -f quantlab

# Verify package structure
python -c "import quantlab; print(quantlab.__file__)"
```

### Version Conflict

```bash
# Check published versions
pip index versions quantlab

# Force reinstall
pip install --force-reinstall --no-cache-dir quantlab
```

### Trusted Publishing Not Working

1. Verify environment name matches in:
   - `.github/workflows/publish-to-pypi.yml`
   - PyPI trusted publisher settings
   - GitHub repository environments

2. Check workflow logs for detailed errors

3. Ensure repository has necessary permissions:
   - Settings → Actions → General → Workflow permissions
   - Select "Read and write permissions"

## Security

### API Tokens (Legacy Method)

If not using trusted publishing, create API tokens:

1. PyPI → Account Settings → API tokens
2. Create token with scope: "Entire account" or specific project
3. Add to GitHub Secrets:
   - `PYPI_API_TOKEN`
   - `TEST_PYPI_API_TOKEN`

**Note**: Trusted publishing (OIDC) is preferred as it's more secure.

## References

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Hatchling Documentation](https://hatch.pypa.io/latest/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Actions for PyPI](https://github.com/pypa/gh-action-pypi-publish)

## Support

For issues with PyPI publishing:
- PyPI Help: https://pypi.org/help/
- GitHub Issues: https://github.com/nittygritty-zzy/quantlab/issues
