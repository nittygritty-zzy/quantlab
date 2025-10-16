"""
Pytest Configuration and Fixtures for CLI Tests

This module provides shared fixtures and configuration for testing the QuantLab CLI.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """
    Provides a Click CLI runner for testing commands.

    Returns:
        CliRunner instance for invoking CLI commands
    """
    return CliRunner()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Provides a temporary directory for test files.

    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config_dir(temp_dir: Path) -> Path:
    """
    Creates a mock config directory structure.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to mock config directory
    """
    config_dir = temp_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create portfolios directory
    portfolios_dir = config_dir / "portfolios"
    portfolios_dir.mkdir(parents=True, exist_ok=True)

    # Create lookup directory
    lookup_dir = config_dir / "lookup"
    lookup_dir.mkdir(parents=True, exist_ok=True)

    return config_dir


@pytest.fixture
def mock_portfolio_data() -> Dict[str, Any]:
    """
    Provides mock portfolio data for testing.

    Returns:
        Dictionary with sample portfolio structure
    """
    return {
        "name": "test_portfolio",
        "description": "Test portfolio for unit tests",
        "created_at": "2025-10-15T10:00:00",
        "positions": [
            {
                "ticker": "AAPL",
                "shares": 100,
                "entry_price": 150.00,
                "entry_date": "2025-01-01"
            },
            {
                "ticker": "GOOGL",
                "shares": 50,
                "entry_price": 2800.00,
                "entry_date": "2025-01-01"
            }
        ]
    }


@pytest.fixture
def mock_portfolio_file(mock_config_dir: Path, mock_portfolio_data: Dict[str, Any]) -> Path:
    """
    Creates a mock portfolio file.

    Args:
        mock_config_dir: Mock config directory fixture
        mock_portfolio_data: Mock portfolio data fixture

    Returns:
        Path to created portfolio file
    """
    portfolio_file = mock_config_dir / "portfolios" / "test_portfolio.json"
    with open(portfolio_file, 'w') as f:
        json.dump(mock_portfolio_data, f, indent=2)
    return portfolio_file


@pytest.fixture
def mock_parquet_data() -> Mock:
    """
    Provides mock Parquet data for testing data queries.

    Returns:
        Mock object simulating Parquet data access
    """
    mock_data = Mock()
    mock_data.columns = ["date", "ticker", "open", "high", "low", "close", "volume"]
    mock_data.shape = (100, 7)
    return mock_data


@pytest.fixture
def mock_lookup_manager() -> Mock:
    """
    Provides mock LookupTableManager for testing lookup commands.

    Returns:
        Mock LookupTableManager instance
    """
    mock_manager = Mock()
    mock_manager.get_table_stats.return_value = {
        "ticker_info": {"rows": 5000, "last_updated": "2025-10-15"},
        "fundamentals": {"rows": 10000, "last_updated": "2025-10-14"}
    }
    return mock_manager


@pytest.fixture
def mock_data_api() -> Mock:
    """
    Provides mock data API for testing data fetching.

    Returns:
        Mock data API instance
    """
    mock_api = Mock()
    mock_api.get_ticker_data.return_value = {
        "ticker": "AAPL",
        "price": 180.50,
        "volume": 50000000,
        "market_cap": 2800000000000
    }
    return mock_api


@pytest.fixture
def patch_config_path(mock_config_dir: Path) -> Generator[None, None, None]:
    """
    Patches the config directory path to use temp directory.

    Args:
        mock_config_dir: Mock config directory fixture

    Yields:
        None (context manager)
    """
    with patch('quantlab.core.config.get_config_dir', return_value=mock_config_dir):
        yield


@pytest.fixture
def patch_data_path(temp_dir: Path) -> Generator[None, None, None]:
    """
    Patches the data directory path to use temp directory.

    Args:
        temp_dir: Temporary directory fixture

    Yields:
        None (context manager)
    """
    data_dir = temp_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    with patch('quantlab.core.config.get_data_dir', return_value=data_dir):
        yield


@pytest.fixture
def isolated_filesystem(cli_runner: CliRunner) -> Generator[None, None, None]:
    """
    Provides an isolated filesystem for CLI tests.

    Args:
        cli_runner: Click CLI runner fixture

    Yields:
        None (context manager)
    """
    with cli_runner.isolated_filesystem():
        yield


@pytest.fixture
def sample_analysis_result() -> Dict[str, Any]:
    """
    Provides sample analysis result for testing analyze commands.

    Returns:
        Dictionary with mock analysis data
    """
    return {
        "ticker": "AAPL",
        "timestamp": "2025-10-15T10:00:00",
        "price_data": {
            "current": 180.50,
            "change": 2.50,
            "change_pct": 1.40
        },
        "fundamentals": {
            "pe_ratio": 28.5,
            "market_cap": 2800000000000
        },
        "sentiment": {
            "score": 0.75,
            "source": "news_api"
        }
    }


@pytest.fixture(autouse=True)
def reset_env_vars(monkeypatch):
    """
    Automatically resets environment variables for each test.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    # Clear any environment variables that might affect tests
    monkeypatch.delenv("QUANTLAB_CONFIG_DIR", raising=False)
    monkeypatch.delenv("QUANTLAB_DATA_DIR", raising=False)
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)


def create_mock_config(temp_dir):
    """
    Create a properly configured mock config object.

    Args:
        temp_dir: Temporary directory path

    Returns:
        Mock config object with proper path attributes
    """
    from pathlib import Path
    mock_config = Mock()
    mock_config.database_path = str(Path(temp_dir) / "quantlab.db")
    mock_config.parquet_root = str(Path(temp_dir) / "data")
    mock_config.polygon_api_key = "test_polygon_key"
    mock_config.alphavantage_api_key = "test_av_key"
    return mock_config


@pytest.fixture
def mock_cli_dependencies(temp_dir):
    """
    Mock all CLI dependencies for testing.

    Returns:
        Dictionary with all mocked objects
    """
    from pathlib import Path

    mocks = {}

    # Create mock config with proper string paths
    mock_config = create_mock_config(temp_dir)

    # Mock database
    mock_db = Mock()
    mock_db.initialize_schema = Mock(return_value=None)

    # Mock parquet reader
    mock_parquet = Mock()
    mock_parquet.check_data_availability = Mock(return_value={})
    mock_parquet.get_available_tickers = Mock(return_value=[])
    mock_parquet.get_date_range = Mock(return_value=(None, None))

    # Mock data manager
    mock_data_mgr = Mock()
    mock_data_mgr.lookup = Mock()

    # Mock portfolio manager
    mock_portfolio_mgr = Mock()

    # Mock analyzer
    mock_analyzer = Mock()

    mocks['config'] = mock_config
    mocks['db'] = mock_db
    mocks['parquet'] = mock_parquet
    mocks['data_mgr'] = mock_data_mgr
    mocks['portfolio_mgr'] = mock_portfolio_mgr
    mocks['analyzer'] = mock_analyzer

    return mocks
