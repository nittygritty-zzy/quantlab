# Advanced Greeks Integration Plan for Options Strategies

**Goal**: Integrate advanced Greeks (Vanna, Charm, Vomma) from the existing calculator into the options strategies module for comprehensive risk analysis.

## Current State

### What's Already Available

**Polygon API Provides**:
- Delta, Gamma, Theta, Vega, Rho (first-order Greeks)
- Implied Volatility
- Market data (bid, ask, last, volume, OI)

**Existing Advanced Greeks Calculator** (`quantlab/analysis/greeks_calculator.py`):
- ✅ **Vanna**: ∂Delta/∂σ (delta sensitivity to volatility changes)
- ✅ **Charm**: ∂Delta/∂t (delta decay over time)
- ✅ **Vomma**: ∂Vega/∂σ (vega sensitivity to volatility changes)
- ✅ Black-Scholes implementation complete

**OptionContract Model** (`quantlab/models/ticker_data.py`):
```python
@dataclass
class OptionContract:
    # Basic Greeks from Polygon
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None

    # Advanced Greeks (currently unused)
    vanna: Optional[float] = None
    charm: Optional[float] = None
    vomma: Optional[float] = None

    implied_volatility: Optional[float] = None
```

## What Advanced Greeks Tell Us

### Vanna (∂Delta/∂σ)
**What it measures**: How delta changes when volatility changes

**Use cases**:
- **Volatility hedging**: High vanna means delta will change significantly with IV moves
- **Pre-earnings**: Vanna shows how position will shift if IV spikes
- **Risk management**: Understand hidden exposure to vol changes

**Example**: Long call with vanna = 0.05
- If IV increases 10% (e.g., 30% → 33%), delta increases by ~0.5
- Position becomes more directional with rising volatility

### Charm (∂Delta/∂t)
**What it measures**: How delta decays over time

**Use cases**:
- **Delta forecasting**: Predict tomorrow's delta without price move
- **Gamma hedging**: High charm means gamma position shifts quickly
- **Rolling decisions**: Know when delta will drift out of range

**Example**: Short ATM call with charm = -0.02
- Delta decreases 0.02 per day
- In 10 days, delta changes by -0.20 (even if stock flat)

### Vomma (∂Vega/∂σ)
**What it measures**: How vega changes when volatility changes

**Use cases**:
- **Vega hedging**: Positive vomma means long vol gets longer with rising IV
- **Vol of vol trading**: Profit from volatility regime shifts
- **Convexity analysis**: Understand non-linear vega exposure

**Example**: Long straddle with vomma = 0.10
- If IV increases 10%, vega increases by 1.0
- Position becomes more sensitive to further vol moves

## Integration Plan

### Phase 1: Core Integration (Week 1)

#### 1.1 Update OptionLeg Class

**File**: `quantlab/analysis/options_strategies.py`

**Add advanced Greeks calculation**:
```python
from ..analysis.greeks_calculator import calculate_advanced_greeks

@dataclass
class OptionLeg:
    # Existing fields...

    # Advanced Greeks (optional, calculated fields)
    vanna: Optional[float] = None
    charm: Optional[float] = None
    vomma: Optional[float] = None

    def calculate_advanced_greeks(
        self,
        stock_price: float,
        risk_free_rate: float = 0.05
    ) -> Dict[str, float]:
        """
        Calculate advanced Greeks using existing calculator

        Requires: implied_volatility and expiration to be set
        """
        if not self.implied_volatility or not self.expiration:
            logger.warning("Cannot calculate advanced Greeks without IV and expiration")
            return {}

        days_to_expiry = (self.expiration - date.today()).days
        if days_to_expiry <= 0:
            return {}

        # Use existing advanced Greeks calculator
        greeks = calculate_advanced_greeks(
            stock_price=stock_price,
            strike_price=self.strike,
            days_to_expiry=days_to_expiry,
            risk_free_rate=risk_free_rate,
            implied_volatility=self.implied_volatility,
            option_type=self.option_type.value
        )

        # Adjust for position type (short reverses signs)
        multiplier = -1 if self.position_type == PositionType.SHORT else 1

        # Adjust for quantity
        adjusted_greeks = {
            k: v * multiplier * self.quantity
            for k, v in greeks.items()
        }

        # Store in leg
        if 'vanna' in adjusted_greeks:
            self.vanna = adjusted_greeks['vanna']
        if 'charm' in adjusted_greeks:
            self.charm = adjusted_greeks['charm']
        if 'vomma' in adjusted_greeks:
            self.vomma = adjusted_greeks['vomma']

        return adjusted_greeks
```

#### 1.2 Add Portfolio Advanced Greeks

**Extend OptionsStrategy class**:
```python
class OptionsStrategy:
    # Existing code...

    def advanced_greeks(self) -> Dict[str, float]:
        """
        Calculate aggregate advanced Greeks for entire strategy

        Returns:
            {
                'vanna': total vanna,
                'charm': total charm,
                'vomma': total vomma,
                'delta': total delta (from basic greeks),
                'gamma': total gamma,
                'theta': total theta,
                'vega': total vega
            }
        """
        totals = {
            'vanna': 0.0,
            'charm': 0.0,
            'vomma': 0.0,
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0
        }

        for leg in self.legs:
            # Calculate advanced Greeks
            advanced = leg.calculate_advanced_greeks(
                self.current_stock_price
            )

            for greek in totals:
                if greek in advanced:
                    totals[greek] += advanced[greek]

        # Add stock position delta (100 shares = 1.0 delta)
        if self.stock_position != 0:
            totals['delta'] += self.stock_position / 100

        return totals

    def greeks_projection(self, days_forward: int = 30) -> Dict[int, Dict[str, float]]:
        """
        Project how Greeks will evolve over time using charm

        Returns: {day: {greek: value}}
        """
        current_greeks = self.advanced_greeks()
        projection = {}

        for day in range(days_forward + 1):
            # Start with current values
            projected = current_greeks.copy()

            # Apply charm (delta decay)
            if 'charm' in current_greeks and 'delta' in current_greeks:
                projected['delta'] = current_greeks['delta'] + current_greeks['charm'] * day

            projection[day] = projected

        return projection

    def volatility_sensitivity(self, vol_changes: List[float]) -> Dict[float, Dict[str, float]]:
        """
        Analyze how position changes with volatility moves using vanna/vomma

        Args:
            vol_changes: List of vol changes in percentage points (e.g., [-5, 0, 5, 10])

        Returns: {vol_change: {greek: new_value}}
        """
        current_greeks = self.advanced_greeks()
        sensitivity = {}

        for vol_change in vol_changes:
            vol_pct = vol_change / 100  # Convert to decimal

            projected = {
                'delta': current_greeks['delta'] + current_greeks['vanna'] * vol_change,
                'vega': current_greeks['vega'] + current_greeks['vomma'] * vol_change,
                'gamma': current_greeks['gamma'],  # Simplified
                'theta': current_greeks['theta']   # Simplified
            }

            sensitivity[vol_change] = projected

        return sensitivity
```

#### 1.3 Update StrategyBuilder

**Add IV and risk-free rate to all builders**:
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
    # Add these parameters
    implied_volatility: Optional[float] = None,
    risk_free_rate: float = 0.05
) -> OptionsStrategy:
    """
    Bull Call Spread with optional advanced Greeks

    Args:
        implied_volatility: IV as decimal (e.g., 0.35 for 35%)
        risk_free_rate: Risk-free rate as decimal (default: 0.05)
    """
    legs = [
        OptionLeg(
            OptionType.CALL, PositionType.LONG, long_strike,
            long_premium, quantity, expiration,
            implied_volatility=implied_volatility
        ),
        OptionLeg(
            OptionType.CALL, PositionType.SHORT, short_strike,
            short_premium, quantity, expiration,
            implied_volatility=implied_volatility
        )
    ]

    return OptionsStrategy(
        name=f"Bull Call Spread on {ticker}",
        strategy_type=StrategyType.BULL_CALL_SPREAD,
        legs=legs,
        current_stock_price=stock_price,
        metadata={
            "ticker": ticker,
            "implied_volatility": implied_volatility,
            "risk_free_rate": risk_free_rate,
            "spread_width": short_strike - long_strike
        }
    )
```

### Phase 2: CLI Integration (Week 1-2)

#### 2.1 Update `strategy build` Command

**File**: `quantlab/cli/strategy.py`

**Add options**:
```python
@click.option('--iv', type=float, help='Implied volatility (decimal, e.g., 0.35 for 35%)')
@click.option('--risk-free-rate', type=float, default=0.05, help='Risk-free rate (default: 0.05)')
```

**Display advanced Greeks**:
```python
def build_strategy(..., iv, risk_free_rate):
    # ... build strategy ...

    # Display advanced Greeks if IV provided
    if iv:
        click.echo("\n📊 Advanced Greeks Analysis:")

        greeks = strat.advanced_greeks()

        click.echo("\nFirst-Order Greeks:")
        click.echo(f"  Delta: {greeks['delta']:.4f}")
        click.echo(f"  Gamma: {greeks['gamma']:.6f}")
        click.echo(f"  Theta: {greeks['theta']:.2f} (per day)")
        click.echo(f"  Vega: {greeks['vega']:.2f} (per 1% vol)")

        click.echo("\nSecond-Order Greeks (Advanced):")
        click.echo(f"  Vanna: {greeks['vanna']:.6f} (∂Delta/∂σ)")
        click.echo(f"  Charm: {greeks['charm']:.6f} (∂Delta/∂t per day)")
        click.echo(f"  Vomma: {greeks['vomma']:.6f} (∂Vega/∂σ)")

        # Interpretation
        click.echo("\n💡 Greeks Interpretation:")

        # Vanna interpretation
        if abs(greeks['vanna']) > 0.01:
            direction = "increase" if greeks['vanna'] > 0 else "decrease"
            click.echo(f"  • Vanna: Delta will {direction} if volatility rises")

        # Charm interpretation
        if abs(greeks['charm']) > 0.01:
            direction = "increase" if greeks['charm'] > 0 else "decrease"
            click.echo(f"  • Charm: Delta will {direction} by {abs(greeks['charm']):.4f} per day")

        # Vomma interpretation
        if abs(greeks['vomma']) > 0.01:
            direction = "increase" if greeks['vomma'] > 0 else "decrease"
            click.echo(f"  • Vomma: Vega will {direction} if volatility rises")
```

#### 2.2 New Command: `strategy greeks-forecast`

```python
@strategy.command('greeks-forecast')
@click.argument('strategy_file', type=click.Path(exists=True))
@click.option('--days', type=int, default=30, help='Days to forecast (default: 30)')
@click.option('--vol-scenarios', help='Vol scenarios to test (e.g., -5,0,5,10)')
def greeks_forecast(strategy_file, days, vol_scenarios):
    """
    Forecast Greeks evolution using advanced Greeks

    Examples:
      # Time decay forecast
      quantlab strategy greeks-forecast results/iron_condor.json --days 30

      # Volatility scenarios
      quantlab strategy greeks-forecast results/iron_condor.json \
        --vol-scenarios -10,-5,0,5,10
    """
    # Load strategy
    with open(strategy_file) as f:
        data = json.load(f)

    # Reconstruct strategy (need helper method)
    strategy = reconstruct_strategy(data)

    if not strategy:
        click.echo("❌ Cannot reconstruct strategy from file")
        return

    # Time decay forecast
    if days:
        click.echo(f"\n📈 Greeks Forecast ({days} days)")
        projection = strategy.greeks_projection(days)

        # Display table
        table_data = []
        for day in [0, 7, 14, 21, 30]:
            if day in projection:
                p = projection[day]
                table_data.append([
                    day,
                    f"{p['delta']:.4f}",
                    f"{p['gamma']:.6f}",
                    f"{p['theta']:.2f}",
                    f"{p['vega']:.2f}"
                ])

        click.echo(tabulate(
            table_data,
            headers=['Day', 'Delta', 'Gamma', 'Theta', 'Vega'],
            tablefmt='simple'
        ))

    # Volatility scenarios
    if vol_scenarios:
        scenarios = [float(x) for x in vol_scenarios.split(',')]
        click.echo(f"\n📊 Volatility Sensitivity Analysis")

        sensitivity = strategy.volatility_sensitivity(scenarios)

        table_data = []
        for vol_change in sorted(scenarios):
            s = sensitivity[vol_change]
            table_data.append([
                f"{vol_change:+.0f}%",
                f"{s['delta']:.4f}",
                f"{s['vega']:.2f}",
                "Better" if s['delta'] > strategy.advanced_greeks()['delta'] else "Worse"
            ])

        click.echo(tabulate(
            table_data,
            headers=['Vol Change', 'New Delta', 'New Vega', 'Position'],
            tablefmt='simple'
        ))
```

#### 2.3 New Command: `strategy greeks-report`

```python
@strategy.command('greeks-report')
@click.argument('strategy_file', type=click.Path(exists=True))
@click.option('--detailed', is_flag=True, help='Show per-leg breakdown')
def greeks_report(strategy_file, detailed):
    """
    Generate comprehensive Greeks report

    Example:
      quantlab strategy greeks-report results/my_strategy.json --detailed
    """
    # Load and reconstruct strategy
    strategy = load_strategy(strategy_file)

    click.echo("\n" + "="*60)
    click.echo(f"📊 ADVANCED GREEKS REPORT: {strategy.name}")
    click.echo("="*60)

    greeks = strategy.advanced_greeks()

    # Summary
    click.echo("\n🎯 PORTFOLIO GREEKS")
    click.echo(f"  Delta: {greeks['delta']:.4f} (${greeks['delta'] * strategy.current_stock_price * 100:,.0f} exposure)")
    click.echo(f"  Gamma: {greeks['gamma']:.6f}")
    click.echo(f"  Theta: {greeks['theta']:.2f}/day (${greeks['theta'] * 100:.0f}/day)")
    click.echo(f"  Vega:  {greeks['vega']:.2f} (${greeks['vega'] * 100:.0f} per 1% vol)")

    click.echo("\n🔬 ADVANCED GREEKS")
    click.echo(f"  Vanna: {greeks['vanna']:.6f}")
    click.echo(f"  Charm: {greeks['charm']:.6f}")
    click.echo(f"  Vomma: {greeks['vomma']:.6f}")

    # Risk Assessment
    click.echo("\n⚠️  RISK ASSESSMENT")

    # Delta risk
    if abs(greeks['delta']) > 0.5:
        click.echo("  ⚠️  HIGH DIRECTIONAL RISK - Position is delta-heavy")
    elif abs(greeks['delta']) < 0.1:
        click.echo("  ✅ LOW DIRECTIONAL RISK - Position is delta-neutral")

    # Vanna risk
    if abs(greeks['vanna']) > 0.05:
        click.echo("  ⚠️  HIGH VANNA - Delta sensitive to vol changes")

    # Charm risk
    if abs(greeks['charm']) > 0.02:
        click.echo("  ⚠️  HIGH CHARM - Delta will decay quickly")

    # Per-leg breakdown
    if detailed:
        click.echo("\n📋 PER-LEG GREEKS")
        for i, leg in enumerate(strategy.legs, 1):
            leg_greeks = leg.calculate_advanced_greeks(strategy.current_stock_price)
            click.echo(f"\n  Leg {i}: {leg.option_type.value.upper()} {leg.position_type.value.upper()} ${leg.strike}")
            click.echo(f"    Delta: {leg_greeks.get('delta', 0):.4f}")
            click.echo(f"    Vanna: {leg_greeks.get('vanna', 0):.6f}")
            click.echo(f"    Charm: {leg_greeks.get('charm', 0):.6f}")
```

### Phase 3: Advanced Analysis (Week 2)

#### 3.1 Greeks-Based Recommendations

**File**: `quantlab/analysis/greeks_advisor.py`

```python
class GreeksAdvisor:
    """Provide recommendations based on advanced Greeks analysis"""

    @staticmethod
    def assess_risk_profile(strategy: OptionsStrategy) -> Dict[str, str]:
        """
        Assess risk profile based on Greeks

        Returns:
            {
                'directional_risk': 'low' | 'medium' | 'high',
                'volatility_risk': 'low' | 'medium' | 'high',
                'time_decay_risk': 'low' | 'medium' | 'high',
                'vanna_risk': 'low' | 'medium' | 'high',
                'overall': 'conservative' | 'moderate' | 'aggressive'
            }
        """
        greeks = strategy.advanced_greeks()

        # Assess each dimension
        delta_risk = 'high' if abs(greeks['delta']) > 0.5 else \
                    'medium' if abs(greeks['delta']) > 0.2 else 'low'

        vega_risk = 'high' if abs(greeks['vega']) > 30 else \
                   'medium' if abs(greeks['vega']) > 10 else 'low'

        theta_risk = 'high' if abs(greeks['theta']) > 20 else \
                    'medium' if abs(greeks['theta']) > 5 else 'low'

        vanna_risk = 'high' if abs(greeks['vanna']) > 0.1 else \
                    'medium' if abs(greeks['vanna']) > 0.03 else 'low'

        # Overall assessment
        high_risks = [delta_risk, vega_risk, theta_risk, vanna_risk].count('high')
        overall = 'aggressive' if high_risks >= 2 else \
                 'moderate' if high_risks == 1 else 'conservative'

        return {
            'directional_risk': delta_risk,
            'volatility_risk': vega_risk,
            'time_decay_risk': theta_risk,
            'vanna_risk': vanna_risk,
            'overall': overall
        }

    @staticmethod
    def suggest_hedges(strategy: OptionsStrategy, target_delta: float = 0.0) -> List[Dict]:
        """
        Suggest hedges to achieve target Greeks

        Returns list of suggestions with estimated impact
        """
        greeks = strategy.advanced_greeks()
        current_delta = greeks['delta']

        suggestions = []

        # Stock hedge
        shares_needed = int((target_delta - current_delta) * 100)
        if shares_needed != 0:
            action = "Buy" if shares_needed > 0 else "Sell"
            suggestions.append({
                'action': f"{action} {abs(shares_needed)} shares",
                'cost': abs(shares_needed) * strategy.current_stock_price,
                'delta_impact': shares_needed / 100,
                'new_delta': target_delta
            })

        return suggestions
```

### Phase 4: Testing & Documentation (Week 2-3)

#### 4.1 Unit Tests

**File**: `tests/analysis/test_advanced_greeks_integration.py`

```python
def test_calculate_advanced_greeks_for_leg():
    """Test advanced Greeks calculation for single leg"""

def test_portfolio_advanced_greeks():
    """Test aggregate advanced Greeks for multi-leg strategy"""

def test_greeks_projection():
    """Test time decay forecast using charm"""

def test_volatility_sensitivity():
    """Test vanna/vomma sensitivity analysis"""

def test_greeks_with_stock_position():
    """Test Greeks with stock position included"""
```

#### 4.2 Integration Tests

**File**: `tests/cli/test_greeks_cli.py`

```python
def test_build_with_iv():
    """Test building strategy with IV parameter"""

def test_greeks_forecast_command():
    """Test greeks-forecast CLI command"""

def test_greeks_report_command():
    """Test greeks-report CLI command"""
```

#### 4.3 Documentation

**Update**: `docs/OPTIONS_STRATEGIES.md`

Add section:
```markdown
## Advanced Greeks Analysis

### Understanding Advanced Greeks

**Vanna (∂Delta/∂σ)**
- Measures how delta changes with volatility
- High vanna = position changes character with vol moves
- Example: Long straddle has high positive vanna

**Charm (∂Delta/∂t)**
- Measures delta decay over time
- Important for maintaining delta hedges
- Example: Short ATM options have high negative charm

**Vomma (∂Vega/∂σ)**
- Measures vega sensitivity to volatility
- Positive vomma = long convexity in vol
- Example: Long options have positive vomma

### Using Advanced Greeks

```bash
# Build with IV for advanced Greeks
quantlab strategy build iron_condor \
  --ticker SPY --stock-price 450 \
  --strikes 440,445,455,460 \
  --premiums 1.00,2.50,2.50,1.00 \
  --iv 0.20 \
  --expiration 2025-11-21

# Forecast Greeks over time
quantlab strategy greeks-forecast results/iron_condor.json \
  --days 30

# Test volatility scenarios
quantlab strategy greeks-forecast results/iron_condor.json \
  --vol-scenarios -10,-5,0,5,10

# Full Greeks report
quantlab strategy greeks-report results/iron_condor.json --detailed
```
```

## Implementation Checklist

### Week 1: Core + CLI
- [ ] Add `calculate_advanced_greeks()` to OptionLeg
- [ ] Add `advanced_greeks()` to OptionsStrategy
- [ ] Add `greeks_projection()` method
- [ ] Add `volatility_sensitivity()` method
- [ ] Update all StrategyBuilder methods with IV parameter
- [ ] Add `--iv` option to `strategy build` command
- [ ] Display advanced Greeks in build output
- [ ] Test with various strategies

### Week 2: Advanced Features
- [ ] Create `greeks-forecast` CLI command
- [ ] Create `greeks-report` CLI command
- [ ] Implement GreeksAdvisor class
- [ ] Add risk assessment logic
- [ ] Add hedge suggestions
- [ ] Test all CLI commands

### Week 3: Testing & Docs
- [ ] Write unit tests (target: 20+ tests)
- [ ] Write integration tests
- [ ] Update OPTIONS_STRATEGIES.md
- [ ] Add advanced Greeks examples
- [ ] Performance testing
- [ ] User acceptance testing

## Success Metrics

- ✅ Advanced Greeks calculated correctly (match existing calculator)
- ✅ Portfolio Greeks aggregate properly
- ✅ CLI displays meaningful interpretations
- ✅ Forecast/sensitivity analysis working
- ✅ 90%+ test coverage for new code
- ✅ Documentation complete with examples

## Example Output (After Implementation)

```bash
$ quantlab strategy build iron_condor --ticker SPY --stock-price 450 \
  --strikes 440,445,455,460 --premiums 1.00,2.50,2.50,1.00 \
  --iv 0.18 --expiration 2025-11-21

📊 Iron Condor on SPY
   Profit from range-bound stock movement

Strategy Legs:
  #  Type  Position  Strike   Premium   Qty  Expiration
---  ----  --------  -------  --------  ---  -----------
  1  PUT   LONG      $440.00  $1.00       1  2025-11-21
  2  PUT   SHORT     $445.00  $2.50       1  2025-11-21
  3  CALL  SHORT     $455.00  $2.50       1  2025-11-21
  4  CALL  LONG      $460.00  $1.00       1  2025-11-21

📈 Risk Analysis:
  Net Premium: $300.00 (Credit)
  Max Profit: $300.00
  Max Loss: $-200.00
  Breakeven: $442.00, $458.00

📊 Advanced Greeks Analysis:

First-Order Greeks:
  Delta: 0.0234 ($1,053 exposure)
  Gamma: 0.0089
  Theta: 5.23 (per day)
  Vega: -2.45 (per 1% vol)

Second-Order Greeks (Advanced):
  Vanna: -0.0234 (∂Delta/∂σ)
  Charm: -0.0012 (∂Delta/∂t per day)
  Vomma: -0.0045 (∂Vega/∂σ)

💡 Greeks Interpretation:
  • Vanna: Delta will decrease if volatility rises (good for credit spreads)
  • Charm: Delta will decrease slightly over time
  • Vomma: Vega will become more negative if volatility rises

⚠️  RISK PROFILE: Conservative
  ✅ LOW DIRECTIONAL RISK - Position is delta-neutral
  ✅ LOW VANNA - Minimal delta sensitivity to vol
  ✅ POSITIVE THETA - Earning time decay
```

## Timeline

- **Week 1**: Core integration + basic CLI (5-7 days)
- **Week 2**: Advanced features + CLI commands (5-7 days)
- **Week 3**: Testing + documentation (5-7 days)

**Total**: 2-3 weeks for complete implementation

## Next Steps

Ready to start with Week 1 implementation?

1. Add `calculate_advanced_greeks()` to OptionLeg
2. Add `advanced_greeks()` to OptionsStrategy
3. Update StrategyBuilder with IV parameter
4. Test with existing calculator

This leverages all existing code - just connecting pieces together!
