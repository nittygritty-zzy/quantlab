# Strategy Builder IV Parameter Expansion Plan

## Overview

Expand IV (Implied Volatility) parameter support to all remaining StrategyBuilder methods, enabling advanced Greeks calculation for all 14 options strategies.

**Current Status**: 3/14 strategies support IV parameter
- ✅ bull_call_spread
- ✅ iron_condor
- ✅ covered_call

**Goal**: Add IV support to remaining 11 strategies

---

## Remaining Strategies to Update

### Single-Leg Strategies (2)
1. **long_call** - Simple long call option
2. **long_put** - Simple long put option

### Two-Leg Strategies (2)
3. **protective_put** - Long stock + long put (downside protection)
4. **bear_put_spread** - Buy higher strike put, sell lower strike put

### Vertical Spreads (2)
5. **bull_put_spread** - Sell higher strike put, buy lower strike put
6. **bear_call_spread** - Sell lower strike call, buy higher strike call

### Volatility Strategies (4)
7. **long_straddle** - Buy ATM call + ATM put
8. **long_strangle** - Buy OTM call + OTM put
9. **short_straddle** - Sell ATM call + ATM put
10. **short_strangle** - Sell OTM call + OTM put

### Complex Spreads (1)
11. **butterfly_spread** - 3 strikes, 4 legs (1 buy low, 2 sell mid, 1 buy high)

---

## Implementation Approach

### Step 1: Parameter Addition Pattern

For each strategy method, add two optional parameters:

```python
@staticmethod
def strategy_name(
    # ... existing parameters ...
    implied_volatility: Optional[float] = None,
    risk_free_rate: float = 0.05
) -> OptionsStrategy:
```

### Step 2: Apply IV to All Option Legs

When creating OptionLeg instances, pass IV parameters:

```python
legs = [
    OptionLeg(
        # ... existing fields ...
        implied_volatility=implied_volatility,
        risk_free_rate=risk_free_rate
    )
]
```

### Step 3: Add IV to Metadata (if applicable)

For strategies with stocks (protective_put), add to metadata:

```python
metadata = {
    # ... existing metadata ...
}
if implied_volatility:
    metadata['implied_volatility'] = implied_volatility
    metadata['risk_free_rate'] = risk_free_rate
```

### Step 4: Update Docstrings

Add documentation for new parameters:

```python
"""
Args:
    # ... existing args ...
    implied_volatility: Implied volatility (decimal, e.g., 0.30 for 30%).
                       If provided, enables advanced Greeks calculation.
    risk_free_rate: Risk-free interest rate (default: 0.05 for 5%)
"""
```

---

## Implementation Sequence

### Phase 1: Simple Strategies (2 methods)
**Estimated Time**: 30 minutes

1. `long_call` - Single leg, straightforward
2. `long_put` - Single leg, straightforward

**Pattern**:
```python
@staticmethod
def long_call(
    stock_price: float,
    strike: float,
    premium: float,
    quantity: int,
    expiration: date,
    ticker: str = "",
    implied_volatility: Optional[float] = None,
    risk_free_rate: float = 0.05
) -> OptionsStrategy:
    legs = [
        OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=strike,
            premium=premium,
            quantity=quantity,
            expiration=expiration,
            implied_volatility=implied_volatility,
            risk_free_rate=risk_free_rate
        )
    ]
    # ... rest of implementation
```

### Phase 2: Two-Leg Strategies (2 methods)
**Estimated Time**: 30 minutes

3. `protective_put` - Stock + put leg (add IV to metadata)
4. `bear_put_spread` - Two put legs

**Special Consideration**: protective_put has stock position, needs metadata update

### Phase 3: Vertical Spreads (2 methods)
**Estimated Time**: 30 minutes

5. `bull_put_spread` - Two put legs (similar to bear_put_spread)
6. `bear_call_spread` - Two call legs (similar to bull_call_spread)

**Pattern**: Already established from bull_call_spread implementation

### Phase 4: Volatility Strategies (4 methods)
**Estimated Time**: 1 hour

7. `long_straddle` - Call + put at same strike
8. `short_straddle` - Opposite of long_straddle
9. `long_strangle` - Call + put at different strikes
10. `short_strangle` - Opposite of long_strangle

**Pattern**: Apply IV to both call and put legs

### Phase 5: Complex Spreads (1 method)
**Estimated Time**: 30 minutes

11. `butterfly_spread` - 4 legs (already has similar pattern from iron_condor)

---

## Testing Strategy

### Unit Tests (Add to test_advanced_greeks.py)

For each new strategy, add 2 tests:

1. **Test with IV**: Verify Greeks are calculated
2. **Test without IV**: Verify strategy works without Greeks

**Pattern**:
```python
def test_{strategy_name}_with_iv(self):
    """Test {strategy_name} builder with IV"""
    strategy = StrategyBuilder.{strategy_name}(
        # ... parameters ...
        implied_volatility=0.30,
        risk_free_rate=0.05
    )

    # Verify IV set on legs
    assert strategy.legs[0].implied_volatility == 0.30

    # Verify Greeks calculated
    greeks = strategy.advanced_greeks()
    assert greeks['delta'] != 0.0
    assert 'vanna' in greeks
```

**Estimated**: 22 new tests (2 per strategy × 11 strategies)

### Integration Tests (Optional)

Add spot checks for 2-3 key strategies in CLI tests:
- long_straddle (volatility play)
- butterfly_spread (complex spread)
- protective_put (stock + option)

---

## CLI Integration (Future Enhancement)

### Current State
CLI `strategy build` command only supports 3 strategies:
- bull_call_spread
- iron_condor
- covered_call

### Future Enhancement
Consider adding CLI commands for popular strategies:
- `quantlab strategy build long_call --iv 0.30 ...`
- `quantlab strategy build protective_put --iv 0.25 ...`
- `quantlab strategy build iron_butterfly --iv 0.20 ...`

**Note**: This is lower priority since StrategyBuilder methods can be used programmatically.

---

## Implementation Timeline

| Phase | Strategies | Time | Cumulative |
|-------|-----------|------|------------|
| Phase 1 | Single-leg (2) | 30 min | 30 min |
| Phase 2 | Two-leg (2) | 30 min | 1 hour |
| Phase 3 | Vertical spreads (2) | 30 min | 1.5 hours |
| Phase 4 | Volatility (4) | 1 hour | 2.5 hours |
| Phase 5 | Complex (1) | 30 min | 3 hours |
| Testing | Unit tests (22) | 1.5 hours | 4.5 hours |
| **Total** | **11 strategies** | **~5 hours** | |

---

## Success Criteria

- ✅ All 11 remaining StrategyBuilder methods accept `implied_volatility` parameter
- ✅ All 11 methods accept `risk_free_rate` parameter
- ✅ All option legs receive IV when provided
- ✅ Strategies work correctly without IV (backwards compatible)
- ✅ Advanced Greeks calculate correctly for all strategies
- ✅ 22 new unit tests pass (2 per strategy)
- ✅ Documentation updated with new parameters

---

## Example Before/After

### Before (long_straddle without IV)
```python
strategy = StrategyBuilder.long_straddle(
    stock_price=100.0,
    strike=100.0,
    call_premium=5.0,
    put_premium=4.5,
    quantity=1,
    expiration=exp_date,
    ticker="SPY"
)

# No Greeks available
greeks = strategy.advanced_greeks()
# Returns all zeros
```

### After (long_straddle with IV)
```python
strategy = StrategyBuilder.long_straddle(
    stock_price=100.0,
    strike=100.0,
    call_premium=5.0,
    put_premium=4.5,
    quantity=1,
    expiration=exp_date,
    ticker="SPY",
    implied_volatility=0.30,  # 30% IV
    risk_free_rate=0.05       # 5% risk-free rate
)

# Greeks now calculated!
greeks = strategy.advanced_greeks()
# Returns: {'delta': 0.02, 'gamma': 0.15, 'vega': 80.5, 'theta': -12.3,
#           'vanna': -0.003, 'charm': -0.001, 'vomma': 0.25}
```

---

## Risk Assessment

**Low Risk** because:
- Pattern already proven with 3 strategies
- IV parameter is optional (backwards compatible)
- No breaking changes to existing code
- Straightforward mechanical updates
- Comprehensive test coverage

---

## Next Steps

1. **Implement Phase 1** (single-leg strategies)
2. **Run unit tests** to verify
3. **Continue through phases 2-5** sequentially
4. **Run full test suite** after each phase
5. **Update project documentation** when complete
