"""
Unit tests for Screen Visualizer module

Tests all visualizer classes and chart generation methods.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, date, timedelta
import pandas as pd

from quantlab.core.screen_visualizer import (
    ScreenBacktestVisualizer,
    ScreenComparisonVisualizer,
    ScreenResultsVisualizer,
    ScreenAlertsVisualizer,
    visualize_backtest_from_file,
    visualize_comparison_from_file,
    visualize_results_from_file,
    visualize_alerts_from_file,
)


# ============================================================================
# Fixtures - Sample Data
# ============================================================================

@pytest.fixture
def sample_backtest_data():
    """Sample backtest data matching screen backtest output"""
    return {
        "criteria": {
            "rsi_max": 30,
            "volume_min": 1000000,
            "description": "Oversold Strategy"
        },
        "results": {
            "start_date": "2025-01-01",
            "end_date": "2025-10-01",
            "total_return": 15.5,
            "annualized_return": 18.2,
            "sharpe_ratio": 1.45,
            "max_drawdown": -8.3,
            "win_rate": 62.5,
            "alpha": 5.2,
            "benchmark_return": 10.3
        },
        "period_results": [
            {"date": "2025-01-07", "avg_return": 2.5, "benchmark_return": 1.2, "stock_count": 15},
            {"date": "2025-01-14", "avg_return": -1.3, "benchmark_return": 0.5, "stock_count": 12},
            {"date": "2025-01-21", "avg_return": 3.2, "benchmark_return": 1.8, "stock_count": 14},
            {"date": "2025-01-28", "avg_return": 1.8, "benchmark_return": 0.9, "stock_count": 13},
            {"date": "2025-02-04", "avg_return": 2.1, "benchmark_return": 1.1, "stock_count": 16},
        ] * 10  # 50 periods
    }


@pytest.fixture
def sample_comparison_data():
    """Sample comparison data matching screen compare-multi output"""
    return {
        "screen_names": ["Oversold", "Momentum", "Value"],
        "individual_results": {
            "Oversold": {
                "results": [
                    {"ticker": "AAPL", "price": 180.0, "sector": "Technology", "rsi": 28.5},
                    {"ticker": "MSFT", "price": 410.0, "sector": "Technology", "rsi": 29.2},
                    {"ticker": "JPM", "price": 145.0, "sector": "Financial", "rsi": 27.8},
                ]
            },
            "Momentum": {
                "results": [
                    {"ticker": "AAPL", "price": 180.0, "sector": "Technology", "macd": 1.5},
                    {"ticker": "NVDA", "price": 485.0, "sector": "Technology", "macd": 2.3},
                ]
            },
            "Value": {
                "results": [
                    {"ticker": "JPM", "price": 145.0, "sector": "Financial", "pe_ratio": 12.5},
                    {"ticker": "BAC", "price": 32.0, "sector": "Financial", "pe_ratio": 11.2},
                ]
            }
        },
        "overlap_analysis": [
            {"screens": "Oversold", "ticker_count": 3},
            {"screens": "Momentum", "ticker_count": 2},
            {"screens": "Value", "ticker_count": 2},
            {"screens": "Oversold+Value", "ticker_count": 1},
        ],
        "consensus_picks": [
            {"ticker": "AAPL", "screen_count": 2, "consensus_score": 85.0},
            {"ticker": "JPM", "screen_count": 2, "consensus_score": 78.0},
        ],
        "comparison_metrics": [
            {"screen_name": "Oversold", "result_count": 3, "avg_price": 245.0},
            {"screen_name": "Momentum", "result_count": 2, "avg_price": 332.5},
            {"screen_name": "Value", "result_count": 2, "avg_price": 88.5},
        ]
    }


@pytest.fixture
def sample_screening_results():
    """Sample screening results matching screen run output"""
    return {
        "screen_name": "Oversold Screen",
        "num_results": 10,
        "criteria": {"rsi_max": 30, "volume_min": 1000000},
        "results": [
            {
                "ticker": "AAPL", "price": 180.0, "volume": 52000000,
                "rsi": 28.5, "pe_ratio": 28.5, "market_cap": 2800.0,
                "sector": "Technology", "industry": "Consumer Electronics"
            },
            {
                "ticker": "MSFT", "price": 410.0, "volume": 24000000,
                "rsi": 29.2, "pe_ratio": 35.2, "market_cap": 3100.0,
                "sector": "Technology", "industry": "Software"
            },
            {
                "ticker": "JPM", "price": 145.0, "volume": 12000000,
                "rsi": 27.8, "pe_ratio": 12.5, "market_cap": 420.0,
                "sector": "Financial", "industry": "Banks"
            },
            {
                "ticker": "BAC", "price": 32.0, "volume": 45000000,
                "rsi": 26.5, "pe_ratio": 11.2, "market_cap": 250.0,
                "sector": "Financial", "industry": "Banks"
            },
            {
                "ticker": "XOM", "price": 105.0, "volume": 18000000,
                "rsi": 29.5, "pe_ratio": 9.8, "market_cap": 425.0,
                "sector": "Energy", "industry": "Oil & Gas"
            },
        ] * 2  # 10 stocks
    }


@pytest.fixture
def sample_alerts_data():
    """Sample watch alerts data"""
    base_time = datetime(2025, 10, 15, 10, 0, 0)
    return {
        "total_alerts": 15,
        "alerts": [
            {
                "ticker": "AAPL",
                "alert_type": "entry",
                "alert_time": (base_time + timedelta(hours=i)).isoformat(),
                "screen_name": "Oversold",
                "details": {"rsi": 28.5}
            }
            for i in range(5)
        ] + [
            {
                "ticker": "MSFT",
                "alert_type": "exit",
                "alert_time": (base_time + timedelta(hours=i+5)).isoformat(),
                "screen_name": "Momentum",
                "details": {"rsi": 72.3}
            }
            for i in range(5)
        ] + [
            {
                "ticker": "JPM",
                "alert_type": "price_change",
                "alert_time": (base_time + timedelta(hours=i+10)).isoformat(),
                "screen_name": "Value",
                "details": {"price_change": 6.5}
            }
            for i in range(5)
        ]
    }


# ============================================================================
# ScreenBacktestVisualizer Tests
# ============================================================================

class TestScreenBacktestVisualizer:
    """Test ScreenBacktestVisualizer class"""

    def test_initialization(self, sample_backtest_data):
        """Test visualizer initialization"""
        viz = ScreenBacktestVisualizer(sample_backtest_data)

        assert viz.data == sample_backtest_data
        assert viz.results == sample_backtest_data['results']
        assert isinstance(viz.period_results, pd.DataFrame)
        assert len(viz.period_results) == 50

    def test_create_cumulative_returns_chart(self, sample_backtest_data):
        """Test cumulative returns chart generation"""
        viz = ScreenBacktestVisualizer(sample_backtest_data)
        fig = viz.create_cumulative_returns_chart()

        assert fig is not None
        assert len(fig.data) == 2  # Strategy + Benchmark
        assert fig.data[0].name == 'Strategy'
        assert fig.data[1].name == 'Benchmark (SPY)'

    def test_create_drawdown_chart(self, sample_backtest_data):
        """Test drawdown chart generation"""
        viz = ScreenBacktestVisualizer(sample_backtest_data)
        fig = viz.create_drawdown_chart()

        assert fig is not None
        assert len(fig.data) == 1  # Drawdown line
        assert 'Drawdown' in fig.data[0].name

    def test_create_rolling_sharpe_chart(self, sample_backtest_data):
        """Test rolling Sharpe ratio chart"""
        viz = ScreenBacktestVisualizer(sample_backtest_data)
        fig = viz.create_rolling_sharpe_chart()

        assert fig is not None
        # Should have at least one trace
        assert len(fig.data) >= 1

    def test_create_metrics_dashboard(self, sample_backtest_data):
        """Test metrics dashboard table"""
        viz = ScreenBacktestVisualizer(sample_backtest_data)
        fig = viz.create_metrics_dashboard()

        assert fig is not None
        assert len(fig.data) == 1  # Table
        assert fig.data[0].type == 'table'

    def test_create_returns_distribution(self, sample_backtest_data):
        """Test returns distribution histogram"""
        viz = ScreenBacktestVisualizer(sample_backtest_data)
        fig = viz.create_returns_distribution()

        assert fig is not None
        assert len(fig.data) == 1  # Histogram
        assert fig.data[0].type == 'histogram'

    def test_create_win_rate_chart(self, sample_backtest_data):
        """Test win rate bar chart"""
        viz = ScreenBacktestVisualizer(sample_backtest_data)
        fig = viz.create_win_rate_chart()

        assert fig is not None
        assert len(fig.data) == 1  # Bar chart
        assert fig.data[0].type == 'bar'

    def test_empty_data_handling(self):
        """Test handling of empty backtest data"""
        empty_data = {
            "results": {},
            "period_results": []
        }
        viz = ScreenBacktestVisualizer(empty_data)

        # Should not crash, should return empty figure
        fig = viz.create_cumulative_returns_chart()
        assert fig is not None

    def test_create_html_report(self, sample_backtest_data):
        """Test HTML report generation"""
        viz = ScreenBacktestVisualizer(sample_backtest_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.html"
            viz.create_html_report(str(output_path))

            assert output_path.exists()
            assert output_path.stat().st_size > 1000  # Should have content

            # Check HTML contains expected elements
            content = output_path.read_text()
            assert '<html>' in content
            assert 'Screen Backtest Report' in content
            assert 'plotly' in content.lower()


# ============================================================================
# ScreenComparisonVisualizer Tests
# ============================================================================

class TestScreenComparisonVisualizer:
    """Test ScreenComparisonVisualizer class"""

    def test_initialization(self, sample_comparison_data):
        """Test visualizer initialization"""
        viz = ScreenComparisonVisualizer(sample_comparison_data)

        assert viz.data == sample_comparison_data
        assert len(viz.screen_names) == 3
        assert isinstance(viz.overlap_analysis, pd.DataFrame)
        assert isinstance(viz.consensus_picks, pd.DataFrame)

    def test_create_overlap_venn(self, sample_comparison_data):
        """Test overlap visualization"""
        viz = ScreenComparisonVisualizer(sample_comparison_data)
        fig = viz.create_overlap_venn()

        assert fig is not None
        # Currently implemented as bar chart
        assert len(fig.data) >= 1

    def test_create_consensus_picks_table(self, sample_comparison_data):
        """Test consensus picks table"""
        viz = ScreenComparisonVisualizer(sample_comparison_data)
        fig = viz.create_consensus_picks_table()

        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == 'table'

    def test_create_sector_comparison(self, sample_comparison_data):
        """Test sector distribution comparison"""
        viz = ScreenComparisonVisualizer(sample_comparison_data)
        fig = viz.create_sector_comparison()

        assert fig is not None
        # Should have one trace per screen
        assert len(fig.data) >= 1

    def test_create_screen_size_comparison(self, sample_comparison_data):
        """Test screen size bar chart"""
        viz = ScreenComparisonVisualizer(sample_comparison_data)
        fig = viz.create_screen_size_comparison()

        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == 'bar'

    def test_empty_consensus_picks(self):
        """Test handling when no consensus picks exist"""
        data = {
            "screen_names": ["Screen1", "Screen2"],
            "individual_results": {},
            "overlap_analysis": [],
            "consensus_picks": [],
            "comparison_metrics": []
        }
        viz = ScreenComparisonVisualizer(data)
        fig = viz.create_consensus_picks_table()

        assert fig is not None  # Should handle gracefully

    def test_create_html_report(self, sample_comparison_data):
        """Test HTML report generation"""
        viz = ScreenComparisonVisualizer(sample_comparison_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "comparison_report.html"
            viz.create_html_report(str(output_path))

            assert output_path.exists()
            content = output_path.read_text()
            assert 'Screen Comparison Report' in content


# ============================================================================
# ScreenResultsVisualizer Tests
# ============================================================================

class TestScreenResultsVisualizer:
    """Test ScreenResultsVisualizer class"""

    def test_initialization(self, sample_screening_results):
        """Test visualizer initialization"""
        viz = ScreenResultsVisualizer(sample_screening_results)

        assert viz.data == sample_screening_results
        assert isinstance(viz.results, pd.DataFrame)
        assert len(viz.results) == 10

    def test_create_sector_pie_chart(self, sample_screening_results):
        """Test sector pie chart"""
        viz = ScreenResultsVisualizer(sample_screening_results)
        fig = viz.create_sector_pie_chart()

        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == 'pie'

    def test_create_industry_bar_chart(self, sample_screening_results):
        """Test industry bar chart"""
        viz = ScreenResultsVisualizer(sample_screening_results)
        fig = viz.create_industry_bar_chart()

        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == 'bar'

    def test_create_price_volume_scatter(self, sample_screening_results):
        """Test price vs volume scatter plot"""
        viz = ScreenResultsVisualizer(sample_screening_results)
        fig = viz.create_price_volume_scatter()

        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == 'scatter'

    def test_create_metric_histograms(self, sample_screening_results):
        """Test metric histograms"""
        viz = ScreenResultsVisualizer(sample_screening_results)
        fig = viz.create_metric_histograms()

        assert fig is not None
        # Should have multiple subplots
        assert len(fig.data) >= 1

    def test_empty_results(self):
        """Test handling of empty screening results"""
        empty_data = {
            "screen_name": "Empty Screen",
            "num_results": 0,
            "results": []
        }
        viz = ScreenResultsVisualizer(empty_data)
        fig = viz.create_sector_pie_chart()

        assert fig is not None  # Should handle gracefully

    def test_create_html_report(self, sample_screening_results):
        """Test HTML report generation"""
        viz = ScreenResultsVisualizer(sample_screening_results)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results_report.html"
            viz.create_html_report(str(output_path))

            assert output_path.exists()
            content = output_path.read_text()
            assert 'Screening Results Report' in content
            assert 'Total Stocks Found: 10' in content


# ============================================================================
# ScreenAlertsVisualizer Tests
# ============================================================================

class TestScreenAlertsVisualizer:
    """Test ScreenAlertsVisualizer class"""

    def test_initialization(self, sample_alerts_data):
        """Test visualizer initialization"""
        viz = ScreenAlertsVisualizer(sample_alerts_data)

        assert viz.data == sample_alerts_data
        assert isinstance(viz.alerts, pd.DataFrame)
        assert len(viz.alerts) == 15

    def test_create_alert_timeline(self, sample_alerts_data):
        """Test alert timeline chart"""
        viz = ScreenAlertsVisualizer(sample_alerts_data)
        fig = viz.create_alert_timeline()

        assert fig is not None
        # Should have one trace per alert type
        assert len(fig.data) >= 3

    def test_create_alert_type_breakdown(self, sample_alerts_data):
        """Test alert type pie chart"""
        viz = ScreenAlertsVisualizer(sample_alerts_data)
        fig = viz.create_alert_type_breakdown()

        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == 'pie'

    def test_create_ticker_frequency_heatmap(self, sample_alerts_data):
        """Test ticker frequency bar chart"""
        viz = ScreenAlertsVisualizer(sample_alerts_data)
        fig = viz.create_ticker_frequency_heatmap()

        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == 'bar'

    def test_create_daily_alert_count(self, sample_alerts_data):
        """Test daily alert count chart"""
        viz = ScreenAlertsVisualizer(sample_alerts_data)
        fig = viz.create_daily_alert_count()

        assert fig is not None
        assert len(fig.data) == 1

    def test_empty_alerts(self):
        """Test handling of empty alerts"""
        empty_data = {
            "total_alerts": 0,
            "alerts": []
        }
        viz = ScreenAlertsVisualizer(empty_data)
        fig = viz.create_alert_timeline()

        assert fig is not None  # Should handle gracefully

    def test_create_html_report(self, sample_alerts_data):
        """Test HTML report generation"""
        viz = ScreenAlertsVisualizer(sample_alerts_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "alerts_report.html"
            viz.create_html_report(str(output_path))

            assert output_path.exists()
            content = output_path.read_text()
            assert 'Watch Mode Alerts Report' in content
            assert 'Total Alerts: 15' in content


# ============================================================================
# Utility Function Tests
# ============================================================================

class TestUtilityFunctions:
    """Test utility functions for file-based visualization"""

    def test_visualize_backtest_from_file(self, sample_backtest_data):
        """Test backtest visualization from file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input JSON
            input_path = Path(tmpdir) / "backtest.json"
            with open(input_path, 'w') as f:
                json.dump(sample_backtest_data, f)

            # Generate visualization
            output_path = Path(tmpdir) / "backtest_report.html"
            visualize_backtest_from_file(str(input_path), str(output_path))

            assert output_path.exists()
            assert output_path.stat().st_size > 1000

    def test_visualize_comparison_from_file(self, sample_comparison_data):
        """Test comparison visualization from file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "comparison.json"
            with open(input_path, 'w') as f:
                json.dump(sample_comparison_data, f)

            output_path = Path(tmpdir) / "comparison_report.html"
            visualize_comparison_from_file(str(input_path), str(output_path))

            assert output_path.exists()

    def test_visualize_results_from_file(self, sample_screening_results):
        """Test screening results visualization from file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "results.json"
            with open(input_path, 'w') as f:
                json.dump(sample_screening_results, f)

            output_path = Path(tmpdir) / "results_report.html"
            visualize_results_from_file(str(input_path), str(output_path))

            assert output_path.exists()

    def test_visualize_alerts_from_file(self, sample_alerts_data):
        """Test alerts visualization from file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "alerts.json"
            with open(input_path, 'w') as f:
                json.dump(sample_alerts_data, f)

            output_path = Path(tmpdir) / "alerts_report.html"
            visualize_alerts_from_file(str(input_path), str(output_path))

            assert output_path.exists()


# ============================================================================
# Edge Cases and Error Handling Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        incomplete_data = {
            "results": {}
        }

        viz = ScreenBacktestVisualizer(incomplete_data)
        # Should not crash
        fig = viz.create_metrics_dashboard()
        assert fig is not None

    def test_malformed_dates(self):
        """Test handling of malformed date strings"""
        data = {
            "results": {},
            "period_results": [
                {"date": "invalid-date", "avg_return": 1.5}
            ]
        }

        viz = ScreenBacktestVisualizer(data)
        # Should handle gracefully
        fig = viz.create_cumulative_returns_chart()
        assert fig is not None

    def test_insufficient_data_for_rolling_sharpe(self):
        """Test Sharpe calculation with insufficient data"""
        data = {
            "results": {"sharpe_ratio": 1.5},
            "period_results": [
                {"date": "2025-01-01", "avg_return": 1.5}
            ] * 5  # Only 5 periods
        }

        viz = ScreenBacktestVisualizer(data)
        fig = viz.create_rolling_sharpe_chart()
        # Should return empty figure with message
        assert fig is not None

    def test_all_negative_returns(self):
        """Test with all negative returns"""
        data = {
            "results": {"win_rate": 0.0},
            "period_results": [
                {"date": f"2025-01-{i:02d}", "avg_return": -1.5}
                for i in range(1, 31)
            ]
        }

        viz = ScreenBacktestVisualizer(data)
        fig = viz.create_win_rate_chart()
        assert fig is not None

    def test_single_screen_comparison(self):
        """Test comparison with only one screen"""
        data = {
            "screen_names": ["Screen1"],
            "individual_results": {"Screen1": {"results": []}},
            "overlap_analysis": [],
            "consensus_picks": [],
            "comparison_metrics": [{"screen_name": "Screen1", "result_count": 0}]
        }

        viz = ScreenComparisonVisualizer(data)
        fig = viz.create_screen_size_comparison()
        assert fig is not None

    def test_large_dataset_performance(self, sample_screening_results):
        """Test performance with large dataset"""
        # Create large dataset (1000 stocks)
        large_results = sample_screening_results.copy()
        large_results['results'] = large_results['results'] * 100

        viz = ScreenResultsVisualizer(large_results)
        # Should complete in reasonable time
        import time
        start = time.time()
        fig = viz.create_sector_pie_chart()
        elapsed = time.time() - start

        assert fig is not None
        assert elapsed < 5.0  # Should be fast


# ============================================================================
# Integration Tests - Would typically be in separate file
# ============================================================================

class TestVisualizationIntegration:
    """Integration tests for end-to-end workflows"""

    def test_full_backtest_workflow(self, sample_backtest_data):
        """Test complete backtest visualization workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Save backtest data
            input_path = Path(tmpdir) / "backtest.json"
            with open(input_path, 'w') as f:
                json.dump(sample_backtest_data, f)

            # Step 2: Generate all charts
            viz = ScreenBacktestVisualizer(sample_backtest_data)
            charts = [
                viz.create_cumulative_returns_chart(),
                viz.create_drawdown_chart(),
                viz.create_rolling_sharpe_chart(),
                viz.create_metrics_dashboard(),
                viz.create_returns_distribution(),
                viz.create_win_rate_chart(),
            ]

            # All charts should be generated
            assert all(chart is not None for chart in charts)

            # Step 3: Generate HTML report
            output_path = Path(tmpdir) / "report.html"
            viz.create_html_report(str(output_path))

            assert output_path.exists()
            assert output_path.stat().st_size > 10000  # Should have substantial content

    def test_multiple_visualizations_same_session(self, sample_backtest_data, sample_comparison_data):
        """Test creating multiple visualizations in same session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create backtest visualization
            viz1 = ScreenBacktestVisualizer(sample_backtest_data)
            path1 = Path(tmpdir) / "backtest.html"
            viz1.create_html_report(str(path1))

            # Create comparison visualization
            viz2 = ScreenComparisonVisualizer(sample_comparison_data)
            path2 = Path(tmpdir) / "comparison.html"
            viz2.create_html_report(str(path2))

            # Both should exist and be independent
            assert path1.exists()
            assert path2.exists()
            assert path1.read_text() != path2.read_text()
