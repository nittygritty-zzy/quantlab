# Options Greeks Integration Plan

**Goal**: Add Greeks calculations (Delta, Gamma, Theta, Vega, Rho) to the options strategies module for comprehensive risk analysis.

## Overview

Greeks measure the sensitivity of option prices to various factors. Integrating them will provide:
- **Position-level Greeks**: Greeks for each option leg
- **Portfolio-level Greeks**: Aggregate Greeks for entire strategy
- **Risk visualization**: Understand how strategies behave under different conditions
- **Hedging insights**: Know what adjustments are needed

## Phase 1: Core Greeks Calculator (Week 1)

### 1.1 Implement Black-Scholes Model

**File**: `quantlab/analysis/greeks_calculator.py`

**Components**:
```python
class GreeksCalculator:
    """Calculate option Greeks using Black-Scholes model"""

    @staticmethod
    def calculate_greeks(
        spot_price: float,
        strike: float,
        time_to_expiry: float,  # years
        volatility: float,       # implied vol
        risk_free_rate: float,
        option_type: str,        # 'call' or 'put'
        dividend_yield: float = 0.0
    ) -> Dict[str, float]:
        """
        Returns: {
            'delta': float,
            'gamma': float,
            'theta': float,
            'vega': float,
            'rho': float,
            'price': float  # theoretical price
        }
        """
```

**Implementation Details**:
- Use `scipy.stats.norm` for cumulative distribution
- Calculate d1 and d2 from Black-Scholes formula
- Implement first-order Greeks (delta, vega, theta, rho)
- Implement second-order Greek (gamma)
- Handle edge cases (zero time to expiry, extreme strikes)

**Formulas**:
```
d1 = [ln(S/K) + (r - q + σ²/2)T] / (σ√T)
d2 = d1 - σ√T

Call Delta = N(d1)
Put Delta = N(d1) - 1

Gamma = N'(d1) / (S·σ√T)
Theta = -[S·N'(d1)·σ / (2√T)] - r·K·e^(-rT)·N(d2)  [call]
Vega = S·√T·N'(d1)
Rho = K·T·e^(-rT)·N(d2)  [call]
```

**Dependencies**:
```python
import numpy as np
from scipy.stats import norm
from typing import Dict
from datetime import date, datetime
```

### 1.2 Add Greeks to OptionLeg

**File**: `quantlab/analysis/options_strategies.py`

**Modifications**:
```python
from .greeks_calculator import GreeksCalculator

@dataclass
class OptionLeg:
    # Existing fields...

    # New optional fields for Greeks
    implied_volatility: Optional[float] = None
    risk_free_rate: Optional[float] = 0.05
    dividend_yield: Optional[float] = 0.0

    def calculate_greeks(self, spot_price: float) -> Dict[str, float]:
        """Calculate Greeks for this leg"""
        if not self.implied_volatility or not self.expiration:
            return None

        time_to_expiry = (self.expiration - date.today()).days / 365.0

        greeks = GreeksCalculator.calculate_greeks(
            spot_price=spot_price,
            strike=self.strike,
            time_to_expiry=time_to_expiry,
            volatility=self.implied_volatility,
            risk_free_rate=self.risk_free_rate,
            option_type=self.option_type.value,
            dividend_yield=self.dividend_yield
        )

        # Adjust for position type (short vs long)
        if self.position_type == PositionType.SHORT:
            greeks = {k: -v for k, v in greeks.items()}

        # Adjust for quantity
        greeks = {k: v * self.quantity for k, v in greeks.items()}

        return greeks
```

### 1.3 Add Aggregate Greeks to Strategy

**Modifications to OptionsStrategy**:
```python
class OptionsStrategy:
    # Existing code...

    def portfolio_greeks(self) -> Dict[str, float]:
        """Calculate aggregate Greeks for entire strategy"""
        total_greeks = {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0,
            'theoretical_value': 0.0
        }

        for leg in self.legs:
            leg_greeks = leg.calculate_greeks(self.current_stock_price)
            if leg_greeks:
                for greek in total_greeks:
                    if greek in leg_greeks:
                        total_greeks[greek] += leg_greeks[greek]

        # Add stock position delta (if any)
        if self.stock_position != 0:
            total_greeks['delta'] += self.stock_position / 100

        return total_greeks

    def delta_adjusted_exposure(self) -> float:
        """Calculate delta-adjusted notional exposure"""
        greeks = self.portfolio_greeks()
        return greeks['delta'] * self.current_stock_price * 100
```

### 1.4 Update StrategyBuilder

**Add IV parameter to all builders**:
```python
@staticmethod
def bull_call_spread(
    stock_price: float,
    long_strike: float,
    short_strike: float,
    long_premium: float,
    short_premium: float,
    quantity: int,
    expiration: date,
    ticker: str = "UNKNOWN",
    # New parameters
    implied_volatility: Optional[float] = None,
    risk_free_rate: float = 0.05
) -> OptionsStrategy:
    legs = [
        OptionLeg(
            ...,
            implied_volatility=implied_volatility,
            risk_free_rate=risk_free_rate
        ),
        ...
    ]
```

## Phase 2: CLI Integration (Week 2)

### 2.1 Update Strategy Build Command

**File**: `quantlab/cli/strategy.py`

**Add options**:
```python
@click.option('--iv', type=float, help='Implied volatility (e.g., 0.25 for 25%)')
@click.option('--risk-free-rate', type=float, default=0.05, help='Risk-free rate (default: 0.05)')
@click.option('--dividend-yield', type=float, default=0.0, help='Dividend yield (default: 0.0)')
```

**Update output**:
```python
# After displaying risk metrics, add Greeks section
if any(leg.implied_volatility for leg in strat.legs):
    click.echo("\n📉 Portfolio Greeks:")
    greeks = strat.portfolio_greeks()

    click.echo(f"  Delta: {greeks['delta']:.4f} (${strat.delta_adjusted_exposure():.2f} exposure)")
    click.echo(f"  Gamma: {greeks['gamma']:.4f}")
    click.echo(f"  Theta: {greeks['theta']:.2f} (per day)")
    click.echo(f"  Vega: {greeks['vega']:.2f} (per 1% vol move)")
    click.echo(f"  Rho: {greeks['rho']:.2f} (per 1% rate move)")
```

### 2.2 Add Greeks Analysis Command

**New command**:
```python
@strategy.command('greeks')
@click.argument('strategy_file', type=click.Path(exists=True))
@click.option('--spot-prices', help='Comma-separated spot prices to analyze')
@click.option('--vol-range', help='Volatility range to analyze (e.g., 0.15,0.35)')
@click.option('--days-forward', type=int, default=30, help='Days forward to project')
def analyze_greeks(strategy_file, spot_prices, vol_range, days_forward):
    """
    Analyze Greeks across different scenarios

    Example:
      quantlab strategy greeks results/my_strategy.json \
        --spot-prices 450,455,460,465,470 \
        --vol-range 0.15,0.35
    """
    # Create Greeks sensitivity table
    # Show how Greeks change with spot price
    # Show how Greeks change with volatility
    # Show time decay projection
```

### 2.3 Add Greeks Heatmap Command

```python
@strategy.command('heatmap')
@click.argument('strategy_file', type=click.Path(exists=True))
@click.option('--greek', type=click.Choice(['delta', 'gamma', 'theta', 'vega']),
              default='delta', help='Greek to visualize')
@click.option('--spot-range', help='Spot price range (e.g., 440,460)')
@click.option('--vol-range', help='Volatility range (e.g., 0.15,0.35)')
def greeks_heatmap(strategy_file, greek, spot_range, vol_range):
    """
    Generate ASCII heatmap of Greeks

    Example:
      quantlab strategy heatmap results/iron_condor.json \
        --greek delta --spot-range 440,460 --vol-range 0.15,0.35
    """
```

## Phase 3: Advanced Features (Week 3)

### 3.1 Greeks-Based Strategy Scoring

**File**: `quantlab/analysis/strategy_scorer.py`

```python
class StrategyScorer:
    """Score strategies based on Greeks profile"""

    @staticmethod
    def calculate_score(strategy: OptionsStrategy,
                       objectives: Dict[str, str]) -> Dict[str, float]:
        """
        objectives = {
            'delta': 'neutral',  # or 'positive', 'negative'
            'theta': 'positive', # want positive time decay
            'vega': 'short',     # want short volatility
            'gamma': 'positive'  # want positive gamma
        }

        Returns score breakdown
        """
```

### 3.2 Auto-Adjustment Recommendations

```python
class HedgingAdvisor:
    """Recommend adjustments to achieve target Greeks"""

    @staticmethod
    def suggest_adjustments(
        strategy: OptionsStrategy,
        target_delta: float = 0.0,
        target_gamma: float = None
    ) -> List[Dict]:
        """
        Returns list of adjustment suggestions:
        [
            {
                'action': 'Buy 50 shares',
                'new_delta': 0.05,
                'cost': 2500
            },
            {
                'action': 'Buy 1x 450 Put @ $3.00',
                'new_delta': -0.02,
                'cost': 300
            }
        ]
        """
```

### 3.3 Greeks Time Series

**Track Greeks evolution**:
```python
class GreeksTracker:
    """Track how Greeks change over time"""

    def track_daily_greeks(self, strategy: OptionsStrategy,
                          days: int = 30) -> pd.DataFrame:
        """
        Simulate how Greeks evolve over time

        Returns DataFrame with columns:
        - day: days from today
        - delta, gamma, theta, vega, rho
        - pnl: estimated P&L at that point
        """
```

## Phase 4: Visualization (Week 4)

### 4.1 Greeks Plots

**File**: `quantlab/analysis/greeks_plotter.py`

```python
class GreeksPlotter:
    """Generate Greeks visualization plots"""

    @staticmethod
    def plot_greeks_vs_spot(strategy, spot_range):
        """Plot all Greeks vs spot price"""

    @staticmethod
    def plot_theta_decay(strategy, days=30):
        """Plot time decay over time"""

    @staticmethod
    def plot_delta_gamma_together(strategy):
        """Overlay delta and gamma"""

    @staticmethod
    def plot_pnl_heatmap(strategy, spot_range, vol_range):
        """2D heatmap of P&L vs spot and vol"""
```

**Export options**:
- Save to PNG/SVG
- Interactive HTML (plotly)
- ASCII art for CLI

### 4.2 Greeks Dashboard

**CLI command**:
```bash
quantlab strategy dashboard results/my_strategy.json --open-browser
```

Creates interactive HTML dashboard with:
- Current Greeks summary
- Greeks vs spot price charts
- Time decay projection
- Volatility sensitivity
- Adjustment recommendations

## Phase 5: Testing & Documentation (Week 5)

### 5.1 Unit Tests

**File**: `tests/analysis/test_greeks_calculator.py`

Tests for:
- Black-Scholes implementation accuracy
- Greeks calculations at different strikes
- ATM, ITM, OTM scenarios
- Time decay behavior
- Volatility sensitivity
- Edge cases (0 days to expiry, extreme vol)

**File**: `tests/analysis/test_strategy_greeks.py`

Tests for:
- Single-leg Greeks
- Multi-leg aggregate Greeks
- Greeks with stock position
- Greeks time series
- Hedging recommendations

### 5.2 Integration Tests

**File**: `tests/integration/test_greeks_cli.py`

Tests for:
- Build strategy with IV
- Greeks analysis command
- Greeks heatmap generation
- Greeks dashboard creation

### 5.3 Documentation

**Update existing docs**:
- `docs/OPTIONS_STRATEGIES.md` - Add Greeks section
- Add Greeks interpretation guide
- Add examples with IV parameter

**New documentation**:
- `docs/OPTIONS_GREEKS_GUIDE.md` - Comprehensive Greeks guide
- Greeks interpretation for each strategy type
- When to adjust based on Greeks
- Common Greeks profiles

## Implementation Checklist

### Phase 1: Core (Priority: High)
- [ ] Implement `GreeksCalculator` class
- [ ] Add unit tests for Black-Scholes calculations
- [ ] Verify Greeks accuracy against known values
- [ ] Add `implied_volatility` to `OptionLeg`
- [ ] Implement `calculate_greeks()` in `OptionLeg`
- [ ] Implement `portfolio_greeks()` in `OptionsStrategy`
- [ ] Add Greeks to all `StrategyBuilder` methods
- [ ] Test aggregate Greeks for multi-leg strategies

### Phase 2: CLI (Priority: High)
- [ ] Add `--iv` option to `strategy build` command
- [ ] Display Greeks in build output
- [ ] Create `strategy greeks` analysis command
- [ ] Add Greeks to `strategy analyze` command
- [ ] Update JSON serialization to include Greeks
- [ ] Test CLI with various strategies

### Phase 3: Advanced (Priority: Medium)
- [ ] Implement `StrategyScorer` class
- [ ] Implement `HedgingAdvisor` class
- [ ] Add `GreeksTracker` for time series
- [ ] Create Greeks sensitivity analysis
- [ ] Add auto-hedging recommendations
- [ ] Test advanced features

### Phase 4: Visualization (Priority: Medium)
- [ ] Implement `GreeksPlotter` class
- [ ] Add matplotlib backend
- [ ] Add ASCII art backend for CLI
- [ ] Create interactive dashboard
- [ ] Add export functionality
- [ ] Test plotting on various strategies

### Phase 5: Polish (Priority: Low)
- [ ] Write comprehensive tests (target: 50+ tests)
- [ ] Write Greeks documentation
- [ ] Add examples to docs
- [ ] Create tutorial notebook
- [ ] Performance optimization
- [ ] Add caching for repeated calculations

## Example Usage (After Implementation)

### Basic Greeks Calculation
```bash
# Build strategy with implied volatility
quantlab strategy build bull_call_spread \
  --ticker NVDA --stock-price 485 --strikes 480,490 \
  --premiums 12.50,7.50 --expiration 2025-12-19 \
  --iv 0.35 --risk-free-rate 0.05 \
  --output results/nvda_with_greeks.json
```

Output would include:
```
📉 Portfolio Greeks:
  Delta: 0.5234 ($25,350 exposure)
  Gamma: 0.0089
  Theta: -12.45 (per day)
  Vega: 18.32 (per 1% vol move)
  Rho: 4.21 (per 1% rate move)
```

### Greeks Analysis
```bash
quantlab strategy greeks results/nvda_with_greeks.json \
  --spot-prices 470,475,480,485,490,495,500 \
  --vol-range 0.25,0.45
```

### Greeks Heatmap
```bash
quantlab strategy heatmap results/iron_condor.json \
  --greek delta --spot-range 440,460 --vol-range 0.15,0.35
```

## Technical Considerations

### Accuracy Requirements
- Greeks should match industry-standard calculators within 1%
- Use double precision for all calculations
- Handle edge cases gracefully (near expiry, extreme vol)

### Performance
- Greeks calculations should be <10ms per leg
- Cache Greeks for same parameters
- Support batch calculations for sensitivity analysis

### Data Sources for IV
- For live trading: Use real-time IV from options chain
- For backtesting: Use historical IV data
- For analysis: Allow manual input or use VIX-based estimates

### Extensibility
- Support alternate pricing models (e.g., Binomial, Monte Carlo)
- Allow custom Greeks calculation plugins
- Support exotic options in future

## Success Metrics

### Functionality
- ✅ All 5 Greeks calculated accurately
- ✅ Aggregate Greeks for complex strategies
- ✅ Greeks displayed in CLI
- ✅ Sensitivity analysis working

### Quality
- ✅ 95%+ test coverage
- ✅ Documented with examples
- ✅ Performance <10ms per calculation
- ✅ Accurate within 1% of industry standards

### Usability
- ✅ Easy to add IV to strategies
- ✅ Clear Greeks interpretation
- ✅ Useful adjustment recommendations
- ✅ Helpful visualizations

## Dependencies

**New Python Packages**:
```toml
dependencies = [
    # Existing...
    "scipy>=1.10.0",  # Already installed
    "matplotlib>=3.7.0",  # For plotting
    "plotly>=5.14.0",  # For interactive plots
]
```

**No breaking changes** to existing code - Greeks are optional enhancements.

## Timeline Estimate

- **Phase 1** (Core): 5-7 days
- **Phase 2** (CLI): 3-4 days
- **Phase 3** (Advanced): 4-5 days
- **Phase 4** (Visualization): 3-4 days
- **Phase 5** (Testing/Docs): 3-4 days

**Total**: 3-4 weeks for complete implementation

## Next Steps

1. Start with Phase 1 implementation of `GreeksCalculator`
2. Validate accuracy against known Black-Scholes values
3. Integrate into `OptionLeg` and `OptionsStrategy`
4. Add CLI support for IV parameter
5. Iterate based on testing and feedback

---

**Ready to proceed?** The plan is modular - we can implement phase by phase and have working features at each step.
