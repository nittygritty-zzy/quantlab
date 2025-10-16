# How to Use Qlib's Alpha158 (The Right Way)

## 🎯 Key Insight

**You don't need to pre-compute Alpha158 features!**

Qlib computes Alpha158 features **on-the-fly** using its expression engine when you load data. Your existing Qlib binary data (with basic OHLCV) is already sufficient.

## 📚 How Qlib Alpha158 Works

### Qlib Expression DSL

Qlib uses its own expression language to define features:

```python
# Qlib expressions (not SQL!)
"($close-$open)/$open"              # KMID: body size
"Mean($close, 20)/$close"           # MA20: 20-day moving average
"Std($close, 20)/$close"            # STD20: 20-day volatility
"Corr($close, Log($volume+1), 20)"  # CORR20: price-volume correlation
```

These are **evaluated on-the-fly** from your binary data.

### Alpha158 Definition (from Qlib source)

Based on `/Users/zheyuanzhao/workspace/quantlab/.venv/lib/python3.12/site-packages/qlib/contrib/data/loader.py`:

**158 features = 9 KBAR + 4 Price + 5 Volume + 140 Rolling**

#### KBAR Features (9)
```python
fields = [
    "($close-$open)/$open",                         # KMID
    "($high-$low)/$open",                           # KLEN
    "($close-$open)/($high-$low+1e-12)",           # KMID2
    "($high-Greater($open, $close))/$open",         # KUP
    "($high-Greater($open, $close))/($high-$low+1e-12)",  # KUP2
    "(Less($open, $close)-$low)/$open",             # KLOW
    "(Less($open, $close)-$low)/($high-$low+1e-12)",# KLOW2
    "(2*$close-$high-$low)/$open",                  # KSFT
    "(2*$close-$high-$low)/($high-$low+1e-12)",     # KSFT2
]
```

#### Rolling Features (140+ features)
Over windows [5, 10, 20, 30, 60], includes:

**ROC** (Rate of Change): `"Ref($close, %d)/$close"` → ROC5, ROC10, ROC20, ROC30, ROC60

**MA** (Moving Average): `"Mean($close, %d)/$close"` → MA5, MA10, MA20, MA30, MA60

**STD** (Std Dev): `"Std($close, %d)/$close"` → STD5, STD10, STD20, STD30, STD60

**CORR** (Correlation): `"Corr($close, Log($volume+1), %d)"` → CORR5, CORR10, CORR20, CORR30, CORR60

**And 20+ more operators** (BETA, RSQR, RESI, MAX, MIN, QTLU, QTLD, RANK, RSV, IMAX, IMIN, IMXD, CORD, CNTP, CNTN, CNTD, SUMP, SUMN, SUMD, VMA, VSTD, WVMA, VSUMP, VSUMN, VSUMD)

## ✅ Using Alpha158 with Your Data

### Method 1: Use Qlib's Alpha158 Handler Directly

```python
import qlib
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH

# Initialize Qlib with your binary data
qlib.init(provider_uri='/Users/zheyuanzhao/sandisk/quantmini-data/data/qlib')

# Alpha158 handler computes features on-the-fly
handler = Alpha158(
    instruments='csi500',  # Or your universe
    start_time='2025-09-01',
    end_time='2025-09-30',
)

# Create dataset
dataset = DatasetH(handler=handler)

# Get data with all 158 features computed!
df_train, df_valid = dataset.prepare(
    ["train", "valid"],
    col_set=["feature", "label"],
)

print(f"Shape: {df_train.shape}")  # Should have 158 feature columns
print(f"Columns: {df_train.columns.tolist()}")
```

### Method 2: Use Specific Alpha158 Features

```python
from qlib.data import D

# Get specific features using Qlib expressions
features = [
    "($close-$open)/$open",           # KMID
    "Mean($close, 20)/$close",        # MA20
    "Std($close, 20)/$close",         # STD20
    "Corr($close, Log($volume+1), 20)" # CORR20
]

df = D.features(
    instruments=['AAPL', 'MSFT'],
    fields=features,
    start_time='2025-09-01',
    end_time='2025-09-30'
)

print(df.head())
```

### Method 3: Custom Configuration

```python
from qlib.contrib.data.loader import Alpha158DL

# Customize Alpha158 config
config = {
    "kbar": {},  # Include KBAR features
    "price": {
        "windows": [0, 1, 2, 3, 4],  # 5 lags
        "feature": ["OPEN", "HIGH", "LOW", "CLOSE", "VWAP"]
    },
    "volume": {
        "windows": [0, 1, 2, 3, 4]
    },
    "rolling": {
        "windows": [5, 10, 20, 30, 60],
        "include": ["ROC", "MA", "STD", "CORR", "RSV"],  # Only these
        # "exclude": ["RANK", "BETA"]  # Or exclude specific ones
    }
}

# Get feature expressions
fields, names = Alpha158DL.get_feature_config(config)

print(f"Total features: {len(fields)}")
print(f"Feature names: {names[:10]}...")  # First 10

# Use with DataLoader
from qlib.data.dataset.handler import DataHandlerLP

handler = DataHandlerLP(
    instruments='csi500',
    start_time='2025-01-01',
    end_time='2025-09-30',
    data_loader={
        "class": "QlibDataLoader",
        "kwargs": {
            "config": {"feature": (fields, names)},
            "freq": "day",
        }
    }
)
```

## 🔍 Verify Your Data Works

```python
import qlib
from qlib.data import D

# Initialize
qlib.init(provider_uri='/Users/zheyuanzhao/sandisk/quantmini-data/data/qlib')

# Test basic fields exist
basic_fields = ['$open', '$high', '$low', '$close', '$volume']
df_basic = D.features(['AAPL'], basic_fields, '2025-09-30', '2025-09-30')
print("Basic fields:")
print(df_basic)

# Test Alpha158 expressions work
alpha158_exprs = [
    "($close-$open)/$open",           # KMID
    "Mean($close, 5)/$close",         # MA5
    "Std($close, 20)/$close",         # STD20
]
df_alpha = D.features(['AAPL'], alpha158_exprs, '2025-09-01', '2025-09-30')
print("\nAlpha158 features:")
print(df_alpha)
```

## ⚠️ Important: Check Binary Data Requirements

Alpha158 needs these **basic fields** in your binary data:
- ✓ `open`
- ✓ `high`
- ✓ `low`
- ✓ `close`
- ✓ `volume`
- ⚠️ `vwap` (optional, for VWAP-based features)

**Verify your data has these:**
```bash
ls /Users/zheyuanzhao/sandisk/quantmini-data/data/qlib/stocks_daily/features/AAPL/

# Should show:
# open.day.bin
# high.day.bin
# low.day.bin
# close.day.bin
# volume.day.bin
```

## 🚀 Quick Example: Train Model with Alpha158

```python
import qlib
from qlib.contrib.model.gbdt import LGBModel
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH

# 1. Initialize Qlib
qlib.init(provider_uri='/Users/zheyuanzhao/sandisk/quantmini-data/data/qlib')

# 2. Create Alpha158 dataset
dataset = DatasetH(
    handler=Alpha158(
        instruments='csi500',
        start_time='2025-01-01',
        end_time='2025-09-30',
        fit_start_time='2025-01-01',
        fit_end_time='2025-07-31',
    )
)

# 3. Train model
model = LGBModel()
model.fit(dataset)

# 4. Predict
predictions = model.predict(dataset)
print(predictions.head())
```

## 🔧 Advanced: Add Custom Features

Extend Alpha158 with your own features:

```python
from qlib.contrib.data.handler import Alpha158

class MyAlpha158(Alpha158):
    def get_feature_config(self):
        # Get original Alpha158 features
        fields, names = super().get_feature_config()

        # Add custom features
        custom_fields = [
            "Ref($close, 1)/$vwap",                    # Close to VWAP ratio
            "($high-$low)/Mean($high-$low, 20)",       # Normalized range
            "Corr($close, $volume, 10)",               # 10-day price-volume corr
        ]
        custom_names = ["CLOSE_VWAP", "NORM_RANGE", "PV_CORR10"]

        fields.extend(custom_fields)
        names.extend(custom_names)

        return fields, names

# Use your custom handler
handler = MyAlpha158(
    instruments='csi500',
    start_time='2025-01-01',
    end_time='2025-09-30'
)
```

## 📊 Performance Tips

### 1. Cache Features
```python
# Alpha158 with caching
dataset = DatasetH(
    handler=Alpha158(...),
    segments={
        "train": ("2025-01-01", "2025-07-31"),
        "valid": ("2025-08-01", "2025-08-31"),
        "test": ("2025-09-01", "2025-09-30"),
    }
)

# Cache processed data
dataset.config(dump_dir='./cache/alpha158', dump=True)
```

### 2. Parallel Processing
```python
# Enable parallel feature computation
import qlib
qlib.init(
    provider_uri='/path/to/qlib',
    expression_provider='FileExpressionProvider',
    dataset_cache=None,
    kernels=4  # Use 4 cores
)
```

## 📝 Summary

**The Right Way to Use Alpha158:**

1. ✅ **Keep your existing Qlib binary data** (with basic OHLCV)
2. ✅ **Use Qlib's Alpha158 handler** - it computes features on-the-fly
3. ✅ **No pre-computation needed** - Qlib's expression engine does it all
4. ✅ **Customize if needed** - extend or filter features easily

**Wrong Approach (what I initially suggested):**
- ❌ Pre-computing Alpha158 in DuckDB SQL
- ❌ Storing 158 separate binary files per symbol
- ❌ Reimplementing Qlib's expression DSL

**Example workflow:**
```python
import qlib
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH
from qlib.contrib.model.gbdt import LGBModel

# Initialize
qlib.init(provider_uri='/Users/zheyuanzhao/sandisk/quantmini-data/data/qlib')

# Use Alpha158 (computes 158 features automatically)
dataset = DatasetH(handler=Alpha158(
    instruments='csi500',
    start_time='2025-01-01',
    end_time='2025-09-30'
))

# Train
model = LGBModel()
model.fit(dataset)
```

**That's it! Your Alpha158 is already available through Qlib's expression engine. 🎉**
