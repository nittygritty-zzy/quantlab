# Patch-Based Qlib Workflow

**Date**: October 15, 2025
**Status**: Production Ready ✅

---

## 🎯 Overview

Instead of keeping the 828MB `qlib_repo/` directory in git, we use **patch files** (~16KB) to store our custom modifications.

---

## ✅ Benefits

### Before (Modified qlib_repo in git)
```
❌ Repository size: > 838 MB
❌ Slow clone times: 10-15 minutes
❌ Hard to review changes
❌ Difficult to update Qlib version
❌ Git operations slow
```

### After (Patch-based approach)
```
✅ Repository size: < 10 MB
✅ Fast clone times: < 1 minute
✅ Easy to review: 3 small patches
✅ Easy to update: git pull + reapply patches
✅ Git operations instant
✅ Patches version-controlled
```

**Size comparison**:
- `qlib_repo/`: 828 MB ❌
- `patches/`: 16 KB ✅
- **Reduction**: **99.998% smaller!**

---

## 📋 What's in patches/

### 3 Patch Files

1. **`0001-fix-alpha158-label-division-by-zero.patch`** (665 bytes)
   - Fixes: `qlib/contrib/data/handler.py`
   - Prevents division by zero in label calculation

2. **`0002-fix-alpha158-features-division-by-zero.patch`** (5.8 KB)
   - Fixes: `qlib/contrib/data/loader.py`
   - Adds epsilon to 20+ Alpha158 features

3. **`0003-fix-pytorch-hist-device-handling.patch`** (576 bytes)
   - Fixes: `qlib/contrib/model/pytorch_hist.py`
   - Fixes PyTorch device handling bug

**Total**: ~7 KB (tracked in git ✅)

---

## 🚀 Workflow

### For New Users (First Time Setup)

```bash
# 1. Clone your QuantLab repository (small & fast!)
git clone https://github.com/yourusername/quantlab.git
cd quantlab

# 2. Set up environment
cp .env.example .env
nano .env  # Add API keys

# 3. Install dependencies
uv sync

# 4. Set up Qlib with patches (automated!)
uv run python scripts/setup_qlib_repo.py
```

**What happens automatically**:
1. Clones Microsoft Qlib (~828 MB)
2. ✨ **Applies your 3 patches** automatically
3. Installs in development mode
4. Verifies installation

**Time**: 5-10 minutes (mostly downloads)

---

### For Existing Developers

#### Option 1: You Have qlib_repo Already
```bash
# Your existing qlib_repo stays as-is
# Nothing changes for you!
cd qlib_repo
git status  # Shows M qlib/contrib/data/handler.py, etc.
```

#### Option 2: Fresh Setup
```bash
# Delete old qlib_repo (it's not in git anyway)
rm -rf qlib_repo

# Run automated setup with patches
uv run python scripts/setup_qlib_repo.py
```

---

## 🔄 Making New Modifications

### Step 1: Make Changes to qlib_repo

```bash
cd qlib_repo

# Edit files as needed
vim qlib/contrib/data/handler.py

# Test your changes
cd ..
cd qlib_repo
uv run qrun ../configs/backtest_dev.yaml
```

### Step 2: Update Patches

```bash
# From project root
cd qlib_repo

# Generate new patches (overwrites old ones)
git diff qlib/contrib/data/handler.py > ../patches/0001-fix-alpha158-label-division-by-zero.patch
git diff qlib/contrib/data/loader.py > ../patches/0002-fix-alpha158-features-division-by-zero.patch
git diff qlib/contrib/model/pytorch_hist.py > ../patches/0003-fix-pytorch-hist-device-handling.patch
```

### Step 3: Commit Patches to Git

```bash
cd ..  # Back to project root

# Add updated patches
git add patches/

# Commit
git commit -m "Update Qlib patches: improved epsilon handling"

# Push
git push
```

**Result**: Your modifications are now in git (as small patches), not the entire 828MB repo!

---

## 📦 What's in Git vs Not

### ✅ Tracked in Git
```
quantlab/
├── patches/                          # 16 KB total ✅
│   ├── 0001-*.patch
│   ├── 0002-*.patch
│   ├── 0003-*.patch
│   └── README.md
├── scripts/setup_qlib_repo.py        # Applies patches ✅
├── docs/                             # All documentation ✅
├── quantlab/                         # Source code ✅
└── configs/                          # YAML configs ✅
```

### 🚫 NOT in Git
```
qlib_repo/                            # 828 MB ❌
data/                                 # All data files ❌
.env                                  # API keys ❌
results/mlruns/                       # MLflow data ❌
```

---

## 🔄 Updating Qlib Version

### Scenario: New Qlib Release

```bash
# 1. Delete old qlib_repo
rm -rf qlib_repo

# 2. Clone new version
git clone https://github.com/microsoft/qlib.git qlib_repo
cd qlib_repo
git checkout v0.10.0  # New version

# 3. Try applying patches
cd ..
git apply patches/0001-*.patch
git apply patches/0002-*.patch
git apply patches/0003-*.patch
```

**If patches apply successfully**:
- ✅ Done! Your fixes work with new Qlib

**If patches fail** (Qlib changed the same code):
- ⚠️ Manual merge needed
- Apply patches manually
- Update patch files
- Commit updated patches

---

## 🛠️ Automated Setup Script

### What `scripts/setup_qlib_repo.py` Does

```
Step 1: Clone Qlib
  ✓ git clone https://github.com/microsoft/qlib.git

Step 2: Apply Patches ← NEW!
  ✓ git apply patches/0001-*.patch
  ✓ git apply patches/0002-*.patch
  ✓ git apply patches/0003-*.patch

Step 3: Install
  ✓ pip install -e .

Step 4: Verify
  ✓ import qlib
  ✓ qrun command available

Step 5: Show next steps
```

**Key Addition**: Step 2 automatically applies all patches! 🎉

---

## 📊 Size Comparison

| What | Size | In Git? | Why |
|------|------|---------|-----|
| **qlib_repo/** | 828 MB | ❌ No | Too large, regenerated from patches |
| **patches/** | 16 KB | ✅ Yes | Small, contains your critical fixes |
| **Full repo** | < 10 MB | ✅ Yes | Includes patches, not qlib_repo |

**Clone time comparison**:
- With qlib_repo: 10-15 minutes ❌
- Without (patches): < 1 minute ✅

---

## 🧪 Testing the Workflow

### Test 1: Fresh Clone

```bash
# Simulate new user
cd /tmp
git clone https://github.com/yourusername/quantlab.git
cd quantlab

# Should see patches/ but not qlib_repo/
ls patches/
ls qlib_repo/  # Should not exist yet

# Run setup
uv run python scripts/setup_qlib_repo.py

# Should see:
# ✓ Cloned Qlib
# ✓ Applied 3 patches  ← IMPORTANT!
# ✓ Installed successfully

# Verify modifications
cd qlib_repo
git diff qlib/contrib/data/handler.py  # Should show epsilon changes
```

### Test 2: Patch Application

```bash
# From quantlab/qlib_repo/
git status

# Should show:
#  M qlib/contrib/data/handler.py
#  M qlib/contrib/data/loader.py
#  M qlib/contrib/model/pytorch_hist.py

# Check patches worked
git diff qlib/contrib/data/handler.py | grep "1e-12"
# Should show: /(Ref($close, -1)+1e-12)
```

---

## 🎓 Best Practices

### DO ✅

1. **Commit patches to git**
   ```bash
   git add patches/
   git commit -m "Update Qlib patches"
   ```

2. **Update patches when you modify qlib_repo**
   ```bash
   cd qlib_repo
   git diff qlib/contrib/data/handler.py > ../patches/0001-*.patch
   ```

3. **Test patches after updating**
   ```bash
   rm -rf qlib_repo
   uv run python scripts/setup_qlib_repo.py
   ```

4. **Document why each patch exists**
   - See `patches/README.md`
   - Reference issue numbers
   - Explain the fix

### DON'T ❌

1. **Don't commit qlib_repo/**
   ```bash
   # This is already in .gitignore
   qlib_repo/  # ❌ Too large (828 MB)
   ```

2. **Don't forget to update patches**
   ```bash
   # If you modify qlib_repo files, update patches!
   git diff > ../patches/xxxx.patch
   ```

3. **Don't apply patches manually**
   ```bash
   # Use the automated script instead
   uv run python scripts/setup_qlib_repo.py
   ```

---

## 🔮 Future: Contribute Upstream

### Eventually, Contribute to Microsoft Qlib

Your patches fix real bugs! Consider contributing:

```bash
# 1. Fork Microsoft Qlib
# 2. Create branch with your fixes
# 3. Submit PR

# If accepted:
# - Patches no longer needed
# - Can use pip install qlib
# - Helps the community!
```

**Until then**: Patches are the best approach ✅

---

## 🆘 Troubleshooting

### Issue: Patches Don't Apply

**Symptom**:
```
error: patch failed: qlib/contrib/data/handler.py:152
```

**Solution**:
```bash
# Qlib changed, manual merge needed
cd qlib_repo

# Apply manually
vim qlib/contrib/data/handler.py
# Add: /(Ref($close, -1)+1e-12)

# Update patch
git diff qlib/contrib/data/handler.py > ../patches/0001-*.patch
```

### Issue: Missing Patches

**Symptom**:
```
WARNING: No patches directory found
```

**Solution**:
```bash
# Patches should be in git
git pull

# If still missing, recreate from qlib_repo
cd qlib_repo
git diff > ../patches/my-changes.patch
```

### Issue: qlib_repo Has Uncommitted Changes

**This is normal!** qlib_repo is not in git:
```bash
cd qlib_repo
git status
# Shows:  M qlib/contrib/data/handler.py  ← EXPECTED ✅
```

---

## 📚 Documentation

- **Patch Contents**: `patches/README.md`
- **Setup Script**: `scripts/setup_qlib_repo.py`
- **Detailed Fixes**: `docs/archive/alpha158/ALPHA158_INF_FIX.md`
- **Modifications Summary**: `docs/QLIB_MODIFICATIONS_SUMMARY.md`

---

## ✅ Summary

**Old Workflow** (qlib_repo in git):
```
1. Clone repo (10-15 min, 838 MB)
2. qlib_repo already has modifications
3. Hard to see what changed
4. Difficult to update Qlib
```

**New Workflow** (patches in git):
```
1. Clone repo (< 1 min, < 10 MB)
2. Run setup script
3. Patches automatically applied
4. Easy to update, review, and maintain
```

**Result**: **99.998% size reduction**, same functionality! ✅

---

**Last Updated**: October 15, 2025
**Approach**: Patch-based
**Repository Size**: < 10 MB (was > 838 MB)
**Patches**: 3 files, 16 KB total
**Status**: ✅ Production Ready

---

*Remember: Commit patches, not qlib_repo. The setup script handles the rest!*
