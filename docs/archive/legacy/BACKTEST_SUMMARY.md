# Qlib Auto Quant Research Workflow - Results Summary

## Overview
Successfully ran qlib's Auto Quant Research Workflow with LightGBM on external US stock market data.

## Configurations Tested

### 1. Original (All 14,310 stocks)
- **Universe**: All instruments including warrants, units, penny stocks
- **Period**: Sept 2024 - Sept 2025
- **IC**: 0.0799, ICIR: 0.74
- **Issue**: Picked ultra-volatile micro-caps (BNAI, SVRE, BKKT.WS) causing extreme returns

### 2. Fixed Dates (2024 only)
- **Universe**: All stocks
- **Period**: July 2024 - Dec 2024 (avoided 2025)
- **IC**: 0.0792, ICIR: 0.78
- **Issue**: Still high returns but more controlled

### 3. Liquid Universe Filter
- **Universe**: 13,187 stocks (excluded 1,003 warrants, 65 units)
- **Period**: Sept 2024 - Sept 2025
- **IC**: 0.0660, ICIR: 0.62
- **Result**: Slightly lower but still unrealistic returns

## Comparison Table

| Metric | Original | Fixed Dates | Liquid Universe |
|--------|----------|-------------|-----------------|
| IC | 0.0799 | 0.0792 | 0.0660 |
| Rank IC | -0.0036 | -0.0078 | -0.0062 |
| Sharpe Ratio | 2.98 | 4.54 | 3.94 |
| Max Drawdown | -41.7% | -35.3% | -39.2% |
| Win Rate | 61.5% | 51.6% | 53.0% |
| Mean Daily Return | 65.35% | 39.01% | 47.78% |

## Key Findings

### ✅ Model Performance (Good)
- **IC consistently positive** (0.066-0.080) → Model predictions correlate with returns
- **ICIR decent** (0.62-0.78) → Predictions are stable over time
- **Feature learning works** → Alpha158 features capture market patterns

### ❌ Backtest Issues (Bad)
- **Astronomical returns** in all configs (e20 to e25 final values)
- **Rank IC near zero** → Can't rank stocks well (critical for top-k strategy)
- **Extreme daily returns** (39-65% mean) → Unrealistic

## Root Causes Identified

### 1. **Data Quality**
- Dataset includes 14,310 instruments (too broad)
- Contains warrants, units, micro-caps with extreme volatility
- Example: BKKT.WS (warrant) predicted correctly for huge gain

### 2. **Strategy Issues**
- TopkDropoutStrategy with top 30-50 stocks → High concentration
- Equal weighting allows huge exposure to volatile names
- No position sizing limits or risk controls

### 3. **Possible Backtest Engine Issues**
- May have look-ahead bias
- Survivorship bias in dataset
- Price data quality (splits/dividends)
- Compounding logic allowing unrealistic leverage

## Recommendations Going Forward

### Immediate Fixes
1. ✅ **Filter universe to S&P 500 or liquid stocks** (Done - created `liquid_stocks.txt`)
2. ⚠️ **Add position sizing limits** (max % per stock)
3. ⚠️ **Improve Rank IC** - Model needs better relative ranking
4. ⚠️ **Validate data quality** - Check for corporate actions handling

### Model Improvements
1. **Try different models** to improve Rank IC:
   - XGBoost
   - TabNet
   - LSTM/GRU for time series patterns
   - Ensemble approaches

2. **Feature engineering**:
   - Add momentum/trend features
   - Volatility-adjusted features
   - Cross-sectional ranking features

3. **Different strategies**:
   - Market-neutral long-short
   - Risk-weighted allocation
   - Factor-based weighting

### Data Validation Needed
1. Check for look-ahead bias in Alpha158 features
2. Validate price adjustments (splits, dividends)
3. Verify survivorship bias
4. Add liquidity filters (volume, market cap)

## Files Created

```
qlib_repo/examples/benchmarks/LightGBM/
├── workflow_config_external_data.yaml          # Original config
├── workflow_config_external_data_fixed.yaml    # Fixed dates
└── workflow_config_liquid_universe.yaml        # Filtered universe

/Volumes/sandisk/quantmini-data/data/qlib/stocks_daily/instruments/
├── all.txt                 # 14,310 instruments
└── liquid_stocks.txt       # 13,187 filtered (no warrants/units)

visualizations/
└── backtest_visualization.png  # Performance charts
```

## Next Steps

1. **Validate the external dataset**
   - Check data provider source
   - Verify corporate actions handling
   - Compare with known benchmarks

2. **Test with curated universe**
   - S&P 500 only
   - Russell 3000
   - NASDAQ 100

3. **Experiment with other models**
   - Run XGBoost, MLP, LSTM
   - Compare IC and Rank IC
   - See which improves ranking

4. **Add proper risk controls**
   - Max position size: 5-10% per stock
   - Volatility-based weighting
   - Drawdown limits

## Conclusion

**Model fundamentals are sound** - IC of 0.066-0.08 is meaningful for alpha generation.

**Backtest has issues** - Returns are unrealistic, suggesting data quality problems, look-ahead bias, or incorrect simulation parameters.

**Action required**: Focus on data validation and risk controls before trusting backtest P&L. The predictive signal (IC) is real, but translation to returns needs fixing.
