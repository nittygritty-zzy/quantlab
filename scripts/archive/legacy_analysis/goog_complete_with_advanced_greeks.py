"""
Complete GOOG Analysis with Advanced Greeks
Integrates Black-Scholes advanced Greeks calculations
"""

import os
import sys
import json
from polygon import RESTClient
from datetime import datetime, timedelta

# Import our advanced Greeks calculator
sys.path.append('/Users/zheyuanzhao/workspace/quantlab/scripts/analysis')
from advanced_greeks_calculator import calculate_advanced_greeks_for_option, BlackScholesGreeks

class CompleteGOOGAnalysis:
    def __init__(self, ticker="GOOG", api_key=None):
        self.ticker = ticker
        if api_key:
            self.client = RESTClient(api_key)
        else:
            self.client = RESTClient()

        self.current_price = None
        self.risk_free_rate = 0.045  # 4.5% - approximate current Fed Funds rate
        self.analysis_results = {
            'ticker': ticker,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'itm_calls_with_advanced_greeks': []
        }

    def fetch_current_price(self):
        """Get current stock price"""
        try:
            snapshot = self.client.get_snapshot_ticker("stocks", self.ticker)
            self.current_price = snapshot.day.close
            return self.current_price
        except Exception as e:
            print(f"Error fetching price: {e}")
            return None

    def fetch_and_enhance_itm_calls(self):
        """Fetch ITM calls and calculate advanced Greeks"""
        print("="*80)
        print("FETCHING ITM CALLS WITH ADVANCED GREEKS")
        print("="*80)

        if not self.current_price:
            self.fetch_current_price()

        print(f"\nCurrent Price: ${self.current_price:.2f}")
        print(f"Risk-free rate: {self.risk_free_rate*100:.2f}%")

        # Get options chain
        print("\nFetching options chain...")
        itm_calls = []

        for snap in self.client.list_snapshot_options_chain(
            self.ticker,
            params={"limit": 250}
        ):
            if not hasattr(snap, 'details') or not snap.details:
                continue

            details = snap.details
            strike = details.strike_price if hasattr(details, 'strike_price') else None
            expiry = details.expiration_date if hasattr(details, 'expiration_date') else None
            opt_type = details.contract_type.upper() if hasattr(details, 'contract_type') else None

            # Filter for ITM calls
            if opt_type != 'CALL' or not strike or not expiry:
                continue

            if strike >= self.current_price:
                continue

            # Get pricing and Greeks from snapshot
            option_data = {
                'ticker': snap.ticker if hasattr(snap, 'ticker') else None,
                'strike': strike,
                'expiry': expiry,
                'type': opt_type,
            }

            # Day data
            if hasattr(snap, 'day') and snap.day:
                option_data['price'] = snap.day.close if hasattr(snap.day, 'close') else None
                option_data['volume'] = snap.day.volume if hasattr(snap.day, 'volume') else None

            # Market Greeks
            if hasattr(snap, 'greeks') and snap.greeks:
                g = snap.greeks
                option_data['market_delta'] = g.delta if hasattr(g, 'delta') and g.delta else None
                option_data['market_gamma'] = g.gamma if hasattr(g, 'gamma') and g.gamma else None
                option_data['market_theta'] = g.theta if hasattr(g, 'theta') and g.theta else None
                option_data['market_vega'] = g.vega if hasattr(g, 'vega') and g.vega else None

            # IV
            if hasattr(snap, 'implied_volatility') and snap.implied_volatility:
                option_data['iv'] = snap.implied_volatility

            # OI
            if hasattr(snap, 'open_interest'):
                option_data['open_interest'] = snap.open_interest

            itm_calls.append(option_data)

        print(f"✓ Found {len(itm_calls)} ITM call options")

        # Calculate advanced Greeks for options with IV
        print("\nCalculating advanced Greeks (Vanna, Charm, Vomma)...")

        enhanced_count = 0
        for option in itm_calls:
            if not option.get('iv') or not option.get('expiry'):
                continue

            try:
                # Calculate days to expiry
                days_to_expiry = BlackScholesGreeks.days_to_expiry(option['expiry'])

                # Calculate all Greeks using Black-Scholes
                bs_greeks = calculate_advanced_greeks_for_option(
                    S=self.current_price,
                    K=option['strike'],
                    T_days=days_to_expiry,
                    r=self.risk_free_rate,
                    sigma=option['iv'],
                    option_type='call'
                )

                # Add Black-Scholes calculated Greeks
                option['bs_delta'] = bs_greeks['delta']
                option['bs_gamma'] = bs_greeks['gamma']
                option['bs_vega'] = bs_greeks['vega']
                option['bs_theta'] = bs_greeks['theta']

                # Add advanced Greeks
                option['vanna'] = bs_greeks['vanna']
                option['charm'] = bs_greeks['charm']
                option['vomma'] = bs_greeks['vomma']

                # Calculate intrinsic and time value
                option['intrinsic_value'] = max(self.current_price - option['strike'], 0)
                option['percent_itm'] = ((self.current_price - option['strike']) / option['strike']) * 100

                if option.get('price'):
                    option['time_value'] = option['price'] - option['intrinsic_value']

                enhanced_count += 1

            except Exception as e:
                # Skip if calculation fails
                continue

        print(f"✓ Calculated advanced Greeks for {enhanced_count} options")

        # Filter to keep only those with advanced Greeks and in our target range (5-20% ITM)
        enhanced_options = [
            o for o in itm_calls
            if o.get('vanna') is not None
            and 5 <= o.get('percent_itm', 0) <= 20
        ]

        # Sort by strike (closest to current price first)
        enhanced_options.sort(key=lambda x: x['strike'], reverse=True)

        self.analysis_results['itm_calls_with_advanced_greeks'] = enhanced_options

        return enhanced_options

    def display_results(self):
        """Display analysis results"""
        options = self.analysis_results['itm_calls_with_advanced_greeks']

        if not options:
            print("\n✗ No options with advanced Greeks calculated")
            return

        print("\n" + "="*120)
        print("ITM CALL OPTIONS WITH ADVANCED GREEKS (5-20% ITM)")
        print("="*120)

        # Table header
        print(f"\n{'Expiry':<12} {'Strike':<10} {'%ITM':<8} {'Price':<10} {'Delta':<8} {'Vanna':<10} {'Charm':<10} {'Vomma':<10} {'OI':<10}")
        print("-"*120)

        for i, opt in enumerate(options[:30], 1):
            expiry = opt['expiry'][:10]
            strike = opt['strike']
            pct_itm = opt.get('percent_itm', 0)
            price = opt.get('price', 0)
            delta = opt.get('bs_delta', 0)
            vanna = opt.get('vanna', 0)
            charm = opt.get('charm', 0)
            vomma = opt.get('vomma', 0)
            oi = opt.get('open_interest', 0) or 0

            print(f"{expiry:<12} ${strike:<9.2f} {pct_itm:<7.2f}% ${price:<9.2f} {delta:<7.4f} {vanna:<9.6f} {charm:<9.6f} {vomma:<9.6f} {oi:<9,}")

        # Show detailed analysis for top 3
        print("\n" + "="*120)
        print("DETAILED ANALYSIS - TOP 3 RECOMMENDATIONS")
        print("="*120)

        for i, opt in enumerate(options[:3], 1):
            print(f"\n{i}. {opt['ticker']} - ${opt['strike']:.2f} Strike, Expires {opt['expiry'][:10]}")
            print(f"   {'─'*100}")

            print(f"\n   BASIC INFO:")
            print(f"   • Strike: ${opt['strike']:.2f} ({opt.get('percent_itm', 0):.2f}% ITM)")
            print(f"   • Current Price: ${opt.get('price', 0):.2f}")
            print(f"   • Intrinsic Value: ${opt.get('intrinsic_value', 0):.2f}")
            print(f"   • Time Value: ${opt.get('time_value', 0):.2f}")
            print(f"   • Days to Expiry: {BlackScholesGreeks.days_to_expiry(opt['expiry'])}")
            print(f"   • Implied Volatility: {opt.get('iv', 0)*100:.2f}%")
            print(f"   • Open Interest: {opt.get('open_interest', 0):,}")

            print(f"\n   FIRST-ORDER GREEKS:")
            print(f"   • Delta: {opt.get('bs_delta', 0):.4f} - If GOOG moves $1, option moves ${opt.get('bs_delta', 0):.2f}")
            print(f"   • Gamma: {opt.get('bs_gamma', 0):.4f} - Delta changes by {opt.get('bs_gamma', 0):.4f} per $1 stock move")
            print(f"   • Vega: {opt.get('bs_vega', 0):.4f} - Gains ${opt.get('bs_vega', 0)*100:.2f} if IV increases 1%")
            print(f"   • Theta: {opt.get('bs_theta', 0):.4f} - Loses ${abs(opt.get('bs_theta', 0)):.2f} per day")

            print(f"\n   ADVANCED GREEKS:")
            vanna = opt.get('vanna', 0)
            charm = opt.get('charm', 0)
            vomma = opt.get('vomma', 0)

            print(f"   • Vanna: {vanna:.6f}")
            print(f"     → If IV increases 1%, delta changes by {vanna:.6f}")
            if vanna < 0:
                print(f"     → NEGATIVE vanna: Higher volatility → Lower delta (bad for long calls)")
            else:
                print(f"     → POSITIVE vanna: Higher volatility → Higher delta (good for long calls)")

            print(f"\n   • Charm: {charm:.6f}")
            print(f"     → Delta changes by {charm:.6f} each day")
            if charm > 0:
                print(f"     → POSITIVE charm: Delta increases toward 1.0 as time passes")
            else:
                print(f"     → NEGATIVE charm: Delta decreases as time passes")

            print(f"\n   • Vomma: {vomma:.6f}")
            print(f"     → If IV increases 1%, vega changes by {vomma:.6f}")
            if vomma > 0:
                print(f"     → POSITIVE vomma: Benefit more from volatility increases")
            else:
                print(f"     → NEGATIVE vomma: Exposed to volatility crush")

    def save_results(self):
        """Save results to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/Users/zheyuanzhao/workspace/quantlab/results/goog_advanced_greeks_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)

        print(f"\n{'='*120}")
        print(f"✓ Results saved to: {filename}")
        return filename

    def run_complete_analysis(self):
        """Run complete analysis"""
        print("\n" + "="*120)
        print("GOOG COMPLETE ANALYSIS WITH ADVANCED GREEKS")
        print("="*120)
        print(f"Analysis Date: {self.analysis_results['timestamp']}")

        self.fetch_current_price()
        self.fetch_and_enhance_itm_calls()
        self.display_results()
        results_file = self.save_results()

        print("\n" + "="*120)
        print("ANALYSIS COMPLETE")
        print("="*120)

        return results_file


if __name__ == "__main__":
    api_key = os.getenv('POLYGON_API_KEY', 'vDr8GDaQ87Z9Mwe5IiCKzGcRP9pnO8TW')
    analyzer = CompleteGOOGAnalysis(ticker="GOOG", api_key=api_key)
    results_file = analyzer.run_complete_analysis()
    print(f"\nResults: {results_file}")
