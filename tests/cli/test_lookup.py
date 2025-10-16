"""
Tests for lookup table management CLI commands

Tests all 5 lookup commands: init, stats, refresh, get, refresh-portfolio
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from click.testing import CliRunner

from quantlab.cli.lookup import (
    lookup,
    init_tables,
    show_stats,
    refresh_tables,
    get_data,
    refresh_portfolio
)


class TestLookupInit:
    """Tests for 'lookup init' command"""

    def test_init_tables_success(self, cli_runner):
        """Test successful table initialization"""
        mock_lookup = Mock()
        mock_lookup.initialize_tables.return_value = None
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['init'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '🔧 Initializing lookup tables' in result.output
        assert '✅ Lookup tables initialized' in result.output
        mock_lookup.initialize_tables.assert_called_once()

    def test_init_tables_error(self, cli_runner):
        """Test table initialization handles errors"""
        mock_lookup = Mock()
        mock_lookup.initialize_tables.side_effect = Exception("Database error")
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['init'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Failed to initialize tables' in result.output


class TestLookupStats:
    """Tests for 'lookup stats' command"""

    def test_show_stats_success(self, cli_runner):
        """Test showing statistics successfully"""
        mock_lookup = Mock()
        mock_lookup.get_refresh_stats.return_value = {
            'company_info_count': 100,
            'analyst_ratings_count': 80,
            'treasury_rates_count': 5,
            'financial_statements_count': 50,
            'corporate_actions_count': 25,
            'company_info_stale': 10,
            'analyst_ratings_stale': 5,
            'treasury_rates_stale': 1
        }
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['stats'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '📊 Lookup Table Statistics' in result.output
        assert 'Company Info: 100' in result.output
        assert 'Analyst Ratings: 80' in result.output
        assert 'Treasury Rates: 5' in result.output
        assert 'Company Info (>7 days): 10' in result.output
        assert 'Analyst Ratings (>1 day): 5' in result.output

    def test_show_stats_empty(self, cli_runner):
        """Test showing statistics with no records"""
        mock_lookup = Mock()
        mock_lookup.get_refresh_stats.return_value = {}
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['stats'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '📊 Lookup Table Statistics' in result.output
        assert 'Company Info: 0' in result.output

    def test_show_stats_error(self, cli_runner):
        """Test showing statistics handles errors"""
        mock_lookup = Mock()
        mock_lookup.get_refresh_stats.side_effect = Exception("Database error")
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['stats'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Failed to get stats' in result.output


class TestLookupRefresh:
    """Tests for 'lookup refresh' command"""

    def test_refresh_company_info(self, cli_runner):
        """Test refreshing company info"""
        mock_lookup = Mock()
        mock_lookup.batch_refresh_company_info.return_value = {
            'AAPL': True,
            'GOOGL': True,
            'MSFT': True
        }
        mock_data_mgr = Mock(lookup=mock_lookup)
        mock_config = Mock()

        result = cli_runner.invoke(
            lookup,
            ['refresh', 'company', 'AAPL', 'GOOGL', 'MSFT'],
            obj={'data_mgr': mock_data_mgr, 'config': mock_config}
        )

        assert result.exit_code == 0
        assert '🏢 Refreshing company info for 3 ticker(s)' in result.output
        assert '✅ 3/3 successful' in result.output

    def test_refresh_company_info_with_failures(self, cli_runner):
        """Test refreshing company info with some failures"""
        mock_lookup = Mock()
        mock_lookup.batch_refresh_company_info.return_value = {
            'AAPL': True,
            'INVALID': False,
            'MSFT': True
        }
        mock_data_mgr = Mock(lookup=mock_lookup)
        mock_config = Mock()

        result = cli_runner.invoke(
            lookup,
            ['refresh', 'company', 'AAPL', 'INVALID', 'MSFT'],
            obj={'data_mgr': mock_data_mgr, 'config': mock_config}
        )

        assert result.exit_code == 0
        assert '✅ 2/3 successful' in result.output
        assert '⚠️  Failed: INVALID' in result.output

    def test_refresh_analyst_ratings(self, cli_runner):
        """Test refreshing analyst ratings"""
        mock_lookup = Mock()
        mock_lookup.batch_refresh_analyst_ratings.return_value = {
            'AAPL': True,
            'GOOGL': True
        }
        mock_data_mgr = Mock(lookup=mock_lookup)
        mock_config = Mock()

        result = cli_runner.invoke(
            lookup,
            ['refresh', 'ratings', 'AAPL', 'GOOGL'],
            obj={'data_mgr': mock_data_mgr, 'config': mock_config}
        )

        assert result.exit_code == 0
        assert '⭐ Refreshing analyst ratings for 2 ticker(s)' in result.output
        assert '✅ 2/2 successful' in result.output

    def test_refresh_treasury_rates(self, cli_runner):
        """Test refreshing treasury rates"""
        mock_lookup = Mock()
        mock_lookup.refresh_treasury_rates.return_value = True
        mock_data_mgr = Mock(lookup=mock_lookup)
        mock_config = Mock(alphavantage_api_key='test_key')

        result = cli_runner.invoke(
            lookup,
            ['refresh', 'treasury'],
            obj={'data_mgr': mock_data_mgr, 'config': mock_config}
        )

        assert result.exit_code == 0
        assert '📈 Refreshing treasury rates' in result.output
        assert '✅ Treasury rates refreshed' in result.output

    def test_refresh_treasury_rates_failure(self, cli_runner):
        """Test refreshing treasury rates with failure"""
        mock_lookup = Mock()
        mock_lookup.refresh_treasury_rates.return_value = False
        mock_data_mgr = Mock(lookup=mock_lookup)
        mock_config = Mock(alphavantage_api_key='test_key')

        result = cli_runner.invoke(
            lookup,
            ['refresh', 'treasury'],
            obj={'data_mgr': mock_data_mgr, 'config': mock_config}
        )

        assert result.exit_code == 0
        assert '⚠️  Treasury rates refresh failed' in result.output

    def test_refresh_all(self, cli_runner):
        """Test refreshing all lookup tables"""
        mock_lookup = Mock()
        mock_lookup.refresh_treasury_rates.return_value = True
        mock_lookup.batch_refresh_company_info.return_value = {'AAPL': True}
        mock_lookup.batch_refresh_analyst_ratings.return_value = {'AAPL': True}
        mock_data_mgr = Mock(lookup=mock_lookup)
        mock_config = Mock(alphavantage_api_key='test_key')

        result = cli_runner.invoke(
            lookup,
            ['refresh', 'all', 'AAPL'],
            obj={'data_mgr': mock_data_mgr, 'config': mock_config}
        )

        assert result.exit_code == 0
        assert '📈 Refreshing treasury rates' in result.output
        assert '🏢 Refreshing company info' in result.output
        assert '⭐ Refreshing analyst ratings' in result.output

    def test_refresh_no_tickers(self, cli_runner):
        """Test refresh command without tickers"""
        mock_data_mgr = Mock(lookup=Mock())
        mock_config = Mock()

        result = cli_runner.invoke(
            lookup,
            ['refresh', 'company'],
            obj={'data_mgr': mock_data_mgr, 'config': mock_config}
        )

        assert result.exit_code == 0
        assert '⚠️  No tickers specified' in result.output

    def test_refresh_error(self, cli_runner):
        """Test refresh command handles errors"""
        mock_lookup = Mock()
        mock_lookup.batch_refresh_company_info.side_effect = Exception("API error")
        mock_data_mgr = Mock(lookup=mock_lookup)
        mock_config = Mock()

        result = cli_runner.invoke(
            lookup,
            ['refresh', 'company', 'AAPL'],
            obj={'data_mgr': mock_data_mgr, 'config': mock_config}
        )

        assert result.exit_code == 0
        assert '❌ Failed to refresh' in result.output


class TestLookupGet:
    """Tests for 'lookup get' command"""

    def test_get_company_info(self, cli_runner):
        """Test getting company info"""
        mock_lookup = Mock()
        mock_lookup.get_company_info.return_value = {
            'company_name': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'exchange': 'NASDAQ',
            'employees': 150000,
            'website': 'https://www.apple.com',
            'last_refreshed': datetime(2025, 10, 15)
        }
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['get', 'company', 'AAPL'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '🏢 Company Info: AAPL' in result.output
        assert 'Name: Apple Inc.' in result.output
        assert 'Sector: Technology' in result.output
        assert 'Exchange: NASDAQ' in result.output
        assert 'Employees: 150,000' in result.output

    def test_get_company_info_not_found(self, cli_runner):
        """Test getting company info when not found"""
        mock_lookup = Mock()
        mock_lookup.get_company_info.return_value = None
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['get', 'company', 'INVALID'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '❌ No company info found for INVALID' in result.output

    def test_get_company_info_no_ticker(self, cli_runner):
        """Test getting company info without ticker"""
        mock_data_mgr = Mock(lookup=Mock())

        result = cli_runner.invoke(
            lookup,
            ['get', 'company'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Ticker required for company info' in result.output

    def test_get_analyst_ratings(self, cli_runner):
        """Test getting analyst ratings"""
        mock_lookup = Mock()
        mock_lookup.get_analyst_ratings.return_value = {
            'strong_buy': 15,
            'buy': 10,
            'hold': 5,
            'sell': 2,
            'strong_sell': 1,
            'average_rating': 2.1,
            'target_mean': 200.0,
            'target_median': 195.0,
            'target_high': 225.0,
            'target_low': 175.0,
            'last_refreshed': datetime(2025, 10, 15)
        }
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['get', 'ratings', 'AAPL'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '⭐ Analyst Ratings: AAPL' in result.output
        assert 'Total Ratings: 33' in result.output
        assert 'Strong Buy: 15' in result.output
        assert 'Buy: 10' in result.output
        assert 'Average Rating: 2.10 (Buy)' in result.output
        assert 'Mean: $200.00' in result.output

    def test_get_analyst_ratings_not_found(self, cli_runner):
        """Test getting analyst ratings when not found"""
        mock_lookup = Mock()
        mock_lookup.get_analyst_ratings.return_value = None
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['get', 'ratings', 'INVALID'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '❌ No analyst ratings found for INVALID' in result.output

    def test_get_analyst_ratings_no_ticker(self, cli_runner):
        """Test getting analyst ratings without ticker"""
        mock_data_mgr = Mock(lookup=Mock())

        result = cli_runner.invoke(
            lookup,
            ['get', 'ratings'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Ticker required for analyst ratings' in result.output

    def test_get_treasury_rate(self, cli_runner):
        """Test getting treasury rate"""
        mock_lookup = Mock()
        mock_lookup.get_treasury_rate.return_value = 0.045  # 4.5%
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['get', 'treasury'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '📈 Treasury Rate (3month): 4.500%' in result.output

    def test_get_treasury_rate_with_maturity(self, cli_runner):
        """Test getting treasury rate with specific maturity"""
        mock_lookup = Mock()
        mock_lookup.get_treasury_rate.return_value = 0.04
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['get', 'treasury', '--maturity', '10year'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '📈 Treasury Rate (10year): 4.000%' in result.output
        mock_lookup.get_treasury_rate.assert_called_once_with('10year')

    def test_get_treasury_rate_not_found(self, cli_runner):
        """Test getting treasury rate when not found"""
        mock_lookup = Mock()
        mock_lookup.get_treasury_rate.return_value = None
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['get', 'treasury'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '❌ No treasury rate found' in result.output
        assert "Run 'quantlab lookup refresh treasury' first" in result.output

    def test_get_data_error(self, cli_runner):
        """Test get command handles errors"""
        mock_lookup = Mock()
        mock_lookup.get_company_info.side_effect = Exception("Database error")
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['get', 'company', 'AAPL'],
            obj={'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Failed to get data' in result.output


class TestLookupRefreshPortfolio:
    """Tests for 'lookup refresh-portfolio' command"""

    def test_refresh_portfolio_success(self, cli_runner):
        """Test refreshing portfolio lookup tables"""
        mock_portfolio_mgr = Mock()
        mock_portfolio_mgr.get_portfolio_summary.return_value = {
            'name': 'Tech Stocks',
            'tickers': ['AAPL', 'GOOGL', 'MSFT']
        }

        mock_lookup = Mock()
        mock_lookup.batch_refresh_company_info.return_value = {
            'AAPL': True, 'GOOGL': True, 'MSFT': True
        }
        mock_lookup.batch_refresh_analyst_ratings.return_value = {
            'AAPL': True, 'GOOGL': True, 'MSFT': True
        }
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['refresh-portfolio', 'tech'],
            obj={'portfolio_mgr': mock_portfolio_mgr, 'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '📊 Refreshing lookup tables for portfolio: Tech Stocks' in result.output
        assert 'Tickers: AAPL, GOOGL, MSFT' in result.output
        assert '🏢 Refreshing company info' in result.output
        assert '⭐ Refreshing analyst ratings' in result.output
        assert '✅ Portfolio lookup tables refreshed' in result.output

    def test_refresh_portfolio_no_company(self, cli_runner):
        """Test refreshing portfolio without company info"""
        mock_portfolio_mgr = Mock()
        mock_portfolio_mgr.get_portfolio_summary.return_value = {
            'name': 'Tech Stocks',
            'tickers': ['AAPL']
        }

        mock_lookup = Mock()
        mock_lookup.batch_refresh_analyst_ratings.return_value = {'AAPL': True}
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['refresh-portfolio', 'tech', '--no-company'],
            obj={'portfolio_mgr': mock_portfolio_mgr, 'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '🏢 Refreshing company info' not in result.output
        assert '⭐ Refreshing analyst ratings' in result.output

    def test_refresh_portfolio_no_ratings(self, cli_runner):
        """Test refreshing portfolio without analyst ratings"""
        mock_portfolio_mgr = Mock()
        mock_portfolio_mgr.get_portfolio_summary.return_value = {
            'name': 'Tech Stocks',
            'tickers': ['AAPL']
        }

        mock_lookup = Mock()
        mock_lookup.batch_refresh_company_info.return_value = {'AAPL': True}
        mock_data_mgr = Mock(lookup=mock_lookup)

        result = cli_runner.invoke(
            lookup,
            ['refresh-portfolio', 'tech', '--no-ratings'],
            obj={'portfolio_mgr': mock_portfolio_mgr, 'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '🏢 Refreshing company info' in result.output
        assert '⭐ Refreshing analyst ratings' not in result.output

    def test_refresh_portfolio_not_found(self, cli_runner):
        """Test refreshing non-existent portfolio"""
        mock_portfolio_mgr = Mock()
        mock_portfolio_mgr.get_portfolio_summary.return_value = None
        mock_data_mgr = Mock(lookup=Mock())

        result = cli_runner.invoke(
            lookup,
            ['refresh-portfolio', 'nonexistent'],
            obj={'portfolio_mgr': mock_portfolio_mgr, 'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Portfolio not found: nonexistent' in result.output

    def test_refresh_portfolio_error(self, cli_runner):
        """Test refresh portfolio handles errors"""
        mock_portfolio_mgr = Mock()
        mock_portfolio_mgr.get_portfolio_summary.side_effect = Exception("Database error")
        mock_data_mgr = Mock(lookup=Mock())

        result = cli_runner.invoke(
            lookup,
            ['refresh-portfolio', 'tech'],
            obj={'portfolio_mgr': mock_portfolio_mgr, 'data_mgr': mock_data_mgr}
        )

        assert result.exit_code == 0
        assert '❌ Failed to refresh portfolio' in result.output


class TestLookupCommandGroup:
    """Tests for the lookup command group"""

    def test_lookup_help(self, cli_runner):
        """Test that lookup --help displays correctly"""
        result = cli_runner.invoke(lookup, ['--help'])
        assert result.exit_code == 0
        assert 'Manage lookup tables' in result.output
        assert 'init' in result.output
        assert 'stats' in result.output
        assert 'refresh' in result.output
        assert 'get' in result.output
        assert 'refresh-portfolio' in result.output

    def test_lookup_has_all_subcommands(self, cli_runner):
        """Test that all expected subcommands are registered"""
        result = cli_runner.invoke(lookup, ['--help'])
        commands = ['init', 'stats', 'refresh', 'get', 'refresh-portfolio']
        for cmd in commands:
            assert cmd in result.output
