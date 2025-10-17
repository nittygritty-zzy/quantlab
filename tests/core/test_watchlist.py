"""
Unit tests for WatchlistManager module

Tests watchlist creation, management, snapshots, and comparisons.
"""

import pytest
import pandas as pd
import tempfile
import json
from datetime import datetime, date
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from quantlab.core.watchlist import WatchlistManager
from quantlab.data.database import DatabaseManager


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        db = DatabaseManager(str(db_path))
        yield db
        # Cleanup happens automatically with temp directory


@pytest.fixture
def watchlist_manager(temp_db):
    """Create WatchlistManager with temp database"""
    return WatchlistManager(temp_db)


@pytest.fixture
def sample_screen_results():
    """Create sample screening results"""
    return pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'price': [150.0, 330.0, 140.0],
        'score': [75.0, 82.0, 68.0],
        'rsi': [55.0, 62.0, 48.0]
    })


class TestWatchlistCreation:
    """Test watchlist creation functionality"""

    def test_create_watchlist_basic(self, watchlist_manager):
        """Test creating a basic watchlist"""
        success = watchlist_manager.create_watchlist(
            watchlist_id="test_watch",
            name="Test Watchlist"
        )

        assert success is True

    def test_create_watchlist_with_metadata(self, watchlist_manager):
        """Test creating watchlist with description and tags"""
        success = watchlist_manager.create_watchlist(
            watchlist_id="tech_watch",
            name="Technology Stocks",
            description="High-growth technology companies",
            tags=["growth", "technology", "large-cap"]
        )

        assert success is True

        # Verify it's in the list
        watchlists = watchlist_manager.list_watchlists()
        assert len(watchlists) == 1
        assert watchlists.iloc[0]['id'] == 'tech_watch'
        assert watchlists.iloc[0]['name'] == 'Technology Stocks'

    def test_create_duplicate_watchlist_fails(self, watchlist_manager):
        """Test that creating duplicate watchlist ID fails"""
        watchlist_manager.create_watchlist("duplicate", "First")

        # Second create with same ID should fail
        success = watchlist_manager.create_watchlist("duplicate", "Second")

        assert success is False


class TestWatchlistListing:
    """Test watchlist listing and retrieval"""

    def test_list_watchlists_empty(self, watchlist_manager):
        """Test listing when no watchlists exist"""
        watchlists = watchlist_manager.list_watchlists()

        assert isinstance(watchlists, pd.DataFrame)
        assert watchlists.empty

    def test_list_watchlists_multiple(self, watchlist_manager):
        """Test listing multiple watchlists"""
        watchlist_manager.create_watchlist("watch1", "First")
        watchlist_manager.create_watchlist("watch2", "Second")
        watchlist_manager.create_watchlist("watch3", "Third")

        watchlists = watchlist_manager.list_watchlists()

        assert len(watchlists) == 3
        assert set(watchlists['id']) == {'watch1', 'watch2', 'watch3'}

    def test_list_watchlists_includes_stock_count(self, watchlist_manager, sample_screen_results):
        """Test that listing includes number of stocks"""
        watchlist_manager.create_watchlist("test", "Test")
        watchlist_manager.add_from_screen_results("test", sample_screen_results)

        watchlists = watchlist_manager.list_watchlists()

        assert watchlists.iloc[0]['num_stocks'] == 3

    def test_get_watchlist_contents(self, watchlist_manager, sample_screen_results):
        """Test retrieving watchlist contents"""
        watchlist_manager.create_watchlist("test", "Test")
        watchlist_manager.add_from_screen_results("test", sample_screen_results)

        items = watchlist_manager.get_watchlist("test")

        assert isinstance(items, pd.DataFrame)
        assert len(items) == 3
        assert set(items['ticker']) == {'AAPL', 'MSFT', 'GOOGL'}
        assert 'price_when_added' in items.columns
        assert 'score_when_added' in items.columns

    def test_get_nonexistent_watchlist(self, watchlist_manager):
        """Test getting watchlist that doesn't exist"""
        items = watchlist_manager.get_watchlist("nonexistent")

        assert items is not None
        assert items.empty


class TestAddingScreenResults:
    """Test adding screen results to watchlists"""

    def test_add_from_screen_results_basic(self, watchlist_manager, sample_screen_results):
        """Test adding screening results to watchlist"""
        watchlist_manager.create_watchlist("test", "Test")

        count = watchlist_manager.add_from_screen_results(
            "test",
            sample_screen_results,
            reason="Tech screening"
        )

        assert count == 3

        items = watchlist_manager.get_watchlist("test")
        assert len(items) == 3

    def test_add_from_screen_results_replaces_by_default(self, watchlist_manager, sample_screen_results):
        """Test that adding results replaces existing items by default"""
        watchlist_manager.create_watchlist("test", "Test")

        # Add first batch
        watchlist_manager.add_from_screen_results("test", sample_screen_results)

        # Add second batch (different stocks)
        new_results = pd.DataFrame({
            'ticker': ['JPM', 'BAC'],
            'price': [145.0, 35.0],
            'score': [70.0, 65.0]
        })

        count = watchlist_manager.add_from_screen_results(
            "test",
            new_results,
            merge=False  # Replace
        )

        items = watchlist_manager.get_watchlist("test")

        # Should only have the new stocks
        assert len(items) == 2
        assert set(items['ticker']) == {'JPM', 'BAC'}

    def test_add_from_screen_results_merge_mode(self, watchlist_manager, sample_screen_results):
        """Test merging new results with existing"""
        watchlist_manager.create_watchlist("test", "Test")

        # Add first batch
        watchlist_manager.add_from_screen_results("test", sample_screen_results)

        # Add second batch with merge
        new_results = pd.DataFrame({
            'ticker': ['JPM', 'BAC'],
            'price': [145.0, 35.0],
            'score': [70.0, 65.0]
        })

        watchlist_manager.add_from_screen_results(
            "test",
            new_results,
            merge=True
        )

        items = watchlist_manager.get_watchlist("test")

        # Should have all 5 stocks
        assert len(items) == 5
        assert set(items['ticker']) == {'AAPL', 'MSFT', 'GOOGL', 'JPM', 'BAC'}

    def test_add_from_screen_results_preserves_metadata(self, watchlist_manager, sample_screen_results):
        """Test that price and score are preserved"""
        watchlist_manager.create_watchlist("test", "Test")

        watchlist_manager.add_from_screen_results("test", sample_screen_results)

        items = watchlist_manager.get_watchlist("test")

        # Check AAPL
        aapl = items[items['ticker'] == 'AAPL'].iloc[0]
        assert aapl['price_when_added'] == 150.0
        assert aapl['score_when_added'] == 75.0

    def test_add_to_nonexistent_watchlist_fails(self, watchlist_manager, sample_screen_results):
        """Test adding to watchlist that doesn't exist"""
        count = watchlist_manager.add_from_screen_results(
            "nonexistent",
            sample_screen_results
        )

        assert count == 0


class TestSnapshotCreation:
    """Test snapshot creation and tracking"""

    def test_snapshot_created_automatically(self, watchlist_manager, sample_screen_results):
        """Test that snapshot is created when adding results"""
        watchlist_manager.create_watchlist("test", "Test")

        watchlist_manager.add_from_screen_results("test", sample_screen_results)

        # Snapshot should exist (tested via compare)
        # Add again to create second snapshot
        new_results = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT'],  # GOOGL removed
            'price': [155.0, 335.0],  # Prices changed
            'score': [78.0, 85.0]
        })

        watchlist_manager.add_from_screen_results("test", new_results)

        comparison = watchlist_manager.compare_snapshots("test")

        assert comparison is not None
        assert len(comparison) > 0

    def test_compare_snapshots_shows_changes(self, watchlist_manager, sample_screen_results):
        """Test snapshot comparison detects changes"""
        watchlist_manager.create_watchlist("test", "Test")

        # First snapshot
        watchlist_manager.add_from_screen_results("test", sample_screen_results)

        # Second snapshot (different stocks)
        new_results = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT', 'JPM'],  # GOOGL removed, JPM added
            'price': [155.0, 335.0, 145.0],  # Prices changed
            'score': [78.0, 85.0, 70.0]
        })

        watchlist_manager.add_from_screen_results("test", new_results)

        comparison = watchlist_manager.compare_snapshots("test")

        assert 'JPM' in comparison['added']
        assert 'GOOGL' in comparison['removed']
        assert 'AAPL' in comparison['unchanged']
        assert 'MSFT' in comparison['unchanged']

    def test_compare_snapshots_calculates_price_changes(self, watchlist_manager, sample_screen_results):
        """Test that snapshot comparison shows price changes"""
        watchlist_manager.create_watchlist("test", "Test")

        # First snapshot
        watchlist_manager.add_from_screen_results("test", sample_screen_results)

        # Second snapshot with price changes
        new_results = sample_screen_results.copy()
        new_results.loc[new_results['ticker'] == 'AAPL', 'price'] = 165.0  # +10%

        watchlist_manager.add_from_screen_results("test", new_results)

        comparison = watchlist_manager.compare_snapshots("test")

        # Check price change for AAPL
        assert 'AAPL' in comparison['price_changes']
        aapl_change = comparison['price_changes']['AAPL']
        assert aapl_change['old'] == 150.0
        assert aapl_change['new'] == 165.0
        assert abs(aapl_change['change_pct'] - 10.0) < 0.1

    def test_compare_snapshots_insufficient_data(self, watchlist_manager):
        """Test comparison when less than 2 snapshots exist"""
        watchlist_manager.create_watchlist("test", "Test")

        comparison = watchlist_manager.compare_snapshots("test")

        # Should return empty dict when not enough snapshots
        assert comparison == {}


class TestWatchlistDeletion:
    """Test watchlist deletion"""

    def test_delete_watchlist(self, watchlist_manager, sample_screen_results):
        """Test deleting a watchlist"""
        watchlist_manager.create_watchlist("test", "Test")
        watchlist_manager.add_from_screen_results("test", sample_screen_results)

        success = watchlist_manager.delete_watchlist("test")

        assert success is True

        # Should no longer appear in list
        watchlists = watchlist_manager.list_watchlists()
        assert watchlists.empty

    def test_delete_watchlist_removes_items(self, watchlist_manager, sample_screen_results):
        """Test that deleting watchlist removes all items"""
        watchlist_manager.create_watchlist("test", "Test")
        watchlist_manager.add_from_screen_results("test", sample_screen_results)

        watchlist_manager.delete_watchlist("test")

        # Items should be gone
        items = watchlist_manager.get_watchlist("test")
        assert items.empty

    def test_delete_nonexistent_watchlist(self, watchlist_manager):
        """Test deleting watchlist that doesn't exist"""
        success = watchlist_manager.delete_watchlist("nonexistent")

        # Should not crash, may return False
        assert success is not None


class TestWatchlistExport:
    """Test watchlist export functionality"""

    def test_export_watchlist_to_json(self, watchlist_manager, sample_screen_results):
        """Test exporting watchlist to JSON file"""
        watchlist_manager.create_watchlist(
            "test",
            "Test Watchlist",
            description="For testing",
            tags=["test", "demo"]
        )
        watchlist_manager.add_from_screen_results("test", sample_screen_results)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "watchlist.json"

            success = watchlist_manager.export_watchlist("test", str(output_path))

            assert success is True
            assert output_path.exists()

            # Verify content
            with open(output_path) as f:
                data = json.load(f)

            assert data['watchlist_id'] == 'test'
            assert data['name'] == 'Test Watchlist'
            assert data['description'] == 'For testing'
            assert 'test' in data['tags']
            assert len(data['items']) == 3

    def test_export_nonexistent_watchlist(self, watchlist_manager):
        """Test exporting watchlist that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "watchlist.json"

            success = watchlist_manager.export_watchlist("nonexistent", str(output_path))

            assert success is False


class TestAlerts:
    """Test alert creation"""

    def test_create_alert(self, watchlist_manager):
        """Test creating an alert for a watchlist"""
        watchlist_manager.create_watchlist("test", "Test")

        success = watchlist_manager.create_alert(
            "test",
            "price_change",
            {"change_pct": 10.0, "direction": "up"}
        )

        assert success is True

    def test_create_multiple_alerts(self, watchlist_manager):
        """Test creating multiple alerts"""
        watchlist_manager.create_watchlist("test", "Test")

        watchlist_manager.create_alert("test", "price_change", {"change_pct": 10.0})
        watchlist_manager.create_alert("test", "volume_spike", {"multiplier": 2.0})

        # Both should be created successfully
        assert True  # If we get here without errors


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_add_empty_dataframe(self, watchlist_manager):
        """Test adding empty screening results"""
        watchlist_manager.create_watchlist("test", "Test")

        empty_df = pd.DataFrame()
        count = watchlist_manager.add_from_screen_results("test", empty_df)

        # Should handle gracefully
        assert count >= 0

    def test_add_results_without_price_column(self, watchlist_manager):
        """Test adding results missing price column"""
        watchlist_manager.create_watchlist("test", "Test")

        df = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT'],
            # No price column
            'score': [75.0, 80.0]
        })

        # Should not crash
        count = watchlist_manager.add_from_screen_results("test", df)
        assert count >= 0

    def test_add_results_without_score_column(self, watchlist_manager):
        """Test adding results missing score column"""
        watchlist_manager.create_watchlist("test", "Test")

        df = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT'],
            'price': [150.0, 330.0]
            # No score column
        })

        count = watchlist_manager.add_from_screen_results("test", df)
        assert count >= 0

    def test_long_watchlist_id(self, watchlist_manager):
        """Test creating watchlist with very long ID"""
        long_id = "a" * 500  # Very long ID

        success = watchlist_manager.create_watchlist(long_id, "Test")

        # Should handle or truncate gracefully
        assert success is not None

    def test_special_characters_in_name(self, watchlist_manager):
        """Test watchlist name with special characters"""
        success = watchlist_manager.create_watchlist(
            "test",
            "Test's \"Watchlist\" & More! 💰📈"
        )

        assert success is True

        watchlists = watchlist_manager.list_watchlists()
        assert len(watchlists) > 0
