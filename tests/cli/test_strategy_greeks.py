"""
Integration tests for Options Strategy CLI with Advanced Greeks

Tests the CLI commands with --iv parameter and Greeks display.
"""

import pytest
import json
import tempfile
from pathlib import Path
from click.testing import CliRunner
from datetime import date, timedelta

from quantlab.cli.main import cli


class TestStrategyBuildWithIV:
    """Test strategy build command with --iv parameter"""

    @pytest.fixture
    def runner(self):
        """Create Click test runner"""
        return CliRunner()

    def test_bull_call_spread_with_iv(self, runner):
        """Test building bull call spread with IV"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'bull_call_spread',
            '--ticker', 'TEST',
            '--stock-price', '100',
            '--strikes', '95,105',
            '--premiums', '7.00,3.00',
            '--expiration', (date.today() + timedelta(days=30)).isoformat(),
            '--iv', '0.30'
        ])

        assert result.exit_code == 0
        assert '📊 Advanced Greeks Analysis:' in result.output
        assert 'Delta:' in result.output
        assert 'Vanna:' in result.output
        assert 'Charm:' in result.output
        assert 'Vomma:' in result.output
        assert 'First-Order Greeks:' in result.output
        assert 'Second-Order Greeks (Advanced):' in result.output

    def test_iron_condor_with_iv(self, runner):
        """Test building iron condor with IV"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'iron_condor',
            '--ticker', 'SPY',
            '--stock-price', '450',
            '--strikes', '440,445,455,460',
            '--premiums', '1.00,2.50,2.50,1.00',
            '--expiration', (date.today() + timedelta(days=30)).isoformat(),
            '--iv', '0.20'
        ])

        assert result.exit_code == 0
        assert 'Advanced Greeks Analysis' in result.output
        assert 'DELTA-NEUTRAL' in result.output or 'MODERATE DELTA' in result.output
        assert 'POSITIVE THETA' in result.output

    def test_covered_call_with_iv(self, runner):
        """Test building covered call with IV"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'covered_call',
            '--ticker', 'AAPL',
            '--stock-price', '175',
            '--strike', '180',
            '--premium', '3.50',
            '--shares', '100',
            '--expiration', (date.today() + timedelta(days=30)).isoformat(),
            '--iv', '0.30'
        ])

        assert result.exit_code == 0
        assert 'Advanced Greeks Analysis' in result.output
        # Covered call should have high delta (includes stock)
        assert 'Delta:' in result.output
        # Should show risk profile
        assert 'Risk Profile:' in result.output

    def test_build_without_iv(self, runner):
        """Test that building without IV works but doesn't show Greeks"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'bull_call_spread',
            '--ticker', 'TEST',
            '--stock-price', '100',
            '--strikes', '95,105',
            '--premiums', '7.00,3.00',
            '--expiration', (date.today() + timedelta(days=30)).isoformat()
            # No --iv parameter
        ])

        assert result.exit_code == 0
        # Should not display Greeks section
        assert 'Advanced Greeks Analysis' not in result.output
        # But should still show risk analysis
        assert 'Risk Analysis' in result.output

    def test_custom_risk_free_rate(self, runner):
        """Test using custom risk-free rate"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'bull_call_spread',
            '--ticker', 'TEST',
            '--stock-price', '100',
            '--strikes', '95,105',
            '--premiums', '7.00,3.00',
            '--expiration', (date.today() + timedelta(days=30)).isoformat(),
            '--iv', '0.30',
            '--risk-free-rate', '0.03'  # Custom rate
        ])

        assert result.exit_code == 0
        assert 'Advanced Greeks Analysis' in result.output


class TestStrategySaveWithGreeks:
    """Test saving strategies with Greeks to JSON"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_save_strategy_with_greeks(self, runner):
        """Test that saved strategy includes Greeks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'test_strategy.json'

            result = runner.invoke(cli, [
                'strategy', 'build', 'bull_call_spread',
                '--ticker', 'TEST',
                '--stock-price', '100',
                '--strikes', '95,105',
                '--premiums', '7.00,3.00',
                '--expiration', (date.today() + timedelta(days=30)).isoformat(),
                '--iv', '0.30',
                '--output', str(output_file)
            ])

            assert result.exit_code == 0
            assert output_file.exists()

            # Load and verify JSON
            with open(output_file) as f:
                data = json.load(f)

            # Should have advanced_greeks
            assert 'advanced_greeks' in data
            assert 'delta' in data['advanced_greeks']
            assert 'vanna' in data['advanced_greeks']
            assert 'charm' in data['advanced_greeks']
            assert 'vomma' in data['advanced_greeks']

            # Legs should have IV
            assert data['legs'][0]['implied_volatility'] == 0.30
            assert data['legs'][1]['implied_volatility'] == 0.30

    def test_save_strategy_without_iv(self, runner):
        """Test that saved strategy without IV doesn't have Greeks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'test_strategy.json'

            result = runner.invoke(cli, [
                'strategy', 'build', 'bull_call_spread',
                '--ticker', 'TEST',
                '--stock-price', '100',
                '--strikes', '95,105',
                '--premiums', '7.00,3.00',
                '--expiration', (date.today() + timedelta(days=30)).isoformat(),
                '--output', str(output_file)
                # No --iv
            ])

            assert result.exit_code == 0

            with open(output_file) as f:
                data = json.load(f)

            # Should not have advanced_greeks
            assert 'advanced_greeks' not in data

            # Legs should have None IV
            assert data['legs'][0]['implied_volatility'] is None


class TestGreeksDisplay:
    """Test Greeks display formatting"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_delta_exposure_displayed(self, runner):
        """Test that delta exposure in dollars is shown"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'bull_call_spread',
            '--ticker', 'NVDA',
            '--stock-price', '485',
            '--strikes', '480,490',
            '--premiums', '12.50,7.50',
            '--expiration', (date.today() + timedelta(days=30)).isoformat(),
            '--iv', '0.35'
        ])

        assert result.exit_code == 0
        # Should show delta with dollar exposure
        assert 'exposure' in result.output.lower()
        assert '$' in result.output

    def test_greeks_interpretation_shown(self, runner):
        """Test that Greeks interpretation is displayed"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'iron_condor',
            '--ticker', 'SPY',
            '--stock-price', '450',
            '--strikes', '440,445,455,460',
            '--premiums', '1.00,2.50,2.50,1.00',
            '--expiration', (date.today() + timedelta(days=30)).isoformat(),
            '--iv', '0.18'
        ])

        assert result.exit_code == 0
        # Should show interpretation section
        assert 'Greeks Interpretation:' in result.output

    def test_risk_profile_assessment(self, runner):
        """Test that risk profile is assessed"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'iron_condor',
            '--ticker', 'SPY',
            '--stock-price', '450',
            '--strikes', '440,445,455,460',
            '--premiums', '1.00,2.50,2.50,1.00',
            '--expiration', (date.today() + timedelta(days=30)).isoformat(),
            '--iv', '0.18'
        ])

        assert result.exit_code == 0
        # Should show risk profile
        assert 'Risk Profile:' in result.output
        # Should show delta risk level
        assert 'DELTA' in result.output
        # Should show theta assessment
        assert 'THETA' in result.output


class TestGreeksEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_invalid_iv_value(self, runner):
        """Test error handling for invalid IV"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'bull_call_spread',
            '--ticker', 'TEST',
            '--stock-price', '100',
            '--strikes', '95,105',
            '--premiums', '7.00,3.00',
            '--expiration', (date.today() + timedelta(days=30)).isoformat(),
            '--iv', '-0.30'  # Negative IV
        ])

        # Should still run (calculator will handle invalid values)
        # Just verify it doesn't crash
        assert result.exit_code == 0 or 'Failed' in result.output

    def test_zero_iv(self, runner):
        """Test with zero IV"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'bull_call_spread',
            '--ticker', 'TEST',
            '--stock-price', '100',
            '--strikes', '95,105',
            '--premiums', '7.00,3.00',
            '--expiration', (date.today() + timedelta(days=30)).isoformat(),
            '--iv', '0.0'  # Zero IV
        ])

        # Should handle gracefully
        # May not show Greeks or show zeros
        assert result.exit_code == 0

    def test_very_high_iv(self, runner):
        """Test with very high IV"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'bull_call_spread',
            '--ticker', 'TEST',
            '--stock-price', '100',
            '--strikes', '95,105',
            '--premiums', '7.00,3.00',
            '--expiration', (date.today() + timedelta(days=30)).isoformat(),
            '--iv', '2.0'  # 200% IV
        ])

        # Should still work
        assert result.exit_code == 0

    def test_expired_strategy_with_iv(self, runner):
        """Test building strategy with expired date"""
        result = runner.invoke(cli, [
            'strategy', 'build', 'bull_call_spread',
            '--ticker', 'TEST',
            '--stock-price', '100',
            '--strikes', '95,105',
            '--premiums', '7.00,3.00',
            '--expiration', (date.today() - timedelta(days=1)).isoformat(),  # Expired
            '--iv', '0.30'
        ])

        # Should handle expired gracefully (Greeks will be empty)
        assert result.exit_code == 0


class TestStrategyCompare:
    """Test comparing strategies with Greeks"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_compare_strategies_with_greeks(self, runner):
        """Test comparing multiple strategies that have Greeks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Build strategy 1
            file1 = Path(tmpdir) / 'strategy1.json'
            runner.invoke(cli, [
                'strategy', 'build', 'bull_call_spread',
                '--ticker', 'TEST1',
                '--stock-price', '100',
                '--strikes', '95,105',
                '--premiums', '7.00,3.00',
                '--expiration', (date.today() + timedelta(days=30)).isoformat(),
                '--iv', '0.30',
                '--output', str(file1)
            ])

            # Build strategy 2
            file2 = Path(tmpdir) / 'strategy2.json'
            runner.invoke(cli, [
                'strategy', 'build', 'iron_condor',
                '--ticker', 'TEST2',
                '--stock-price', '100',
                '--strikes', '90,95,105,110',
                '--premiums', '1.00,2.50,2.50,1.00',
                '--expiration', (date.today() + timedelta(days=30)).isoformat(),
                '--iv', '0.25',
                '--output', str(file2)
            ])

            # Compare them
            result = runner.invoke(cli, [
                'strategy', 'compare',
                str(file1),
                str(file2)
            ])

            assert result.exit_code == 0
            assert 'Comparing' in result.output
            # Should show both strategies
            assert 'TEST1' in result.output
            assert 'TEST2' in result.output


class TestStrategyAnalyze:
    """Test analyzing strategies with Greeks"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_analyze_strategy_with_greeks(self, runner):
        """Test analyzing a saved strategy that has Greeks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'strategy.json'

            # Build and save
            runner.invoke(cli, [
                'strategy', 'build', 'iron_condor',
                '--ticker', 'SPY',
                '--stock-price', '450',
                '--strikes', '440,445,455,460',
                '--premiums', '1.00,2.50,2.50,1.00',
                '--expiration', (date.today() + timedelta(days=30)).isoformat(),
                '--iv', '0.18',
                '--output', str(output_file)
            ])

            # Analyze it
            result = runner.invoke(cli, [
                'strategy', 'analyze',
                str(output_file)
            ])

            assert result.exit_code == 0
            assert 'Strategy Analysis' in result.output
            # Should show basic metrics
            assert 'Max Profit' in result.output
            assert 'Max Loss' in result.output
