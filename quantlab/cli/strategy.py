"""
Options Strategy CLI commands

Create, analyze, and compare options trading strategies.
"""

import click
import json
from datetime import datetime, timedelta
from tabulate import tabulate
from pathlib import Path

from ..analysis.options_strategies import StrategyBuilder, StrategyType
from ..visualization import create_payoff_diagram, save_figure
import numpy as np


@click.group()
def strategy():
    """Options trading strategies"""
    pass


@strategy.command('list')
def list_strategies():
    """List all available options strategies"""
    click.echo("\n📊 Available Options Strategies\n")

    strategies = {
        "Single-Leg Strategies": [
            ("Long Call", "Bullish speculation with limited risk"),
            ("Long Put", "Bearish speculation with limited risk"),
            ("Covered Call", "Generate income on stock holdings"),
            ("Protective Put", "Protect stock position with downside insurance"),
            ("Cash-Secured Put", "Generate income or acquire stock at discount"),
        ],
        "Vertical Spreads": [
            ("Bull Call Spread", "Bullish with capped profit and loss"),
            ("Bull Put Spread", "Bullish credit spread"),
            ("Bear Call Spread", "Bearish credit spread"),
            ("Bear Put Spread", "Bearish with capped profit and loss"),
        ],
        "Advanced Strategies": [
            ("Iron Condor", "Profit from range-bound movement"),
            ("Butterfly", "Profit from low volatility around target price"),
            ("Straddle", "Profit from high volatility (any direction)"),
            ("Strangle", "Profit from high volatility (cheaper than straddle)"),
            ("Calendar Spread", "Profit from time decay and volatility"),
        ]
    }

    for category, strats in strategies.items():
        click.echo(f"🎯 {category}:")
        for name, desc in strats:
            click.echo(f"  • {name:<25} {desc}")
        click.echo()

    click.echo("💡 Use 'quantlab strategy build <strategy_type> --help' for details")


@strategy.command('build')
@click.argument('strategy_type', type=click.Choice([
    'long_call', 'long_put', 'covered_call', 'protective_put', 'cash_secured_put',
    'bull_call_spread', 'bull_put_spread', 'bear_call_spread', 'bear_put_spread',
    'iron_condor', 'butterfly', 'straddle', 'strangle', 'calendar_spread'
]))
@click.option('--ticker', required=True, help='Underlying ticker symbol')
@click.option('--stock-price', type=float, required=True, help='Current stock price')
@click.option('--strike', type=float, help='Strike price (for single-leg strategies)')
@click.option('--premium', type=float, help='Option premium (for single-leg strategies)')
@click.option('--quantity', type=int, default=1, help='Number of contracts (default: 1)')
@click.option('--expiration', help='Expiration date (YYYY-MM-DD)')
@click.option('--shares', type=int, help='Number of shares (for covered call/protective put)')
# Multi-leg options
@click.option('--strikes', help='Comma-separated strikes (e.g., 100,105 for spreads)')
@click.option('--premiums', help='Comma-separated premiums (e.g., 2.50,1.20)')
@click.option('--position', type=click.Choice(['long', 'short']), default='long', help='For straddle/strangle')
@click.option('--option-type', type=click.Choice(['call', 'put']), default='call', help='For butterfly/calendar')
# Calendar spread specific
@click.option('--near-expiration', help='Near-term expiration (YYYY-MM-DD)')
@click.option('--far-expiration', help='Far-term expiration (YYYY-MM-DD)')
# Advanced Greeks parameters
@click.option('--iv', type=float, help='Implied volatility (decimal, e.g., 0.35 for 35%)')
@click.option('--risk-free-rate', type=float, default=0.05, help='Risk-free rate (default: 0.05)')
@click.option('--output', type=click.Path(), help='Save strategy to JSON file')
@click.option('--chart', type=click.Path(), help='Generate payoff diagram and save to HTML file')
def build_strategy(strategy_type, ticker, stock_price, strike, premium, quantity,
                   expiration, shares, strikes, premiums, position, option_type,
                   near_expiration, far_expiration, iv, risk_free_rate, output, chart):
    """
    Build an options strategy

    Examples:

      # Long Call
      quantlab strategy build long_call --ticker AAPL --stock-price 175 \\
        --strike 180 --premium 3.50 --expiration 2025-12-19

      # Covered Call
      quantlab strategy build covered_call --ticker AAPL --stock-price 175 \\
        --strike 180 --premium 3.50 --shares 100 --expiration 2025-12-19

      # Bull Call Spread
      quantlab strategy build bull_call_spread --ticker AAPL --stock-price 175 \\
        --strikes 170,180 --premiums 7.50,3.50 --expiration 2025-12-19

      # Iron Condor
      quantlab strategy build iron_condor --ticker SPY --stock-price 450 \\
        --strikes 440,445,455,460 --premiums 1.00,2.50,2.50,1.00 --expiration 2025-12-19
    """
    try:
        # Parse expiration
        if expiration:
            exp_date = datetime.strptime(expiration, '%Y-%m-%d').date()
        else:
            # Default to 30 days from now
            exp_date = (datetime.now() + timedelta(days=30)).date()

        # Parse strikes and premiums for multi-leg strategies
        strike_list = [float(s.strip()) for s in strikes.split(',')] if strikes else []
        premium_list = [float(p.strip()) for p in premiums.split(',')] if premiums else []

        # Build strategy based on type
        if strategy_type == 'long_call':
            if not strike or not premium:
                raise ValueError("--strike and --premium required for long_call")
            strat = StrategyBuilder.long_call(stock_price, strike, premium, quantity, exp_date, ticker)

        elif strategy_type == 'long_put':
            if not strike or not premium:
                raise ValueError("--strike and --premium required for long_put")
            strat = StrategyBuilder.long_put(stock_price, strike, premium, quantity, exp_date, ticker)

        elif strategy_type == 'covered_call':
            if not strike or not premium or not shares:
                raise ValueError("--strike, --premium, and --shares required for covered_call")
            strat = StrategyBuilder.covered_call(stock_price, shares, strike, premium, exp_date, ticker,
                                                implied_volatility=iv, risk_free_rate=risk_free_rate)

        elif strategy_type == 'protective_put':
            if not strike or not premium or not shares:
                raise ValueError("--strike, --premium, and --shares required for protective_put")
            strat = StrategyBuilder.protective_put(stock_price, shares, strike, premium, exp_date, ticker)

        elif strategy_type == 'cash_secured_put':
            if not strike or not premium:
                raise ValueError("--strike and --premium required for cash_secured_put")
            strat = StrategyBuilder.cash_secured_put(stock_price, strike, premium, quantity, exp_date, ticker)

        elif strategy_type == 'bull_call_spread':
            if len(strike_list) != 2 or len(premium_list) != 2:
                raise ValueError("--strikes and --premiums must have 2 values (e.g., --strikes 100,105 --premiums 5.00,2.50)")
            strat = StrategyBuilder.bull_call_spread(
                stock_price, strike_list[0], strike_list[1],
                premium_list[0], premium_list[1], quantity, exp_date, ticker,
                implied_volatility=iv, risk_free_rate=risk_free_rate
            )

        elif strategy_type == 'bull_put_spread':
            if len(strike_list) != 2 or len(premium_list) != 2:
                raise ValueError("--strikes and --premiums must have 2 values")
            strat = StrategyBuilder.bull_put_spread(
                stock_price, strike_list[0], strike_list[1],
                premium_list[0], premium_list[1], quantity, exp_date, ticker
            )

        elif strategy_type == 'bear_call_spread':
            if len(strike_list) != 2 or len(premium_list) != 2:
                raise ValueError("--strikes and --premiums must have 2 values")
            strat = StrategyBuilder.bear_call_spread(
                stock_price, strike_list[1], strike_list[0],
                premium_list[1], premium_list[0], quantity, exp_date, ticker
            )

        elif strategy_type == 'bear_put_spread':
            if len(strike_list) != 2 or len(premium_list) != 2:
                raise ValueError("--strikes and --premiums must have 2 values")
            strat = StrategyBuilder.bear_put_spread(
                stock_price, strike_list[1], strike_list[0],
                premium_list[1], premium_list[0], quantity, exp_date, ticker
            )

        elif strategy_type == 'iron_condor':
            if len(strike_list) != 4 or len(premium_list) != 4:
                raise ValueError("--strikes and --premiums must have 4 values (put_long, put_short, call_short, call_long)")
            strat = StrategyBuilder.iron_condor(
                stock_price, strike_list[0], strike_list[1], strike_list[2], strike_list[3],
                premium_list[0], premium_list[1], premium_list[2], premium_list[3],
                quantity, exp_date, ticker,
                implied_volatility=iv, risk_free_rate=risk_free_rate
            )

        elif strategy_type == 'butterfly':
            if len(strike_list) != 3 or len(premium_list) != 3:
                raise ValueError("--strikes and --premiums must have 3 values (lower, middle, upper)")
            strat = StrategyBuilder.butterfly(
                stock_price, strike_list[0], strike_list[1], strike_list[2],
                premium_list[0], premium_list[1], premium_list[2],
                quantity, exp_date, option_type, ticker
            )

        elif strategy_type == 'straddle':
            if len(premium_list) != 2:
                raise ValueError("--premiums must have 2 values (call_premium, put_premium)")
            if not strike:
                raise ValueError("--strike required for straddle")
            strat = StrategyBuilder.straddle(
                stock_price, strike, premium_list[0], premium_list[1],
                quantity, exp_date, position, ticker
            )

        elif strategy_type == 'strangle':
            if len(strike_list) != 2 or len(premium_list) != 2:
                raise ValueError("--strikes and --premiums must have 2 values (put_strike, call_strike)")
            strat = StrategyBuilder.strangle(
                stock_price, strike_list[0], strike_list[1],
                premium_list[0], premium_list[1], quantity, exp_date, position, ticker
            )

        elif strategy_type == 'calendar_spread':
            if not near_expiration or not far_expiration:
                raise ValueError("--near-expiration and --far-expiration required for calendar_spread")
            if not strike or len(premium_list) != 2:
                raise ValueError("--strike and --premiums (near,far) required for calendar_spread")
            near_exp = datetime.strptime(near_expiration, '%Y-%m-%d').date()
            far_exp = datetime.strptime(far_expiration, '%Y-%m-%d').date()
            strat = StrategyBuilder.calendar_spread(
                stock_price, strike, premium_list[0], premium_list[1],
                near_exp, far_exp, quantity, option_type, ticker
            )

        else:
            raise ValueError(f"Unsupported strategy type: {strategy_type}")

        # Display strategy summary
        click.echo(f"\n📊 {strat.name}")
        click.echo(f"   {strat.metadata.get('strategy_description', '')}\n")

        # Display legs
        click.echo("Strategy Legs:")
        leg_data = []
        for i, leg in enumerate(strat.legs, 1):
            leg_data.append([
                i,
                leg.option_type.value.upper(),
                leg.position_type.value.upper(),
                f"${leg.strike:.2f}",
                f"${leg.premium:.2f}",
                leg.quantity,
                leg.expiration.isoformat() if leg.expiration else "N/A"
            ])
        click.echo(tabulate(leg_data,
                          headers=['#', 'Type', 'Position', 'Strike', 'Premium', 'Qty', 'Expiration'],
                          tablefmt='simple'))

        if strat.stock_position != 0:
            click.echo(f"\nStock Position: {strat.stock_position} shares")

        # Display risk metrics
        click.echo("\n📈 Risk Analysis:")
        metrics = strat.risk_metrics()

        click.echo(f"  Net Premium: ${metrics['net_premium']:.2f} ({metrics['debit_credit']})")

        if metrics['max_profit'] is not None:
            if metrics['max_profit'] == float('inf'):
                click.echo(f"  Max Profit: Unlimited")
            else:
                click.echo(f"  Max Profit: ${metrics['max_profit']:.2f}")

        if metrics['max_loss'] is not None:
            if metrics['max_loss'] == float('-inf'):
                click.echo(f"  Max Loss: Unlimited")
            else:
                click.echo(f"  Max Loss: ${metrics['max_loss']:.2f}")

        if metrics['risk_reward_ratio']:
            click.echo(f"  Risk/Reward: {metrics['risk_reward_ratio']:.2f}")

        if metrics['breakeven_points']:
            be_str = ", ".join(f"${be:.2f}" for be in metrics['breakeven_points'])
            click.echo(f"  Breakeven: {be_str}")

        if metrics['probability_of_profit']:
            click.echo(f"  Probability of Profit: ~{metrics['probability_of_profit']:.0f}%")

        # Display advanced Greeks if IV provided
        if iv:
            click.echo("\n📊 Advanced Greeks Analysis:")

            greeks = strat.advanced_greeks()

            click.echo("\nFirst-Order Greeks:")
            click.echo(f"  Delta: {greeks['delta']:.4f} (${greeks['delta'] * stock_price * 100:,.0f} exposure)")
            click.echo(f"  Gamma: {greeks['gamma']:.6f}")
            click.echo(f"  Theta: {greeks['theta']:.2f} (per day)")
            click.echo(f"  Vega:  {greeks['vega']:.2f} (per 1% vol)")

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
                days_to_change = 0.1 / abs(greeks['charm']) if greeks['charm'] != 0 else 999
                click.echo(f"  • Charm: Delta will {direction} by {abs(greeks['charm']):.4f} per day (~0.1 change in {days_to_change:.0f} days)")

            # Vomma interpretation
            if abs(greeks['vomma']) > 0.01:
                direction = "increase" if greeks['vomma'] > 0 else "decrease"
                click.echo(f"  • Vomma: Vega will {direction} if volatility rises")

            # Overall position assessment
            click.echo("\n⚠️  Risk Profile:")
            if abs(greeks['delta']) < 0.1:
                click.echo("  ✅ DELTA-NEUTRAL - Low directional risk")
            elif abs(greeks['delta']) < 0.5:
                click.echo("  ⚡ MODERATE DELTA - Some directional exposure")
            else:
                click.echo("  ⚠️  HIGH DELTA - Significant directional risk")

            if greeks['theta'] > 0:
                click.echo("  ✅ POSITIVE THETA - Earning time decay")
            elif greeks['theta'] < -10:
                click.echo("  ⚠️  NEGATIVE THETA - Losing to time decay")

            if abs(greeks['vanna']) < 0.03:
                click.echo("  ✅ LOW VANNA - Delta stable across vol changes")
            else:
                click.echo("  ⚠️  HIGH VANNA - Delta sensitive to volatility")

        # Generate payoff diagram if requested
        if chart:
            click.echo("\n📈 Generating payoff diagram...")

            # Generate price range (±30% from current price)
            price_min = stock_price * 0.7
            price_max = stock_price * 1.3
            prices = np.linspace(price_min, price_max, 100)

            # Calculate P&L at each price
            pnls = np.array([strat.pnl_at_price(p) for p in prices])

            # Get risk metrics for chart annotations
            metrics = strat.risk_metrics()

            # Create payoff diagram
            fig = create_payoff_diagram(
                prices=prices,
                pnls=pnls,
                strategy_name=strat.name,
                current_price=stock_price,
                breakeven_points=metrics['breakeven_points'],
                max_profit=metrics['max_profit'] if metrics['max_profit'] != float('inf') else None,
                max_loss=metrics['max_loss'] if metrics['max_loss'] != float('-inf') else None
            )

            # Save chart
            chart_path = Path(chart)
            chart_path.parent.mkdir(parents=True, exist_ok=True)
            save_figure(fig, str(chart_path))
            click.echo(f"📊 Payoff diagram saved to: {chart_path}")
            click.echo(f"   Open in browser to view interactive chart")

        # Save to file if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(strat.to_dict(), f, indent=2)
            click.echo(f"\n💾 Strategy saved to: {output_path}")
            click.echo(f"   Use 'quantlab strategy analyze {output_path}' to analyze further")

    except ValueError as e:
        click.echo(f"❌ Invalid input: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Failed to build strategy: {e}", err=True)


@strategy.command('analyze')
@click.argument('strategy_file', type=click.Path(exists=True))
@click.option('--price-range', help='Price range for analysis (e.g., 150,200)')
@click.option('--price-points', type=int, default=20, help='Number of price points to analyze')
def analyze_strategy(strategy_file, price_range, price_points):
    """
    Analyze a saved strategy from JSON file

    Example:
      quantlab strategy analyze results/my_strategy.json --price-range 160,190
    """
    try:
        # Load strategy from file
        with open(strategy_file, 'r') as f:
            data = json.load(f)

        click.echo(f"\n📊 Strategy Analysis: {data['name']}")
        click.echo(f"   Type: {data['strategy_type']}")
        click.echo(f"   Current Stock Price: ${data['current_stock_price']:.2f}\n")

        # Display risk metrics
        metrics = data['risk_metrics']
        click.echo("📈 Risk Metrics:")
        click.echo(f"  Net Premium: ${metrics['net_premium']:.2f} ({metrics['debit_credit']})")
        if metrics['max_profit']:
            click.echo(f"  Max Profit: ${metrics['max_profit']:.2f}")
        if metrics['max_loss']:
            click.echo(f"  Max Loss: ${metrics['max_loss']:.2f}")
        if metrics['breakeven_points']:
            be_str = ", ".join(f"${be:.2f}" for be in metrics['breakeven_points'])
            click.echo(f"  Breakeven: {be_str}")

        # TODO: Generate P&L at different prices
        # This would require reconstructing the OptionsStrategy object from JSON
        # For now, just display the stored metrics

        click.echo("\n💡 To visualize payoff diagram, export to external plotting tool")

    except Exception as e:
        click.echo(f"❌ Failed to analyze strategy: {e}", err=True)


@strategy.command('compare')
@click.argument('strategy_files', nargs=-1, required=True, type=click.Path(exists=True))
def compare_strategies(strategy_files):
    """
    Compare multiple strategies side-by-side

    Example:
      quantlab strategy compare strategy1.json strategy2.json strategy3.json
    """
    try:
        if len(strategy_files) < 2:
            click.echo("❌ Need at least 2 strategies to compare", err=True)
            return

        click.echo(f"\n📊 Comparing {len(strategy_files)} Strategies\n")

        # Load all strategies
        strategies = []
        for file_path in strategy_files:
            with open(file_path, 'r') as f:
                strategies.append(json.load(f))

        # Build comparison table
        comparison = []
        for strat in strategies:
            metrics = strat['risk_metrics']
            comparison.append([
                strat['name'][:30],
                strat['strategy_type'],
                f"${strat['current_stock_price']:.2f}",
                f"${metrics['net_premium']:.2f}",
                f"${metrics['max_profit']:.2f}" if metrics['max_profit'] else "Unlimited",
                f"${metrics['max_loss']:.2f}" if metrics['max_loss'] else "Unlimited",
                f"{metrics['risk_reward_ratio']:.2f}" if metrics['risk_reward_ratio'] else "N/A"
            ])

        headers = ['Strategy', 'Type', 'Stock Price', 'Net Premium', 'Max Profit', 'Max Loss', 'Risk/Reward']
        click.echo(tabulate(comparison, headers=headers, tablefmt='grid'))

        click.echo("\n💡 Use 'quantlab strategy analyze <file>' for detailed analysis")

    except Exception as e:
        click.echo(f"❌ Failed to compare strategies: {e}", err=True)
