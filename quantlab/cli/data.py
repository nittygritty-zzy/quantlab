"""
Data query CLI commands
"""

import click
from datetime import datetime, timedelta
from tabulate import tabulate


@click.group()
def data():
    """Query historical Parquet data"""
    pass


@data.command('check')
@click.pass_context
def check_data(ctx):
    """Check available Parquet data"""
    try:
        parquet = ctx.obj['parquet']

        click.echo("\n📁 Parquet Data Availability\n")

        availability = parquet.check_data_availability()

        for data_type, info in availability.items():
            status = "✓" if info['exists'] else "✗"
            click.echo(f"{status} {data_type.upper().replace('_', ' ')}")
            click.echo(f"  Path: {info['path']}")

            if info['exists']:
                if info.get('min_date'):
                    click.echo(f"  Date Range: {info['min_date']} to {info['max_date']}")
                if info.get('tickers'):
                    click.echo(f"  Tickers: {info['tickers']}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Failed to check data: {e}", err=True)


@data.command('tickers')
@click.option('--type', 'data_type', default='stocks_daily',
              type=click.Choice(['stocks_daily', 'stocks_minute', 'options_daily', 'options_minute']),
              help='Data type to check')
@click.pass_context
def list_tickers(ctx, data_type):
    """List available tickers in Parquet data"""
    try:
        parquet = ctx.obj['parquet']

        tickers = parquet.get_available_tickers(data_type)

        if not tickers:
            click.echo(f"No tickers found in {data_type}")
            return

        click.echo(f"\n📊 Available Tickers in {data_type} ({len(tickers)} total)\n")

        # Display in columns
        cols = 6
        for i in range(0, len(tickers), cols):
            row = tickers[i:i+cols]
            click.echo("  ".join(f"{t:<8}" for t in row))

    except Exception as e:
        click.echo(f"❌ Failed to list tickers: {e}", err=True)


@data.command('query')
@click.argument('tickers', nargs=-1, required=True)
@click.option('--start', help='Start date (YYYY-MM-DD)')
@click.option('--end', help='End date (YYYY-MM-DD)')
@click.option('--limit', type=int, default=10, help='Row limit (default: 10)')
@click.option('--type', 'data_type', default='stocks_daily',
              type=click.Choice(['stocks_daily', 'options_daily']),
              help='Data type (default: stocks_daily)')
@click.pass_context
def query_data(ctx, tickers, start, end, limit, data_type):
    """Query Parquet data for specific tickers"""
    try:
        parquet = ctx.obj['parquet']

        # Parse dates
        start_date = datetime.strptime(start, '%Y-%m-%d').date() if start else None
        end_date = datetime.strptime(end, '%Y-%m-%d').date() if end else None

        # Query data
        if data_type == 'stocks_daily':
            df = parquet.get_stock_daily(
                tickers=list(tickers),
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
        else:
            df = parquet.get_options_daily(
                underlying_tickers=list(tickers),
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )

        if df is None or df.empty:
            click.echo("No data found")
            return

        click.echo(f"\n📈 Query Results ({len(df)} rows)\n")

        # Display as table
        if len(df) > 20:
            click.echo("Showing first 20 rows (use --limit to change)\n")
            display_df = df.head(20)
        else:
            display_df = df

        click.echo(tabulate(display_df, headers='keys', tablefmt='simple', showindex=False))

        if len(df) > 20:
            click.echo(f"\n... {len(df) - 20} more rows")

    except Exception as e:
        click.echo(f"❌ Failed to query data: {e}", err=True)


@data.command('range')
@click.option('--type', 'data_type', default='stocks_daily',
              type=click.Choice(['stocks_daily', 'stocks_minute', 'options_daily', 'options_minute']),
              help='Data type to check')
@click.pass_context
def date_range(ctx, data_type):
    """Show date range for Parquet data"""
    try:
        parquet = ctx.obj['parquet']

        min_date, max_date = parquet.get_date_range(data_type)

        if min_date and max_date:
            click.echo(f"\n📅 Date Range for {data_type}")
            click.echo(f"  Start: {min_date}")
            click.echo(f"  End:   {max_date}")

            # Calculate duration
            duration = (max_date - min_date).days
            click.echo(f"  Duration: {duration} days ({duration/365:.1f} years)")
        else:
            click.echo(f"No data found for {data_type}")

    except Exception as e:
        click.echo(f"❌ Failed to get date range: {e}", err=True)


@data.command('options-minute')
@click.argument('tickers', nargs=-1, required=True)
@click.option('--start', required=True, help='Start datetime (YYYY-MM-DD HH:MM)')
@click.option('--end', required=True, help='End datetime (YYYY-MM-DD HH:MM)')
@click.option('--type', 'option_type', type=click.Choice(['call', 'put']), help='Option type filter')
@click.option('--min-strike', type=float, help='[NOT IMPLEMENTED] Minimum strike price')
@click.option('--max-strike', type=float, help='[NOT IMPLEMENTED] Maximum strike price')
@click.option('--limit', type=int, default=10000, help='Row limit (default: 10000)')
@click.pass_context
def query_options_minute(ctx, tickers, start, end, option_type, min_strike, max_strike, limit):
    """
    Query minute-level options data (1-day delayed from S3)

    Perfect for historical analysis, backtesting, and research.
    Data has 1-day delay - not for live trading.

    NOTE: Only data from August 2025 onwards is supported. Strike price
    filtering is not yet implemented (metadata encoded in ticker string).

    Examples:

      # Analyze AAPL call options intraday behavior
      quantlab data options-minute AAPL \\
        --start "2025-10-03 09:30" \\
        --end "2025-10-03 16:00" \\
        --type call \\
        --limit 1000

      # Study options flow during market open
      quantlab data options-minute NVDA \\
        --start "2025-09-15 09:30" \\
        --end "2025-09-15 10:00" \\
        --type call \\
        --limit 5000
    """
    try:
        parquet = ctx.obj['parquet']

        # Parse datetimes
        start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")

        # Validate time range
        duration = (end_dt - start_dt).total_seconds() / 3600
        if duration > 8:
            click.echo("⚠️  Warning: Querying more than 8 hours of minute data")
            click.echo("   This may return a large dataset. Consider narrowing the time range.")

        click.echo(f"\n🔍 Querying options minute data (1-day delayed from S3)...")
        click.echo(f"   Time range: {start} to {end} ({duration:.1f} hours)")
        click.echo(f"   Tickers: {', '.join(tickers)}")
        if option_type:
            click.echo(f"   Type: {option_type}")
        if min_strike and max_strike:
            click.echo(f"   Strike range: ${min_strike} - ${max_strike}")
        click.echo()

        # Query
        df = parquet.get_options_minute(
            underlying_tickers=list(tickers),
            start_datetime=start_dt,
            end_datetime=end_dt,
            option_type=option_type,
            min_strike=min_strike,
            max_strike=max_strike,
            limit=limit
        )

        if df is None or df.empty:
            click.echo("❌ No data found for the specified parameters")
            click.echo("\nTips:")
            click.echo("  • Data has 1-day delay - use yesterday's date")
            click.echo("  • Check data availability with: quantlab data check")
            click.echo("  • Try a different date range or strike prices")
            return

        # Display summary
        click.echo(f"📊 Retrieved {len(df):,} rows of minute options data\n")

        # Extract underlying symbols from tickers (format: O:AAPL251003C00220000)
        underlying_symbols = set()
        for ticker in df['ticker']:
            # Extract symbol between 'O:' and first digit
            parts = ticker.split(':', 1)
            if len(parts) == 2:
                symbol_part = parts[1]
                # Find where digits start
                for i, char in enumerate(symbol_part):
                    if char.isdigit():
                        underlying_symbols.add(symbol_part[:i])
                        break

        click.echo(f"Time Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        if underlying_symbols:
            click.echo(f"Underlying: {', '.join(sorted(underlying_symbols))}")
        click.echo(f"Unique Contracts: {df['ticker'].nunique()}\n")

        # Statistical summary (using OHLC data)
        click.echo("📈 Price Summary:")
        click.echo(f"  Close: ${df['close'].mean():.2f} avg, ${df['close'].min():.2f} - ${df['close'].max():.2f}")
        click.echo(f"  Volume: {df['volume'].sum():,} total, {df['volume'].mean():.0f} avg")
        click.echo(f"  Transactions: {df['transactions'].sum():,} total\n")

        # Show sample data
        click.echo("📋 Sample Data (first 10 rows):\n")

        display_cols = ['timestamp', 'ticker', 'open', 'high', 'low', 'close', 'volume', 'transactions']
        display_df = df[display_cols].head(10)

        click.echo(tabulate(display_df, headers='keys', tablefmt='simple', showindex=False))

        if len(df) > 10:
            click.echo(f"\n... {len(df) - 10:,} more rows")

        # Usage suggestions
        click.echo("\n💡 Analysis Suggestions:")
        click.echo("  • Calculate volume-weighted average price (VWAP)")
        click.echo("  • Analyze intraday price patterns and volatility")
        click.echo("  • Detect large volume spikes and unusual options flow")
        click.echo("  • Study bid-ask spreads during different market conditions")
        click.echo("  • Track contract liquidity throughout the trading day")

    except ValueError as e:
        click.echo(f"❌ Invalid datetime format: {e}", err=True)
        click.echo("   Use format: YYYY-MM-DD HH:MM (e.g., '2025-10-14 09:30')")
    except Exception as e:
        click.echo(f"❌ Failed to query options minute data: {e}", err=True)
