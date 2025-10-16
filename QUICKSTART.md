# QuantLab Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Activate Environment
```bash
cd /Users/zheyuanzhao/workspace/quantlab
source .venv/bin/activate
```

### 2. Choose a Configuration

**Option A: Liquid Universe (Recommended)**
```bash
cd qlib_repo/examples
uv run qrun ../../configs/lightgbm_liquid_universe.yaml
```

**Option B: Fixed Dates (2024 only)**
```bash
cd qlib_repo/examples  
uv run qrun ../../configs/lightgbm_fixed_dates.yaml
```

**Option C: Full Universe (All stocks)**
```bash
cd qlib_repo/examples
uv run qrun ../../configs/lightgbm_external_data.yaml
```

### 3. View Results

The backtest will output:
- IC and Rank IC metrics
- Portfolio analysis
- Results saved to `results/mlruns/`

### 4. Visualize

Find your experiment ID from the output, then:

```bash
# Edit scripts/analysis/visualize_results.py
# Update EXP_DIR to your experiment ID

cd /Users/zheyuanzhao/workspace/quantlab
uv run python scripts/analysis/visualize_results.py
```

Output: `results/visualizations/backtest_visualization.png`

## 📊 What You'll See

### Console Output
```
IC: 0.066
ICIR: 0.622
Rank IC: -0.006
Sharpe Ratio: 3.94
Max Drawdown: -39.19%
```

### Visualization
- IC over time (predictive power)
- Rank IC over time (ranking ability)
- Cumulative returns chart
- Drawdown analysis
- Daily returns distribution

## 🔍 Understanding the Results

### Good Signs ✅
- **IC > 0.05**: Model has predictive power
- **ICIR > 0.5**: Predictions are consistent
- **Sharpe > 2**: Good risk-adjusted returns

### Warning Signs ⚠️
- **Rank IC ≈ 0**: Model can't rank stocks well
- **Extreme returns**: May indicate data quality issues
- **High drawdown**: Needs better risk controls

## 📁 Where Are My Results?

```
results/
├── mlruns/489214785307856385/
│   ├── [run_id_1]/artifacts/
│   │   ├── pred.pkl              # Model predictions
│   │   ├── sig_analysis/         # IC analysis
│   │   └── portfolio_analysis/   # Backtest results
│   └── [run_id_2]/artifacts/
│       └── ...
└── visualizations/
    └── backtest_visualization.png
```

## 🔄 Next Steps

1. **Read the analysis**: `docs/BACKTEST_SUMMARY.md`
2. **Try different models**: Edit configs to use XGBoost, MLP
3. **Improve features**: Add custom Alpha features
4. **Better universe**: Filter by market cap, volume

## ⚙️ Common Commands

### List all experiment runs
```bash
ls results/mlruns/489214785307856385/
```

### Check MLflow UI (if installed)
```bash
cd results
mlflow ui
# Open http://localhost:5000
```

### Clean old runs
```bash
rm -rf results/mlruns/.trash
```

### Update data
```bash
python scripts/data/refresh_today_data.py
```

## 🐛 Troubleshooting

### "Module not found: qlib"
```bash
uv pip install qlib
```

### "Data not found"
Check: `/Volumes/sandisk/quantmini-data/data/qlib/stocks_daily/`

### "Import error"
Make sure you're in project root when running scripts

### Visualization fails
```bash
uv pip install matplotlib seaborn pandas
```

## 📚 Learn More

- **README.md** - Full project overview
- **docs/BACKTEST_SUMMARY.md** - Detailed analysis
- **docs/USE_QLIB_ALPHA158.md** - Feature guide
- **PROJECT_STRUCTURE.md** - Directory layout

## 💡 Tips

1. Start with `lightgbm_liquid_universe.yaml` - it's the most realistic
2. Check IC before trusting backtest returns
3. Compare multiple runs to validate results
4. Read the docs - lots of insights there!

Happy backtesting! 🎯
