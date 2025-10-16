# Qlib Patches

This directory contains patch files for critical bug fixes to Microsoft Qlib.

---

## 📋 Patches

### 1. `0001-fix-alpha158-label-division-by-zero.patch`

**File**: `qlib/contrib/data/handler.py`
**Issue**: Division by zero in Alpha158 label calculation
**Fix**: Add epsilon (1e-12) to denominator

```python
# Before: Ref($close, -2)/Ref($close, -1) - 1
# After:  Ref($close, -2)/(Ref($close, -1)+1e-12) - 1
```

**Impact**: Prevents `inf` values when stock price is zero (halted stocks, data errors)

---

### 2. `0002-fix-alpha158-features-division-by-zero.patch`

**File**: `qlib/contrib/data/loader.py`
**Issue**: Division by zero in 20+ Alpha158 features
**Fix**: Add epsilon (1e-12) to all price/open and price/close divisions

**Features Fixed**:
- KMID, KLEN, KSFT, KUP, KLOW (kbar features)
- OPEN, HIGH, LOW, CLOSE, VWAP ratios (price features)
- ROC, MA, STD, BETA, RESI, MAX, MIN, QTLU, QTLD (rolling features)

**Impact**:
- XGBoost now works (was failing with "Input contains inf")
- Improved IC from 0.0660 to 0.0764 (+16%)

---

### 3. `0003-fix-pytorch-hist-device-handling.patch`

**File**: `qlib/contrib/model/pytorch_hist.py`
**Issue**: Invalid PyTorch device call `torch.get_device()`
**Fix**: Use `x.device` instead

```python
# Before: device = torch.device(torch.get_device(x))  # ❌ Invalid
# After:  device = x.device  # ✅ Correct
```

**Impact**: HIST model now works on both CPU and CUDA

---

## 🚀 How Patches Are Applied

The `scripts/setup_qlib_repo.py` script automatically applies these patches after cloning Qlib:

```bash
# 1. Clone Microsoft Qlib
git clone https://github.com/microsoft/qlib.git qlib_repo

# 2. Apply patches
cd qlib_repo
git apply ../patches/0001-fix-alpha158-label-division-by-zero.patch
git apply ../patches/0002-fix-alpha158-features-division-by-zero.patch
git apply ../patches/0003-fix-pytorch-hist-device-handling.patch

# 3. Install in development mode
pip install -e .
```

**Automated**: Just run `uv run python scripts/setup_qlib_repo.py`

---

## 🔄 Updating Patches

If you make new modifications to qlib_repo:

```bash
# Navigate to qlib_repo
cd qlib_repo

# Make your changes to files...

# Generate new patch
git diff qlib/contrib/data/handler.py > ../patches/0001-fix-alpha158-label-division-by-zero.patch

# Or update all patches at once
git diff qlib/contrib/data/handler.py > ../patches/0001-fix-alpha158-label-division-by-zero.patch
git diff qlib/contrib/data/loader.py > ../patches/0002-fix-alpha158-features-division-by-zero.patch
git diff qlib/contrib/model/pytorch_hist.py > ../patches/0003-fix-pytorch-hist-device-handling.patch
```

---

## ✅ Verifying Patches

After applying patches:

```bash
# Check that files are modified
cd qlib_repo
git status

# Should show:
#  M qlib/contrib/data/handler.py
#  M qlib/contrib/data/loader.py
#  M qlib/contrib/model/pytorch_hist.py

# Verify specific changes
git diff qlib/contrib/data/handler.py | grep "1e-12"
```

---

## 📚 Related Documentation

- **Detailed Fix Documentation**: `../docs/archive/alpha158/ALPHA158_INF_FIX.md`
- **Modifications Summary**: `../docs/QLIB_MODIFICATIONS_SUMMARY.md`
- **Setup Script**: `../scripts/setup_qlib_repo.py`

---

## 🎯 Why Patches?

**Benefits**:
- ✅ Small files (~7KB total vs 828MB repo)
- ✅ Version controlled with your project
- ✅ Easy to review changes
- ✅ Automatic application via setup script
- ✅ Can update Qlib independently

**vs. Keeping Modified Repo**:
- ❌ 828MB in git (too large)
- ❌ Hard to see what changed
- ❌ Difficult to update Qlib version

---

## 🔮 Future: Upstream Contribution

These patches could be contributed to Microsoft Qlib:

1. Check if fixes are already in latest Qlib
2. Create GitHub issue describing the problems
3. Submit PR with these fixes
4. Reference this directory and ALPHA158_INF_FIX.md

**GitHub**: https://github.com/microsoft/qlib

---

**Last Updated**: October 15, 2025
**Total Size**: ~7 KB (3 patches)
**Applied by**: `scripts/setup_qlib_repo.py`
