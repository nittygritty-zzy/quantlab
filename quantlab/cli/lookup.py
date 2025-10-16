"""
Lookup table management CLI commands
"""

import click
from tabulate import tabulate


@click.group()
def lookup():
    """Manage lookup tables (slowly-changing data)"""
    pass


@lookup.command('init')
@click.pass_context
def init_tables(ctx):
    """Initialize lookup tables"""
    try:
        data_mgr = ctx.obj['data_mgr']

        click.echo("🔧 Initializing lookup tables...")
        data_mgr.lookup.initialize_tables()

        click.echo("✅ Lookup tables initialized")

    except Exception as e:
        click.echo(f"❌ Failed to initialize tables: {e}", err=True)


@lookup.command('stats')
@click.pass_context
def show_stats(ctx):
    """Show lookup table statistics"""
    try:
        data_mgr = ctx.obj['data_mgr']

        click.echo("\n📊 Lookup Table Statistics\n")

        stats = data_mgr.lookup.get_refresh_stats()

        # Display counts
        click.echo("Record Counts:")
        click.echo(f"  Company Info: {stats.get('company_info_count', 0)}")
        click.echo(f"  Analyst Ratings: {stats.get('analyst_ratings_count', 0)}")
        click.echo(f"  Treasury Rates: {stats.get('treasury_rates_count', 0)}")
        click.echo(f"  Financial Statements: {stats.get('financial_statements_count', 0)}")
        click.echo(f"  Corporate Actions: {stats.get('corporate_actions_count', 0)}")
        click.echo()

        # Display staleness
        click.echo("Stale Records (need refresh):")
        click.echo(f"  Company Info (>7 days): {stats.get('company_info_stale', 0)}")
        click.echo(f"  Analyst Ratings (>1 day): {stats.get('analyst_ratings_stale', 0)}")
        click.echo(f"  Treasury Rates (>1 day): {stats.get('treasury_rates_stale', 0)}")
        click.echo()

    except Exception as e:
        click.echo(f"❌ Failed to get stats: {e}", err=True)


@lookup.command('refresh')
@click.argument('table_type', type=click.Choice(['company', 'ratings', 'treasury', 'all']))
@click.argument('tickers', nargs=-1)
@click.pass_context
def refresh_tables(ctx, table_type, tickers):
    """
    Refresh lookup tables

    TABLE_TYPE: company, ratings, treasury, or all
    TICKERS: One or more ticker symbols (not required for treasury)

    Examples:
        quantlab lookup refresh company AAPL MSFT GOOGL
        quantlab lookup refresh ratings AAPL
        quantlab lookup refresh treasury
        quantlab lookup refresh all AAPL MSFT
    """
    try:
        data_mgr = ctx.obj['data_mgr']
        config = ctx.obj['config']

        if table_type == 'treasury' or table_type == 'all':
            click.echo("📈 Refreshing treasury rates...")
            success = data_mgr.lookup.refresh_treasury_rates(config.alphavantage_api_key)
            if success:
                click.echo("  ✅ Treasury rates refreshed")
            else:
                click.echo("  ⚠️  Treasury rates refresh failed", err=True)

        if table_type in ['company', 'all'] and tickers:
            click.echo(f"\n🏢 Refreshing company info for {len(tickers)} ticker(s)...")
            results = data_mgr.lookup.batch_refresh_company_info(list(tickers))

            success_count = sum(results.values())
            click.echo(f"  ✅ {success_count}/{len(tickers)} successful")

            # Show failures
            failures = [ticker for ticker, success in results.items() if not success]
            if failures:
                click.echo(f"  ⚠️  Failed: {', '.join(failures)}")

        if table_type in ['ratings', 'all'] and tickers:
            click.echo(f"\n⭐ Refreshing analyst ratings for {len(tickers)} ticker(s)...")
            results = data_mgr.lookup.batch_refresh_analyst_ratings(list(tickers))

            success_count = sum(results.values())
            click.echo(f"  ✅ {success_count}/{len(tickers)} successful")

            # Show failures
            failures = [ticker for ticker, success in results.items() if not success]
            if failures:
                click.echo(f"  ⚠️  Failed: {', '.join(failures)}")

        if not tickers and table_type != 'treasury':
            click.echo("⚠️  No tickers specified. Provide ticker symbols to refresh.", err=True)
            click.echo("Example: quantlab lookup refresh company AAPL MSFT")

    except Exception as e:
        click.echo(f"❌ Failed to refresh: {e}", err=True)


@lookup.command('get')
@click.argument('data_type', type=click.Choice(['company', 'ratings', 'treasury']))
@click.argument('ticker', required=False)
@click.option('--maturity', default='3month', help='Treasury maturity (3month, 2year, 5year, 10year, 30year)')
@click.pass_context
def get_data(ctx, data_type, ticker, maturity):
    """
    Get data from lookup tables

    Examples:
        quantlab lookup get company AAPL
        quantlab lookup get ratings MSFT
        quantlab lookup get treasury --maturity 10year
    """
    try:
        data_mgr = ctx.obj['data_mgr']

        if data_type == 'company':
            if not ticker:
                click.echo("❌ Ticker required for company info", err=True)
                return

            info = data_mgr.lookup.get_company_info(ticker)
            if info:
                click.echo(f"\n🏢 Company Info: {ticker}\n")
                click.echo(f"Name: {info['company_name']}")
                click.echo(f"Sector: {info['sector']}")
                click.echo(f"Industry: {info['industry']}")
                click.echo(f"Exchange: {info['exchange']}")
                click.echo(f"Employees: {info['employees']:,}" if info['employees'] else "Employees: N/A")
                click.echo(f"Website: {info['website']}")
                click.echo(f"\nLast Refreshed: {info['last_refreshed']}")
            else:
                click.echo(f"❌ No company info found for {ticker}", err=True)

        elif data_type == 'ratings':
            if not ticker:
                click.echo("❌ Ticker required for analyst ratings", err=True)
                return

            ratings = data_mgr.lookup.get_analyst_ratings(ticker)
            if ratings:
                click.echo(f"\n⭐ Analyst Ratings: {ticker}\n")

                total = ratings['strong_buy'] + ratings['buy'] + ratings['hold'] + ratings['sell'] + ratings['strong_sell']
                click.echo(f"Total Ratings: {total}")
                click.echo(f"  Strong Buy: {ratings['strong_buy']}")
                click.echo(f"  Buy: {ratings['buy']}")
                click.echo(f"  Hold: {ratings['hold']}")
                click.echo(f"  Sell: {ratings['sell']}")
                click.echo(f"  Strong Sell: {ratings['strong_sell']}")

                if ratings['average_rating']:
                    rating_labels = {1: 'Strong Buy', 2: 'Buy', 3: 'Hold', 4: 'Sell', 5: 'Strong Sell'}
                    rating_str = rating_labels.get(round(ratings['average_rating']), 'Unknown')
                    click.echo(f"\nAverage Rating: {ratings['average_rating']:.2f} ({rating_str})")

                click.echo(f"\nPrice Targets:")
                if ratings['target_mean']:
                    click.echo(f"  Mean: ${ratings['target_mean']:.2f}")
                if ratings['target_median']:
                    click.echo(f"  Median: ${ratings['target_median']:.2f}")
                if ratings['target_high']:
                    click.echo(f"  High: ${ratings['target_high']:.2f}")
                if ratings['target_low']:
                    click.echo(f"  Low: ${ratings['target_low']:.2f}")

                click.echo(f"\nLast Refreshed: {ratings['last_refreshed']}")
            else:
                click.echo(f"❌ No analyst ratings found for {ticker}", err=True)

        elif data_type == 'treasury':
            rate = data_mgr.lookup.get_treasury_rate(maturity)
            if rate:
                click.echo(f"\n📈 Treasury Rate ({maturity}): {rate*100:.3f}%")
            else:
                click.echo(f"❌ No treasury rate found for {maturity}", err=True)
                click.echo("Tip: Run 'quantlab lookup refresh treasury' first")

    except Exception as e:
        click.echo(f"❌ Failed to get data: {e}", err=True)


@lookup.command('refresh-portfolio')
@click.argument('portfolio_id')
@click.option('--company/--no-company', default=True, help='Refresh company info')
@click.option('--ratings/--no-ratings', default=True, help='Refresh analyst ratings')
@click.pass_context
def refresh_portfolio(ctx, portfolio_id, company, ratings):
    """
    Refresh lookup tables for all tickers in a portfolio

    Example:
        quantlab lookup refresh-portfolio tech
        quantlab lookup refresh-portfolio growth --no-company
    """
    try:
        portfolio_mgr = ctx.obj['portfolio_mgr']
        data_mgr = ctx.obj['data_mgr']

        # Get portfolio tickers
        summary = portfolio_mgr.get_portfolio_summary(portfolio_id)
        if not summary:
            click.echo(f"❌ Portfolio not found: {portfolio_id}", err=True)
            return

        tickers = summary['tickers']
        click.echo(f"📊 Refreshing lookup tables for portfolio: {summary['name']}")
        click.echo(f"Tickers: {', '.join(tickers)}\n")

        # Refresh company info
        if company:
            click.echo("🏢 Refreshing company info...")
            results = data_mgr.lookup.batch_refresh_company_info(tickers)
            success_count = sum(results.values())
            click.echo(f"  ✅ {success_count}/{len(tickers)} successful\n")

        # Refresh analyst ratings
        if ratings:
            click.echo("⭐ Refreshing analyst ratings...")
            results = data_mgr.lookup.batch_refresh_analyst_ratings(tickers)
            success_count = sum(results.values())
            click.echo(f"  ✅ {success_count}/{len(tickers)} successful\n")

        click.echo("✅ Portfolio lookup tables refreshed")

    except Exception as e:
        click.echo(f"❌ Failed to refresh portfolio: {e}", err=True)
