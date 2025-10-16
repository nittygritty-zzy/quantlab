"""
Integration tests for portfolio CLI commands

Tests portfolio commands with real database and no mocks.
"""

import pytest
from pathlib import Path

from quantlab.cli.portfolio import portfolio


class TestPortfolioIntegration:
    """Integration tests for portfolio commands"""

    def test_create_and_list_portfolio(self, cli_runner, cli_context):
        """Test creating a portfolio and listing it"""
        # Create portfolio
        result = cli_runner.invoke(
            portfolio,
            ['create', 'growth', '--name', 'Growth Portfolio', '--description', 'High growth stocks'],
            obj=cli_context
        )

        assert result.exit_code == 0
        assert '✅ Created portfolio: Growth Portfolio' in result.output

        # List portfolios
        result = cli_runner.invoke(
            portfolio,
            ['list'],
            obj=cli_context
        )

        assert result.exit_code == 0
        assert 'growth' in result.output
        assert 'Growth Portfolio' in result.output

    def test_create_show_and_delete_portfolio(self, cli_runner, cli_context):
        """Test full portfolio lifecycle"""
        # Create
        result = cli_runner.invoke(
            portfolio,
            ['create', 'temp', '--name', 'Temporary Portfolio'],
            obj=cli_context
        )
        assert result.exit_code == 0

        # Show
        result = cli_runner.invoke(
            portfolio,
            ['show', 'temp'],
            obj=cli_context
        )
        assert result.exit_code == 0
        assert '📊 Portfolio: Temporary Portfolio' in result.output
        assert 'No positions' in result.output

        # Delete
        result = cli_runner.invoke(
            portfolio,
            ['delete', 'temp', '--yes'],
            obj=cli_context
        )
        assert result.exit_code == 0
        assert '✅ Deleted portfolio: temp' in result.output

        # Verify deleted
        result = cli_runner.invoke(
            portfolio,
            ['show', 'temp'],
            obj=cli_context
        )
        assert '❌ Portfolio not found' in result.output

    def test_add_and_remove_positions(self, cli_runner, cli_context):
        """Test adding and removing positions"""
        # Create portfolio
        cli_runner.invoke(
            portfolio,
            ['create', 'tech', '--name', 'Tech Stocks'],
            obj=cli_context
        )

        # Add single position
        result = cli_runner.invoke(
            portfolio,
            ['add', 'tech', 'AAPL', '--weight', '0.5', '--shares', '100'],
            obj=cli_context
        )
        assert result.exit_code == 0
        assert '✅ Added to tech: AAPL' in result.output

        # Add multiple positions
        result = cli_runner.invoke(
            portfolio,
            ['add', 'tech', 'GOOGL', 'MSFT', '--weight', '0.25'],
            obj=cli_context
        )
        assert result.exit_code == 0
        assert 'GOOGL, MSFT' in result.output

        # Show portfolio with positions
        result = cli_runner.invoke(
            portfolio,
            ['show', 'tech'],
            obj=cli_context
        )
        assert result.exit_code == 0
        assert 'AAPL' in result.output
        assert 'GOOGL' in result.output
        assert 'MSFT' in result.output
        assert '📈 Positions: 3' in result.output

        # Remove position
        result = cli_runner.invoke(
            portfolio,
            ['remove', 'tech', 'MSFT'],
            obj=cli_context
        )
        assert result.exit_code == 0
        assert '✅ Removed from tech: MSFT' in result.output

        # Verify removed
        result = cli_runner.invoke(
            portfolio,
            ['show', 'tech'],
            obj=cli_context
        )
        assert 'MSFT' not in result.output or 'Positions: 2' in result.output

    def test_update_position(self, cli_runner, cli_context):
        """Test updating position attributes"""
        # Create portfolio and add position
        cli_runner.invoke(
            portfolio,
            ['create', 'value', '--name', 'Value Stocks'],
            obj=cli_context
        )

        cli_runner.invoke(
            portfolio,
            ['add', 'value', 'AAPL', '--weight', '0.3', '--shares', '50'],
            obj=cli_context
        )

        # Update weight
        result = cli_runner.invoke(
            portfolio,
            ['update', 'value', 'AAPL', '--weight', '0.5'],
            obj=cli_context
        )
        assert result.exit_code == 0
        assert '✅ Updated AAPL in value' in result.output

        # Update shares
        result = cli_runner.invoke(
            portfolio,
            ['update', 'value', 'AAPL', '--shares', '100'],
            obj=cli_context
        )
        assert result.exit_code == 0

        # Update cost basis
        result = cli_runner.invoke(
            portfolio,
            ['update', 'value', 'AAPL', '--cost-basis', '175.50'],
            obj=cli_context
        )
        assert result.exit_code == 0

        # Update notes
        result = cli_runner.invoke(
            portfolio,
            ['update', 'value', 'AAPL', '--notes', 'Updated position'],
            obj=cli_context
        )
        assert result.exit_code == 0

    def test_portfolio_with_existing_data(self, cli_runner, cli_context, sample_portfolio):
        """Test working with pre-existing portfolio"""
        # Show existing portfolio
        result = cli_runner.invoke(
            portfolio,
            ['show', 'test_portfolio'],
            obj=cli_context
        )

        assert result.exit_code == 0
        assert '📊 Portfolio: Test Portfolio' in result.output
        assert 'AAPL' in result.output
        assert 'GOOGL' in result.output
        assert 'MSFT' in result.output
        assert '📈 Positions: 3' in result.output

        # List should include it
        result = cli_runner.invoke(
            portfolio,
            ['list'],
            obj=cli_context
        )

        assert 'test_portfolio' in result.output
        assert 'Test Portfolio' in result.output

    def test_portfolio_error_handling(self, cli_runner, cli_context):
        """Test error handling in portfolio commands"""
        # Show non-existent portfolio
        result = cli_runner.invoke(
            portfolio,
            ['show', 'nonexistent'],
            obj=cli_context
        )
        assert '❌ Portfolio not found' in result.output

        # Delete non-existent portfolio
        result = cli_runner.invoke(
            portfolio,
            ['delete', 'nonexistent', '--yes'],
            obj=cli_context
        )
        assert '❌ Portfolio not found' in result.output

        # Update non-existent position
        cli_runner.invoke(
            portfolio,
            ['create', 'test', '--name', 'Test'],
            obj=cli_context
        )

        result = cli_runner.invoke(
            portfolio,
            ['update', 'test', 'INVALID', '--weight', '0.5'],
            obj=cli_context
        )
        assert '❌ Position not found' in result.output

    def test_multiple_portfolios(self, cli_runner, cli_context):
        """Test managing multiple portfolios"""
        # Create multiple portfolios
        portfolios = [
            ('growth', 'Growth Stocks'),
            ('value', 'Value Stocks'),
            ('dividend', 'Dividend Stocks'),
        ]

        for pid, name in portfolios:
            result = cli_runner.invoke(
                portfolio,
                ['create', pid, '--name', name],
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
        for pid, name in portfolios:
            assert pid in result.output
            assert name in result.output

    def test_position_weights(self, cli_runner, cli_context):
        """Test that position weights are calculated correctly"""
        # Create portfolio
        cli_runner.invoke(
            portfolio,
            ['create', 'weighted', '--name', 'Weighted Portfolio'],
            obj=cli_context
        )

        # Add positions with weights
        cli_runner.invoke(
            portfolio,
            ['add', 'weighted', 'AAPL', '--weight', '0.40'],
            obj=cli_context
        )

        cli_runner.invoke(
            portfolio,
            ['add', 'weighted', 'GOOGL', '--weight', '0.35'],
            obj=cli_context
        )

        cli_runner.invoke(
            portfolio,
            ['add', 'weighted', 'MSFT', '--weight', '0.25'],
            obj=cli_context
        )

        # Show portfolio and verify weights
        result = cli_runner.invoke(
            portfolio,
            ['show', 'weighted'],
            obj=cli_context
        )

        assert result.exit_code == 0
        assert '40.00%' in result.output  # AAPL weight
        assert '35.00%' in result.output  # GOOGL weight
        assert '25.00%' in result.output  # MSFT weight
        assert 'Total Weight: 100.00%' in result.output

    def test_duplicate_portfolio_id(self, cli_runner, cli_context):
        """Test that duplicate portfolio IDs are rejected"""
        # Create first portfolio
        result = cli_runner.invoke(
            portfolio,
            ['create', 'duplicate', '--name', 'First'],
            obj=cli_context
        )
        assert result.exit_code == 0

        # Try to create duplicate
        result = cli_runner.invoke(
            portfolio,
            ['create', 'duplicate', '--name', 'Second'],
            obj=cli_context
        )
        # Should fail (exact error message depends on implementation)
        assert result.exit_code == 0  # CLI returns 0 but shows error
        assert '❌' in result.output


class TestPortfolioDataPersistence:
    """Test that portfolio data persists across operations"""

    def test_data_persists_across_commands(self, cli_runner, cli_context):
        """Test that portfolio data persists in database"""
        # Create portfolio
        cli_runner.invoke(
            portfolio,
            ['create', 'persist', '--name', 'Persistent Portfolio'],
            obj=cli_context
        )

        # Add position
        cli_runner.invoke(
            portfolio,
            ['add', 'persist', 'AAPL', '--shares', '100', '--cost-basis', '150.00'],
            obj=cli_context
        )

        # Show portfolio (reads from DB)
        result = cli_runner.invoke(
            portfolio,
            ['show', 'persist'],
            obj=cli_context
        )

        assert 'AAPL' in result.output
        assert '100' in result.output  # shares
        assert '$150.00' in result.output  # cost basis

        # List portfolios (reads from DB)
        result = cli_runner.invoke(
            portfolio,
            ['list'],
            obj=cli_context
        )

        assert 'persist' in result.output

    def test_updates_persist(self, cli_runner, cli_context):
        """Test that updates persist in database"""
        # Create and add position
        cli_runner.invoke(
            portfolio,
            ['create', 'update_test', '--name', 'Update Test'],
            obj=cli_context
        )

        cli_runner.invoke(
            portfolio,
            ['add', 'update_test', 'AAPL', '--weight', '0.5'],
            obj=cli_context
        )

        # Update position
        cli_runner.invoke(
            portfolio,
            ['update', 'update_test', 'AAPL', '--weight', '0.75', '--notes', 'Increased allocation'],
            obj=cli_context
        )

        # Verify update persisted
        result = cli_runner.invoke(
            portfolio,
            ['show', 'update_test'],
            obj=cli_context
        )

        assert '75.00%' in result.output
        assert 'Increased allocation' in result.output
