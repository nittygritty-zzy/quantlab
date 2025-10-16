"""
Integration Test Fixtures

Provides real components for integration testing (no mocks).
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner
import sqlite3

from quantlab.utils.config import Config
from quantlab.data.database import DatabaseManager
from quantlab.data.parquet_reader import ParquetReader
from quantlab.core.portfolio_manager import PortfolioManager


@pytest.fixture
def cli_runner():
    """Provides a Click CLI runner for testing commands"""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Provides a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_db_path(temp_dir):
    """Provides a path for test database"""
    return temp_dir / "test_quantlab.db"


@pytest.fixture
def test_parquet_dir(temp_dir):
    """Provides a directory for test parquet data"""
    parquet_dir = temp_dir / "data" / "parquet"
    parquet_dir.mkdir(parents=True, exist_ok=True)
    return parquet_dir


@pytest.fixture
def test_config(test_db_path, test_parquet_dir, temp_dir):
    """Provides a real Config object for testing"""
    config = Config(
        polygon_api_key="test_key",
        alphavantage_api_key="test_av_key",
        database_path=str(test_db_path),
        parquet_root=str(test_parquet_dir)
    )
    return config


@pytest.fixture
def real_db(test_db_path):
    """Provides a real DatabaseManager with initialized schema"""
    db = DatabaseManager(str(test_db_path))
    db.initialize_schema()
    yield db
    # Cleanup
    db.close()
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def real_parquet_reader(test_parquet_dir):
    """Provides a real ParquetReader (won't have actual data)"""
    return ParquetReader(str(test_parquet_dir))


@pytest.fixture
def real_portfolio_manager(real_db):
    """Provides a real PortfolioManager"""
    return PortfolioManager(real_db)


@pytest.fixture
def sample_portfolio(real_portfolio_manager):
    """Creates a sample portfolio for testing"""
    portfolio = real_portfolio_manager.create_portfolio(
        portfolio_id="test_portfolio",
        name="Test Portfolio",
        description="Integration test portfolio"
    )

    # Add some positions
    real_portfolio_manager.add_position(
        portfolio_id="test_portfolio",
        ticker="AAPL",
        weight=0.40,
        shares=100,
        cost_basis=150.00
    )

    real_portfolio_manager.add_position(
        portfolio_id="test_portfolio",
        ticker="GOOGL",
        weight=0.35,
        shares=50,
        cost_basis=2800.00
    )

    real_portfolio_manager.add_position(
        portfolio_id="test_portfolio",
        ticker="MSFT",
        weight=0.25,
        shares=75,
        cost_basis=380.00
    )

    return portfolio


@pytest.fixture
def portfolio_config_dir(test_config):
    """Creates portfolio config directory"""
    portfolio_dir = test_config.config_dir / "portfolios"
    portfolio_dir.mkdir(parents=True, exist_ok=True)
    return portfolio_dir


@pytest.fixture
def cli_context(test_config, real_db, real_parquet_reader, real_portfolio_manager):
    """Provides a complete CLI context with real objects"""
    return {
        'config': test_config,
        'db': real_db,
        'parquet': real_parquet_reader,
        'portfolio_mgr': real_portfolio_manager,
        'data_mgr': None,  # Would need real API keys
        'analyzer': None   # Would need real API keys
    }


@pytest.fixture(autouse=True)
def cleanup_test_files(temp_dir):
    """Automatically cleanup test files after each test"""
    yield
    # Cleanup happens automatically with temp_dir context manager


# Mark all integration tests
def pytest_collection_modifyitems(items):
    """Add integration marker to all tests in this directory"""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
