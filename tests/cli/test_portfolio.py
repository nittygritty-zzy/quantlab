"""
Tests for portfolio management CLI commands

Tests all 7 portfolio commands: create, list, show, delete, add, remove, update
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from click.testing import CliRunner

from quantlab.cli.portfolio import (
    portfolio,
    create_portfolio,
    list_portfolios,
    show_portfolio,
    delete_portfolio,
    add_position,
    remove_position,
    update_position
)


class TestPortfolioCreate:
    """Tests for 'portfolio create' command"""

    def test_create_portfolio_success(self, cli_runner):
        """Test successful portfolio creation"""
        mock_mgr = Mock()
        mock_portfolio = Mock()
        mock_portfolio.portfolio_id = 'test_portfolio'
        mock_portfolio.name = 'Test Portfolio'
        mock_portfolio.description = 'A test portfolio'
        mock_mgr.create_portfolio.return_value = mock_portfolio

        result = cli_runner.invoke(
            portfolio,
            ['create', 'test_portfolio', '--name', 'Test Portfolio'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Created portfolio: Test Portfolio' in result.output
        mock_mgr.create_portfolio.assert_called_once_with(
            portfolio_id='test_portfolio',
            name='Test Portfolio',
            description=None
        )

    def test_create_portfolio_with_description(self, cli_runner):
        """Test portfolio creation with description"""
        mock_mgr = Mock()
        mock_portfolio = Mock()
        mock_portfolio.portfolio_id = 'tech_stocks'
        mock_portfolio.name = 'Tech Stocks'
        mock_portfolio.description = 'Technology sector holdings'
        mock_mgr.create_portfolio.return_value = mock_portfolio

        result = cli_runner.invoke(
            portfolio,
            ['create', 'tech_stocks', '--name', 'Tech Stocks', '--description', 'Technology sector holdings'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Created portfolio: Tech Stocks' in result.output

    def test_create_portfolio_missing_name(self, cli_runner):
        """Test portfolio creation fails without name"""
        mock_mgr = Mock()

        result = cli_runner.invoke(
            portfolio,
            ['create', 'test_portfolio'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code != 0
        # Should require --name option

    def test_create_portfolio_value_error(self, cli_runner):
        """Test portfolio creation handles ValueError"""
        mock_mgr = Mock()
        mock_mgr.create_portfolio.side_effect = ValueError("Portfolio already exists")

        result = cli_runner.invoke(
            portfolio,
            ['create', 'duplicate', '--name', 'Duplicate'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0  # Click doesn't exit on ValueError
        assert '❌ Portfolio already exists' in result.output

    def test_create_portfolio_general_error(self, cli_runner):
        """Test portfolio creation handles general errors"""
        mock_mgr = Mock()
        mock_mgr.create_portfolio.side_effect = Exception("Database error")

        result = cli_runner.invoke(
            portfolio,
            ['create', 'test', '--name', 'Test'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Failed to create portfolio' in result.output


class TestPortfolioList:
    """Tests for 'portfolio list' command"""

    def test_list_portfolios_success(self, cli_runner):
        """Test listing portfolios successfully"""
        mock_mgr = Mock()
        mock_portfolios = [
            Mock(
                portfolio_id='tech',
                name='Tech Stocks',
                description='Technology sector',
                created_at=datetime(2025, 1, 1)
            ),
            Mock(
                portfolio_id='value',
                name='Value Stocks',
                description='Undervalued stocks',
                created_at=datetime(2025, 2, 1)
            )
        ]
        mock_mgr.list_portfolios.return_value = mock_portfolios

        result = cli_runner.invoke(
            portfolio,
            ['list'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert 'tech' in result.output
        assert 'Tech Stocks' in result.output
        assert 'value' in result.output
        assert 'Value Stocks' in result.output

    def test_list_portfolios_empty(self, cli_runner):
        """Test listing when no portfolios exist"""
        mock_mgr = Mock()
        mock_mgr.list_portfolios.return_value = []

        result = cli_runner.invoke(
            portfolio,
            ['list'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert 'No portfolios found' in result.output
        assert 'quantlab portfolio create' in result.output

    def test_list_portfolios_error(self, cli_runner):
        """Test listing portfolios handles errors"""
        mock_mgr = Mock()
        mock_mgr.list_portfolios.side_effect = Exception("Database error")

        result = cli_runner.invoke(
            portfolio,
            ['list'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Failed to list portfolios' in result.output


class TestPortfolioShow:
    """Tests for 'portfolio show' command"""

    def test_show_portfolio_success(self, cli_runner):
        """Test showing portfolio details successfully"""
        mock_mgr = Mock()
        mock_position = Mock(
            ticker='AAPL',
            weight=0.50,
            shares=100,
            cost_basis=150.00,
            entry_date=datetime(2025, 1, 1),
            notes='Long term hold'
        )
        mock_summary = {
            'name': 'Tech Stocks',
            'portfolio_id': 'tech',
            'description': 'Technology sector',
            'created_at': datetime(2025, 1, 1, 10, 0, 0),
            'updated_at': datetime(2025, 10, 15, 14, 30, 0),
            'num_positions': 1,
            'positions': [mock_position],
            'total_weight': 0.50
        }
        mock_mgr.get_portfolio_summary.return_value = mock_summary

        result = cli_runner.invoke(
            portfolio,
            ['show', 'tech'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '📊 Portfolio: Tech Stocks' in result.output
        assert 'AAPL' in result.output
        assert '50.00%' in result.output
        assert 'Total Weight: 50.00%' in result.output

    def test_show_portfolio_not_found(self, cli_runner):
        """Test showing non-existent portfolio"""
        mock_mgr = Mock()
        mock_mgr.get_portfolio_summary.return_value = None

        result = cli_runner.invoke(
            portfolio,
            ['show', 'nonexistent'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Portfolio not found: nonexistent' in result.output

    def test_show_portfolio_no_positions(self, cli_runner):
        """Test showing portfolio with no positions"""
        mock_mgr = Mock()
        mock_summary = {
            'name': 'Empty Portfolio',
            'portfolio_id': 'empty',
            'description': None,
            'created_at': datetime(2025, 1, 1),
            'updated_at': datetime(2025, 1, 1),
            'num_positions': 0,
            'positions': [],
            'total_weight': None
        }
        mock_mgr.get_portfolio_summary.return_value = mock_summary

        result = cli_runner.invoke(
            portfolio,
            ['show', 'empty'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert 'No positions' in result.output
        assert 'quantlab portfolio add' in result.output

    def test_show_portfolio_error(self, cli_runner):
        """Test showing portfolio handles errors"""
        mock_mgr = Mock()
        mock_mgr.get_portfolio_summary.side_effect = Exception("Database error")

        result = cli_runner.invoke(
            portfolio,
            ['show', 'test'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Failed to show portfolio' in result.output


class TestPortfolioDelete:
    """Tests for 'portfolio delete' command"""

    def test_delete_portfolio_success(self, cli_runner):
        """Test deleting portfolio successfully"""
        mock_mgr = Mock()
        mock_mgr.delete_portfolio.return_value = True

        result = cli_runner.invoke(
            portfolio,
            ['delete', 'test_portfolio', '--yes'],  # --yes to skip confirmation
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Deleted portfolio: test_portfolio' in result.output

    def test_delete_portfolio_not_found(self, cli_runner):
        """Test deleting non-existent portfolio"""
        mock_mgr = Mock()
        mock_mgr.delete_portfolio.return_value = False

        result = cli_runner.invoke(
            portfolio,
            ['delete', 'nonexistent', '--yes'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Portfolio not found: nonexistent' in result.output

    def test_delete_portfolio_error(self, cli_runner):
        """Test deleting portfolio handles errors"""
        mock_mgr = Mock()
        mock_mgr.delete_portfolio.side_effect = Exception("Database error")

        result = cli_runner.invoke(
            portfolio,
            ['delete', 'test', '--yes'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Failed to delete portfolio' in result.output


class TestPortfolioAdd:
    """Tests for 'portfolio add' command"""

    def test_add_single_position(self, cli_runner):
        """Test adding a single position"""
        mock_mgr = Mock()
        mock_position = Mock(ticker='AAPL')
        mock_mgr.add_position.return_value = mock_position

        result = cli_runner.invoke(
            portfolio,
            ['add', 'tech', 'AAPL', '--weight', '0.5', '--shares', '100'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Added to tech: AAPL' in result.output
        mock_mgr.add_position.assert_called_once()

    def test_add_multiple_positions(self, cli_runner):
        """Test adding multiple positions at once"""
        mock_mgr = Mock()
        mock_mgr.add_position.return_value = Mock()

        result = cli_runner.invoke(
            portfolio,
            ['add', 'tech', 'AAPL', 'GOOGL', 'MSFT', '--weight', '0.33'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Added to tech: AAPL, GOOGL, MSFT' in result.output
        assert mock_mgr.add_position.call_count == 3

    def test_add_position_with_all_options(self, cli_runner):
        """Test adding position with all optional parameters"""
        mock_mgr = Mock()
        mock_mgr.add_position.return_value = Mock()

        result = cli_runner.invoke(
            portfolio,
            ['add', 'tech', 'AAPL', '--weight', '0.5', '--shares', '100', '--cost-basis', '150.00', '--notes', 'Long term'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Added to tech: AAPL' in result.output

    def test_add_position_partial_errors(self, cli_runner):
        """Test adding multiple positions with some errors"""
        mock_mgr = Mock()

        def add_position_side_effect(portfolio_id, ticker, **kwargs):
            if ticker == 'INVALID':
                raise ValueError("Invalid ticker")
            return Mock()

        mock_mgr.add_position.side_effect = add_position_side_effect

        result = cli_runner.invoke(
            portfolio,
            ['add', 'tech', 'AAPL', 'INVALID', 'GOOGL'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert 'AAPL' in result.output
        assert 'GOOGL' in result.output
        assert 'INVALID' in result.output
        assert '⚠️  Errors:' in result.output

    def test_add_position_general_error(self, cli_runner):
        """Test adding position handles general errors"""
        mock_mgr = Mock()
        mock_mgr.add_position.side_effect = Exception("Database error")

        result = cli_runner.invoke(
            portfolio,
            ['add', 'tech', 'AAPL'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        # Error is reported per-ticker, not as overall failure
        assert '⚠️  Errors:' in result.output
        assert 'AAPL: Database error' in result.output


class TestPortfolioRemove:
    """Tests for 'portfolio remove' command"""

    def test_remove_single_position(self, cli_runner):
        """Test removing a single position"""
        mock_mgr = Mock()
        mock_mgr.remove_position.return_value = True

        result = cli_runner.invoke(
            portfolio,
            ['remove', 'tech', 'AAPL'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Removed from tech: AAPL' in result.output

    def test_remove_multiple_positions(self, cli_runner):
        """Test removing multiple positions at once"""
        mock_mgr = Mock()
        mock_mgr.remove_position.return_value = True

        result = cli_runner.invoke(
            portfolio,
            ['remove', 'tech', 'AAPL', 'GOOGL', 'MSFT'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Removed from tech: AAPL, GOOGL, MSFT' in result.output

    def test_remove_position_not_found(self, cli_runner):
        """Test removing non-existent position"""
        mock_mgr = Mock()
        mock_mgr.remove_position.return_value = False

        result = cli_runner.invoke(
            portfolio,
            ['remove', 'tech', 'NONEXISTENT'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert 'NONEXISTENT: not found' in result.output

    def test_remove_position_partial_errors(self, cli_runner):
        """Test removing multiple positions with some not found"""
        mock_mgr = Mock()

        def remove_position_side_effect(portfolio_id, ticker):
            return ticker != 'INVALID'

        mock_mgr.remove_position.side_effect = remove_position_side_effect

        result = cli_runner.invoke(
            portfolio,
            ['remove', 'tech', 'AAPL', 'INVALID', 'GOOGL'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert 'AAPL' in result.output
        assert 'GOOGL' in result.output
        assert 'INVALID: not found' in result.output

    def test_remove_position_error(self, cli_runner):
        """Test removing position handles errors"""
        mock_mgr = Mock()
        mock_mgr.remove_position.side_effect = Exception("Database error")

        result = cli_runner.invoke(
            portfolio,
            ['remove', 'tech', 'AAPL'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Failed to remove positions' in result.output


class TestPortfolioUpdate:
    """Tests for 'portfolio update' command"""

    def test_update_position_weight(self, cli_runner):
        """Test updating position weight"""
        mock_mgr = Mock()
        mock_mgr.update_position.return_value = True

        result = cli_runner.invoke(
            portfolio,
            ['update', 'tech', 'AAPL', '--weight', '0.6'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Updated AAPL in tech' in result.output

    def test_update_position_shares(self, cli_runner):
        """Test updating position shares"""
        mock_mgr = Mock()
        mock_mgr.update_position.return_value = True

        result = cli_runner.invoke(
            portfolio,
            ['update', 'tech', 'AAPL', '--shares', '200'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Updated AAPL in tech' in result.output

    def test_update_position_cost_basis(self, cli_runner):
        """Test updating position cost basis"""
        mock_mgr = Mock()
        mock_mgr.update_position.return_value = True

        result = cli_runner.invoke(
            portfolio,
            ['update', 'tech', 'AAPL', '--cost-basis', '175.00'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Updated AAPL in tech' in result.output

    def test_update_position_notes(self, cli_runner):
        """Test updating position notes"""
        mock_mgr = Mock()
        mock_mgr.update_position.return_value = True

        result = cli_runner.invoke(
            portfolio,
            ['update', 'tech', 'AAPL', '--notes', 'Updated strategy'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Updated AAPL in tech' in result.output

    def test_update_position_multiple_fields(self, cli_runner):
        """Test updating multiple fields at once"""
        mock_mgr = Mock()
        mock_mgr.update_position.return_value = True

        result = cli_runner.invoke(
            portfolio,
            ['update', 'tech', 'AAPL', '--weight', '0.7', '--shares', '150', '--notes', 'Increased position'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '✅ Updated AAPL in tech' in result.output

    def test_update_position_no_updates(self, cli_runner):
        """Test updating position with no options specified"""
        mock_mgr = Mock()

        result = cli_runner.invoke(
            portfolio,
            ['update', 'tech', 'AAPL'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '❌ No updates specified' in result.output

    def test_update_position_not_found(self, cli_runner):
        """Test updating non-existent position"""
        mock_mgr = Mock()
        mock_mgr.update_position.return_value = False

        result = cli_runner.invoke(
            portfolio,
            ['update', 'tech', 'NONEXISTENT', '--weight', '0.5'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Position not found: NONEXISTENT' in result.output

    def test_update_position_value_error(self, cli_runner):
        """Test updating position handles ValueError"""
        mock_mgr = Mock()
        mock_mgr.update_position.side_effect = ValueError("Invalid weight")

        result = cli_runner.invoke(
            portfolio,
            ['update', 'tech', 'AAPL', '--weight', '1.5'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Invalid weight' in result.output

    def test_update_position_error(self, cli_runner):
        """Test updating position handles general errors"""
        mock_mgr = Mock()
        mock_mgr.update_position.side_effect = Exception("Database error")

        result = cli_runner.invoke(
            portfolio,
            ['update', 'tech', 'AAPL', '--weight', '0.5'],
            obj={'portfolio_mgr': mock_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Failed to update position' in result.output
