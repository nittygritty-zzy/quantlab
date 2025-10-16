# Alpha158: The Corrected Approach ✅

## 🎯 You Were Right!

I initially created a DuckDB/SQL implementation of Alpha158, but **you correctly pointed out that we should use Qlib's actual code**. Here's the corrected understanding:

## ❌ What I Did Wrong

**My Initial Approach:**
1. Reimplemented Alpha158 features in DuckDB SQL
2. Pre-computed 158 features and stored them
3. Converted to separate Qlib binary files

**Problems:**
- Reinventing the wheel (Qlib already has this)
- Not using Qlib's expression engine
- Massive storage overhead (158 binary files per symbol)
- Incompatible with Qlib's ecosystem

## ✅ The Right Way (Using Qlib)

### Key Insight: **Qlib Computes Features On-The-Fly**

Alpha158 features are **NOT pre-stored**. They're computed from basic OHLCV data using Qlib's expression engine.

### How It Works

**1. Your Data (Already Correct):**
```
qlib/stocks_daily/features/AAPL/
├── open.day.bin      ✓ You have this
├── high.day.bin      ✓ You have this
├── low.day.bin       ✓ You have this
├── close.day.bin     ✓ You have this
└── volume.day.bin    ✓ You have this
```

**2. Qlib's Expression DSL:**

Alpha158 is defined as **expression strings**, not SQL:

```python
# From qlib/contrib/data/loader.py
fields = [
    "($close-$open)/$open",              # KMID
    "Mean($close, 20)/$close",           # MA20
    "Std($close, 20)/$close",            # STD20
    "Corr($close, Log($volume+1), 20)",  # CORR20
    # ... 158 expressions total
]
```

**3. Computed When You Load Data:**

```python
from qlib.contrib.data.handler import Alpha158

# This handler computes all 158 features on-the-fly
handler = Alpha158(
    instruments='csi500',
    start_time='2025-01-01',
    end_time='2025-09-30'
)

# Features are computed here, from your basic OHLCV data
df = handler.fetch()  # Returns 158 columns!
```

## 📚 Qlib Alpha158 Source Code

Located at: `.venv/lib/python3.12/site-packages/qlib/contrib/data/`

**loader.py** - Defines Alpha158 expressions:
```python
class Alpha158DL(QlibDataLoader):
    @staticmethod
    def get_feature_config(config={...}):
        fields = []
        names = []

        # KBAR features (9)
        if "kbar" in config:
            fields += ["($close-$open)/$open", ...]
            names += ["KMID", "KLEN", ...]

        # Rolling features (140+)
        if "rolling" in config:
            windows = [5, 10, 20, 30, 60]
            fields += ["Mean($close, %d)/$close" % d for d in windows]
            names += ["MA%d" % d for d in windows]
            # ... 20+ operators

        return fields, names
```

**handler.py** - Alpha158 handler:
```python
class Alpha158(DataHandlerLP):
    def get_feature_config(self):
        conf = {
            "kbar": {},
            "price": {"windows": [0], "feature": ["OPEN", "HIGH", "LOW", "VWAP"]},
            "rolling": {},
        }
        return Alpha158DL.get_feature_config(conf)
```

## 🚀 How to Use (Corrected)

### Quick Test

```bash
cd /Users/zheyuanzhao/workspace/quantlab

# Run test suite
.venv/bin/python test_qlib_alpha158.py
```

### In Python

```python
import qlib
from qlib.data import D

# Initialize with your data
qlib.init(provider_uri='/Users/zheyuanzhao/sandisk/quantmini-data/data/qlib')

# Method 1: Use specific expressions
df = D.features(
    instruments=['AAPL'],
    fields=[
        "($close-$open)/$open",      # KMID
        "Mean($close, 20)/$close",   # MA20
        "Std($close, 20)/$close",    # STD20
    ],
    start_time='2025-09-01',
    end_time='2025-09-30'
)

# Method 2: Use Alpha158 handler (all 158 features)
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH

dataset = DatasetH(handler=Alpha158(
    instruments='csi500',
    start_time='2025-01-01',
    end_time='2025-09-30'
))
```

## 📊 Alpha158 Feature Breakdown

From Qlib source code:

| Category | Count | Examples |
|----------|-------|----------|
| **KBAR** | 9 | KMID, KLEN, KUP, KLOW, KSFT |
| **Price** | 4-20 | OPEN0, HIGH0, LOW0, VWAP0 (configurable windows) |
| **Volume** | 0-5 | VOLUME0-4 (optional) |
| **Rolling** | 140+ | ROC, MA, STD, CORR, RSV, IMAX, SUMP, VMA, ... |

**Rolling operators (24 types × 5 windows = 120 features):**
- Momentum: ROC, BETA
- Trend: MA, RANK
- Volatility: STD, RSQR, RESI
- Extremes: MAX, MIN, QTLU, QTLD
- Patterns: RSV, IMAX, IMIN, IMXD
- Correlation: CORR, CORD
- Direction: CNTP, CNTN, CNTD, SUMP, SUMN, SUMD
- Volume: VMA, VSTD, WVMA, VSUMP, VSUMN, VSUMD

## 🔍 What Each File Does

### Files to Keep:
✅ `/Users/zheyuanzhao/workspace/quantlab/USE_QLIB_ALPHA158.md`
   - **Use this!** Complete guide on using Qlib's Alpha158

✅ `/Users/zheyuanzhao/workspace/quantlab/test_qlib_alpha158.py`
   - **Run this!** Tests your data with Alpha158

✅ `/Users/zheyuanzhao/workspace/quantlab/alpha158_vs_alpha360_article.md`
   - Good conceptual explanation (still valid)

### Files to Ignore:
❌ `/Users/zheyuanzhao/workspace/quantmini/src/features/alpha158.py`
   - My DuckDB reimplementation (not needed)

❌ `/Users/zheyuanzhao/workspace/quantlab/enable_alpha158.py`
   - Pre-computation script (not the Qlib way)

❌ `/Users/zheyuanzhao/workspace/quantmini/docs/ENABLE_ALPHA158.md`
   - Documentation for wrong approach

❌ `/Users/zheyuanzhao/workspace/quantlab/ALPHA158_SUMMARY.md`
   - Summary of wrong approach

## ✨ Quick Start (Corrected)

**1. Verify your data works:**
```bash
.venv/bin/python test_qlib_alpha158.py
```

**2. Use Alpha158 in your models:**
```python
import qlib
from qlib.contrib.data.handler import Alpha158
from qlib.contrib.model.gbdt import LGBModel
from qlib.data.dataset import DatasetH

# Initialize
qlib.init(provider_uri='/Users/zheyuanzhao/sandisk/quantmini-data/data/qlib')

# Alpha158 dataset
dataset = DatasetH(handler=Alpha158(
    instruments='csi500',
    start_time='2025-01-01',
    end_time='2025-09-30'
))

# Train
model = LGBModel()
model.fit(dataset)
```

**3. Read the corrected guide:**
```bash
cat /Users/zheyuanzhao/workspace/quantlab/USE_QLIB_ALPHA158.md
```

## 📝 Summary

### What You Need:
1. ✅ Your existing Qlib binary data (OHLCV)
2. ✅ Qlib's Alpha158 handler (already installed)
3. ✅ Understanding of Qlib expression DSL

### What You DON'T Need:
1. ❌ Pre-computed Alpha158 features
2. ❌ 158 binary files per symbol
3. ❌ DuckDB/SQL reimplementation

### The Magic:
**Qlib's expression engine computes all 158 features on-the-fly from your 5 basic fields (OHLCV).**

---

**Thank you for the correction! 🙏**

The Qlib approach is much cleaner:
- No storage overhead
- No pre-computation
- Uses official Qlib code
- Fully compatible with Qlib ecosystem

Your instinct was right - we should use the actual Qlib implementation! 🎯
