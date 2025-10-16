"""
Integration tests for main CLI and init command

Tests main CLI functionality with real components.
"""

import pytest
from pathlib import Path

from quantlab.cli.main import cli, init


class TestMainCLIIntegration:
    """Integration tests for main CLI"""

    def test_cli_help_displays(self, cli_runner):
        """Test that CLI help works"""
        result = cli_runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert 'QuantLab' in result.output
        assert 'portfolio' in result.output
        assert 'data' in result.output
        assert 'analyze' in result.output
        assert 'lookup' in result.output

    def test_cli_version(self, cli_runner):
        """Test version command"""
        result = cli_runner.invoke(cli, ['--version'])

        assert result.exit_code == 0
        assert '0.1.0' in result.output

    def test_all_subcommands_registered(self, cli_runner):
        """Test that all subcommands are available"""
        result = cli_runner.invoke(cli, ['--help'])

        subcommands = ['init', 'portfolio', 'data', 'analyze', 'lookup']
        for cmd in subcommands:
            assert cmd in result.output


class TestInitCommandIntegration:
    """Integration tests for init command"""

    def test_init_creates_database_schema(self, cli_runner, cli_context, temp_dir):
        """Test that init creates database schema"""
        # Run init
        result = cli_runner.invoke(
            init,
            [],
            obj=cli_context
        )

        assert result.exit_code == 0
        assert '🚀 Initializing QuantLab' in result.output
        assert '📊 Initializing database schema' in result.output
        assert '✅ Initialization complete' in result.output

        # Verify database was created
        db_path = cli_context['db'].db_path
        assert Path(db_path).exists()

        # Verify tables were created using DuckDB API
        conn = cli_context['db'].conn

        # Check for portfolios table
        result = conn.execute(
            "SELECT table_name FROM duckdb_tables() WHERE table_name='portfolios'"
        )
        assert result.fetchone() is not None

        # Check for positions table
        result = conn.execute(
            "SELECT table_name FROM duckdb_tables() WHERE table_name='portfolio_positions'"
        )
        assert result.fetchone() is not None

    def test_init_checks_data_availability(self, cli_runner, cli_context):
        """Test that init checks for parquet data"""
        result = cli_runner.invoke(
            init,
            [],
            obj=cli_context
        )

        assert result.exit_code == 0
        assert '📁 Checking Parquet data availability' in result.output
        assert 'Data Availability:' in result.output

    def test_init_shows_next_steps(self, cli_runner, cli_context):
        """Test that init shows helpful next steps"""
        result = cli_runner.invoke(
            init,
            [],
            obj=cli_context
        )

        assert result.exit_code == 0
        assert '📝 Edit config at:' in result.output
        assert "🎯 Run 'quantlab --help' to get started" in result.output

    def test_init_multiple_times(self, cli_runner, cli_context):
        """Test that init can be run multiple times"""
        # First init
        result1 = cli_runner.invoke(init, [], obj=cli_context)
        assert result1.exit_code == 0

        # Second init (should not fail)
        result2 = cli_runner.invoke(init, [], obj=cli_context)
        assert result2.exit_code == 0


class TestCLIWorkflow:
    """Test complete workflows using CLI"""

    def test_full_portfolio_workflow(self, cli_runner, cli_context):
        """Test complete portfolio management workflow"""
        # Init
        result = cli_runner.invoke(init, [], obj=cli_context)
        assert result.exit_code == 0

        # Import portfolio command
        from quantlab.cli.portfolio import portfolio

        # Create portfolio
        result = cli_runner.invoke(
            portfolio,
            ['create', 'workflow', '--name', 'Workflow Test'],
            obj=cli_context
        )
        assert result.exit_code == 0

        # Add positions
        result = cli_runner.invoke(
            portfolio,
            ['add', 'workflow', 'AAPL', 'GOOGL', '--weight', '0.5'],
            obj=cli_context
        )
        assert result.exit_code == 0

        # Show portfolio
        result = cli_runner.invoke(
            portfolio,
            ['show', 'workflow'],
            obj=cli_context
        )
        assert result.exit_code == 0
        assert 'AAPL' in result.output
        assert 'GOOGL' in result.output

        # Update position
        result = cli_runner.invoke(
            portfolio,
            ['update', 'workflow', 'AAPL', '--weight', '0.6'],
            obj=cli_context
        )
        assert result.exit_code == 0

        # List all portfolios
        result = cli_runner.invoke(
            portfolio,
            ['list'],
            obj=cli_context
        )
        assert result.exit_code == 0
        assert 'workflow' in result.output

        # Remove position
        result = cli_runner.invoke(
            portfolio,
            ['remove', 'workflow', 'GOOGL'],
            obj=cli_context
        )
        assert result.exit_code == 0

        # Delete portfolio
        result = cli_runner.invoke(
            portfolio,
            ['delete', 'workflow', '--yes'],
            obj=cli_context
        )
        assert result.exit_code == 0


class TestDatabasePersistence:
    """Test that database operations persist correctly"""

    def test_data_survives_reconnection(self, cli_runner, test_db_path, test_config):
        """Test that data persists across database reconnections"""
        from quantlab.data.database import DatabaseManager
        from quantlab.core.portfolio_manager import PortfolioManager

        # First connection - create portfolio
        db1 = DatabaseManager(str(test_db_path))
        db1.initialize_schema()
        pm1 = PortfolioManager(db1)

        portfolio = pm1.create_portfolio(
            portfolio_id="persist_test",
            name="Persistence Test"
        )
        pm1.add_position("persist_test", "AAPL", weight=0.5)

        db1.close()

        # Second connection - verify data exists
        db2 = DatabaseManager(str(test_db_path))
        pm2 = PortfolioManager(db2)

        portfolios = pm2.list_portfolios()
        assert len(portfolios) > 0
        assert any(p.portfolio_id == "persist_test" for p in portfolios)

        summary = pm2.get_portfolio_summary("persist_test")
        assert summary is not None
        assert summary['name'] == "Persistence Test"
        assert len(summary['positions']) == 1
        assert summary['positions'][0].ticker == 'AAPL'

        db2.close()


class TestConcurrentOperations:
    """Test handling of concurrent-like operations"""

    def test_multiple_portfolio_operations(self, cli_runner, cli_context):
        """Test multiple portfolio operations in sequence"""
        from quantlab.cli.portfolio import portfolio

        # Create multiple portfolios rapidly
        for i in range(5):
            result = cli_runner.invoke(
                portfolio,
                ['create', f'multi{i}', '--name', f'Multi Portfolio {i}'],
                obj=cli_context
            )
            assert result.exit_code == 0

        # List all - should show 5
        result = cli_runner.invoke(portfolio, ['list'], obj=cli_context)
        assert result.exit_code == 0
        for i in range(5):
            assert f'multi{i}' in result.output

        # Delete all
        for i in range(5):
            result = cli_runner.invoke(
                portfolio,
                ['delete', f'multi{i}', '--yes'],
                obj=cli_context
            )
            assert result.exit_code == 0
