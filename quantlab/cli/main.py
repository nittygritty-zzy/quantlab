"""
Main CLI entry point using Click framework
"""

import click
import sys
from pathlib import Path

from ..utils.config import load_config, create_default_config
from ..utils.logger import setup_logger
from ..data.database import DatabaseManager
from ..data.parquet_reader import ParquetReader
from ..data.data_manager import DataManager
from ..core.portfolio_manager import PortfolioManager
from ..core.analyzer import Analyzer

logger = setup_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
@click.option('--config', type=click.Path(), help='Path to config file')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """
    QuantLab - Quantitative Trading Research Platform

    Portfolio management and multi-source options analysis system.
    """
    # Set up logging
    if verbose:
        import logging
        logger.setLevel(logging.DEBUG)

    # Load config
    try:
        ctx.ensure_object(dict)
        ctx.obj['config'] = load_config(config)

        # Initialize database
        ctx.obj['db'] = DatabaseManager(ctx.obj['config'].database_path)

        # Initialize Parquet reader
        ctx.obj['parquet'] = ParquetReader(ctx.obj['config'].parquet_root)

        # Initialize data manager (with API clients)
        ctx.obj['data_mgr'] = DataManager(
            config=ctx.obj['config'],
            db=ctx.obj['db'],
            parquet=ctx.obj['parquet']
        )

        # Initialize portfolio manager
        ctx.obj['portfolio_mgr'] = PortfolioManager(ctx.obj['db'])

        # Initialize analyzer
        ctx.obj['analyzer'] = Analyzer(
            config=ctx.obj['config'],
            db_manager=ctx.obj['db'],
            data_manager=ctx.obj['data_mgr']
        )

    except Exception as e:
        click.echo(f"❌ Failed to initialize: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize QuantLab database and configuration"""
    try:
        click.echo("🚀 Initializing QuantLab...")

        # Create default config if it doesn't exist
        config_path = Path.home() / ".quantlab" / "config.yaml"
        if not config_path.exists():
            click.echo(f"📝 Creating default config at: {config_path}")
            create_default_config()

        # Initialize database schema
        click.echo("📊 Initializing database schema...")
        ctx.obj['db'].initialize_schema()

        # Check Parquet data availability
        click.echo("📁 Checking Parquet data availability...")
        availability = ctx.obj['parquet'].check_data_availability()

        click.echo("\n✅ Initialization complete!\n")

        # Display data availability
        click.echo("Data Availability:")
        for data_type, info in availability.items():
            status = "✓" if info['exists'] else "✗"
            click.echo(f"  {status} {data_type}: {info['path']}")
            if info.get('min_date'):
                click.echo(f"      Date range: {info['min_date']} to {info['max_date']}")
                click.echo(f"      Tickers: {info['tickers']}")

        click.echo(f"\n📝 Edit config at: {config_path}")
        click.echo("🎯 Run 'quantlab --help' to get started")

    except Exception as e:
        click.echo(f"❌ Initialization failed: {e}", err=True)
        sys.exit(1)


# Import subcommands
from .portfolio import portfolio as portfolio_cmd
from .data import data as data_cmd
from .analyze import analyze as analyze_cmd
from .lookup import lookup as lookup_cmd

cli.add_command(portfolio_cmd)
cli.add_command(data_cmd)
cli.add_command(analyze_cmd)
cli.add_command(lookup_cmd)


if __name__ == '__main__':
    cli(obj={})
