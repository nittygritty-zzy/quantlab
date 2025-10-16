"""
Integration tests for data query CLI commands

Tests data commands with real ParquetReader (no actual data files).
"""

import pytest
from pathlib import Path

from quantlab.cli.data import data


class TestDataIntegration:
    """Integration tests for data query commands"""

    def test_check_data_with_empty_directory(self, cli_runner, cli_context):
        """Test data check with no parquet files"""
        result = cli_runner.invoke(
            data,
            ['check'],
            obj=cli_context
        )

        assert result.exit_code == 0
        assert '📁 Parquet Data Availability' in result.output
        # Should show data types even if they don't exist
        assert 'stocks_daily' in result.output.lower() or '✗' in result.output

    def test_list_tickers_empty(self, cli_runner, cli_context):
        """Test listing tickers with no data"""
        result = cli_runner.invoke(
            data,
            ['tickers'],
            obj=cli_context
        )

        # Should handle empty data gracefully
        assert result.exit_code == 0
        # Either shows no tickers or appropriate message
        assert 'No tickers found' in result.output or '📊 Available Tickers' in result.output

    def test_date_range_no_data(self, cli_runner, cli_context):
        """Test date range with no data"""
        result = cli_runner.invoke(
            data,
            ['range'],
            obj=cli_context
        )

        assert result.exit_code == 0
        # Should indicate no data found
        assert 'No data found' in result.output or '📅 Date Range' in result.output

    def test_query_data_no_data(self, cli_runner, cli_context):
        """Test querying data when no files exist"""
        result = cli_runner.invoke(
            data,
            ['query', 'AAPL'],
            obj=cli_context
        )

        # Should handle gracefully
        assert result.exit_code == 0
        # Will either show "No data found" or error
        assert 'No data found' in result.output or '❌' in result.output


class TestDataCommandOptions:
    """Test data command options and parameters"""

    def test_tickers_with_type_option(self, cli_runner, cli_context):
        """Test tickers command with different data types"""
        data_types = ['stocks_daily', 'stocks_minute', 'options_daily', 'options_minute']

        for dtype in data_types:
            result = cli_runner.invoke(
                data,
                ['tickers', '--type', dtype],
                obj=cli_context
            )

            assert result.exit_code == 0
            # Should accept the data type without error

    def test_range_with_type_option(self, cli_runner, cli_context):
        """Test range command with different data types"""
        result = cli_runner.invoke(
            data,
            ['range', '--type', 'stocks_daily'],
            obj=cli_context
        )

        assert result.exit_code == 0

        result = cli_runner.invoke(
            data,
            ['range', '--type', 'options_daily'],
            obj=cli_context
        )

        assert result.exit_code == 0

    def test_query_with_date_range(self, cli_runner, cli_context):
        """Test query command with date parameters"""
        result = cli_runner.invoke(
            data,
            ['query', 'AAPL', '--start', '2024-01-01', '--end', '2024-12-31'],
            obj=cli_context
        )

        # Should accept date parameters
        assert result.exit_code == 0

    def test_query_with_limit(self, cli_runner, cli_context):
        """Test query command with limit parameter"""
        result = cli_runner.invoke(
            data,
            ['query', 'AAPL', '--limit', '50'],
            obj=cli_context
        )

        assert result.exit_code == 0

    def test_query_multiple_tickers(self, cli_runner, cli_context):
        """Test querying multiple tickers"""
        result = cli_runner.invoke(
            data,
            ['query', 'AAPL', 'GOOGL', 'MSFT'],
            obj=cli_context
        )

        assert result.exit_code == 0


class TestDataErrorHandling:
    """Test error handling in data commands"""

    def test_query_invalid_date_format(self, cli_runner, cli_context):
        """Test query with invalid date format"""
        result = cli_runner.invoke(
            data,
            ['query', 'AAPL', '--start', 'invalid-date'],
            obj=cli_context
        )

        # Should show error
        assert '❌' in result.output or result.exit_code != 0

    def test_query_without_ticker(self, cli_runner, cli_context):
        """Test query command without ticker argument"""
        result = cli_runner.invoke(
            data,
            ['query'],
            obj=cli_context
        )

        # Should require ticker
        assert result.exit_code != 0 or 'required' in result.output.lower()
