"""
Unit tests for IV Parameter Expansion Across All StrategyBuilder Methods

Tests all 11 remaining strategies that were updated to support IV parameter.
"""

import pytest
from datetime import date, timedelta
from quantlab.analysis.options_strategies import (
    StrategyBuilder, OptionType, PositionType
)


class TestSingleLegStrategiesWithIV:
    """Test single-leg strategies with IV parameter"""

    def test_long_call_with_iv(self):
        """Test long_call with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.long_call(
            stock_price=100.0,
            strike=105.0,
            premium=3.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST",
            implied_volatility=0.30,
            risk_free_rate=0.05
        )

        assert strategy.legs[0].implied_volatility == 0.30
        assert strategy.legs[0].risk_free_rate == 0.05

        greeks = strategy.advanced_greeks()
        assert greeks['delta'] != 0.0
        assert 'vanna' in greeks
        assert 'charm' in greeks

    def test_long_call_without_iv(self):
        """Test long_call without IV still works"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.long_call(
            stock_price=100.0,
            strike=105.0,
            premium=3.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None
        greeks = strategy.advanced_greeks()
        assert greeks['delta'] == 0.0

    def test_long_put_with_iv(self):
        """Test long_put with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.long_put(
            stock_price=100.0,
            strike=95.0,
            premium=2.5,
            quantity=1,
            expiration=expiration,
            ticker="TEST",
            implied_volatility=0.28,
            risk_free_rate=0.04
        )

        assert strategy.legs[0].implied_volatility == 0.28
        assert strategy.legs[0].risk_free_rate == 0.04

        greeks = strategy.advanced_greeks()
        assert greeks['delta'] < 0  # Put delta is negative
        assert 'vomma' in greeks

    def test_long_put_without_iv(self):
        """Test long_put without IV still works"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.long_put(
            stock_price=100.0,
            strike=95.0,
            premium=2.5,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None


class TestTwoLegStrategiesWithIV:
    """Test two-leg strategies with IV parameter"""

    def test_protective_put_with_iv(self):
        """Test protective_put with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.protective_put(
            stock_price=100.0,
            shares=100,
            put_strike=95.0,
            put_premium=2.0,
            expiration=expiration,
            ticker="TEST",
            implied_volatility=0.25,
            risk_free_rate=0.05
        )

        assert strategy.legs[0].implied_volatility == 0.25
        assert strategy.stock_position == 100

        greeks = strategy.advanced_greeks()
        # Should have delta close to 1.0 due to stock position
        assert 0.5 < greeks['delta'] < 1.2

    def test_protective_put_without_iv(self):
        """Test protective_put without IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.protective_put(
            stock_price=100.0,
            shares=100,
            put_strike=95.0,
            put_premium=2.0,
            expiration=expiration,
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None
        assert strategy.stock_position == 100

    def test_cash_secured_put_with_iv(self):
        """Test cash_secured_put with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.cash_secured_put(
            stock_price=100.0,
            put_strike=95.0,
            put_premium=2.5,
            quantity=1,
            expiration=expiration,
            ticker="TEST",
            implied_volatility=0.30,
            risk_free_rate=0.05
        )

        assert strategy.legs[0].implied_volatility == 0.30

        greeks = strategy.advanced_greeks()
        assert greeks['delta'] > 0  # Short put has positive delta (benefits from stock rise)

    def test_cash_secured_put_without_iv(self):
        """Test cash_secured_put without IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.cash_secured_put(
            stock_price=100.0,
            put_strike=95.0,
            put_premium=2.5,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None

    def test_bear_put_spread_with_iv(self):
        """Test bear_put_spread with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.bear_put_spread(
            stock_price=100.0,
            long_strike=105.0,
            short_strike=95.0,
            long_premium=8.0,
            short_premium=3.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST",
            implied_volatility=0.32,
            risk_free_rate=0.05
        )

        assert strategy.legs[0].implied_volatility == 0.32
        assert strategy.legs[1].implied_volatility == 0.32

        greeks = strategy.advanced_greeks()
        assert greeks['delta'] < 0  # Bearish position

    def test_bear_put_spread_without_iv(self):
        """Test bear_put_spread without IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.bear_put_spread(
            stock_price=100.0,
            long_strike=105.0,
            short_strike=95.0,
            long_premium=8.0,
            short_premium=3.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None


class TestVerticalSpreadsWithIV:
    """Test vertical spread strategies with IV parameter"""

    def test_bull_put_spread_with_iv(self):
        """Test bull_put_spread with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.bull_put_spread(
            stock_price=100.0,
            long_strike=90.0,
            short_strike=95.0,
            long_premium=1.0,
            short_premium=2.5,
            quantity=1,
            expiration=expiration,
            ticker="TEST",
            implied_volatility=0.25,
            risk_free_rate=0.05
        )

        for leg in strategy.legs:
            assert leg.implied_volatility == 0.25

        greeks = strategy.advanced_greeks()
        assert greeks['delta'] > 0  # Bullish position
        assert greeks['theta'] > 0  # Positive theta (credit spread)

    def test_bull_put_spread_without_iv(self):
        """Test bull_put_spread without IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.bull_put_spread(
            stock_price=100.0,
            long_strike=90.0,
            short_strike=95.0,
            long_premium=1.0,
            short_premium=2.5,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None

    def test_bear_call_spread_with_iv(self):
        """Test bear_call_spread with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.bear_call_spread(
            stock_price=100.0,
            long_strike=110.0,
            short_strike=105.0,
            long_premium=2.0,
            short_premium=4.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST",
            implied_volatility=0.28,
            risk_free_rate=0.05
        )

        for leg in strategy.legs:
            assert leg.implied_volatility == 0.28

        greeks = strategy.advanced_greeks()
        assert greeks['delta'] < 0  # Bearish position
        assert greeks['theta'] > 0  # Positive theta (credit spread)

    def test_bear_call_spread_without_iv(self):
        """Test bear_call_spread without IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.bear_call_spread(
            stock_price=100.0,
            long_strike=110.0,
            short_strike=105.0,
            long_premium=2.0,
            short_premium=4.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None


class TestVolatilityStrategiesWithIV:
    """Test volatility strategies with IV parameter"""

    def test_long_straddle_with_iv(self):
        """Test long straddle with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.straddle(
            stock_price=100.0,
            strike=100.0,
            call_premium=5.0,
            put_premium=4.5,
            quantity=1,
            expiration=expiration,
            position="long",
            ticker="TEST",
            implied_volatility=0.30,
            risk_free_rate=0.05
        )

        for leg in strategy.legs:
            assert leg.implied_volatility == 0.30

        greeks = strategy.advanced_greeks()
        # ATM straddle should be near delta-neutral
        assert abs(greeks['delta']) < 0.1
        # Long straddle has high vega
        assert greeks['vega'] > 0

    def test_long_straddle_without_iv(self):
        """Test long straddle without IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.straddle(
            stock_price=100.0,
            strike=100.0,
            call_premium=5.0,
            put_premium=4.5,
            quantity=1,
            expiration=expiration,
            position="long",
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None

    def test_short_straddle_with_iv(self):
        """Test short straddle with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.straddle(
            stock_price=100.0,
            strike=100.0,
            call_premium=5.0,
            put_premium=4.5,
            quantity=1,
            expiration=expiration,
            position="short",
            ticker="TEST",
            implied_volatility=0.28,
            risk_free_rate=0.05
        )

        for leg in strategy.legs:
            assert leg.implied_volatility == 0.28

        greeks = strategy.advanced_greeks()
        # Short straddle has negative vega
        assert greeks['vega'] < 0
        # Positive theta (time decay benefits us)
        assert greeks['theta'] > 0

    def test_short_straddle_without_iv(self):
        """Test short straddle without IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.straddle(
            stock_price=100.0,
            strike=100.0,
            call_premium=5.0,
            put_premium=4.5,
            quantity=1,
            expiration=expiration,
            position="short",
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None

    def test_long_strangle_with_iv(self):
        """Test long strangle with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.strangle(
            stock_price=100.0,
            put_strike=95.0,
            call_strike=105.0,
            put_premium=2.5,
            call_premium=3.0,
            quantity=1,
            expiration=expiration,
            position="long",
            ticker="TEST",
            implied_volatility=0.32,
            risk_free_rate=0.05
        )

        for leg in strategy.legs:
            assert leg.implied_volatility == 0.32

        greeks = strategy.advanced_greeks()
        # Long strangle should be near delta-neutral
        assert abs(greeks['delta']) < 0.15
        assert greeks['vega'] > 0

    def test_long_strangle_without_iv(self):
        """Test long strangle without IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.strangle(
            stock_price=100.0,
            put_strike=95.0,
            call_strike=105.0,
            put_premium=2.5,
            call_premium=3.0,
            quantity=1,
            expiration=expiration,
            position="long",
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None

    def test_short_strangle_with_iv(self):
        """Test short strangle with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.strangle(
            stock_price=100.0,
            put_strike=95.0,
            call_strike=105.0,
            put_premium=2.5,
            call_premium=3.0,
            quantity=1,
            expiration=expiration,
            position="short",
            ticker="TEST",
            implied_volatility=0.26,
            risk_free_rate=0.05
        )

        for leg in strategy.legs:
            assert leg.implied_volatility == 0.26

        greeks = strategy.advanced_greeks()
        # Short strangle has negative vega
        assert greeks['vega'] < 0
        # Positive theta
        assert greeks['theta'] > 0

    def test_short_strangle_without_iv(self):
        """Test short strangle without IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.strangle(
            stock_price=100.0,
            put_strike=95.0,
            call_strike=105.0,
            put_premium=2.5,
            call_premium=3.0,
            quantity=1,
            expiration=expiration,
            position="short",
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None


class TestComplexSpreadsWithIV:
    """Test complex spread strategies with IV parameter"""

    def test_butterfly_with_iv(self):
        """Test butterfly spread with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.butterfly(
            stock_price=100.0,
            lower_strike=95.0,
            middle_strike=100.0,
            upper_strike=105.0,
            lower_premium=1.0,
            middle_premium=3.0,
            upper_premium=1.0,
            quantity=1,
            expiration=expiration,
            option_type="call",
            ticker="TEST",
            implied_volatility=0.25,
            risk_free_rate=0.05
        )

        for leg in strategy.legs:
            assert leg.implied_volatility == 0.25

        greeks = strategy.advanced_greeks()
        # Butterfly should be near delta-neutral at center strike
        assert abs(greeks['delta']) < 0.2
        # Negative gamma (short gamma at center)
        assert greeks['gamma'] < 0

    def test_butterfly_without_iv(self):
        """Test butterfly spread without IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.butterfly(
            stock_price=100.0,
            lower_strike=95.0,
            middle_strike=100.0,
            upper_strike=105.0,
            lower_premium=1.0,
            middle_premium=3.0,
            upper_premium=1.0,
            quantity=1,
            expiration=expiration,
            option_type="call",
            ticker="TEST"
        )

        assert strategy.legs[0].implied_volatility is None

    def test_butterfly_put_with_iv(self):
        """Test put butterfly spread with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.butterfly(
            stock_price=100.0,
            lower_strike=95.0,
            middle_strike=100.0,
            upper_strike=105.0,
            lower_premium=1.0,
            middle_premium=3.5,
            upper_premium=1.0,
            quantity=1,
            expiration=expiration,
            option_type="put",
            ticker="TEST",
            implied_volatility=0.28,
            risk_free_rate=0.04
        )

        for leg in strategy.legs:
            assert leg.implied_volatility == 0.28
            assert leg.option_type == OptionType.PUT

        greeks = strategy.advanced_greeks()
        assert 'vanna' in greeks
        assert 'vomma' in greeks


class TestGreeksConsistency:
    """Test that Greeks are consistent across all strategies"""

    def test_all_strategies_have_greeks_when_iv_provided(self):
        """Verify all strategies calculate Greeks when IV is provided"""
        expiration = date.today() + timedelta(days=30)

        strategies = [
            StrategyBuilder.long_call(100.0, 105.0, 3.0, 1, expiration, "TEST", 0.30),
            StrategyBuilder.long_put(100.0, 95.0, 2.5, 1, expiration, "TEST", 0.30),
            StrategyBuilder.bull_put_spread(100.0, 90.0, 95.0, 1.0, 2.5, 1, expiration, "TEST", 0.30),
            StrategyBuilder.bear_call_spread(100.0, 110.0, 105.0, 2.0, 4.0, 1, expiration, "TEST", 0.30),
            StrategyBuilder.straddle(100.0, 100.0, 5.0, 4.5, 1, expiration, "long", "TEST", 0.30),
            StrategyBuilder.strangle(100.0, 95.0, 105.0, 2.5, 3.0, 1, expiration, "long", "TEST", 0.30),
            StrategyBuilder.butterfly(100.0, 95.0, 100.0, 105.0, 1.0, 3.0, 1.0, 1, expiration, "call", "TEST", 0.30),
        ]

        for strategy in strategies:
            greeks = strategy.advanced_greeks()
            # All should have non-zero Greeks (except possibly delta for delta-neutral strategies)
            assert 'delta' in greeks
            assert 'vanna' in greeks
            assert 'charm' in greeks
            assert 'vomma' in greeks
            assert greeks['vega'] != 0.0  # Vega should always be non-zero with IV

    def test_metadata_includes_iv(self):
        """Verify metadata includes IV when provided"""
        expiration = date.today() + timedelta(days=30)

        strategy = StrategyBuilder.long_call(
            100.0, 105.0, 3.0, 1, expiration, "TEST",
            implied_volatility=0.35
        )

        assert strategy.metadata['implied_volatility'] == 0.35
