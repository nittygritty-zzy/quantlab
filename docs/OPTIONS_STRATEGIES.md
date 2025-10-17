# Options Trading Strategies

Complete guide to using QuantLab's options strategies module for building, analyzing, and comparing options trading strategies.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Strategy Types](#strategy-types)
  - [Single-Leg Strategies](#single-leg-strategies)
  - [Vertical Spreads](#vertical-spreads)
  - [Advanced Strategies](#advanced-strategies)
- [CLI Usage](#cli-usage)
- [Python API](#python-api)
- [Risk Metrics](#risk-metrics)
- [Examples](#examples)

## Overview

The options strategies module provides:

- **14 pre-built strategies**: From simple calls/puts to complex iron condors
- **Profit/Loss calculations**: Analyze P&L at any stock price
- **Risk metrics**: Max profit/loss, breakevens, risk/reward ratios
- **Payoff diagrams**: Generate data for visualizing strategy payoffs
- **CLI tools**: Build and compare strategies from command line
- **JSON serialization**: Save and share strategy configurations

## Getting Started

### List Available Strategies

```bash
quantlab strategy list
```

Output:
```
📊 Available Options Strategies

🎯 Single-Leg Strategies:
  • Long Call                 Bullish speculation with limited risk
  • Long Put                  Bearish speculation with limited risk
  • Covered Call              Generate income on stock holdings
  • Protective Put            Protect stock position with downside insurance
  • Cash-Secured Put          Generate income or acquire stock at discount

🎯 Vertical Spreads:
  • Bull Call Spread          Bullish with capped profit and loss
  • Bull Put Spread           Bullish credit spread
  • Bear Call Spread          Bearish credit spread
  • Bear Put Spread           Bearish with capped profit and loss

🎯 Advanced Strategies:
  • Iron Condor               Profit from range-bound movement
  • Butterfly                 Profit from low volatility around target price
  • Straddle                  Profit from high volatility (any direction)
  • Strangle                  Profit from high volatility (cheaper than straddle)
  • Calendar Spread           Profit from time decay and volatility
```

## Strategy Types

### Single-Leg Strategies

#### Long Call

**When to Use**: Bullish outlook, expect significant upward move

**Example**:
```bash
quantlab strategy build long_call \
  --ticker AAPL \
  --stock-price 175 \
  --strike 180 \
  --premium 3.50 \
  --quantity 2 \
  --expiration 2025-12-19 \
  --output results/aapl_long_call.json
```

**Characteristics**:
- Max Profit: Unlimited
- Max Loss: Premium paid
- Breakeven: Strike + Premium
- Best Case: Stock rises significantly

#### Long Put

**When to Use**: Bearish outlook, expect significant downward move

**Example**:
```bash
quantlab strategy build long_put \
  --ticker TSLA \
  --stock-price 250 \
  --strike 240 \
  --premium 8.50 \
  --expiration 2025-11-21
```

**Characteristics**:
- Max Profit: Strike - Premium (if stock goes to zero)
- Max Loss: Premium paid
- Breakeven: Strike - Premium
- Best Case: Stock declines significantly

#### Covered Call

**When to Use**: Own stock, want to generate income, neutral to slightly bullish

**Example**:
```bash
quantlab strategy build covered_call \
  --ticker NVDA \
  --stock-price 485 \
  --strike 500 \
  --premium 12.00 \
  --shares 100 \
  --expiration 2025-12-19
```

**Characteristics**:
- Max Profit: (Strike - Stock Price) + Premium
- Max Loss: Stock declines to zero minus premium
- Breakeven: Stock Price - Premium
- Best Case: Stock rises to strike price

#### Protective Put

**When to Use**: Own stock, want downside protection, bullish long-term

**Example**:
```bash
quantlab strategy build protective_put \
  --ticker SPY \
  --stock-price 450 \
  --strike 440 \
  --premium 5.00 \
  --shares 100 \
  --expiration 2026-01-15
```

**Characteristics**:
- Max Profit: Unlimited (stock can rise infinitely)
- Max Loss: (Stock Price - Strike) + Premium
- Breakeven: Stock Price + Premium
- Best Case: Stock rises, put expires worthless

#### Cash-Secured Put

**When to Use**: Want to acquire stock at lower price, generate income

**Example**:
```bash
quantlab strategy build cash_secured_put \
  --ticker MSFT \
  --stock-price 380 \
  --strike 370 \
  --premium 6.50 \
  --quantity 2 \
  --expiration 2025-11-21
```

**Characteristics**:
- Max Profit: Premium received
- Max Loss: Strike - Premium (if stock goes to zero)
- Breakeven: Strike - Premium
- Best Case: Stock stays above strike, keep premium

### Vertical Spreads

#### Bull Call Spread

**When to Use**: Moderately bullish, want to reduce cost vs. long call

**Example**:
```bash
quantlab strategy build bull_call_spread \
  --ticker GOOG \
  --stock-price 140 \
  --strikes 135,145 \
  --premiums 8.50,3.50 \
  --expiration 2025-12-19
```

**Characteristics**:
- Max Profit: (Spread Width) - Net Debit
- Max Loss: Net Debit
- Breakeven: Long Strike + Net Debit
- Best Case: Stock rises above short strike

#### Bull Put Spread

**When to Use**: Moderately bullish, want to collect credit

**Example**:
```bash
quantlab strategy build bull_put_spread \
  --ticker SPY \
  --stock-price 450 \
  --strikes 440,445 \
  --premiums 2.00,4.00 \
  --expiration 2025-11-21
```

**Characteristics**:
- Max Profit: Net Credit
- Max Loss: (Spread Width) - Net Credit
- Breakeven: Short Strike - Net Credit
- Best Case: Stock stays above short strike

#### Bear Call Spread

**When to Use**: Moderately bearish, want to collect credit

**Example**:
```bash
quantlab strategy build bear_call_spread \
  --ticker NVDA \
  --stock-price 485 \
  --strikes 490,500 \
  --premiums 8.00,4.00 \
  --expiration 2025-12-19
```

**Characteristics**:
- Max Profit: Net Credit
- Max Loss: (Spread Width) - Net Credit
- Breakeven: Short Strike + Net Credit
- Best Case: Stock stays below short strike

#### Bear Put Spread

**When to Use**: Moderately bearish, want to reduce cost vs. long put

**Example**:
```bash
quantlab strategy build bear_put_spread \
  --ticker TSLA \
  --stock-price 250 \
  --strikes 245,255 \
  --premiums 6.00,10.00 \
  --expiration 2025-11-21
```

**Characteristics**:
- Max Profit: (Spread Width) - Net Debit
- Max Loss: Net Debit
- Breakeven: Long Strike - Net Debit
- Best Case: Stock drops below long strike

### Advanced Strategies

#### Iron Condor

**When to Use**: Expect low volatility, stock to stay in range

**Example**:
```bash
quantlab strategy build iron_condor \
  --ticker SPY \
  --stock-price 450 \
  --strikes 440,445,455,460 \
  --premiums 1.00,2.50,2.50,1.00 \
  --expiration 2025-11-21 \
  --output results/spy_iron_condor.json
```

**Characteristics**:
- Max Profit: Net Credit
- Max Loss: (Widest Spread) - Net Credit
- Breakevens: Two points (put side and call side)
- Best Case: Stock stays between short strikes

#### Butterfly

**When to Use**: Expect very low volatility around specific price

**Example**:
```bash
quantlab strategy build butterfly \
  --ticker AAPL \
  --stock-price 175 \
  --strikes 170,175,180 \
  --premiums 8.00,3.00,1.00 \
  --option-type call \
  --expiration 2025-12-19
```

**Characteristics**:
- Max Profit: (Spread Width) - Net Debit
- Max Loss: Net Debit
- Breakevens: Two points around middle strike
- Best Case: Stock ends exactly at middle strike

#### Straddle

**When to Use**: Expect high volatility in either direction

**Example - Long Straddle**:
```bash
quantlab strategy build straddle \
  --ticker NVDA \
  --stock-price 485 \
  --strike 485 \
  --premiums 15.00,15.00 \
  --position long \
  --expiration 2025-12-19
```

**Example - Short Straddle**:
```bash
quantlab strategy build straddle \
  --ticker SPY \
  --stock-price 450 \
  --strike 450 \
  --premiums 8.00,8.00 \
  --position short \
  --expiration 2025-11-21
```

**Long Straddle**:
- Max Profit: Unlimited
- Max Loss: Total premium paid
- Breakevens: Strike ± Total Premium
- Best Case: Large move in either direction

**Short Straddle**:
- Max Profit: Total premium received
- Max Loss: Unlimited
- Breakevens: Strike ± Total Premium
- Best Case: Stock stays near strike

#### Strangle

**When to Use**: Expect high volatility, cheaper than straddle

**Example**:
```bash
quantlab strategy build strangle \
  --ticker TSLA \
  --stock-price 250 \
  --strikes 240,260 \
  --premiums 8.00,8.00 \
  --position long \
  --expiration 2025-11-21
```

**Characteristics**:
- Max Profit: Unlimited (long) / Premium received (short)
- Max Loss: Total premium (long) / Unlimited (short)
- Breakevens: Put Strike - Premium, Call Strike + Premium
- Best Case: Large move beyond strikes (long) / No move (short)

#### Calendar Spread

**When to Use**: Expect low volatility, profit from time decay difference

**Example**:
```bash
quantlab strategy build calendar_spread \
  --ticker AAPL \
  --stock-price 175 \
  --strike 175 \
  --premiums 3.00,7.00 \
  --near-expiration 2025-11-21 \
  --far-expiration 2025-12-19 \
  --option-type call
```

**Characteristics**:
- Max Profit: Varies (depends on volatility)
- Max Loss: Net Debit
- Best Case: Stock stays near strike at near expiration

## CLI Usage

### Building Strategies

All strategies follow similar patterns:

```bash
# Single-leg: --strike and --premium
quantlab strategy build <type> --ticker <TICKER> --stock-price <PRICE> \
  --strike <STRIKE> --premium <PREMIUM> --expiration <DATE>

# Spreads: --strikes and --premiums (comma-separated)
quantlab strategy build <type> --ticker <TICKER> --stock-price <PRICE> \
  --strikes <S1>,<S2> --premiums <P1>,<P2> --expiration <DATE>

# With stock position: --shares
quantlab strategy build covered_call --ticker <TICKER> --stock-price <PRICE> \
  --strike <STRIKE> --premium <PREMIUM> --shares <N> --expiration <DATE>
```

### Analyzing Strategies

```bash
# Analyze a saved strategy
quantlab strategy analyze results/my_strategy.json

# Output:
📊 Strategy Analysis: Bull Call Spread on NVDA
   Type: bull_call_spread
   Current Stock Price: $485.00

📈 Risk Metrics:
  Net Premium: $-500.00 (Debit)
  Max Profit: $500.00
  Max Loss: $-500.00
  Breakeven: $485.00
```

### Comparing Strategies

```bash
# Compare multiple strategies side-by-side
quantlab strategy compare \
  results/aapl_long_call.json \
  results/spy_iron_condor.json \
  results/nvda_bull_call.json
```

Output:
```
📊 Comparing 3 Strategies

| Strategy                 | Type             | Stock Price | Net Premium | Max Profit | Max Loss   | Risk/Reward |
|--------------------------|------------------|-------------|-------------|------------|------------|-------------|
| Long Call on AAPL        | long_call        | $175.50     | $-700.00    | $68600.00  | $-700.00   | 98.00       |
| Iron Condor on SPY       | iron_condor      | $450.00     | $300.00     | $300.00    | $-200.00   | 1.50        |
| Bull Call Spread on NVDA | bull_call_spread | $485.00     | $-500.00    | $500.00    | $-500.00   | 1.00        |
```

## Python API

### Building Strategies Programmatically

```python
from datetime import date, timedelta
from quantlab.analysis.options_strategies import StrategyBuilder

# Create expiration date
expiration = date.today() + timedelta(days=30)

# Build a bull call spread
strategy = StrategyBuilder.bull_call_spread(
    stock_price=100.0,
    long_strike=95.0,
    short_strike=105.0,
    long_premium=8.0,
    short_premium=3.0,
    quantity=1,
    expiration=expiration,
    ticker="AAPL"
)

# Analyze risk metrics
metrics = strategy.risk_metrics()
print(f"Max Profit: ${metrics['max_profit']:.2f}")
print(f"Max Loss: ${metrics['max_loss']:.2f}")
print(f"Breakevens: {metrics['breakeven_points']}")

# Calculate P&L at different prices
for price in [90, 95, 100, 105, 110]:
    pnl = strategy.pnl_at_price(price)
    print(f"Stock @ ${price}: P&L = ${pnl:.2f}")

# Generate payoff diagram data
prices, pnls = strategy.payoff_diagram()

# Save to JSON
import json
with open('my_strategy.json', 'w') as f:
    json.dump(strategy.to_dict(), f, indent=2)
```

### Creating Custom Strategies

```python
from quantlab.analysis.options_strategies import (
    OptionLeg, OptionsStrategy, StrategyType,
    OptionType, PositionType
)

# Create custom legs
legs = [
    OptionLeg(
        option_type=OptionType.CALL,
        position_type=PositionType.LONG,
        strike=100.0,
        premium=5.0,
        quantity=1,
        expiration=expiration
    ),
    OptionLeg(
        option_type=OptionType.PUT,
        position_type=PositionType.LONG,
        strike=100.0,
        premium=5.0,
        quantity=1,
        expiration=expiration
    )
]

# Create custom strategy
custom_strategy = OptionsStrategy(
    name="Custom Long Straddle",
    strategy_type=StrategyType.STRADDLE,
    legs=legs,
    current_stock_price=100.0,
    stock_position=0,
    metadata={"notes": "Custom implementation"}
)

# Analyze
print(f"Net Premium: ${custom_strategy.net_premium():.2f}")
print(f"Max Profit: ${custom_strategy.max_profit():.2f}")
print(f"Max Loss: ${custom_strategy.max_loss():.2f}")
```

## Risk Metrics

Each strategy provides comprehensive risk metrics:

| Metric | Description |
|--------|-------------|
| **Max Profit** | Maximum potential profit |
| **Max Loss** | Maximum potential loss |
| **Net Premium** | Net debit or credit (positive = credit) |
| **Breakeven Points** | Stock prices where P&L = 0 |
| **Risk/Reward Ratio** | Max Profit / Max Loss |
| **Probability of Profit** | Estimated probability (simplified model) |
| **Current P&L** | P&L at current stock price |
| **Debit/Credit** | Whether strategy costs money or generates income |

### Interpreting Risk Metrics

**High Risk/Reward Ratio (>2)**:
- Greater profit potential relative to risk
- Example: Long call (potentially unlimited profit)

**Low Risk/Reward Ratio (<1)**:
- Greater risk relative to profit potential
- Example: Naked call writing (unlimited risk)

**Balanced Risk/Reward (~1)**:
- Equal profit and loss potential
- Example: Vertical spreads

## Examples

### Example 1: Income Generation with Covered Calls

```bash
# Own 500 shares of AAPL at $175
# Sell 5 covered calls at $180 strike for $3.50 premium

quantlab strategy build covered_call \
  --ticker AAPL \
  --stock-price 175 \
  --strike 180 \
  --premium 3.50 \
  --shares 500 \
  --expiration 2025-12-19 \
  --output results/aapl_income.json

# Result:
# - Income: $1,750 (5 contracts × $3.50 × 100)
# - Max additional gain: $2,500 if stock rises to $180
# - Protected down to: $171.50 ($175 - $3.50)
```

### Example 2: Downside Protection with Protective Puts

```bash
# Own 200 shares of NVDA at $485
# Buy 2 puts at $470 strike for $12 premium

quantlab strategy build protective_put \
  --ticker NVDA \
  --stock-price 485 \
  --strike 470 \
  --premium 12.00 \
  --shares 200 \
  --expiration 2026-01-15 \
  --output results/nvda_protection.json

# Result:
# - Max loss capped at: $3,400 (15 points × 200 + $2,400 premium)
# - Upside: Unlimited minus premium
# - Insurance cost: $2,400
```

### Example 3: Range Trading with Iron Condor

```bash
# SPY at $450, expect to stay between $445-$455

quantlab strategy build iron_condor \
  --ticker SPY \
  --stock-price 450 \
  --strikes 440,445,455,460 \
  --premiums 1.00,2.50,2.50,1.00 \
  --quantity 5 \
  --expiration 2025-11-21 \
  --output results/spy_iron_condor.json

# Result:
# - Net credit: $1,500 (5 contracts × $300)
# - Max loss: $1,000 (5 contracts × $200)
# - Profit range: $442 - $458
# - Risk/Reward: 1.5
```

### Example 4: Comparing Bullish Strategies

```bash
# Compare different bullish strategies on AAPL

# 1. Long call
quantlab strategy build long_call \
  --ticker AAPL --stock-price 175 --strike 180 --premium 7.00 \
  --expiration 2025-12-19 --output results/aapl_call.json

# 2. Bull call spread
quantlab strategy build bull_call_spread \
  --ticker AAPL --stock-price 175 --strikes 175,185 --premiums 10.00,4.00 \
  --expiration 2025-12-19 --output results/aapl_spread.json

# 3. Bull put spread
quantlab strategy build bull_put_spread \
  --ticker AAPL --stock-price 175 --strikes 165,170 --premiums 2.00,4.50 \
  --expiration 2025-12-19 --output results/aapl_put_spread.json

# Compare them
quantlab strategy compare \
  results/aapl_call.json \
  results/aapl_spread.json \
  results/aapl_put_spread.json
```

## Best Practices

### Strategy Selection

1. **Match outlook to strategy**:
   - Strong bullish → Long call
   - Moderate bullish → Bull call spread, covered call
   - Neutral → Iron condor, butterfly
   - High volatility → Straddle, strangle
   - Low volatility → Iron condor, butterfly

2. **Consider risk tolerance**:
   - Defined risk → Vertical spreads, long options
   - Undefined risk → Naked options (advanced)
   - Limited capital → Spreads instead of outright

3. **Account for volatility**:
   - High IV → Sell premium (spreads, iron condors)
   - Low IV → Buy premium (long options)

### Risk Management

1. **Position sizing**: Never risk more than 2-5% of portfolio per trade
2. **Stop losses**: Close positions at 2x max loss (e.g., -$1000 on $500 debit)
3. **Profit targets**: Take profits at 50-75% of max profit
4. **Diversification**: Use different strategies across multiple underlyings

### Execution Tips

1. **Timing**:
   - Build strategies when IV is favorable
   - Consider earnings dates
   - Watch for major events

2. **Strike selection**:
   - ITM: Higher delta, more expensive
   - ATM: Balanced risk/reward
   - OTM: Lower cost, lower probability

3. **Expiration selection**:
   - Short-term (<30 days): Faster theta decay
   - Medium-term (30-60 days): Balanced
   - Long-term (>60 days): More time value

## Troubleshooting

### Common Issues

**Issue**: "ValueError: --strikes and --premiums must have 2 values"
**Solution**: Ensure comma-separated values match expected count
```bash
# Wrong: --strikes 100,105,110
# Right: --strikes 100,105
```

**Issue**: Strategy shows unexpected P&L
**Solution**: Verify strike prices and premium values are correct

**Issue**: Cannot compare strategies
**Solution**: Ensure all strategy files exist and are valid JSON

## Further Resources

- [Options Greeks and Pricing](OPTIONS_GREEKS.md)
- [Backtesting Options Strategies](BACKTEST_OPTIONS.md)
- [Risk Management Guide](RISK_MANAGEMENT.md)
- [Real-world Case Studies](CASE_STUDIES.md)

## Support

For questions or issues:
- GitHub Issues: https://github.com/nittygritty-zzy/quantlab/issues
- Documentation: https://github.com/nittygritty-zzy/quantlab/docs

---

**Happy Trading! Remember: Options carry significant risk. Always understand the strategy before trading with real money.**
