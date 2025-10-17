# Greeks Forecast Command Implementation Plan

## Overview

Implement a CLI command that forecasts how options Greeks will evolve over time, helping traders understand time decay effects and plan position adjustments.

**Command**: `quantlab strategy greeks-forecast`

**Purpose**: Project advanced Greeks (delta, gamma, theta, vega, vanna, charm, vomma) forward in time to visualize time decay and changing risk characteristics.

---

## Use Cases

### 1. Time Decay Analysis
- See how theta decay affects position value over time
- Understand when to adjust or close positions
- Plan exit strategies based on Greeks evolution

### 2. Delta Management
- Forecast when delta will drift (using charm)
- Anticipate when rebalancing is needed
- Understand directional risk over time

### 3. Volatility Exposure
- See how vega decreases as expiration approaches
- Plan volatility trades (straddles/strangles)
- Understand vomma effects on vega sensitivity

### 4. Position Planning
- Determine optimal holding periods
- Compare strategies at different time horizons
- Identify critical time points for adjustments

---

## Command Design

### Basic Command Structure

```bash
quantlab strategy greeks-forecast <strategy-file> [OPTIONS]
```

### Input Options

#### Strategy Source
```bash
# Load from saved strategy file
quantlab strategy greeks-forecast results/my_strategy.json

# Or inline build (reuse existing build syntax)
quantlab strategy greeks-forecast --build bull_call_spread \
    --ticker SPY --stock-price 450 --strikes 445,455 \
    --premiums 7.00,3.00 --expiration 2025-12-19 --iv 0.25
```

#### Time Projection Options
```bash
--forecast-days DAYS          # Number of days to forecast (default: until expiration)
--time-steps STEPS            # Number of time points to show (default: 5)
--time-points "T+1,T+5,T+10"  # Explicit time points to evaluate

# Examples:
# Show 7 days ahead in 1-day increments
--forecast-days 7 --time-steps 7

# Show at specific days: today, 5 days, 10 days, 20 days
--time-points "T+0,T+5,T+10,T+20"
```

#### Stock Price Scenarios
```bash
--stock-scenarios "95,100,105"     # Explicit prices
--stock-range "-5%,0%,+5%"         # Percentage changes
--stock-steps 5                    # Auto-generate 5 price points around current

# Examples:
# Show at current, +/-5%, +/-10%
--stock-range "-10%,-5%,0%,+5%,+10%"

# Show 5 scenarios from -10% to +10%
--stock-steps 5 --stock-range-pct 10
```

#### Display Options
```bash
--format [table|csv|json]          # Output format (default: table)
--greeks [all|first|second]        # Which Greeks to show
--highlight-risks                  # Highlight significant risk changes
--output FILE                      # Save to file
--plot                             # Generate matplotlib visualization
```

---

## Technical Implementation

### Phase 1: Core Calculation Engine (2 hours)

**File**: `quantlab/analysis/greeks_forecast.py`

#### 1.1 Time Projection Calculator

```python
from dataclasses import dataclass
from typing import List, Dict
from datetime import date, timedelta

@dataclass
class GreeksForecastPoint:
    """Greeks at a specific time and stock price"""
    days_forward: int
    stock_price: float
    days_to_expiry: int
    greeks: Dict[str, float]

    @property
    def date(self) -> date:
        return date.today() + timedelta(days=self.days_forward)


class GreeksForecastCalculator:
    """Calculate Greeks projections over time"""

    def __init__(self, strategy: OptionsStrategy):
        self.strategy = strategy

    def forecast_timeline(
        self,
        forecast_days: int = None,
        time_steps: int = 5,
        time_points: List[int] = None
    ) -> List[GreeksForecastPoint]:
        """
        Calculate Greeks at multiple time points

        Args:
            forecast_days: Days to forecast (default: until expiration)
            time_steps: Number of evenly-spaced time points
            time_points: Explicit list of days forward (e.g., [0, 5, 10, 20])

        Returns:
            List of forecast points with Greeks at each time
        """
        # Determine time points to evaluate
        if time_points is None:
            if forecast_days is None:
                # Default: forecast until expiration
                forecast_days = self._days_until_expiration()

            # Generate evenly spaced points
            time_points = self._generate_time_points(forecast_days, time_steps)

        forecast_points = []
        for days_forward in time_points:
            # Simulate time passing by reducing days_to_expiry
            forecast_point = self._calculate_greeks_at_time(
                days_forward=days_forward,
                stock_price=self.strategy.current_stock_price
            )
            forecast_points.append(forecast_point)

        return forecast_points

    def forecast_matrix(
        self,
        time_points: List[int],
        stock_prices: List[float]
    ) -> List[List[GreeksForecastPoint]]:
        """
        Calculate Greeks at multiple time and price points (2D matrix)

        Returns:
            2D list: forecast_matrix[time_idx][price_idx]
        """
        matrix = []
        for days_forward in time_points:
            row = []
            for stock_price in stock_prices:
                forecast_point = self._calculate_greeks_at_time(
                    days_forward=days_forward,
                    stock_price=stock_price
                )
                row.append(forecast_point)
            matrix.append(row)

        return matrix

    def _calculate_greeks_at_time(
        self,
        days_forward: int,
        stock_price: float
    ) -> GreeksForecastPoint:
        """Calculate Greeks at specific future time and price"""
        # For each leg, recalculate Greeks with reduced time to expiry
        # This simulates time decay

        # Note: We need to temporarily modify the strategy's legs
        # to have the reduced expiration time

        # Calculate new Greeks using existing calculator
        # ... implementation details ...

        return GreeksForecastPoint(
            days_forward=days_forward,
            stock_price=stock_price,
            days_to_expiry=self._get_days_to_expiry(days_forward),
            greeks=calculated_greeks
        )
```

#### 1.2 Stock Price Scenario Generator

```python
class StockScenarioGenerator:
    """Generate stock price scenarios for forecast"""

    @staticmethod
    def from_percentages(
        current_price: float,
        percentages: List[str]  # ["-10%", "-5%", "0%", "+5%", "+10%"]
    ) -> List[float]:
        """Convert percentage strings to absolute prices"""
        prices = []
        for pct_str in percentages:
            pct = float(pct_str.strip('%')) / 100
            price = current_price * (1 + pct)
            prices.append(price)
        return prices

    @staticmethod
    def generate_range(
        current_price: float,
        range_pct: float = 10.0,
        steps: int = 5
    ) -> List[float]:
        """Generate evenly spaced prices around current"""
        # Generate from (current - range%) to (current + range%)
        min_price = current_price * (1 - range_pct / 100)
        max_price = current_price * (1 + range_pct / 100)
        return list(np.linspace(min_price, max_price, steps))
```

### Phase 2: CLI Integration (1.5 hours)

**File**: `quantlab/cli/strategy.py`

#### 2.1 Add Forecast Command

```python
@strategy_group.command('greeks-forecast')
@click.argument('strategy_file', type=click.Path(exists=True), required=False)
@click.option('--build', type=click.Choice([
    'bull_call_spread', 'iron_condor', 'long_straddle',
    'long_strangle', 'butterfly', 'covered_call'
]), help='Build strategy inline instead of loading file')
# ... all build options (ticker, strikes, premiums, etc.) ...
@click.option('--forecast-days', type=int, help='Days to forecast')
@click.option('--time-steps', type=int, default=5, help='Number of time points')
@click.option('--time-points', type=str, help='Comma-separated days (e.g., "0,5,10,20")')
@click.option('--stock-scenarios', type=str, help='Comma-separated prices')
@click.option('--stock-range', type=str, help='Percentage range (e.g., "-10%,-5%,0%,+5%,+10%")')
@click.option('--stock-steps', type=int, default=5, help='Number of price scenarios')
@click.option('--stock-range-pct', type=float, default=10.0, help='Stock range percentage')
@click.option('--format', type=click.Choice(['table', 'csv', 'json']), default='table')
@click.option('--greeks', type=click.Choice(['all', 'first', 'second']), default='all')
@click.option('--output', type=click.Path(), help='Save output to file')
@click.option('--plot', is_flag=True, help='Generate visualization')
def greeks_forecast(strategy_file, build, forecast_days, time_steps, time_points,
                   stock_scenarios, stock_range, stock_steps, stock_range_pct,
                   format, greeks, output, plot, **build_kwargs):
    """
    Forecast how Greeks evolve over time for an options strategy.

    Examples:

        # Forecast 30 days for saved strategy
        quantlab strategy greeks-forecast results/my_iron_condor.json --forecast-days 30

        # Build straddle and forecast at specific times
        quantlab strategy greeks-forecast --build long_straddle \\
            --ticker SPY --stock-price 450 --strike 450 \\
            --call-premium 10 --put-premium 9 --expiration 2025-12-19 \\
            --iv 0.28 --time-points "0,7,14,21,30"

        # Show 2D matrix: time vs stock price
        quantlab strategy greeks-forecast results/strategy.json \\
            --time-points "0,10,20" --stock-range "-10%,0%,+10%"
    """
    # Load or build strategy
    if strategy_file:
        strategy = load_strategy_from_file(strategy_file)
    elif build:
        strategy = build_strategy_inline(build, **build_kwargs)
    else:
        raise click.UsageError("Must provide strategy file or --build option")

    # Validate strategy has IV
    if not any(leg.implied_volatility for leg in strategy.legs):
        click.echo("⚠️  Warning: Strategy does not have IV. Greeks forecast requires IV.")
        click.echo("    Use 'strategy build' with --iv parameter or update strategy file.")
        return

    # Parse time points
    if time_points:
        time_points = [int(x.strip().replace('T+', '')) for x in time_points.split(',')]
    else:
        time_points = None

    # Parse stock scenarios
    if stock_scenarios:
        stock_prices = [float(x.strip()) for x in stock_scenarios.split(',')]
    elif stock_range:
        stock_prices = StockScenarioGenerator.from_percentages(
            strategy.current_stock_price,
            [x.strip() for x in stock_range.split(',')]
        )
    else:
        # Default: generate range
        stock_prices = StockScenarioGenerator.generate_range(
            strategy.current_stock_price,
            range_pct=stock_range_pct,
            steps=stock_steps
        )

    # Calculate forecast
    calculator = GreeksForecastCalculator(strategy)

    if len(stock_prices) == 1:
        # 1D forecast: time only
        forecast_points = calculator.forecast_timeline(
            forecast_days=forecast_days,
            time_steps=time_steps,
            time_points=time_points
        )
        display_timeline_forecast(forecast_points, greeks, format)
    else:
        # 2D forecast: time × stock price
        forecast_matrix = calculator.forecast_matrix(time_points, stock_prices)
        display_matrix_forecast(forecast_matrix, greeks, format)

    # Generate plot if requested
    if plot:
        generate_forecast_plot(forecast_points or forecast_matrix, output)

    # Save to file if requested
    if output and format != 'table':
        save_forecast_to_file(forecast_points or forecast_matrix, output, format)
```

### Phase 3: Display Formatters (1.5 hours)

**File**: `quantlab/cli/formatters.py`

#### 3.1 Timeline Display (1D)

```python
def display_timeline_forecast(
    forecast_points: List[GreeksForecastPoint],
    greeks_filter: str = 'all',
    format: str = 'table'
):
    """Display Greeks forecast over time (single stock price)"""

    if format == 'table':
        # Rich table format
        from rich.table import Table
        from rich.console import Console

        console = Console()
        table = Table(title="📈 Greeks Forecast Timeline", show_header=True)

        # Columns
        table.add_column("Days Fwd", style="cyan")
        table.add_column("Date", style="blue")
        table.add_column("DTE", style="yellow")

        # Add Greek columns based on filter
        greek_names = _get_greeks_to_display(greeks_filter)
        for greek in greek_names:
            table.add_column(greek.capitalize(), style="green")

        # Rows
        for point in forecast_points:
            row = [
                f"T+{point.days_forward}",
                point.date.isoformat(),
                str(point.days_to_expiry)
            ]

            for greek in greek_names:
                value = point.greeks.get(greek, 0.0)
                row.append(f"{value:.4f}")

            table.add_row(*row)

        console.print(table)

        # Add interpretation
        _display_forecast_insights(forecast_points)

    elif format == 'csv':
        # CSV output
        import csv
        import sys
        writer = csv.writer(sys.stdout)
        # ... CSV formatting ...

    elif format == 'json':
        # JSON output
        import json
        data = [
            {
                'days_forward': p.days_forward,
                'date': p.date.isoformat(),
                'days_to_expiry': p.days_to_expiry,
                'greeks': p.greeks
            }
            for p in forecast_points
        ]
        click.echo(json.dumps(data, indent=2))
```

#### 3.2 Matrix Display (2D)

```python
def display_matrix_forecast(
    forecast_matrix: List[List[GreeksForecastPoint]],
    greeks_filter: str = 'all',
    format: str = 'table'
):
    """Display Greeks forecast matrix (time × stock price)"""

    if format == 'table':
        # Display as heatmap-style table for each Greek
        console = Console()

        greek_names = _get_greeks_to_display(greeks_filter)

        for greek in greek_names:
            table = Table(title=f"📊 {greek.upper()} Forecast Matrix")

            # Header: stock prices
            table.add_column("Days Fwd", style="cyan")
            stock_prices = [point.stock_price for point in forecast_matrix[0]]
            for price in stock_prices:
                table.add_column(f"${price:.2f}", style="blue")

            # Rows: time points
            for time_row in forecast_matrix:
                days_fwd = time_row[0].days_forward
                row_data = [f"T+{days_fwd}"]

                for point in time_row:
                    value = point.greeks.get(greek, 0.0)
                    # Color-code based on magnitude
                    styled_value = _style_greek_value(value, greek)
                    row_data.append(styled_value)

                table.add_row(*row_data)

            console.print(table)
            console.print()  # Blank line between tables
```

#### 3.3 Insights & Interpretation

```python
def _display_forecast_insights(forecast_points: List[GreeksForecastPoint]):
    """Display automated insights about the forecast"""
    console = Console()

    console.print("\n💡 Forecast Insights:", style="bold yellow")

    # Delta drift
    delta_change = forecast_points[-1].greeks['delta'] - forecast_points[0].greeks['delta']
    if abs(delta_change) > 0.1:
        console.print(f"  • Delta drift: {delta_change:+.3f} over forecast period")
        if delta_change > 0:
            console.print("    ↗️  Position becoming more bullish")
        else:
            console.print("    ↘️  Position becoming more bearish")

    # Theta decay
    theta_now = forecast_points[0].greeks['theta']
    theta_later = forecast_points[-1].greeks['theta']
    if abs(theta_later) > abs(theta_now) * 1.5:
        console.print(f"  • Theta acceleration: ${theta_later:.2f}/day at end")
        console.print("    ⚡ Time decay increasing - consider early exit")

    # Vega decay
    vega_pct_change = (forecast_points[-1].greeks['vega'] - forecast_points[0].greeks['vega']) / forecast_points[0].greeks['vega'] * 100
    if vega_pct_change < -30:
        console.print(f"  • Vega decay: {vega_pct_change:.1f}%")
        console.print("    📉 Volatility exposure declining")

    # Critical time points
    for i, point in enumerate(forecast_points):
        if point.days_to_expiry <= 7 and i > 0:
            console.print(f"  ⚠️  Critical: {point.days_to_expiry} DTE at T+{point.days_forward}")
            console.print("    Gamma risk increases sharply near expiration")
            break
```

### Phase 4: Visualization (1.5 hours)

**File**: `quantlab/visualization/greeks_forecast_plot.py`

#### 4.1 Time Series Plot

```python
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def generate_forecast_plot(
    forecast_data,
    output_file: str = None
):
    """Generate matplotlib visualization of Greeks forecast"""

    if isinstance(forecast_data[0], GreeksForecastPoint):
        # 1D: Timeline plot
        _plot_timeline(forecast_data, output_file)
    else:
        # 2D: Matrix heatmap
        _plot_matrix(forecast_data, output_file)


def _plot_timeline(forecast_points: List[GreeksForecastPoint], output_file: str):
    """Plot Greeks over time"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Greeks Forecast Timeline', fontsize=16, fontweight='bold')

    dates = [p.date for p in forecast_points]

    # Plot 1: Delta
    ax = axes[0, 0]
    deltas = [p.greeks['delta'] for p in forecast_points]
    ax.plot(dates, deltas, 'o-', color='blue', linewidth=2, markersize=6)
    ax.set_title('Delta Evolution')
    ax.set_ylabel('Delta')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)

    # Plot 2: Theta
    ax = axes[0, 1]
    thetas = [p.greeks['theta'] for p in forecast_points]
    ax.plot(dates, thetas, 'o-', color='red', linewidth=2, markersize=6)
    ax.set_title('Theta (Daily P&L from Time Decay)')
    ax.set_ylabel('Theta ($)')
    ax.grid(True, alpha=0.3)

    # Plot 3: Vega
    ax = axes[1, 0]
    vegas = [p.greeks['vega'] for p in forecast_points]
    ax.plot(dates, vegas, 'o-', color='green', linewidth=2, markersize=6)
    ax.set_title('Vega (Volatility Exposure)')
    ax.set_ylabel('Vega')
    ax.grid(True, alpha=0.3)

    # Plot 4: Advanced Greeks
    ax = axes[1, 1]
    vannas = [p.greeks['vanna'] for p in forecast_points]
    charms = [p.greeks['charm'] for p in forecast_points]
    ax.plot(dates, vannas, 'o-', label='Vanna', linewidth=2, markersize=5)
    ax.plot(dates, charms, 's-', label='Charm', linewidth=2, markersize=5)
    ax.set_title('Advanced Greeks')
    ax.set_ylabel('Value')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Format x-axis
    for ax in axes.flat:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        click.echo(f"📊 Plot saved to: {output_file}")
    else:
        plt.show()
```

#### 4.2 Heatmap (2D)

```python
def _plot_matrix(forecast_matrix, output_file: str):
    """Plot Greeks as heatmap matrix"""
    import seaborn as sns

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Greeks Forecast Matrix (Time × Stock Price)', fontsize=16)

    greeks_to_plot = ['delta', 'theta', 'vega', 'vanna']

    for idx, greek in enumerate(greeks_to_plot):
        ax = axes[idx // 2, idx % 2]

        # Extract data for this Greek
        data = []
        for time_row in forecast_matrix:
            row_values = [point.greeks[greek] for point in time_row]
            data.append(row_values)

        # Create heatmap
        sns.heatmap(data, annot=True, fmt='.3f', cmap='RdYlGn',
                   center=0, ax=ax, cbar_kws={'label': greek.capitalize()})

        ax.set_title(f'{greek.capitalize()} Forecast')
        ax.set_xlabel('Stock Price Scenario')
        ax.set_ylabel('Days Forward')

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    else:
        plt.show()
```

---

## Example Outputs

### Example 1: Timeline Forecast

```bash
$ quantlab strategy greeks-forecast results/iron_condor.json \
    --time-points "0,7,14,21,30"

📈 Greeks Forecast Timeline
┏━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Days Fwd ┃ Date       ┃ DTE ┃ Delta   ┃ Gamma   ┃ Theta  ┃ Vega   ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ T+0      │ 2025-10-16 │ 64  │ -0.0027 │ -0.0045 │ 0.0100 │ -0.125 │
│ T+7      │ 2025-10-23 │ 57  │ -0.0031 │ -0.0052 │ 0.0115 │ -0.108 │
│ T+14     │ 2025-10-30 │ 50  │ -0.0038 │ -0.0062 │ 0.0135 │ -0.089 │
│ T+21     │ 2025-11-06 │ 43  │ -0.0048 │ -0.0078 │ 0.0165 │ -0.067 │
│ T+30     │ 2025-11-15 │ 34  │ -0.0065 │ -0.0105 │ 0.0225 │ -0.042 │
└──────────┴────────────┴─────┴─────────┴─────────┴────────┴────────┘

💡 Forecast Insights:
  • Delta drift: -0.004 over forecast period
    ↘️  Position becoming more bearish
  • Theta acceleration: $0.02/day at end
    ⚡ Time decay increasing - consider early exit
  • Vega decay: -66.4%
    📉 Volatility exposure declining
```

### Example 2: Matrix Forecast

```bash
$ quantlab strategy greeks-forecast results/long_straddle.json \
    --time-points "0,15,30" --stock-range "-10%,0%,+10%"

📊 DELTA Forecast Matrix
┏━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Days Fwd ┃ $405.0 ┃ $450.0 ┃ $495.0 ┃
┡━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ T+0      │ -0.425 │ 0.015  │ 0.455  │
│ T+15     │ -0.512 │ 0.018  │ 0.548  │
│ T+30     │ -0.655 │ 0.023  │ 0.701  │
└──────────┴────────┴────────┴────────┘

📊 VEGA Forecast Matrix
┏━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Days Fwd ┃ $405.0 ┃ $450.0 ┃ $495.0 ┃
┡━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ T+0      │ 0.145  │ 0.180  │ 0.145  │
│ T+15     │ 0.118  │ 0.155  │ 0.118  │
│ T+30     │ 0.078  │ 0.112  │ 0.078  │
└──────────┴────────┴────────┴────────┘
```

---

## Implementation Timeline

| Phase | Task | Time | Cumulative |
|-------|------|------|------------|
| 1 | Core calculation engine | 2 hours | 2 hours |
| 2 | CLI integration | 1.5 hours | 3.5 hours |
| 3 | Display formatters | 1.5 hours | 5 hours |
| 4 | Visualization | 1.5 hours | 6.5 hours |
| 5 | Testing | 1 hour | 7.5 hours |
| 6 | Documentation | 0.5 hours | 8 hours |
| **Total** | | **~8 hours** | **1 work day** |

---

## Testing Strategy

### Unit Tests

```python
# tests/analysis/test_greeks_forecast.py

class TestGreeksForecastCalculator:
    def test_timeline_forecast_basic(self):
        """Test basic timeline forecast"""
        strategy = StrategyBuilder.long_call(...)
        calculator = GreeksForecastCalculator(strategy)

        forecast = calculator.forecast_timeline(
            forecast_days=30,
            time_steps=5
        )

        assert len(forecast) == 5
        assert forecast[0].days_forward == 0
        assert forecast[-1].days_forward == 30

    def test_greeks_decay_over_time(self):
        """Test that vega decays as expiration approaches"""
        # Vega should decrease over time
        assert forecast[0].greeks['vega'] > forecast[-1].greeks['vega']

    def test_matrix_forecast(self):
        """Test 2D matrix forecast"""
        forecast = calculator.forecast_matrix(
            time_points=[0, 10, 20],
            stock_prices=[95, 100, 105]
        )

        assert len(forecast) == 3  # 3 time points
        assert len(forecast[0]) == 3  # 3 price points
```

### Integration Tests

```python
# tests/cli/test_greeks_forecast_cli.py

def test_forecast_command_basic(runner):
    """Test basic forecast command"""
    result = runner.invoke(cli, [
        'strategy', 'greeks-forecast',
        'results/test_strategy.json',
        '--time-points', '0,10,20'
    ])

    assert result.exit_code == 0
    assert 'Greeks Forecast' in result.output
    assert 'T+0' in result.output
    assert 'T+10' in result.output
```

---

## Success Criteria

- ✅ Command accepts both file and inline strategy building
- ✅ Forecasts Greeks at multiple time points
- ✅ Supports 1D (time) and 2D (time × price) forecasts
- ✅ Three output formats: table, CSV, JSON
- ✅ Optional matplotlib visualization
- ✅ Automated insights and interpretations
- ✅ Comprehensive test coverage
- ✅ Clear documentation and examples

---

## Future Enhancements (Optional)

### Advanced Features
1. **Volatility scenarios**: Forecast under different IV assumptions
2. **Monte Carlo simulation**: Probabilistic forecast
3. **Optimal exit points**: Suggest when to close position
4. **Comparative forecasts**: Compare multiple strategies side-by-side
5. **Interactive mode**: Real-time adjustments and what-if analysis

### Integration
1. **Export to dashboard**: Save forecast data for web visualization
2. **Alert triggers**: Notify when Greeks cross thresholds
3. **Historical validation**: Compare forecasts to actual Greeks evolution

---

## Risk & Considerations

### Technical Risks
- **Accuracy**: Forecasts assume constant IV - may not reflect reality
- **Performance**: Matrix calculations can be slow for many scenarios
- **Complexity**: 2D displays may be hard to read in terminal

### Mitigations
- Add disclaimer about forecast limitations
- Optimize calculations with numpy vectorization
- Provide both summary and detailed views
- Allow CSV/JSON export for external analysis

---

## Documentation Updates

### User Guide
- Add "Greeks Forecasting" section
- Include practical examples for common strategies
- Explain how to interpret forecast results
- Describe limitations and assumptions

### CLI Help Text
- Comprehensive `--help` for all options
- Examples in help text
- Link to online documentation

---

## Dependencies

**Required**:
- ✅ Existing `calculate_advanced_greeks()` function
- ✅ OptionsStrategy and StrategyBuilder
- ✅ Click CLI framework

**Optional**:
- matplotlib (for --plot)
- seaborn (for heatmaps)
- rich (for enhanced tables)

**No new dependencies required for core functionality!**

---

## Next Steps

1. Review and approve plan
2. Implement Phase 1 (core engine)
3. Add CLI command (Phase 2)
4. Implement display (Phase 3)
5. Add visualization (Phase 4)
6. Write tests (Phase 5)
7. Update documentation (Phase 6)
8. User acceptance testing

---

**Ready to implement?** This feature will provide powerful insights for options traders to manage time decay and plan position adjustments! 📈
