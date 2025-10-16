"""
Visualization CLI commands for charts and dashboards
"""

import click
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


@click.group()
def visualize():
    """Create interactive charts and visualizations"""
    pass


@visualize.command('backtest')
@click.argument('run_id')
@click.option('--output', type=click.Path(), help='Output HTML file path (default: results/backtest_viz.html)')
@click.option('--strategy-name', default='Strategy', help='Strategy display name')
@click.option('--benchmark-name', default='Benchmark', help='Benchmark display name')
@click.option('--chart-type', type=click.Choice(['dashboard', 'returns', 'drawdown', 'heatmap', 'sharpe']),
              default='dashboard', help='Chart type to generate')
@click.pass_context
def visualize_backtest(ctx, run_id, output, strategy_name, benchmark_name, chart_type):
    """
    Visualize backtest results from MLflow run

    Examples:
        quantlab visualize backtest <run_id>
        quantlab visualize backtest <run_id> --chart-type returns
        quantlab visualize backtest <run_id> --output results/my_backtest.html
        quantlab visualize backtest <run_id> --strategy-name "Tech Strategy" --benchmark-name SPY
    """
    try:
        from ..visualization import (
            load_backtest_report,
            create_backtest_dashboard,
            create_cumulative_returns_chart,
            create_drawdown_chart,
            create_monthly_returns_heatmap,
            create_rolling_sharpe_chart,
            calculate_backtest_metrics,
            save_figure
        )

        click.echo(f"\n📊 Loading backtest results for run: {run_id}...\n")

        # Construct MLflow run path
        mlruns_base = Path("results/mlruns")

        # Try to find the run (could be in different experiments)
        run_path = None
        for exp_dir in mlruns_base.glob("*/"):
            if exp_dir.is_dir() and exp_dir.name != "0" and exp_dir.name != ".trash":
                potential_path = exp_dir / run_id
                if potential_path.exists():
                    run_path = potential_path
                    break

        if not run_path:
            click.echo(f"❌ Run {run_id} not found in {mlruns_base}", err=True)
            click.echo(f"\nTip: Use 'mlflow ui' in results/ directory to browse available runs", err=True)
            return

        # Load backtest data
        try:
            report_df = load_backtest_report(str(run_path))
        except FileNotFoundError as e:
            click.echo(f"❌ Backtest report not found: {e}", err=True)
            return

        click.echo(f"✓ Loaded backtest data: {len(report_df)} days")

        # Calculate metrics
        metrics = calculate_backtest_metrics(report_df)
        click.echo(f"\n📈 Performance Metrics:")
        click.echo(f"   Total Return: {metrics['total_return']:.2%}")
        click.echo(f"   Annual Return: {metrics['annual_return']:.2%}")
        click.echo(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        click.echo(f"   Max Drawdown: {metrics['max_drawdown']:.2%}")
        click.echo(f"   Win Rate: {metrics['win_rate']:.2%}")
        click.echo()

        # Generate chart based on type
        if chart_type == 'dashboard':
            fig = create_backtest_dashboard(
                report_df,
                strategy_name=strategy_name,
                benchmark_name=benchmark_name
            )
        elif chart_type == 'returns':
            fig = create_cumulative_returns_chart(
                report_df,
                title=f"{strategy_name} - Cumulative Returns",
                benchmark_name=benchmark_name
            )
        elif chart_type == 'drawdown':
            fig = create_drawdown_chart(
                report_df,
                title=f"{strategy_name} - Drawdown"
            )
        elif chart_type == 'heatmap':
            fig = create_monthly_returns_heatmap(
                report_df,
                title=f"{strategy_name} - Monthly Returns"
            )
        elif chart_type == 'sharpe':
            fig = create_rolling_sharpe_chart(
                report_df,
                window=60,
                title=f"{strategy_name} - Rolling Sharpe Ratio"
            )

        # Save figure
        if not output:
            output = f"results/backtest_{chart_type}_{run_id[:8]}.html"

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_figure(fig, str(output_path))

        click.echo(f"📊 Chart saved to: {output_path}")
        click.echo(f"   Open in browser to view interactive chart")

    except Exception as e:
        click.echo(f"❌ Visualization failed: {e}", err=True)
        import traceback
        traceback.print_exc()


@visualize.command('price')
@click.argument('ticker')
@click.option('--period', default='90d', help='Time period (e.g., 7d, 30d, 90d, 1y) - works with both daily and intraday')
@click.option('--interval', type=click.Choice(['1min', '5min', '15min', '30min', '1hour', '1day']),
              default='1day', help='Data interval (1day for daily, 1min-1hour for intraday)')
@click.option('--chart-type', type=click.Choice(['candlestick', 'line', 'technical']),
              default='candlestick', help='Chart type')
@click.option('--output', type=click.Path(), help='Output HTML file path')
@click.pass_context
def visualize_price(ctx, ticker, period, interval, chart_type, output):
    """
    Visualize price data for a ticker

    Examples:
        # Daily data
        quantlab visualize price AAPL
        quantlab visualize price MSFT --period 180d
        quantlab visualize price GOOGL --chart-type line

        # Intraday data (today only)
        quantlab visualize price TSLA --interval 5min
        quantlab visualize price AAPL --interval 1hour

        # Intraday data with historical period
        quantlab visualize price AAPL --interval 5min --period 7d   # 1 week of 5-min bars
        quantlab visualize price MSFT --interval 15min --period 30d  # 1 month of 15-min bars
        quantlab visualize price GOOGL --interval 1hour --period 1y  # 1 year of hourly bars
    """
    try:
        from ..visualization import (
            create_candlestick_chart,
            create_price_line_chart,
            create_technical_dashboard,
            save_figure
        )

        parquet = ctx.obj['parquet']
        data_manager = ctx.obj['data_mgr']

        click.echo(f"\n📈 Loading price data for {ticker}...\n")

        # Handle intraday data
        if interval != '1day':
            # For intraday data, use DataManager
            # Parse period to get date range
            days = _parse_period(period)

            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            from_date = start_date.isoformat()
            to_date = end_date.isoformat()

            # Warn about large data requests
            if days > 30:
                click.echo(f"⚠️  Warning: Requesting {days} days of {interval} data. This may take a while...")

            df = data_manager.get_intraday_prices(
                ticker=ticker,
                interval=interval,
                from_date=from_date,
                to_date=to_date
            )

            if df is None or df.empty:
                click.echo(f"❌ No intraday data available for {ticker}", err=True)
                return

            click.echo(f"✓ Loaded {len(df)} {interval} bars")
            click.echo(f"   Time range: {df['date'].min()} to {df['date'].max()}")
        else:
            # Parse period for daily data
            days = _parse_period(period)

            # Load data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            df = parquet.get_stock_daily(
                tickers=[ticker],
                start_date=start_date,
                end_date=end_date
            )

            if df is None or df.empty:
                click.echo(f"❌ No data available for {ticker}", err=True)
                return

            # Filter to single ticker
            if 'ticker' in df.columns:
                df = df[df['ticker'] == ticker].copy()

            df = df.sort_values('date')

            click.echo(f"✓ Loaded {len(df)} trading days")
            click.echo(f"   Date range: {df['date'].min()} to {df['date'].max()}")

        # Determine if this is intraday data
        is_intraday = interval != '1day'

        # Generate chart
        if chart_type == 'candlestick':
            fig = create_candlestick_chart(df, ticker=ticker, intraday=is_intraday)
        elif chart_type == 'line':
            fig = create_price_line_chart(df, ticker=ticker, intraday=is_intraday)
        elif chart_type == 'technical':
            # Calculate indicators
            df = _calculate_technical_indicators(df)
            fig = create_technical_dashboard(df, ticker=ticker, intraday=is_intraday)

        # Save figure
        if not output:
            interval_str = interval if interval != '1day' else period
            output = f"results/{ticker.lower()}_{chart_type}_{interval_str}.html"

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_figure(fig, str(output_path))

        click.echo(f"\n📊 Chart saved to: {output_path}")
        click.echo(f"   Open in browser to view interactive chart")

    except Exception as e:
        click.echo(f"❌ Visualization failed: {e}", err=True)
        import traceback
        traceback.print_exc()


@visualize.command('compare')
@click.argument('tickers', nargs=-1, required=True)
@click.option('--period', default='90d', help='Time period (e.g., 30d, 90d, 1y)')
@click.option('--normalize/--absolute', default=True, help='Normalize to percentage change or show absolute prices')
@click.option('--output', type=click.Path(), help='Output HTML file path')
@click.pass_context
def visualize_compare(ctx, tickers, period, normalize, output):
    """
    Compare multiple tickers on one chart

    Examples:
        quantlab visualize compare AAPL MSFT GOOGL
        quantlab visualize compare AAPL SPY --period 180d
        quantlab visualize compare TSLA NIO RIVN --absolute
    """
    try:
        from ..visualization import create_multi_ticker_comparison, save_figure

        parquet = ctx.obj['parquet']

        if len(tickers) < 2:
            click.echo("❌ Please provide at least 2 tickers to compare", err=True)
            return

        if len(tickers) > 5:
            click.echo("⚠️  Warning: Comparing more than 5 tickers may be difficult to read", err=True)

        click.echo(f"\n📊 Loading price data for {len(tickers)} tickers...\n")

        # Parse period
        days = _parse_period(period)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Load data for each ticker
        data_dict = {}
        for ticker in tickers:
            df = parquet.get_stock_daily(
                tickers=[ticker],
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                if 'ticker' in df.columns:
                    df = df[df['ticker'] == ticker].copy()
                df = df.sort_values('date')
                data_dict[ticker] = df
                click.echo(f"   ✓ {ticker}: {len(df)} days")
            else:
                click.echo(f"   ✗ {ticker}: No data available")

        if len(data_dict) < 2:
            click.echo(f"\n❌ Need at least 2 tickers with data", err=True)
            return

        # Generate comparison chart
        mode = 'normalized' if normalize else 'absolute'
        click.echo(f"\n📈 Creating comparison chart (mode: {mode})...")

        fig = create_multi_ticker_comparison(
            data_dict,
            normalize=normalize
        )

        # Save figure
        if not output:
            tickers_str = '_'.join([t.lower() for t in list(data_dict.keys())[:3]])
            output = f"results/compare_{tickers_str}_{period}.html"

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_figure(fig, str(output_path))

        click.echo(f"\n📊 Chart saved to: {output_path}")
        click.echo(f"   Open in browser to view interactive chart")

    except Exception as e:
        click.echo(f"❌ Visualization failed: {e}", err=True)
        import traceback
        traceback.print_exc()


@visualize.command('portfolio')
@click.argument('portfolio_id')
@click.option('--chart-type', type=click.Choice(['dashboard', 'allocation', 'pnl']),
              default='dashboard', help='Chart type')
@click.option('--output', type=click.Path(), help='Output HTML file path')
@click.pass_context
def visualize_portfolio(ctx, portfolio_id, chart_type, output):
    """
    Visualize portfolio allocation and performance

    Examples:
        quantlab visualize portfolio tech
        quantlab visualize portfolio growth --chart-type allocation
        quantlab visualize portfolio value --output results/value_portfolio.html
    """
    try:
        from ..visualization import (
            create_portfolio_pie_chart,
            create_position_pnl_chart,
            create_portfolio_summary_dashboard,
            save_figure
        )

        portfolio_mgr = ctx.obj['portfolio_mgr']

        click.echo(f"\n💼 Loading portfolio: {portfolio_id}...\n")

        # Get portfolio
        portfolio = portfolio_mgr.get_portfolio(portfolio_id)

        if not portfolio:
            click.echo(f"❌ Portfolio '{portfolio_id}' not found", err=True)
            click.echo(f"\nTip: Use 'quantlab portfolio list' to see available portfolios", err=True)
            return

        # Get positions
        positions_data = []
        for pos in portfolio.positions:
            positions_data.append({
                'ticker': pos.ticker,
                'weight': pos.weight,
                'value': pos.value,
                'pnl': pos.unrealized_pnl if hasattr(pos, 'unrealized_pnl') else 0,
                'pnl_percent': (pos.unrealized_pnl / pos.cost_basis) if hasattr(pos, 'unrealized_pnl') and pos.cost_basis > 0 else 0
            })

        if not positions_data:
            click.echo(f"❌ Portfolio is empty", err=True)
            return

        click.echo(f"✓ Loaded portfolio: {len(positions_data)} positions")

        # Calculate portfolio totals
        total_value = sum(p['value'] for p in positions_data)
        total_pnl = sum(p['pnl'] for p in positions_data)
        total_pnl_percent = (total_pnl / (total_value - total_pnl)) if (total_value - total_pnl) > 0 else 0

        portfolio_data = {
            'name': portfolio.name,
            'total_value': total_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent
        }

        click.echo(f"   Total Value: ${total_value:,.2f}")
        click.echo(f"   Total P&L: ${total_pnl:,.2f} ({total_pnl_percent:.2%})")
        click.echo()

        # Generate chart
        if chart_type == 'dashboard':
            fig = create_portfolio_summary_dashboard(portfolio_data, positions_data)
        elif chart_type == 'allocation':
            fig = create_portfolio_pie_chart(
                positions_data,
                portfolio_name=portfolio.name,
                value_type='weight'
            )
        elif chart_type == 'pnl':
            fig = create_position_pnl_chart(
                positions_data,
                portfolio_name=portfolio.name
            )

        # Save figure
        if not output:
            output = f"results/portfolio_{portfolio_id}_{chart_type}.html"

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_figure(fig, str(output_path))

        click.echo(f"📊 Chart saved to: {output_path}")
        click.echo(f"   Open in browser to view interactive chart")

    except Exception as e:
        click.echo(f"❌ Visualization failed: {e}", err=True)
        import traceback
        traceback.print_exc()


@visualize.command('options')
@click.argument('strategy_type', type=click.Choice([
    'long_call', 'long_put', 'bull_call_spread', 'bear_put_spread',
    'iron_condor', 'long_straddle', 'short_straddle', 'long_strangle', 'short_strangle'
]))
@click.option('--current-price', type=float, required=True, help='Current underlying price')
@click.option('--strike', type=float, help='Strike price (for single leg strategies)')
@click.option('--strike1', type=float, help='First strike (for multi-leg strategies)')
@click.option('--strike2', type=float, help='Second strike (for multi-leg strategies)')
@click.option('--strike3', type=float, help='Third strike (for 4-leg strategies)')
@click.option('--strike4', type=float, help='Fourth strike (for 4-leg strategies)')
@click.option('--premium', type=float, help='Premium paid/received')
@click.option('--output', type=click.Path(), help='Output HTML file path')
def visualize_options(strategy_type, current_price, strike, strike1, strike2, strike3, strike4, premium, output):
    """
    Visualize options strategy payoff diagram

    Examples:
        quantlab visualize options long_call --current-price 100 --strike 100 --premium 5
        quantlab visualize options bull_call_spread --current-price 100 --strike1 95 --strike2 105
        quantlab visualize options iron_condor --current-price 100 --strike1 90 --strike2 95 --strike3 105 --strike4 110
    """
    try:
        from ..visualization import create_payoff_diagram, create_strategy_comparison, save_figure

        click.echo(f"\n📊 Generating payoff diagram for {strategy_type.replace('_', ' ').title()}...\n")

        # Create price range
        price_min = current_price * 0.8
        price_max = current_price * 1.2
        prices = np.linspace(price_min, price_max, 200)

        # Calculate payoff based on strategy type
        if strategy_type == 'long_call':
            if not strike or not premium:
                click.echo("❌ --strike and --premium required for long_call", err=True)
                return
            pnls = np.maximum(prices - strike, 0) - premium
            breakeven = [strike + premium]
            max_profit = None
            max_loss = -premium

        elif strategy_type == 'long_put':
            if not strike or not premium:
                click.echo("❌ --strike and --premium required for long_put", err=True)
                return
            pnls = np.maximum(strike - prices, 0) - premium
            breakeven = [strike - premium]
            max_profit = strike - premium
            max_loss = -premium

        elif strategy_type == 'bull_call_spread':
            if not strike1 or not strike2:
                click.echo("❌ --strike1 and --strike2 required for bull_call_spread", err=True)
                return
            premium = premium if premium else (strike2 - strike1) * 0.5
            long_call = np.maximum(prices - strike1, 0)
            short_call = np.maximum(prices - strike2, 0)
            pnls = long_call - short_call - premium
            breakeven = [strike1 + premium]
            max_profit = (strike2 - strike1) - premium
            max_loss = -premium

        elif strategy_type == 'bear_put_spread':
            if not strike1 or not strike2:
                click.echo("❌ --strike1 and --strike2 required for bear_put_spread", err=True)
                return
            premium = premium if premium else (strike2 - strike1) * 0.5
            short_put = np.maximum(strike1 - prices, 0)
            long_put = np.maximum(strike2 - prices, 0)
            pnls = long_put - short_put - premium
            breakeven = [strike2 - premium]
            max_profit = (strike2 - strike1) - premium
            max_loss = -premium

        elif strategy_type == 'iron_condor':
            if not all([strike1, strike2, strike3, strike4]):
                click.echo("❌ All 4 strikes required for iron_condor", err=True)
                return
            credit = premium if premium else 6.0
            put_spread = np.minimum(np.maximum(strike2 - prices, 0) - np.maximum(strike1 - prices, 0), strike2 - strike1)
            call_spread = np.minimum(np.maximum(prices - strike3, 0) - np.maximum(prices - strike4, 0), strike4 - strike3)
            pnls = credit - put_spread - call_spread
            breakeven = [strike2 - credit, strike3 + credit]
            max_profit = credit
            max_loss = -(strike4 - strike3 - credit)

        elif strategy_type == 'long_straddle':
            if not strike or not premium:
                click.echo("❌ --strike and --premium required for long_straddle", err=True)
                return
            pnls = np.abs(prices - strike) - premium
            breakeven = [strike - premium, strike + premium]
            max_profit = None
            max_loss = -premium

        elif strategy_type == 'short_straddle':
            if not strike or not premium:
                click.echo("❌ --strike and --premium required for short_straddle", err=True)
                return
            pnls = premium - np.abs(prices - strike)
            breakeven = [strike - premium, strike + premium]
            max_profit = premium
            max_loss = None

        elif strategy_type == 'long_strangle':
            if not strike1 or not strike2 or not premium:
                click.echo("❌ --strike1, --strike2, and --premium required for long_strangle", err=True)
                return
            pnls = np.maximum(prices - strike2, 0) + np.maximum(strike1 - prices, 0) - premium
            breakeven = [strike1 - premium, strike2 + premium]
            max_profit = None
            max_loss = -premium

        elif strategy_type == 'short_strangle':
            if not strike1 or not strike2 or not premium:
                click.echo("❌ --strike1, --strike2, and --premium required for short_strangle", err=True)
                return
            pnls = premium - np.maximum(prices - strike2, 0) - np.maximum(strike1 - prices, 0)
            breakeven = [strike1 - premium, strike2 + premium]
            max_profit = premium
            max_loss = None

        # Create payoff diagram
        fig = create_payoff_diagram(
            prices=prices,
            pnls=pnls,
            strategy_name=strategy_type.replace('_', ' ').title(),
            current_price=current_price,
            breakeven_points=breakeven,
            max_profit=max_profit,
            max_loss=max_loss
        )

        # Save figure
        if not output:
            output = f"results/options_{strategy_type}.html"

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_figure(fig, str(output_path))

        # Display summary
        click.echo(f"✓ Strategy: {strategy_type.replace('_', ' ').title()}")
        click.echo(f"   Current Price: ${current_price:.2f}")
        if breakeven:
            click.echo(f"   Breakeven: {', '.join([f'${b:.2f}' for b in breakeven])}")
        if max_profit is not None:
            click.echo(f"   Max Profit: ${max_profit:.2f}")
        else:
            click.echo(f"   Max Profit: Unlimited")
        if max_loss is not None:
            click.echo(f"   Max Loss: ${max_loss:.2f}")
        else:
            click.echo(f"   Max Loss: Unlimited")
        click.echo()

        click.echo(f"📊 Chart saved to: {output_path}")
        click.echo(f"   Open in browser to view interactive chart")

    except Exception as e:
        click.echo(f"❌ Visualization failed: {e}", err=True)
        import traceback
        traceback.print_exc()


def _parse_period(period_str):
    """Parse period string like '30d', '90d', '1y' into days"""
    period_str = period_str.lower().strip()

    if period_str.endswith('d'):
        return int(period_str[:-1])
    elif period_str.endswith('w'):
        return int(period_str[:-1]) * 7
    elif period_str.endswith('m'):
        return int(period_str[:-1]) * 30
    elif period_str.endswith('y'):
        return int(period_str[:-1]) * 365
    else:
        try:
            return int(period_str)
        except ValueError:
            return 90  # Default to 90 days


def _calculate_technical_indicators(df):
    """Calculate technical indicators for a dataframe"""
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (2 * std)
    df['bb_lower'] = df['bb_middle'] - (2 * std)

    return df.dropna()
