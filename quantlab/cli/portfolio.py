"""
Portfolio management CLI commands
"""

import click
from tabulate import tabulate


@click.group()
def portfolio():
    """Manage portfolios and positions"""
    pass


@portfolio.command('create')
@click.argument('portfolio_id')
@click.option('--name', required=True, help='Portfolio display name')
@click.option('--description', help='Portfolio description')
@click.pass_context
def create_portfolio(ctx, portfolio_id, name, description):
    """Create a new portfolio"""
    try:
        portfolio_mgr = ctx.obj['portfolio_mgr']

        portfolio = portfolio_mgr.create_portfolio(
            portfolio_id=portfolio_id,
            name=name,
            description=description
        )

        click.echo(f"✅ Created portfolio: {portfolio.name} (ID: {portfolio.portfolio_id})")

    except ValueError as e:
        click.echo(f"❌ {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Failed to create portfolio: {e}", err=True)


@portfolio.command('list')
@click.pass_context
def list_portfolios(ctx):
    """List all portfolios"""
    try:
        portfolio_mgr = ctx.obj['portfolio_mgr']
        portfolios = portfolio_mgr.list_portfolios()

        if not portfolios:
            click.echo("No portfolios found. Create one with: quantlab portfolio create")
            return

        # Format as table
        table_data = [
            [p.portfolio_id, p.name, p.description or '', p.created_at.strftime('%Y-%m-%d') if p.created_at else '']
            for p in portfolios
        ]

        headers = ['ID', 'Name', 'Description', 'Created']
        click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))

    except Exception as e:
        click.echo(f"❌ Failed to list portfolios: {e}", err=True)


@portfolio.command('show')
@click.argument('portfolio_id')
@click.pass_context
def show_portfolio(ctx, portfolio_id):
    """Show portfolio details and positions"""
    try:
        portfolio_mgr = ctx.obj['portfolio_mgr']

        summary = portfolio_mgr.get_portfolio_summary(portfolio_id)

        if not summary:
            click.echo(f"❌ Portfolio not found: {portfolio_id}", err=True)
            return

        # Display portfolio info
        click.echo(f"\n📊 Portfolio: {summary['name']}")
        click.echo(f"ID: {summary['portfolio_id']}")
        if summary['description']:
            click.echo(f"Description: {summary['description']}")
        click.echo(f"Created: {summary['created_at'].strftime('%Y-%m-%d %H:%M:%S') if summary['created_at'] else 'N/A'}")
        click.echo(f"Updated: {summary['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if summary['updated_at'] else 'N/A'}")
        click.echo(f"\n📈 Positions: {summary['num_positions']}")

        if summary['positions']:
            # Format positions as table
            table_data = [
                [
                    p.ticker,
                    f"{p.weight*100:.2f}%" if p.weight else '-',
                    p.shares or '-',
                    f"${p.cost_basis:.2f}" if p.cost_basis else '-',
                    p.entry_date.strftime('%Y-%m-%d') if p.entry_date else '-',
                    p.notes or ''
                ]
                for p in summary['positions']
            ]

            headers = ['Ticker', 'Weight', 'Shares', 'Cost Basis', 'Entry Date', 'Notes']
            click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))

            if summary['total_weight']:
                click.echo(f"\nTotal Weight: {summary['total_weight']*100:.2f}%")
        else:
            click.echo("No positions. Add tickers with: quantlab portfolio add")

    except Exception as e:
        click.echo(f"❌ Failed to show portfolio: {e}", err=True)


@portfolio.command('delete')
@click.argument('portfolio_id')
@click.confirmation_option(prompt='Are you sure you want to delete this portfolio?')
@click.pass_context
def delete_portfolio(ctx, portfolio_id):
    """Delete a portfolio"""
    try:
        portfolio_mgr = ctx.obj['portfolio_mgr']

        success = portfolio_mgr.delete_portfolio(portfolio_id)

        if success:
            click.echo(f"✅ Deleted portfolio: {portfolio_id}")
        else:
            click.echo(f"❌ Portfolio not found: {portfolio_id}", err=True)

    except Exception as e:
        click.echo(f"❌ Failed to delete portfolio: {e}", err=True)


@portfolio.command('add')
@click.argument('portfolio_id')
@click.argument('tickers', nargs=-1, required=True)
@click.option('--weight', type=float, help='Position weight (0.0-1.0)')
@click.option('--shares', type=int, help='Number of shares')
@click.option('--cost-basis', type=float, help='Cost basis per share')
@click.option('--notes', help='Position notes')
@click.pass_context
def add_position(ctx, portfolio_id, tickers, weight, shares, cost_basis, notes):
    """Add position(s) to portfolio"""
    try:
        portfolio_mgr = ctx.obj['portfolio_mgr']

        added = []
        errors = []

        for ticker in tickers:
            try:
                position = portfolio_mgr.add_position(
                    portfolio_id=portfolio_id,
                    ticker=ticker,
                    weight=weight,
                    shares=shares,
                    cost_basis=cost_basis,
                    notes=notes
                )
                added.append(ticker)
            except Exception as e:
                errors.append(f"{ticker}: {e}")

        # Report results
        if added:
            click.echo(f"✅ Added to {portfolio_id}: {', '.join(added)}")

        if errors:
            click.echo("\n⚠️  Errors:", err=True)
            for error in errors:
                click.echo(f"  • {error}", err=True)

    except Exception as e:
        click.echo(f"❌ Failed to add positions: {e}", err=True)


@portfolio.command('remove')
@click.argument('portfolio_id')
@click.argument('tickers', nargs=-1, required=True)
@click.pass_context
def remove_position(ctx, portfolio_id, tickers):
    """Remove position(s) from portfolio"""
    try:
        portfolio_mgr = ctx.obj['portfolio_mgr']

        removed = []
        errors = []

        for ticker in tickers:
            success = portfolio_mgr.remove_position(portfolio_id, ticker)
            if success:
                removed.append(ticker)
            else:
                errors.append(f"{ticker}: not found")

        # Report results
        if removed:
            click.echo(f"✅ Removed from {portfolio_id}: {', '.join(removed)}")

        if errors:
            click.echo("\n⚠️  Errors:", err=True)
            for error in errors:
                click.echo(f"  • {error}", err=True)

    except Exception as e:
        click.echo(f"❌ Failed to remove positions: {e}", err=True)


@portfolio.command('update')
@click.argument('portfolio_id')
@click.argument('ticker')
@click.option('--weight', type=float, help='New position weight (0.0-1.0)')
@click.option('--shares', type=int, help='New number of shares')
@click.option('--cost-basis', type=float, help='New cost basis per share')
@click.option('--notes', help='New position notes')
@click.pass_context
def update_position(ctx, portfolio_id, ticker, weight, shares, cost_basis, notes):
    """Update a position's attributes"""
    try:
        portfolio_mgr = ctx.obj['portfolio_mgr']

        # Check if any updates provided
        if weight is None and shares is None and cost_basis is None and notes is None:
            click.echo("❌ No updates specified. Use --weight, --shares, --cost-basis, or --notes", err=True)
            return

        success = portfolio_mgr.update_position(
            portfolio_id=portfolio_id,
            ticker=ticker,
            weight=weight,
            shares=shares,
            cost_basis=cost_basis,
            notes=notes
        )

        if success:
            click.echo(f"✅ Updated {ticker} in {portfolio_id}")
        else:
            click.echo(f"❌ Position not found: {ticker} in {portfolio_id}", err=True)

    except ValueError as e:
        click.echo(f"❌ {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Failed to update position: {e}", err=True)
