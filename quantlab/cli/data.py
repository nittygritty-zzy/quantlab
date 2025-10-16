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
