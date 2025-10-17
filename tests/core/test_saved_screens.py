"""
Unit tests for SavedScreenManager module

Tests saving, loading, listing, and managing screening criteria templates.
"""

import pytest
import pandas as pd
import tempfile
import json
from datetime import datetime
from pathlib import Path

from quantlab.core.saved_screens import SavedScreenManager
from quantlab.core.screener import ScreenCriteria
from quantlab.data.database import DatabaseManager


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        db = DatabaseManager(str(db_path))
        yield db


@pytest.fixture
def saved_mgr(temp_db):
    """Create SavedScreenManager with temp database"""
    return SavedScreenManager(temp_db)


@pytest.fixture
def sample_criteria():
    """Create sample screening criteria"""
    return ScreenCriteria(
        rsi_max=30,
        volume_min=1000000,
        pe_max=20,
        revenue_growth_min=10,
        sectors=['Technology', 'Healthcare']
    )


class TestScreenSaving:
    """Test saving screening criteria"""

    def test_save_screen_basic(self, saved_mgr, sample_criteria):
        """Test saving a basic screen"""
        success = saved_mgr.save_screen(
            screen_id="test_screen",
            name="Test Screen",
            criteria=sample_criteria
        )

        assert success is True

    def test_save_screen_with_metadata(self, saved_mgr, sample_criteria):
        """Test saving screen with description and tags"""
        success = saved_mgr.save_screen(
            screen_id="oversold_tech",
            name="Oversold Tech Stocks",
            criteria=sample_criteria,
            description="RSI < 30 in Technology sector",
            tags=["oversold", "technical", "technology"]
        )

        assert success is True

        # Verify metadata saved
        info = saved_mgr.get_screen_info("oversold_tech")
        assert info is not None
        assert info['description'] == "RSI < 30 in Technology sector"
        assert 'oversold' in info['tags']

    def test_save_screen_updates_existing(self, saved_mgr, sample_criteria):
        """Test that saving with same ID updates existing screen"""
        # Save first version
        saved_mgr.save_screen("test", "Original Name", sample_criteria)

        # Update with new name
        success = saved_mgr.save_screen(
            "test",
            "Updated Name",
            sample_criteria,
            description="New description"
        )

        assert success is True

        # Verify updated
        info = saved_mgr.get_screen_info("test")
        assert info['name'] == "Updated Name"
        assert info['description'] == "New description"

    def test_save_all_criteria_attributes(self, saved_mgr):
        """Test that all ScreenCriteria attributes are saved"""
        comprehensive_criteria = ScreenCriteria(
            rsi_min=20,
            rsi_max=80,
            macd_signal='bullish',
            pe_max=15,
            forward_pe_max=12,
            revenue_growth_min=10,
            profit_margin_min=15,
            debt_equity_max=1.5,
            sentiment_min=0.5,
            sectors=['Technology'],
            exclude_industries=['Software']
        )

        saved_mgr.save_screen("comprehensive", "Comprehensive", comprehensive_criteria)

        # Load and verify all fields
        loaded = saved_mgr.load_screen("comprehensive")
        assert loaded is not None
        assert loaded.rsi_min == 20
        assert loaded.macd_signal == 'bullish'
        assert loaded.profit_margin_min == 15
        assert loaded.sectors == ['Technology']


class TestScreenLoading:
    """Test loading saved screens"""

    def test_load_screen_basic(self, saved_mgr, sample_criteria):
        """Test loading a saved screen"""
        saved_mgr.save_screen("test", "Test", sample_criteria)

        loaded = saved_mgr.load_screen("test")

        assert loaded is not None
        assert isinstance(loaded, ScreenCriteria)
        assert loaded.rsi_max == 30
        assert loaded.volume_min == 1000000

    def test_load_nonexistent_screen(self, saved_mgr):
        """Test loading screen that doesn't exist"""
        loaded = saved_mgr.load_screen("nonexistent")

        assert loaded is None

    def test_load_screen_preserves_all_fields(self, saved_mgr):
        """Test that loading preserves all criteria fields"""
        original = ScreenCriteria(
            rsi_max=30,
            pe_max=20,
            revenue_growth_min=15,
            sectors=['Technology', 'Healthcare'],
            volume_min=500000
        )

        saved_mgr.save_screen("preserve", "Preserve Test", original)
        loaded = saved_mgr.load_screen("preserve")

        assert loaded.rsi_max == original.rsi_max
        assert loaded.pe_max == original.pe_max
        assert loaded.revenue_growth_min == original.revenue_growth_min
        assert loaded.sectors == original.sectors
        assert loaded.volume_min == original.volume_min


class TestScreenListing:
    """Test listing saved screens"""

    def test_list_screens_empty(self, saved_mgr):
        """Test listing when no screens exist"""
        screens = saved_mgr.list_screens()

        assert isinstance(screens, pd.DataFrame)
        assert screens.empty

    def test_list_screens_multiple(self, saved_mgr, sample_criteria):
        """Test listing multiple saved screens"""
        saved_mgr.save_screen("screen1", "First Screen", sample_criteria)
        saved_mgr.save_screen("screen2", "Second Screen", sample_criteria)
        saved_mgr.save_screen("screen3", "Third Screen", sample_criteria)

        screens = saved_mgr.list_screens()

        assert len(screens) == 3
        assert set(screens['id']) == {'screen1', 'screen2', 'screen3'}

    def test_list_screens_includes_metadata(self, saved_mgr, sample_criteria):
        """Test that listing includes all metadata columns"""
        saved_mgr.save_screen("test", "Test Screen", sample_criteria, tags=["test"])

        screens = saved_mgr.list_screens()

        assert 'id' in screens.columns
        assert 'name' in screens.columns
        assert 'tags' in screens.columns
        assert 'created_date' in screens.columns
        assert 'run_count' in screens.columns

    def test_list_screens_sorted_by_modified(self, saved_mgr, sample_criteria):
        """Test that screens are sorted by last modified"""
        saved_mgr.save_screen("first", "First", sample_criteria)
        saved_mgr.save_screen("second", "Second", sample_criteria)
        saved_mgr.save_screen("third", "Third", sample_criteria)

        screens = saved_mgr.list_screens()

        # Most recently modified should be first
        assert screens.iloc[0]['id'] == 'third'


class TestScreenInfo:
    """Test getting detailed screen information"""

    def test_get_screen_info_basic(self, saved_mgr, sample_criteria):
        """Test getting basic screen info"""
        saved_mgr.save_screen("test", "Test Screen", sample_criteria)

        info = saved_mgr.get_screen_info("test")

        assert info is not None
        assert info['id'] == 'test'
        assert info['name'] == 'Test Screen'
        assert 'criteria' in info
        assert 'created_date' in info

    def test_get_screen_info_includes_criteria(self, saved_mgr, sample_criteria):
        """Test that info includes full criteria"""
        saved_mgr.save_screen("test", "Test", sample_criteria)

        info = saved_mgr.get_screen_info("test")

        criteria = info['criteria']
        assert criteria['rsi_max'] == 30
        assert criteria['volume_min'] == 1000000

    def test_get_screen_info_nonexistent(self, saved_mgr):
        """Test getting info for nonexistent screen"""
        info = saved_mgr.get_screen_info("nonexistent")

        assert info is None


class TestScreenDeletion:
    """Test deleting saved screens"""

    def test_delete_screen(self, saved_mgr, sample_criteria):
        """Test deleting a saved screen"""
        saved_mgr.save_screen("test", "Test", sample_criteria)

        success = saved_mgr.delete_screen("test")

        assert success is True

        # Should no longer exist
        screens = saved_mgr.list_screens()
        assert screens.empty

    def test_delete_screen_removes_from_list(self, saved_mgr, sample_criteria):
        """Test that deleted screen is removed from listing"""
        saved_mgr.save_screen("keep", "Keep", sample_criteria)
        saved_mgr.save_screen("delete", "Delete", sample_criteria)

        saved_mgr.delete_screen("delete")

        screens = saved_mgr.list_screens()
        assert len(screens) == 1
        assert screens.iloc[0]['id'] == 'keep'

    def test_delete_nonexistent_screen(self, saved_mgr):
        """Test deleting screen that doesn't exist"""
        success = saved_mgr.delete_screen("nonexistent")

        # Should not crash
        assert success is not None


class TestRunStatistics:
    """Test run statistics tracking"""

    def test_update_run_stats_increments_count(self, saved_mgr, sample_criteria):
        """Test that run stats are updated"""
        saved_mgr.save_screen("test", "Test", sample_criteria)

        # Update run stats multiple times
        saved_mgr.update_run_stats("test")
        saved_mgr.update_run_stats("test")
        saved_mgr.update_run_stats("test")

        info = saved_mgr.get_screen_info("test")
        assert info['run_count'] == 3

    def test_update_run_stats_updates_last_run(self, saved_mgr, sample_criteria):
        """Test that last_run timestamp is updated"""
        saved_mgr.save_screen("test", "Test", sample_criteria)

        info_before = saved_mgr.get_screen_info("test")
        assert info_before['last_run'] is None

        saved_mgr.update_run_stats("test")

        info_after = saved_mgr.get_screen_info("test")
        assert info_after['last_run'] is not None


class TestExportImport:
    """Test export and import functionality"""

    def test_export_screen_to_json(self, saved_mgr, sample_criteria):
        """Test exporting screen to JSON file"""
        saved_mgr.save_screen(
            "test",
            "Test Screen",
            sample_criteria,
            description="For testing",
            tags=["test", "demo"]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "screen.json"

            success = saved_mgr.export_screen("test", str(output_path))

            assert success is True
            assert output_path.exists()

            # Verify content
            with open(output_path) as f:
                data = json.load(f)

            assert data['id'] == 'test'
            assert data['name'] == 'Test Screen'
            assert data['description'] == 'For testing'
            assert 'test' in data['tags']
            assert 'criteria' in data

    def test_export_nonexistent_screen(self, saved_mgr):
        """Test exporting screen that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "screen.json"

            success = saved_mgr.export_screen("nonexistent", str(output_path))

            assert success is False

    def test_import_screen_from_json(self, saved_mgr, sample_criteria):
        """Test importing screen from JSON file"""
        # First export
        saved_mgr.save_screen("original", "Original", sample_criteria)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "screen.json"
            saved_mgr.export_screen("original", str(export_path))

            # Create new manager (simulating fresh state)
            new_mgr = SavedScreenManager(saved_mgr.db)

            # Import
            success = new_mgr.import_screen(str(export_path))

            assert success is True

            # Verify imported
            loaded = new_mgr.load_screen("original")
            assert loaded is not None
            assert loaded.rsi_max == sample_criteria.rsi_max

    def test_import_screen_with_new_id(self, saved_mgr, sample_criteria):
        """Test importing screen with different ID"""
        saved_mgr.save_screen("original", "Original", sample_criteria)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "screen.json"
            saved_mgr.export_screen("original", str(export_path))

            # Import with new ID
            success = saved_mgr.import_screen(str(export_path), screen_id="imported")

            assert success is True

            # Should exist under new ID
            loaded = saved_mgr.load_screen("imported")
            assert loaded is not None


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_save_empty_criteria(self, saved_mgr):
        """Test saving screen with all-None criteria"""
        empty_criteria = ScreenCriteria()

        success = saved_mgr.save_screen("empty", "Empty", empty_criteria)

        assert success is True

        # Should be able to load
        loaded = saved_mgr.load_screen("empty")
        assert loaded is not None

    def test_save_screen_with_long_name(self, saved_mgr, sample_criteria):
        """Test saving screen with very long name"""
        long_name = "A" * 500

        success = saved_mgr.save_screen("test", long_name, sample_criteria)

        assert success is True

    def test_save_screen_with_special_characters(self, saved_mgr, sample_criteria):
        """Test screen name with special characters"""
        success = saved_mgr.save_screen(
            "test",
            "Test's \"Screen\" & More! 💰📈",
            sample_criteria
        )

        assert success is True

        info = saved_mgr.get_screen_info("test")
        assert "Test's" in info['name']

    def test_save_screen_with_empty_tags(self, saved_mgr, sample_criteria):
        """Test saving screen with empty tags list"""
        success = saved_mgr.save_screen("test", "Test", sample_criteria, tags=[])

        assert success is True

        info = saved_mgr.get_screen_info("test")
        assert info['tags'] == []

    def test_save_screen_with_list_criteria_values(self, saved_mgr):
        """Test that list-type criteria fields are preserved"""
        criteria = ScreenCriteria(
            sectors=['Technology', 'Healthcare', 'Finance'],
            exclude_industries=['Software', 'Biotech']
        )

        saved_mgr.save_screen("lists", "Lists Test", criteria)
        loaded = saved_mgr.load_screen("lists")

        assert loaded.sectors == ['Technology', 'Healthcare', 'Finance']
        assert loaded.exclude_industries == ['Software', 'Biotech']


class TestConcurrency:
    """Test concurrent access scenarios"""

    def test_multiple_saves_sequential(self, saved_mgr, sample_criteria):
        """Test multiple sequential saves don't corrupt data"""
        for i in range(10):
            success = saved_mgr.save_screen(f"screen_{i}", f"Screen {i}", sample_criteria)
            assert success is True

        screens = saved_mgr.list_screens()
        assert len(screens) == 10

    def test_save_load_interleaved(self, saved_mgr, sample_criteria):
        """Test interleaved save and load operations"""
        saved_mgr.save_screen("s1", "Screen 1", sample_criteria)
        l1 = saved_mgr.load_screen("s1")
        saved_mgr.save_screen("s2", "Screen 2", sample_criteria)
        l2 = saved_mgr.load_screen("s2")
        saved_mgr.save_screen("s3", "Screen 3", sample_criteria)

        assert l1 is not None
        assert l2 is not None
        assert len(saved_mgr.list_screens()) == 3
