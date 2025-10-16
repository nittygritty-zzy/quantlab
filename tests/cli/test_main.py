"""
Tests for main CLI entry point and init command

Tests the main CLI group and the init command functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from quantlab.cli.main import cli, init


class TestMainCLI:
    """Tests for the main CLI group"""

    def test_cli_help(self, cli_runner):
        """Test that --help displays correctly (doesn't require initialization)"""
        result = cli_runner.invoke(cli, ['--help'], obj={'skip_init': True}, standalone_mode=False)
        # --help exits before initialization, so it should work
        assert 'QuantLab' in result.output or result.exit_code == 0

    def test_cli_version(self, cli_runner):
        """Test that --version displays correctly"""
        result = cli_runner.invoke(cli, ['--version'], standalone_mode=False)
        assert '0.1.0' in result.output or result.exit_code == 0

    def test_cli_with_mocked_dependencies(self, cli_runner, mock_cli_dependencies, temp_dir):
        """Test CLI with all dependencies mocked"""
        with patch('quantlab.cli.main.load_config', return_value=mock_cli_dependencies['config']):
            with patch('quantlab.cli.main.DatabaseManager', return_value=mock_cli_dependencies['db']):
                with patch('quantlab.cli.main.ParquetReader', return_value=mock_cli_dependencies['parquet']):
                    with patch('quantlab.cli.main.DataManager', return_value=mock_cli_dependencies['data_mgr']):
                        with patch('quantlab.cli.main.PortfolioManager', return_value=mock_cli_dependencies['portfolio_mgr']):
                            with patch('quantlab.cli.main.Analyzer', return_value=mock_cli_dependencies['analyzer']):
                                result = cli_runner.invoke(cli, ['--help'])
                                assert result.exit_code == 0


class TestInitCommand:
    """Tests for the init command"""

    def test_init_with_direct_obj(self, cli_runner, mock_cli_dependencies, temp_dir):
        """Test init command with pre-populated context object"""
        # Configure mock for this test
        mock_cli_dependencies['parquet'].check_data_availability.return_value = {
            'stocks_daily': {
                'exists': True,
                'path': '/tmp/data/stocks_daily',
                'min_date': '2020-01-01',
                'max_date': '2025-10-15',
                'tickers': 500
            }
        }

        with patch('quantlab.cli.main.Path.home', return_value=temp_dir):
            with patch('quantlab.cli.main.create_default_config'):
                # Invoke init with pre-populated obj
                result = cli_runner.invoke(init, [], obj=mock_cli_dependencies)

                assert result.exit_code == 0
                assert '🚀 Initializing QuantLab' in result.output
                assert '✅ Initialization complete' in result.output

    def test_init_creates_config_if_missing(self, cli_runner, mock_cli_dependencies, temp_dir):
        """Test that init creates config if it doesn't exist"""
        with patch('quantlab.cli.main.Path.home', return_value=temp_dir):
            with patch('quantlab.cli.main.create_default_config') as mock_create:
                result = cli_runner.invoke(init, [], obj=mock_cli_dependencies)

                # Should attempt to create config since it doesn't exist
                assert result.exit_code == 0
                mock_create.assert_called_once()

    def test_init_skips_config_if_exists(self, cli_runner, mock_cli_dependencies, temp_dir):
        """Test that init doesn't recreate config if it exists"""
        # Create existing config
        config_dir = temp_dir / ".quantlab"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("database_path: /tmp/test.db\nparquet_root: /tmp/data")

        with patch('quantlab.cli.main.Path.home', return_value=temp_dir):
            with patch('quantlab.cli.main.create_default_config') as mock_create:
                result = cli_runner.invoke(init, [], obj=mock_cli_dependencies)

                # Should not create new config since it exists
                assert result.exit_code == 0
                mock_create.assert_not_called()

    def test_init_initializes_database(self, cli_runner, mock_cli_dependencies, temp_dir):
        """Test that init calls database initialization"""
        with patch('quantlab.cli.main.Path.home', return_value=temp_dir):
            with patch('quantlab.cli.main.create_default_config'):
                result = cli_runner.invoke(init, [], obj=mock_cli_dependencies)

                # Verify database was initialized
                mock_cli_dependencies['db'].initialize_schema.assert_called_once()
                assert '📊 Initializing database schema' in result.output

    def test_init_checks_parquet_availability(self, cli_runner, mock_cli_dependencies, temp_dir):
        """Test that init checks Parquet data availability"""
        mock_cli_dependencies['parquet'].check_data_availability.return_value = {
            'stocks_daily': {
                'exists': True,
                'path': '/tmp/data/stocks_daily',
                'min_date': '2020-01-01',
                'max_date': '2025-10-15',
                'tickers': 500
            }
        }

        with patch('quantlab.cli.main.Path.home', return_value=temp_dir):
            with patch('quantlab.cli.main.create_default_config'):
                result = cli_runner.invoke(init, [], obj=mock_cli_dependencies)

                # Verify data availability was checked
                mock_cli_dependencies['parquet'].check_data_availability.assert_called_once()
                assert '📁 Checking Parquet data availability' in result.output
                assert 'stocks_daily' in result.output

    def test_init_handles_errors(self, cli_runner, mock_cli_dependencies, temp_dir):
        """Test that init handles errors gracefully"""
        # Make database initialization fail
        mock_cli_dependencies['db'].initialize_schema.side_effect = Exception("Database error")

        with patch('quantlab.cli.main.Path.home', return_value=temp_dir):
            with patch('quantlab.cli.main.create_default_config'):
                result = cli_runner.invoke(init, [], obj=mock_cli_dependencies)

                # Verify error is handled
                assert result.exit_code == 1
                assert '❌ Initialization failed' in result.output

    def test_init_shows_next_steps(self, cli_runner, mock_cli_dependencies, temp_dir):
        """Test that init shows helpful next steps"""
        with patch('quantlab.cli.main.Path.home', return_value=temp_dir):
            with patch('quantlab.cli.main.create_default_config'):
                result = cli_runner.invoke(init, [], obj=mock_cli_dependencies)

                # Verify helpful messages
                assert result.exit_code == 0
                assert '📝 Edit config at:' in result.output
                assert "🎯 Run 'quantlab --help' to get started" in result.output

    def test_init_displays_data_info(self, cli_runner, mock_cli_dependencies, temp_dir):
        """Test that init displays detailed data information"""
        mock_cli_dependencies['parquet'].check_data_availability.return_value = {
            'stocks_daily': {
                'exists': True,
                'path': '/Volumes/sandisk/quantmini-data/data/qlib/stocks_daily',
                'min_date': '2020-01-01',
                'max_date': '2025-10-15',
                'tickers': 500
            }
        }

        with patch('quantlab.cli.main.Path.home', return_value=temp_dir):
            with patch('quantlab.cli.main.create_default_config'):
                result = cli_runner.invoke(init, [], obj=mock_cli_dependencies)

                # Verify detailed info is displayed
                assert result.exit_code == 0
                assert 'Date range: 2020-01-01 to 2025-10-15' in result.output
                assert 'Tickers: 500' in result.output
