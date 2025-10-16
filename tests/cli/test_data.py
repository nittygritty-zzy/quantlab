"""
Tests for data query CLI commands

Tests all 4 data commands: check, tickers, query, range
"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock
import pandas as pd
from click.testing import CliRunner

from quantlab.cli.data import (
    data,
    check_data,
    list_tickers,
    query_data,
    date_range
)


class TestDataCheck:
    """Tests for 'data check' command"""

    def test_check_data_all_exists(self, cli_runner):
        """Test checking data when all data types exist"""
        mock_parquet = Mock()
        mock_parquet.check_data_availability.return_value = {
            'stocks_daily': {
                'exists': True,
                'path': '/data/stocks_daily',
                'min_date': date(2020, 1, 1),
                'max_date': date(2025, 10, 15),
                'tickers': 500
            },
            'options_daily': {
                'exists': True,
                'path': '/data/options_daily',
                'min_date': date(2020, 1, 1),
                'max_date': date(2025, 10, 15),
                'tickers': 100
            }
        }

        result = cli_runner.invoke(
            data,
            ['check'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert '📁 Parquet Data Availability' in result.output
        assert 'STOCKS DAILY' in result.output
        assert 'OPTIONS DAILY' in result.output
        assert '2020-01-01' in result.output
        assert '500' in result.output

    def test_check_data_some_missing(self, cli_runner):
        """Test checking data when some data types don't exist"""
        mock_parquet = Mock()
        mock_parquet.check_data_availability.return_value = {
            'stocks_daily': {
                'exists': True,
                'path': '/data/stocks_daily',
                'min_date': date(2020, 1, 1),
                'max_date': date(2025, 10, 15),
                'tickers': 500
            },
            'options_daily': {
                'exists': False,
                'path': '/data/options_daily'
            }
        }

        result = cli_runner.invoke(
            data,
            ['check'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert '✓ STOCKS DAILY' in result.output
        assert '✗ OPTIONS DAILY' in result.output

    def test_check_data_error(self, cli_runner):
        """Test check data handles errors"""
        mock_parquet = Mock()
        mock_parquet.check_data_availability.side_effect = Exception("Data access error")

        result = cli_runner.invoke(
            data,
            ['check'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert '❌ Failed to check data' in result.output


class TestDataTickers:
    """Tests for 'data tickers' command"""

    def test_list_tickers_success(self, cli_runner):
        """Test listing tickers successfully"""
        mock_parquet = Mock()
        mock_tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
        mock_parquet.get_available_tickers.return_value = mock_tickers

        result = cli_runner.invoke(
            data,
            ['tickers'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert '📊 Available Tickers in stocks_daily (8 total)' in result.output
        assert 'AAPL' in result.output
        assert 'GOOGL' in result.output

    def test_list_tickers_with_type(self, cli_runner):
        """Test listing tickers with specific data type"""
        mock_parquet = Mock()
        mock_tickers = ['AAPL', 'GOOGL', 'MSFT']
        mock_parquet.get_available_tickers.return_value = mock_tickers

        result = cli_runner.invoke(
            data,
            ['tickers', '--type', 'options_daily'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert 'options_daily' in result.output
        mock_parquet.get_available_tickers.assert_called_once_with('options_daily')

    def test_list_tickers_empty(self, cli_runner):
        """Test listing tickers when none found"""
        mock_parquet = Mock()
        mock_parquet.get_available_tickers.return_value = []

        result = cli_runner.invoke(
            data,
            ['tickers'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert 'No tickers found' in result.output

    def test_list_tickers_large_list(self, cli_runner):
        """Test listing many tickers displays in columns"""
        mock_parquet = Mock()
        mock_tickers = [f'TICK{i:03d}' for i in range(100)]
        mock_parquet.get_available_tickers.return_value = mock_tickers

        result = cli_runner.invoke(
            data,
            ['tickers'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert '(100 total)' in result.output
        assert 'TICK000' in result.output

    def test_list_tickers_error(self, cli_runner):
        """Test listing tickers handles errors"""
        mock_parquet = Mock()
        mock_parquet.get_available_tickers.side_effect = Exception("Data access error")

        result = cli_runner.invoke(
            data,
            ['tickers'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert '❌ Failed to list tickers' in result.output


class TestDataQuery:
    """Tests for 'data query' command"""

    def test_query_data_basic(self, cli_runner):
        """Test basic data query"""
        mock_parquet = Mock()
        mock_df = pd.DataFrame({
            'date': ['2025-01-01', '2025-01-02'],
            'ticker': ['AAPL', 'AAPL'],
            'close': [180.5, 182.3]
        })
        mock_parquet.get_stock_daily.return_value = mock_df

        result = cli_runner.invoke(
            data,
            ['query', 'AAPL'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert '📈 Query Results (2 rows)' in result.output
        assert 'AAPL' in result.output

    def test_query_data_with_date_range(self, cli_runner):
        """Test querying data with date range"""
        mock_parquet = Mock()
        mock_df = pd.DataFrame({
            'date': ['2025-01-01'],
            'ticker': ['AAPL'],
            'close': [180.5]
        })
        mock_parquet.get_stock_daily.return_value = mock_df

        result = cli_runner.invoke(
            data,
            ['query', 'AAPL', '--start', '2025-01-01', '--end', '2025-01-31'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        mock_parquet.get_stock_daily.assert_called_once()
        call_args = mock_parquet.get_stock_daily.call_args
        assert call_args[1]['start_date'] == date(2025, 1, 1)
        assert call_args[1]['end_date'] == date(2025, 1, 31)

    def test_query_data_with_limit(self, cli_runner):
        """Test querying data with row limit"""
        mock_parquet = Mock()
        mock_df = pd.DataFrame({
            'date': ['2025-01-01'],
            'ticker': ['AAPL'],
            'close': [180.5]
        })
        mock_parquet.get_stock_daily.return_value = mock_df

        result = cli_runner.invoke(
            data,
            ['query', 'AAPL', '--limit', '50'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        call_args = mock_parquet.get_stock_daily.call_args
        assert call_args[1]['limit'] == 50

    def test_query_data_multiple_tickers(self, cli_runner):
        """Test querying multiple tickers"""
        mock_parquet = Mock()
        mock_df = pd.DataFrame({
            'date': ['2025-01-01', '2025-01-01'],
            'ticker': ['AAPL', 'GOOGL'],
            'close': [180.5, 2850.0]
        })
        mock_parquet.get_stock_daily.return_value = mock_df

        result = cli_runner.invoke(
            data,
            ['query', 'AAPL', 'GOOGL', 'MSFT'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        call_args = mock_parquet.get_stock_daily.call_args
        assert set(call_args[1]['tickers']) == {'AAPL', 'GOOGL', 'MSFT'}

    def test_query_data_options(self, cli_runner):
        """Test querying options data"""
        mock_parquet = Mock()
        mock_df = pd.DataFrame({
            'date': ['2025-01-01'],
            'underlying': ['AAPL'],
            'strike': [180.0],
            'option_type': ['call']
        })
        mock_parquet.get_options_daily.return_value = mock_df

        result = cli_runner.invoke(
            data,
            ['query', 'AAPL', '--type', 'options_daily'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        mock_parquet.get_options_daily.assert_called_once()

    def test_query_data_no_results(self, cli_runner):
        """Test querying data with no results"""
        mock_parquet = Mock()
        mock_parquet.get_stock_daily.return_value = pd.DataFrame()

        result = cli_runner.invoke(
            data,
            ['query', 'INVALID'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert 'No data found' in result.output

    def test_query_data_large_result(self, cli_runner):
        """Test querying data with large result set"""
        mock_parquet = Mock()
        # Create 50 rows
        mock_df = pd.DataFrame({
            'date': [f'2025-01-{i:02d}' for i in range(1, 51)],
            'ticker': ['AAPL'] * 50,
            'close': [180.0 + i for i in range(50)]
        })
        mock_parquet.get_stock_daily.return_value = mock_df

        result = cli_runner.invoke(
            data,
            ['query', 'AAPL', '--limit', '50'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert '📈 Query Results (50 rows)' in result.output
        assert 'Showing first 20 rows' in result.output
        assert '... 30 more rows' in result.output

    def test_query_data_error(self, cli_runner):
        """Test querying data handles errors"""
        mock_parquet = Mock()
        mock_parquet.get_stock_daily.side_effect = Exception("Query error")

        result = cli_runner.invoke(
            data,
            ['query', 'AAPL'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert '❌ Failed to query data' in result.output


class TestDataRange:
    """Tests for 'data range' command"""

    def test_date_range_success(self, cli_runner):
        """Test showing date range successfully"""
        mock_parquet = Mock()
        mock_parquet.get_date_range.return_value = (
            date(2020, 1, 1),
            date(2025, 10, 15)
        )

        result = cli_runner.invoke(
            data,
            ['range'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert '📅 Date Range for stocks_daily' in result.output
        assert 'Start: 2020-01-01' in result.output
        assert 'End:   2025-10-15' in result.output
        assert 'Duration:' in result.output
        assert 'years' in result.output

    def test_date_range_with_type(self, cli_runner):
        """Test showing date range for specific data type"""
        mock_parquet = Mock()
        mock_parquet.get_date_range.return_value = (
            date(2020, 1, 1),
            date(2025, 10, 15)
        )

        result = cli_runner.invoke(
            data,
            ['range', '--type', 'options_daily'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert 'options_daily' in result.output
        mock_parquet.get_date_range.assert_called_once_with('options_daily')

    def test_date_range_no_data(self, cli_runner):
        """Test showing date range when no data exists"""
        mock_parquet = Mock()
        mock_parquet.get_date_range.return_value = (None, None)

        result = cli_runner.invoke(
            data,
            ['range'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert 'No data found' in result.output

    def test_date_range_calculates_duration(self, cli_runner):
        """Test that date range calculates duration correctly"""
        mock_parquet = Mock()
        # 365 days = 1 year
        mock_parquet.get_date_range.return_value = (
            date(2024, 1, 1),
            date(2025, 1, 1)
        )

        result = cli_runner.invoke(
            data,
            ['range'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert 'Duration: 366 days' in result.output  # 2024 is a leap year
        assert '1.0 years' in result.output

    def test_date_range_error(self, cli_runner):
        """Test date range handles errors"""
        mock_parquet = Mock()
        mock_parquet.get_date_range.side_effect = Exception("Data access error")

        result = cli_runner.invoke(
            data,
            ['range'],
            obj={'parquet': mock_parquet}
        )

        assert result.exit_code == 0
        assert '❌ Failed to get date range' in result.output


class TestDataCommandGroup:
    """Tests for the data command group"""

    def test_data_help(self, cli_runner):
        """Test that data --help displays correctly"""
        result = cli_runner.invoke(data, ['--help'])
        assert result.exit_code == 0
        assert 'Query historical Parquet data' in result.output
        assert 'check' in result.output
        assert 'tickers' in result.output
        assert 'query' in result.output
        assert 'range' in result.output

    def test_data_has_all_subcommands(self, cli_runner):
        """Test that all expected subcommands are registered"""
        result = cli_runner.invoke(data, ['--help'])
        commands = ['check', 'tickers', 'query', 'range']
        for cmd in commands:
            assert cmd in result.output
