"""
Unit tests for Advanced Greeks Integration

Tests the integration of advanced Greeks (Vanna, Charm, Vomma) with options strategies.
"""

import pytest
from datetime import date, timedelta
from quantlab.analysis.options_strategies import (
    OptionLeg, OptionsStrategy, StrategyBuilder,
    OptionType, PositionType, StrategyType
)


class TestOptionLegAdvancedGreeks:
    """Test advanced Greeks calculation for OptionLeg"""

    def test_calculate_greeks_with_iv(self):
        """Test that Greeks are calculated when IV is provided"""
        expiration = date.today() + timedelta(days=30)
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30,
            risk_free_rate=0.05
        )

        greeks = leg.calculate_advanced_greeks(stock_price=100.0)

        # Should have all 7 Greeks
        assert 'delta' in greeks
        assert 'gamma' in greeks
        assert 'theta' in greeks
        assert 'vega' in greeks
        assert 'vanna' in greeks
        assert 'charm' in greeks
        assert 'vomma' in greeks

        # ATM call delta should be around 0.5
        assert 0.4 < greeks['delta'] < 0.6

        # Gamma should be positive
        assert greeks['gamma'] > 0

        # Long call theta should be negative
        assert greeks['theta'] < 0

    def test_calculate_greeks_without_iv(self):
        """Test that Greeks return empty dict without IV"""
        expiration = date.today() + timedelta(days=30)
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=None  # No IV
        )

        greeks = leg.calculate_advanced_greeks(stock_price=100.0)

        # Should return empty dict
        assert greeks == {}

    def test_calculate_greeks_expired_option(self):
        """Test that expired options return empty Greeks"""
        expiration = date.today() - timedelta(days=1)  # Expired
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30
        )

        greeks = leg.calculate_advanced_greeks(stock_price=100.0)

        # Should return empty dict for expired option
        assert greeks == {}

    def test_short_position_reverses_greeks(self):
        """Test that short positions have reversed Greek signs"""
        expiration = date.today() + timedelta(days=30)

        # Long call
        long_leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30
        )

        # Short call (same parameters)
        short_leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.SHORT,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30
        )

        long_greeks = long_leg.calculate_advanced_greeks(stock_price=100.0)
        short_greeks = short_leg.calculate_advanced_greeks(stock_price=100.0)

        # Signs should be opposite
        assert long_greeks['delta'] == pytest.approx(-short_greeks['delta'], abs=0.01)
        assert long_greeks['gamma'] == pytest.approx(-short_greeks['gamma'], abs=0.0001)
        assert long_greeks['vega'] == pytest.approx(-short_greeks['vega'], abs=0.01)

    def test_quantity_multiplier(self):
        """Test that quantity multiplies Greeks correctly"""
        expiration = date.today() + timedelta(days=30)

        leg_1 = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30
        )

        leg_3 = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=3,
            expiration=expiration,
            implied_volatility=0.30
        )

        greeks_1 = leg_1.calculate_advanced_greeks(stock_price=100.0)
        greeks_3 = leg_3.calculate_advanced_greeks(stock_price=100.0)

        # Quantity 3 should be 3x quantity 1
        assert greeks_3['delta'] == pytest.approx(greeks_1['delta'] * 3, abs=0.01)
        assert greeks_3['vanna'] == pytest.approx(greeks_1['vanna'] * 3, abs=0.001)


class TestStrategyAdvancedGreeks:
    """Test portfolio-level Greeks aggregation"""

    def test_single_leg_greeks(self):
        """Test Greeks for single-leg strategy"""
        expiration = date.today() + timedelta(days=30)
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30
        )

        strategy = OptionsStrategy(
            name="Long Call",
            strategy_type=StrategyType.LONG_CALL,
            legs=[leg],
            current_stock_price=100.0,
            stock_position=0
        )

        greeks = strategy.advanced_greeks()

        # Should have all Greeks
        assert 'delta' in greeks
        assert 'vanna' in greeks
        assert 'charm' in greeks
        assert 'vomma' in greeks

        # Delta should be around 0.5 for ATM call
        assert 0.4 < greeks['delta'] < 0.6

    def test_multi_leg_greeks_aggregation(self):
        """Test that multi-leg strategies aggregate Greeks correctly"""
        expiration = date.today() + timedelta(days=30)

        # Bull call spread: Buy 95 call, Sell 105 call
        legs = [
            OptionLeg(OptionType.CALL, PositionType.LONG, 95.0, 7.0, 1, expiration,
                     implied_volatility=0.30),
            OptionLeg(OptionType.CALL, PositionType.SHORT, 105.0, 3.0, 1, expiration,
                     implied_volatility=0.30)
        ]

        strategy = OptionsStrategy(
            name="Bull Call Spread",
            strategy_type=StrategyType.BULL_CALL_SPREAD,
            legs=legs,
            current_stock_price=100.0,
            stock_position=0
        )

        greeks = strategy.advanced_greeks()

        # Bull call spread should have positive delta
        assert greeks['delta'] > 0

        # But lower than single long call (due to short call)
        assert greeks['delta'] < 0.6

    def test_greeks_with_stock_position(self):
        """Test that stock position adds to delta"""
        expiration = date.today() + timedelta(days=30)

        # Short call only
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.SHORT,
            strike=105.0,
            premium=3.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30
        )

        strategy = OptionsStrategy(
            name="Covered Call",
            strategy_type=StrategyType.COVERED_CALL,
            legs=[leg],
            current_stock_price=100.0,
            stock_position=100  # Long 100 shares
        )

        greeks = strategy.advanced_greeks()

        # 100 shares = 1.0 delta
        # Short OTM call has negative delta around -0.4
        # Total should be around 0.6
        assert 0.4 < greeks['delta'] < 0.8

    def test_iron_condor_near_delta_neutral(self):
        """Test that iron condor is near delta-neutral"""
        expiration = date.today() + timedelta(days=30)

        # Iron condor at 100: 90/95 put spread, 105/110 call spread
        legs = [
            OptionLeg(OptionType.PUT, PositionType.LONG, 90.0, 1.0, 1, expiration,
                     implied_volatility=0.25),
            OptionLeg(OptionType.PUT, PositionType.SHORT, 95.0, 2.5, 1, expiration,
                     implied_volatility=0.25),
            OptionLeg(OptionType.CALL, PositionType.SHORT, 105.0, 2.5, 1, expiration,
                     implied_volatility=0.25),
            OptionLeg(OptionType.CALL, PositionType.LONG, 110.0, 1.0, 1, expiration,
                     implied_volatility=0.25)
        ]

        strategy = OptionsStrategy(
            name="Iron Condor",
            strategy_type=StrategyType.IRON_CONDOR,
            legs=legs,
            current_stock_price=100.0,
            stock_position=0
        )

        greeks = strategy.advanced_greeks()

        # Should be near delta-neutral
        assert abs(greeks['delta']) < 0.15

        # Should have negative gamma (short gamma position)
        assert greeks['gamma'] < 0

        # Should have positive theta (time decay benefits us)
        assert greeks['theta'] > 0

    def test_greeks_without_iv_returns_zeros(self):
        """Test that strategy without IV returns zero Greeks"""
        expiration = date.today() + timedelta(days=30)
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=None  # No IV
        )

        strategy = OptionsStrategy(
            name="Long Call",
            strategy_type=StrategyType.LONG_CALL,
            legs=[leg],
            current_stock_price=100.0,
            stock_position=0
        )

        greeks = strategy.advanced_greeks()

        # Should return all zeros
        assert greeks['delta'] == 0.0
        assert greeks['vanna'] == 0.0
        assert greeks['charm'] == 0.0


class TestStrategyBuilderWithIV:
    """Test StrategyBuilder methods with IV parameter"""

    def test_bull_call_spread_with_iv(self):
        """Test bull call spread builder with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.bull_call_spread(
            stock_price=100.0,
            long_strike=95.0,
            short_strike=105.0,
            long_premium=7.0,
            short_premium=3.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST",
            implied_volatility=0.30,
            risk_free_rate=0.05
        )

        # Check that IV was set on legs
        assert strategy.legs[0].implied_volatility == 0.30
        assert strategy.legs[1].implied_volatility == 0.30

        # Check that Greeks can be calculated
        greeks = strategy.advanced_greeks()
        assert greeks['delta'] != 0.0
        assert 'vanna' in greeks

    def test_iron_condor_with_iv(self):
        """Test iron condor builder with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.iron_condor(
            stock_price=100.0,
            put_long_strike=90.0,
            put_short_strike=95.0,
            call_short_strike=105.0,
            call_long_strike=110.0,
            put_long_premium=1.0,
            put_short_premium=2.5,
            call_short_premium=2.5,
            call_long_premium=1.0,
            quantity=1,
            expiration=expiration,
            ticker="TEST",
            implied_volatility=0.25
        )

        # All legs should have IV
        for leg in strategy.legs:
            assert leg.implied_volatility == 0.25

        # Should be able to calculate Greeks
        greeks = strategy.advanced_greeks()
        assert abs(greeks['delta']) < 0.15  # Near delta-neutral
        assert greeks['theta'] > 0  # Positive theta

    def test_covered_call_with_iv(self):
        """Test covered call with IV"""
        expiration = date.today() + timedelta(days=30)
        strategy = StrategyBuilder.covered_call(
            stock_price=100.0,
            shares=100,
            call_strike=105.0,
            call_premium=3.0,
            expiration=expiration,
            ticker="TEST",
            implied_volatility=0.30
        )

        # Check IV on option leg
        assert strategy.legs[0].implied_volatility == 0.30

        # Check metadata
        assert strategy.metadata['implied_volatility'] == 0.30

        # Greeks should include stock position
        greeks = strategy.advanced_greeks()
        assert 0.5 < greeks['delta'] < 0.8  # Stock delta + short call delta


class TestAdvancedGreeksMetrics:
    """Test specific advanced Greeks behaviors"""

    def test_vanna_itm_vs_otm(self):
        """Test that vanna differs for ITM vs OTM options"""
        expiration = date.today() + timedelta(days=30)

        # ITM call (stock at 110, strike 100)
        itm_leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=12.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30
        )

        # OTM call (stock at 90, strike 100)
        otm_leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=2.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30
        )

        itm_greeks = itm_leg.calculate_advanced_greeks(stock_price=110.0)
        otm_greeks = otm_leg.calculate_advanced_greeks(stock_price=90.0)

        # Vanna should be different for ITM vs OTM
        assert itm_greeks['vanna'] != otm_greeks['vanna']

    def test_charm_time_decay(self):
        """Test charm represents delta decay over time"""
        # Near expiration (5 days)
        near_exp = date.today() + timedelta(days=5)
        near_leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=3.0,
            quantity=1,
            expiration=near_exp,
            implied_volatility=0.30
        )

        # Far expiration (60 days)
        far_exp = date.today() + timedelta(days=60)
        far_leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=far_exp,
            implied_volatility=0.30
        )

        near_greeks = near_leg.calculate_advanced_greeks(stock_price=100.0)
        far_greeks = far_leg.calculate_advanced_greeks(stock_price=100.0)

        # Near expiration should have higher (more negative) charm magnitude
        assert abs(near_greeks['charm']) > abs(far_greeks['charm'])

    def test_vomma_volatility_sensitivity(self):
        """Test vomma measures vega's sensitivity to vol"""
        expiration = date.today() + timedelta(days=30)

        # ATM option
        atm_leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30
        )

        # OTM option
        otm_leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=120.0,
            premium=1.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30
        )

        atm_greeks = atm_leg.calculate_advanced_greeks(stock_price=100.0)
        otm_greeks = otm_leg.calculate_advanced_greeks(stock_price=100.0)

        # Both should have vomma calculated
        assert 'vomma' in atm_greeks
        assert 'vomma' in otm_greeks
        # Vomma should differ based on moneyness
        assert atm_greeks['vomma'] != otm_greeks['vomma']


class TestGreeksSerialization:
    """Test that Greeks are properly serialized to dict"""

    def test_to_dict_includes_greeks(self):
        """Test that to_dict includes advanced Greeks when IV provided"""
        expiration = date.today() + timedelta(days=30)
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30
        )

        strategy = OptionsStrategy(
            name="Long Call",
            strategy_type=StrategyType.LONG_CALL,
            legs=[leg],
            current_stock_price=100.0,
            stock_position=0
        )

        data = strategy.to_dict()

        # Should include advanced_greeks
        assert 'advanced_greeks' in data
        assert 'delta' in data['advanced_greeks']
        assert 'vanna' in data['advanced_greeks']
        assert 'charm' in data['advanced_greeks']
        assert 'vomma' in data['advanced_greeks']

    def test_to_dict_includes_iv_in_legs(self):
        """Test that leg IV is serialized"""
        expiration = date.today() + timedelta(days=30)
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=0.30,
            risk_free_rate=0.05
        )

        strategy = OptionsStrategy(
            name="Long Call",
            strategy_type=StrategyType.LONG_CALL,
            legs=[leg],
            current_stock_price=100.0,
            stock_position=0
        )

        data = strategy.to_dict()

        # Legs should include IV and risk-free rate
        assert data['legs'][0]['implied_volatility'] == 0.30
        assert data['legs'][0]['risk_free_rate'] == 0.05

    def test_to_dict_without_iv(self):
        """Test serialization without IV doesn't include Greeks"""
        expiration = date.today() + timedelta(days=30)
        leg = OptionLeg(
            option_type=OptionType.CALL,
            position_type=PositionType.LONG,
            strike=100.0,
            premium=5.0,
            quantity=1,
            expiration=expiration,
            implied_volatility=None  # No IV
        )

        strategy = OptionsStrategy(
            name="Long Call",
            strategy_type=StrategyType.LONG_CALL,
            legs=[leg],
            current_stock_price=100.0,
            stock_position=0
        )

        data = strategy.to_dict()

        # Should not include advanced_greeks
        assert 'advanced_greeks' not in data
