# Options Code - Quick Reference

## Core Files

| File | Purpose | Key Class/Functions |
|------|---------|-------------------|
| `quantlab/analysis/options_analyzer.py` | Main options analysis | `OptionsAnalyzer.analyze_itm_calls()` |
| `quantlab/analysis/greeks_calculator.py` | Greeks calculations | `BlackScholesGreeks`, `calculate_advanced_greeks()` |
| `quantlab/models/ticker_data.py` | Data models | `OptionContract` dataclass |
| `quantlab/data/data_manager.py` | Data routing | `DataManager.get_options_chain()` |
| `scripts/analysis/multi_source_options_analysis.py` | End-to-end analysis | `MultiSourceOptionsAnalysis` class |

## Greeks At A Glance

### First-Order Greeks
- **Delta** (Δ): Directional exposure. Range: 0-1 (calls), -1-0 (puts)
- **Gamma** (Γ): Delta sensitivity. Higher = faster delta changes
- **Theta** (Θ): Time decay. Negative = losing value daily
- **Vega** (ν): Volatility sensitivity. Per 1% IV change
- **Rho** (ρ): Interest rate sensitivity (minor for stocks)

### Advanced Greeks
- **Vanna**: How delta changes when IV changes. Important for vol traders
- **Charm**: How delta changes daily (delta decay). Critical for short-term
- **Vomma**: How vega changes when IV changes. Positive = good on vol moves

## Key Data Structures

### OptionContract
```python
# Most important fields:
contract_ticker: str        # "AAPL240119C00175000"
underlying_ticker: str      # "AAPL"
strike_price: float         # 175.00
expiration_date: date       # 2024-01-19
option_type: str            # "call" or "put"

# Greeks (all Optional[float]):
delta, gamma, theta, vega, rho  # First-order
vanna, charm, vomma             # Advanced

# Metrics:
implied_volatility: float
open_interest: int
itm_percentage: float
```

## How to Use

### 1. Get Options with Greeks
```python
from quantlab.data.data_manager import DataManager

dm = DataManager(config, db, parquet)
options = dm.get_options_chain("AAPL", min_itm_pct=5.0, max_itm_pct=20.0)

for opt in options:
    print(f"{opt.contract_ticker}: Delta={opt.delta}, Vanna={opt.vanna}")
```

### 2. Analyze & Rank Options
```python
from quantlab.analysis.options_analyzer import OptionsAnalyzer

analyzer = OptionsAnalyzer(dm)
top_calls = analyzer.analyze_itm_calls("AAPL", top_n=10)

for rec in top_calls:
    print(f"Score: {rec['score']}")
    print(f"Analysis: {rec['analysis']}")
```

### 3. Calculate Greeks Directly
```python
from quantlab.analysis.greeks_calculator import calculate_advanced_greeks

greeks = calculate_advanced_greeks(
    stock_price=175.50,
    strike_price=175.00,
    days_to_expiry=30,
    risk_free_rate=0.045,
    implied_volatility=0.30,
    option_type='call'
)

print(f"Delta: {greeks['delta']}")
print(f"Vanna: {greeks['vanna']}")
```

## Important Constants

| Parameter | Default | Notes |
|-----------|---------|-------|
| `min_itm_pct` | 5.0 | Minimum ITM % for filtering |
| `max_itm_pct` | 20.0 | Maximum ITM % for filtering |
| `min_open_interest` | 100 | Liquidity filter |
| `risk_free_rate` | 0.045 | 3-month Treasury (updated daily) |
| `rsi_oversold` | 30 | Entry signal for mean reversion |
| `rsi_overbought` | 70 | Exit signal for mean reversion |

## Scoring Weights (OptionsAnalyzer)

For ITM calls (max ~100 points):
- Delta (0.7-0.9 range): +30 pts
- Theta (low abs value): +25 pts  
- Liquidity (OI > 1000): +20 pts
- Charm (positive): +15 pts
- Vanna/Vomma: +10 pts

## Data Sources

| Source | Used For | Rate Limit |
|--------|----------|------------|
| **Polygon** | Options chains, Greeks | 5 req/min (free) |
| **Alpha Vantage** | Treasury rates, sentiment | 5 req/min (free) |
| **yfinance** | VIX, analyst data | No limit |
| **Parquet** | Historical daily/minute data | Local (fast) |

## Multi-Source Analysis Flow

```
User Request
    ↓
Polygon → Get options chains, current price
    ↓
Alpha Vantage → Get Treasury rate, news sentiment
    ↓
yfinance → Get VIX, holdings, recommendations
    ↓
Black-Scholes → Calculate Greeks with REAL treasury rate
    ↓
Score & Rank → Filter 5-20% ITM, score by criteria
    ↓
Generate Report → JSON + Markdown with full analysis
```

## Common Patterns

### Pattern 1: Find Best ITM Calls
```python
analyzer = OptionsAnalyzer(dm)
recommendations = analyzer.analyze_itm_calls(
    ticker="AAPL",
    min_itm_pct=5.0,
    max_itm_pct=20.0,
    top_n=5
)
```

### Pattern 2: Check Greeks for Position Sizing
```python
for opt in options:
    # High delta = more directional exposure
    position_size = 100 / opt.delta if opt.delta else 0
    
    # Check theta decay risk
    daily_loss = abs(opt.theta) * position_size
```

### Pattern 3: Volatility Environment Context
```python
vix_data = dm.get_vix()
# If VIX > 20: Expensive options, favor selling strategies
# If VIX < 15: Cheap options, favor buying strategies
```

## CLI Commands (Available)
```bash
# Run multi-source analysis
python scripts/analysis/multi_source_options_analysis.py --ticker AAPL

# Direct Greeks calculation
python scripts/analysis/advanced_greeks_calculator.py
```

## CLI Commands (NOT Yet Available)
```bash
# Would be nice to have:
quantlab options analyze AAPL
quantlab options chain AAPL --type call --itm 5-20
quantlab options minute AAPL --start "2025-10-15 09:30" --limit 10000
```

## Troubleshooting

**Problem:** No Greeks data returned
- Solution: Check if Polygon API key is valid in .env
- Fallback: System will auto-calculate using Black-Scholes

**Problem:** Treasury rate shows as 4.5% (default)
- Solution: Check Alpha Vantage API key
- Note: Affects Greeks accuracy by ~1-2%

**Problem:** Minute data query too slow
- Solution: Add stronger filters (strike range, time window)
- Tip: 1 ticker × 1 hour × ATM ±$5 = ~30K rows (manageable)

## Performance Tips

1. **Always specify ITM range** (don't fetch all options)
2. **Use open_interest filter** (min 100+ for liquidity)
3. **Cache results** (15-min TTL for real-time, 1h for daily)
4. **Batch API calls** (Polygon rate limit: 5/min)

## See Also

- `docs/OPTIONS_ANALYSIS_REVIEW.md` - Comprehensive review
- `docs/OPTIONS_MINUTE_IMPLEMENTATION.md` - Future minute data support
- `quantlab/backtest/strategies/mean_reversion_strategy.py` - Strategy pattern
