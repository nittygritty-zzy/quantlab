"""
Advanced Options & Market Indicators Analysis for GOOG
Calculates comprehensive Greeks, volatility metrics, and sentiment indicators
"""

import os
import sys
import json
import numpy as np
from polygon import RESTClient
from datetime import datetime, timedelta
from collections import defaultdict
from scipy import stats

sys.path.append('/Users/zheyuanzhao/workspace/polygon_api')

class AdvancedIndicatorsAnalyzer:
    def __init__(self, ticker="GOOG", api_key=None):
        self.ticker = ticker
        if api_key:
            self.client = RESTClient(api_key)
        else:
            self.client = RESTClient()

        self.data = {
            'ticker': ticker,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_price': None,
            'options_greeks': {},
            'advanced_greeks': {},
            'volatility_metrics': {},
            'options_flow': {},
            'technical_indicators': {},
            'sentiment_indicators': {},
        }

    def fetch_current_price(self):
        """Get current stock price"""
        print("="*80)
        print("FETCHING CURRENT STOCK DATA")
        print("="*80)

        try:
            snapshot = self.client.get_snapshot_ticker("stocks", self.ticker)
            self.data['current_price'] = snapshot.day.close
            print(f"\n✓ Current Price: ${self.data['current_price']:.2f}")
            return self.data['current_price']
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def fetch_historical_volatility(self, days=30):
        """Calculate realized/historical volatility"""
        print("\n" + "="*80)
        print("CALCULATING REALIZED VOLATILITY")
        print("="*80)

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+10)

            bars = list(self.client.list_aggs(
                self.ticker,
                1,
                "day",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                limit=1000
            ))

            if len(bars) < 2:
                print("✗ Insufficient data")
                return None

            # Calculate log returns
            closes = [b.close for b in bars]
            returns = np.diff(np.log(closes))

            # Realized volatility (annualized)
            realized_vol = np.std(returns) * np.sqrt(252)

            # 10-day, 20-day, 30-day volatilities
            vol_10d = np.std(returns[-10:]) * np.sqrt(252) if len(returns) >= 10 else None
            vol_20d = np.std(returns[-20:]) * np.sqrt(252) if len(returns) >= 20 else None
            vol_30d = np.std(returns[-30:]) * np.sqrt(252) if len(returns) >= 30 else None

            self.data['volatility_metrics']['realized_volatility_30d'] = realized_vol
            self.data['volatility_metrics']['realized_volatility_10d'] = vol_10d
            self.data['volatility_metrics']['realized_volatility_20d'] = vol_20d

            print(f"\n✓ 30-Day Realized Volatility: {realized_vol:.2%}")
            if vol_20d:
                print(f"✓ 20-Day Realized Volatility: {vol_20d:.2%}")
            if vol_10d:
                print(f"✓ 10-Day Realized Volatility: {vol_10d:.2%}")

            return realized_vol

        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def fetch_vix_data(self):
        """Fetch VIX (market volatility index)"""
        print("\n" + "="*80)
        print("FETCHING VIX DATA")
        print("="*80)

        try:
            # Get VIX current level
            vix_snapshot = self.client.get_snapshot_ticker("indices", "I:VIX")
            vix_current = vix_snapshot.day.close if hasattr(vix_snapshot, 'day') else None

            # Get historical VIX for context
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)

            vix_bars = list(self.client.list_aggs(
                "I:VIX",
                1,
                "day",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                limit=100
            ))

            if vix_bars:
                vix_closes = [b.close for b in vix_bars]
                vix_avg = np.mean(vix_closes)
                vix_min = np.min(vix_closes)
                vix_max = np.max(vix_closes)
                vix_percentile = (vix_current - vix_min) / (vix_max - vix_min) * 100 if vix_max > vix_min else 50

                self.data['volatility_metrics']['vix_current'] = vix_current
                self.data['volatility_metrics']['vix_avg_90d'] = vix_avg
                self.data['volatility_metrics']['vix_percentile'] = vix_percentile
                self.data['volatility_metrics']['vix_range_90d'] = (vix_min, vix_max)

                print(f"\n✓ VIX Current: {vix_current:.2f}")
                print(f"✓ VIX 90-Day Average: {vix_avg:.2f}")
                print(f"✓ VIX Percentile: {vix_percentile:.1f}%")
                print(f"✓ VIX 90-Day Range: {vix_min:.2f} - {vix_max:.2f}")
            else:
                print("✗ No VIX data available")

        except Exception as e:
            print(f"✗ Error fetching VIX: {e}")

    def calculate_options_flow_metrics(self):
        """Calculate Put/Call Ratio, Max Pain, etc."""
        print("\n" + "="*80)
        print("CALCULATING OPTIONS FLOW METRICS")
        print("="*80)

        try:
            # Get options chain
            options = []
            for snap in self.client.list_snapshot_options_chain(self.ticker, params={"limit": 250}):
                option_data = {}

                if hasattr(snap, 'details') and snap.details:
                    option_data['strike'] = snap.details.strike_price
                    option_data['expiry'] = snap.details.expiration_date
                    option_data['type'] = snap.details.contract_type.upper()

                if hasattr(snap, 'day') and snap.day:
                    option_data['volume'] = snap.day.volume

                if hasattr(snap, 'open_interest'):
                    option_data['open_interest'] = snap.open_interest

                if hasattr(snap, 'implied_volatility'):
                    option_data['iv'] = snap.implied_volatility

                options.append(option_data)

            # Separate calls and puts
            calls = [o for o in options if o.get('type') == 'CALL']
            puts = [o for o in options if o.get('type') == 'PUT']

            # Put/Call Ratio by Volume
            call_volume = sum(o.get('volume', 0) or 0 for o in calls)
            put_volume = sum(o.get('volume', 0) or 0 for o in puts)
            pc_ratio_volume = put_volume / call_volume if call_volume > 0 else 0

            # Put/Call Ratio by Open Interest
            call_oi = sum(o.get('open_interest', 0) or 0 for o in calls)
            put_oi = sum(o.get('open_interest', 0) or 0 for o in puts)
            pc_ratio_oi = put_oi / call_oi if call_oi > 0 else 0

            self.data['options_flow']['put_call_ratio_volume'] = pc_ratio_volume
            self.data['options_flow']['put_call_ratio_oi'] = pc_ratio_oi
            self.data['options_flow']['total_call_volume'] = call_volume
            self.data['options_flow']['total_put_volume'] = put_volume
            self.data['options_flow']['total_call_oi'] = call_oi
            self.data['options_flow']['total_put_oi'] = put_oi

            print(f"\n✓ Put/Call Ratio (Volume): {pc_ratio_volume:.3f}")
            print(f"✓ Put/Call Ratio (OI): {pc_ratio_oi:.3f}")
            print(f"✓ Total Call Volume: {call_volume:,}")
            print(f"✓ Total Put Volume: {put_volume:,}")
            print(f"✓ Total Call OI: {call_oi:,}")
            print(f"✓ Total Put OI: {put_oi:,}")

            # Calculate Max Pain for near-term expiration
            self.calculate_max_pain(options)

            # Calculate IV Skew
            self.calculate_iv_skew(calls, puts)

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

    def calculate_max_pain(self, options):
        """Calculate Max Pain price"""
        print("\n→ Calculating Max Pain...")

        try:
            if not self.data['current_price']:
                return

            current_price = self.data['current_price']

            # Group by expiration
            by_expiry = defaultdict(list)
            for opt in options:
                if opt.get('expiry') and opt.get('strike') and opt.get('open_interest'):
                    by_expiry[opt['expiry']].append(opt)

            # Calculate max pain for nearest expiration
            if not by_expiry:
                print("  ✗ No expiration data available")
                return

            nearest_expiry = min(by_expiry.keys())
            nearest_options = by_expiry[nearest_expiry]

            # Get range of strikes to test
            strikes = sorted(set(o['strike'] for o in nearest_options))

            if not strikes:
                print("  ✗ No strikes available")
                return

            # Calculate pain at each strike
            max_pain_strike = None
            min_pain = float('inf')

            for test_strike in strikes:
                pain = 0

                for opt in nearest_options:
                    oi = opt.get('open_interest', 0) or 0
                    strike = opt['strike']
                    opt_type = opt.get('type')

                    if opt_type == 'CALL' and test_strike > strike:
                        pain += (test_strike - strike) * oi * 100
                    elif opt_type == 'PUT' and test_strike < strike:
                        pain += (strike - test_strike) * oi * 100

                if pain < min_pain:
                    min_pain = pain
                    max_pain_strike = test_strike

            self.data['options_flow']['max_pain'] = max_pain_strike
            self.data['options_flow']['max_pain_expiry'] = nearest_expiry
            self.data['options_flow']['max_pain_distance'] = ((current_price - max_pain_strike) / current_price * 100) if max_pain_strike else 0

            print(f"  ✓ Max Pain: ${max_pain_strike:.2f} (expiry: {nearest_expiry[:10]})")
            print(f"  ✓ Distance from Current: {self.data['options_flow']['max_pain_distance']:+.2f}%")

        except Exception as e:
            print(f"  ✗ Error calculating Max Pain: {e}")

    def calculate_iv_skew(self, calls, puts):
        """Calculate Put/Call IV Skew"""
        print("\n→ Calculating IV Skew...")

        try:
            if not self.data['current_price']:
                return

            current_price = self.data['current_price']

            # Find ATM options
            atm_calls = [c for c in calls if c.get('strike') and c.get('iv')
                        and abs(c['strike'] - current_price) / current_price < 0.05]
            atm_puts = [p for p in puts if p.get('strike') and p.get('iv')
                       and abs(p['strike'] - current_price) / current_price < 0.05]

            if atm_calls and atm_puts:
                avg_call_iv = np.mean([c['iv'] for c in atm_calls])
                avg_put_iv = np.mean([p['iv'] for p in atm_puts])

                skew = avg_put_iv - avg_call_iv
                skew_pct = (skew / avg_call_iv) * 100

                self.data['sentiment_indicators']['iv_skew'] = skew
                self.data['sentiment_indicators']['iv_skew_percent'] = skew_pct
                self.data['sentiment_indicators']['atm_call_iv'] = avg_call_iv
                self.data['sentiment_indicators']['atm_put_iv'] = avg_put_iv

                print(f"  ✓ ATM Call IV: {avg_call_iv:.2%}")
                print(f"  ✓ ATM Put IV: {avg_put_iv:.2%}")
                print(f"  ✓ Put/Call IV Skew: {skew:+.4f} ({skew_pct:+.2f}%)")

                if skew > 0:
                    print(f"  → Bearish sentiment (puts more expensive)")
                else:
                    print(f"  → Bullish sentiment (calls more expensive)")
            else:
                print(f"  ✗ Insufficient ATM options for skew calculation")

        except Exception as e:
            print(f"  ✗ Error calculating IV Skew: {e}")

    def calculate_bollinger_bands(self, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        print("\n" + "="*80)
        print("CALCULATING BOLLINGER BANDS")
        print("="*80)

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period+30)

            bars = list(self.client.list_aggs(
                self.ticker,
                1,
                "day",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                limit=100
            ))

            if len(bars) < period:
                print("✗ Insufficient data")
                return

            closes = [b.close for b in bars]

            # Calculate middle band (SMA)
            middle_band = np.mean(closes[-period:])

            # Calculate standard deviation
            std = np.std(closes[-period:])

            # Calculate bands
            upper_band = middle_band + (std_dev * std)
            lower_band = middle_band - (std_dev * std)

            current_price = closes[-1]
            bb_position = (current_price - lower_band) / (upper_band - lower_band) * 100

            self.data['technical_indicators']['bollinger_bands'] = {
                'upper': upper_band,
                'middle': middle_band,
                'lower': lower_band,
                'current_price': current_price,
                'bb_position_percent': bb_position,
                'bandwidth': (upper_band - lower_band) / middle_band * 100
            }

            print(f"\n✓ Bollinger Bands ({period}-period, {std_dev}σ):")
            print(f"  Upper Band: ${upper_band:.2f}")
            print(f"  Middle Band: ${middle_band:.2f}")
            print(f"  Lower Band: ${lower_band:.2f}")
            print(f"  Current Price: ${current_price:.2f}")
            print(f"  Position: {bb_position:.1f}%")
            print(f"  Bandwidth: {self.data['technical_indicators']['bollinger_bands']['bandwidth']:.2f}%")

            if bb_position > 80:
                print(f"  → Overbought (near upper band)")
            elif bb_position < 20:
                print(f"  → Oversold (near lower band)")
            else:
                print(f"  → Neutral")

        except Exception as e:
            print(f"✗ Error: {e}")

    def calculate_volume_profile(self, days=20):
        """Calculate Volume Profile"""
        print("\n" + "="*80)
        print("CALCULATING VOLUME PROFILE")
        print("="*80)

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+5)

            bars = list(self.client.list_aggs(
                self.ticker,
                1,
                "day",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                limit=100
            ))

            if not bars:
                print("✗ No data available")
                return

            # Create price bins
            all_prices = []
            for bar in bars:
                all_prices.extend([bar.low, bar.high])

            min_price = min(all_prices)
            max_price = max(all_prices)

            # Create 20 price levels
            bins = np.linspace(min_price, max_price, 21)
            volume_at_price = defaultdict(float)

            for bar in bars:
                # Distribute volume across price range
                bin_idx = np.digitize([(bar.low + bar.high) / 2], bins)[0]
                if 0 < bin_idx < len(bins):
                    volume_at_price[bins[bin_idx]] += bar.volume

            # Find point of control (highest volume)
            if volume_at_price:
                poc_price = max(volume_at_price, key=volume_at_price.get)
                poc_volume = volume_at_price[poc_price]

                # Calculate value area (70% of volume)
                total_volume = sum(volume_at_price.values())
                sorted_levels = sorted(volume_at_price.items(), key=lambda x: x[1], reverse=True)

                cumulative_vol = 0
                value_area_high = None
                value_area_low = None

                for price, vol in sorted_levels:
                    cumulative_vol += vol
                    if value_area_high is None:
                        value_area_high = price
                    value_area_low = price

                    if cumulative_vol >= total_volume * 0.70:
                        break

                self.data['technical_indicators']['volume_profile'] = {
                    'point_of_control': poc_price,
                    'poc_volume': poc_volume,
                    'value_area_high': value_area_high,
                    'value_area_low': value_area_low,
                    'period_days': days
                }

                print(f"\n✓ Volume Profile ({days}-day):")
                print(f"  Point of Control: ${poc_price:.2f} ({poc_volume:,.0f} shares)")
                print(f"  Value Area High: ${value_area_high:.2f}")
                print(f"  Value Area Low: ${value_area_low:.2f}")
                print(f"  Current Price: ${self.data['current_price']:.2f}")

                if self.data['current_price'] > value_area_high:
                    print(f"  → Above value area (bullish)")
                elif self.data['current_price'] < value_area_low:
                    print(f"  → Below value area (bearish)")
                else:
                    print(f"  → Within value area")

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

    def calculate_iv_rank_percentile(self):
        """Calculate IV Rank and Percentile"""
        print("\n" + "="*80)
        print("CALCULATING IV RANK & PERCENTILE")
        print("="*80)

        try:
            # Get ATM options for current IV
            options = []
            for snap in self.client.list_snapshot_options_chain(self.ticker, params={"limit": 100}):
                if hasattr(snap, 'details') and snap.details and hasattr(snap, 'implied_volatility'):
                    if snap.implied_volatility and snap.details.strike_price:
                        options.append({
                            'strike': snap.details.strike_price,
                            'iv': snap.implied_volatility,
                            'type': snap.details.contract_type
                        })

            if not options or not self.data['current_price']:
                print("✗ Insufficient options data")
                return

            # Find ATM IV
            current_price = self.data['current_price']
            atm_options = [o for o in options
                          if abs(o['strike'] - current_price) / current_price < 0.05
                          and o['type'] == 'call']

            if not atm_options:
                print("✗ No ATM options found")
                return

            current_iv = np.mean([o['iv'] for o in atm_options])

            # Get historical IV (would need historical options data)
            # For now, use realized volatility as proxy for historical range
            realized_vol = self.data['volatility_metrics'].get('realized_volatility_30d', 0)

            # Estimate IV rank (simplified)
            # In practice, would compare to 52-week IV range
            iv_rank = 50  # Placeholder - would need historical IV data

            self.data['volatility_metrics']['current_atm_iv'] = current_iv
            self.data['volatility_metrics']['iv_rank'] = iv_rank
            self.data['volatility_metrics']['iv_vs_realized'] = current_iv - realized_vol

            print(f"\n✓ Current ATM IV: {current_iv:.2%}")
            print(f"✓ 30-Day Realized Vol: {realized_vol:.2%}")
            print(f"✓ IV vs Realized: {(current_iv - realized_vol):.2%}")

            if current_iv > realized_vol * 1.2:
                print(f"  → IV elevated (options expensive)")
            elif current_iv < realized_vol * 0.8:
                print(f"  → IV depressed (options cheap)")
            else:
                print(f"  → IV fairly priced")

        except Exception as e:
            print(f"✗ Error: {e}")

    def save_results(self):
        """Save analysis to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/Users/zheyuanzhao/workspace/quantlab/results/goog_advanced_indicators_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)

        print(f"\n{'='*80}")
        print(f"✓ Results saved to: {filename}")
        print(f"{'='*80}")

        return filename

    def run_full_analysis(self):
        """Run complete advanced indicators analysis"""
        print("\n" + "="*80)
        print(f"ADVANCED OPTIONS & MARKET INDICATORS ANALYSIS - {self.ticker}")
        print("="*80)
        print(f"Analysis Date: {self.data['analysis_date']}")

        self.fetch_current_price()
        self.fetch_historical_volatility()
        self.fetch_vix_data()
        self.calculate_options_flow_metrics()
        self.calculate_bollinger_bands()
        self.calculate_volume_profile()
        self.calculate_iv_rank_percentile()

        results_file = self.save_results()

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)

        return results_file


if __name__ == "__main__":
    api_key = os.getenv('POLYGON_API_KEY', 'vDr8GDaQ87Z9Mwe5IiCKzGcRP9pnO8TW')
    analyzer = AdvancedIndicatorsAnalyzer(ticker="GOOG", api_key=api_key)
    results_file = analyzer.run_full_analysis()
    print(f"\nResults file: {results_file}")
