"""
Comprehensive GOOG Stock and Options Analysis
Uses Polygon API to analyze stock fundamentals, technicals, and options chain
Focus: ITM Call Options Analysis for bullish position
"""

import os
import sys
from polygon import RESTClient
from datetime import datetime, timedelta
import json

# Add polygon_api path for any utilities if needed
sys.path.append('/Users/zheyuanzhao/workspace/polygon_api')

class GOOGAnalyzer:
    def __init__(self, api_key=None):
        if api_key:
            self.client = RESTClient(api_key)
        else:
            self.client = RESTClient()
        self.ticker = "GOOG"
        self.data = {
            'ticker_details': None,
            'current_snapshot': None,
            'historical_bars': [],
            'financials': [],
            'technical_indicators': {},
            'options_chain': [],
            'itm_calls': [],
            'news': []
        }

    def fetch_ticker_details(self):
        """Fetch company information and details"""
        print(f"\n{'='*80}")
        print(f"1. FETCHING TICKER DETAILS FOR {self.ticker}")
        print(f"{'='*80}")

        try:
            details = self.client.get_ticker_details(self.ticker)
            self.data['ticker_details'] = {
                'name': details.name,
                'description': details.description if hasattr(details, 'description') else 'N/A',
                'market_cap': details.market_cap if hasattr(details, 'market_cap') else 0,
                'total_employees': details.total_employees if hasattr(details, 'total_employees') else 0,
                'primary_exchange': details.primary_exchange,
                'currency': details.currency_name,
                'list_date': details.list_date if hasattr(details, 'list_date') else 'N/A',
                'active': details.active,
                'sic_description': details.sic_description if hasattr(details, 'sic_description') else 'N/A',
                'homepage_url': details.homepage_url if hasattr(details, 'homepage_url') else 'N/A'
            }

            print(f"\n✓ Company: {self.data['ticker_details']['name']}")
            print(f"✓ Market Cap: ${self.data['ticker_details']['market_cap']:,.0f}")
            print(f"✓ Employees: {self.data['ticker_details']['total_employees']:,}")
            print(f"✓ Exchange: {self.data['ticker_details']['primary_exchange']}")

        except Exception as e:
            print(f"\n✗ Error fetching ticker details: {e}")

    def fetch_current_snapshot(self):
        """Fetch current price and snapshot data"""
        print(f"\n{'='*80}")
        print(f"2. FETCHING CURRENT MARKET SNAPSHOT")
        print(f"{'='*80}")

        try:
            snapshot = self.client.get_snapshot_ticker("stocks", self.ticker)

            # Use day.close as primary price source (last_trade can be None)
            current_price = None
            if hasattr(snapshot, 'day') and snapshot.day and hasattr(snapshot.day, 'close'):
                current_price = snapshot.day.close
            elif hasattr(snapshot, 'last_trade') and snapshot.last_trade and hasattr(snapshot.last_trade, 'price'):
                current_price = snapshot.last_trade.price

            self.data['current_snapshot'] = {
                'ticker': snapshot.ticker,
                'current_price': current_price,
                'day_open': snapshot.day.open if hasattr(snapshot, 'day') and snapshot.day else None,
                'day_high': snapshot.day.high if hasattr(snapshot, 'day') and snapshot.day else None,
                'day_low': snapshot.day.low if hasattr(snapshot, 'day') and snapshot.day else None,
                'day_close': snapshot.day.close if hasattr(snapshot, 'day') and snapshot.day else None,
                'day_volume': snapshot.day.volume if hasattr(snapshot, 'day') and snapshot.day else None,
                'day_vwap': snapshot.day.vwap if hasattr(snapshot, 'day') and snapshot.day else None,
                'prev_close': snapshot.prev_day.close if hasattr(snapshot, 'prev_day') and snapshot.prev_day else None,
                'todays_change': snapshot.todays_change if hasattr(snapshot, 'todays_change') else None,
                'todays_change_percent': snapshot.todays_change_percent if hasattr(snapshot, 'todays_change_percent') else None,
            }

            current = self.data['current_snapshot']
            if current['current_price'] and current['prev_close']:
                change = current['todays_change'] or (current['current_price'] - current['prev_close'])
                change_pct = current['todays_change_percent'] or ((change / current['prev_close']) * 100)

                print(f"\n✓ Current Price: ${current['current_price']:.2f}")
                print(f"✓ Change: ${change:+.2f} ({change_pct:+.2f}%)")
                print(f"✓ Day Range: ${current['day_low']:.2f} - ${current['day_high']:.2f}")
                print(f"✓ Volume: {current['day_volume']:,}")
                print(f"✓ VWAP: ${current['day_vwap']:.2f}")

        except Exception as e:
            print(f"\n✗ Error fetching snapshot: {e}")
            import traceback
            traceback.print_exc()

    def fetch_historical_data(self, days=90):
        """Fetch historical price data"""
        print(f"\n{'='*80}")
        print(f"3. FETCHING HISTORICAL DATA (Last {days} days)")
        print(f"{'='*80}")

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            bars = []
            for bar in self.client.list_aggs(
                self.ticker,
                1,
                "day",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                limit=1000
            ):
                bars.append({
                    'date': datetime.fromtimestamp(bar.timestamp / 1000).strftime('%Y-%m-%d'),
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                    'vwap': bar.vwap if hasattr(bar, 'vwap') else None
                })

            self.data['historical_bars'] = bars

            if bars:
                print(f"\n✓ Fetched {len(bars)} daily bars")
                print(f"✓ Date Range: {bars[0]['date']} to {bars[-1]['date']}")

                # Calculate basic stats
                closes = [b['close'] for b in bars]
                avg_price = sum(closes) / len(closes)
                max_price = max(closes)
                min_price = min(closes)

                print(f"✓ Price Range: ${min_price:.2f} - ${max_price:.2f}")
                print(f"✓ Average Price: ${avg_price:.2f}")

        except Exception as e:
            print(f"\n✗ Error fetching historical data: {e}")

    def fetch_technical_indicators(self):
        """Fetch technical indicators: RSI, SMA, EMA, MACD"""
        print(f"\n{'='*80}")
        print(f"4. FETCHING TECHNICAL INDICATORS")
        print(f"{'='*80}")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)

        # RSI
        try:
            print("\n→ Fetching RSI (14-period)...")
            rsi_result = self.client.get_rsi(
                ticker=self.ticker,
                timespan="day",
                window=14,
                series_type="close",
                timestamp_gte=start_date.strftime("%Y-%m-%d"),
                timestamp_lte=end_date.strftime("%Y-%m-%d"),
                limit=5
            )

            if hasattr(rsi_result, 'values') and rsi_result.values:
                latest_rsi = rsi_result.values[-1]
                rsi_value = latest_rsi.value
                rsi_date = datetime.fromtimestamp(latest_rsi.timestamp / 1000).strftime('%Y-%m-%d')

                self.data['technical_indicators']['rsi'] = {
                    'value': rsi_value,
                    'date': rsi_date,
                    'signal': 'Overbought' if rsi_value >= 70 else 'Oversold' if rsi_value <= 30 else 'Neutral'
                }

                print(f"  ✓ RSI: {rsi_value:.2f} ({self.data['technical_indicators']['rsi']['signal']})")
        except Exception as e:
            print(f"  ✗ RSI Error: {e}")

        # SMA
        try:
            print("\n→ Fetching SMA (50-period)...")
            sma_result = self.client.get_sma(
                ticker=self.ticker,
                timespan="day",
                window=50,
                series_type="close",
                timestamp_gte=start_date.strftime("%Y-%m-%d"),
                timestamp_lte=end_date.strftime("%Y-%m-%d"),
                limit=5
            )

            if hasattr(sma_result, 'values') and sma_result.values:
                latest_sma = sma_result.values[-1]
                sma_value = latest_sma.value
                sma_date = datetime.fromtimestamp(latest_sma.timestamp / 1000).strftime('%Y-%m-%d')

                self.data['technical_indicators']['sma_50'] = {
                    'value': sma_value,
                    'date': sma_date
                }

                print(f"  ✓ SMA(50): ${sma_value:.2f}")
        except Exception as e:
            print(f"  ✗ SMA Error: {e}")

        # EMA
        try:
            print("\n→ Fetching EMA (20-period)...")
            ema_result = self.client.get_ema(
                ticker=self.ticker,
                timespan="day",
                window=20,
                series_type="close",
                timestamp_gte=start_date.strftime("%Y-%m-%d"),
                timestamp_lte=end_date.strftime("%Y-%m-%d"),
                limit=5
            )

            if hasattr(ema_result, 'values') and ema_result.values:
                latest_ema = ema_result.values[-1]
                ema_value = latest_ema.value
                ema_date = datetime.fromtimestamp(latest_ema.timestamp / 1000).strftime('%Y-%m-%d')

                self.data['technical_indicators']['ema_20'] = {
                    'value': ema_value,
                    'date': ema_date
                }

                print(f"  ✓ EMA(20): ${ema_value:.2f}")
        except Exception as e:
            print(f"  ✗ EMA Error: {e}")

        # MACD
        try:
            print("\n→ Fetching MACD (12, 26, 9)...")
            macd_result = self.client.get_macd(
                ticker=self.ticker,
                timespan="day",
                short_window=12,
                long_window=26,
                signal_window=9,
                series_type="close",
                timestamp_gte=start_date.strftime("%Y-%m-%d"),
                timestamp_lte=end_date.strftime("%Y-%m-%d"),
                limit=5
            )

            if hasattr(macd_result, 'values') and macd_result.values:
                latest_macd = macd_result.values[-1]
                macd_value = latest_macd.value
                signal_value = latest_macd.signal if hasattr(latest_macd, 'signal') else None
                histogram = latest_macd.histogram if hasattr(latest_macd, 'histogram') else None
                macd_date = datetime.fromtimestamp(latest_macd.timestamp / 1000).strftime('%Y-%m-%d')

                self.data['technical_indicators']['macd'] = {
                    'value': macd_value,
                    'signal': signal_value,
                    'histogram': histogram,
                    'date': macd_date
                }

                print(f"  ✓ MACD: {macd_value:.2f}")
                if signal_value:
                    print(f"  ✓ Signal: {signal_value:.2f}")
                if histogram:
                    print(f"  ✓ Histogram: {histogram:.2f}")
        except Exception as e:
            print(f"  ✗ MACD Error: {e}")

    def fetch_financials(self):
        """Fetch fundamental financial data"""
        print(f"\n{'='*80}")
        print(f"5. FETCHING FINANCIAL FUNDAMENTALS")
        print(f"{'='*80}")

        try:
            financials = []
            for fin in self.client.vx.list_stock_financials(ticker=self.ticker, limit=4):
                fin_data = {
                    'fiscal_period': fin.fiscal_period if hasattr(fin, 'fiscal_period') else 'N/A',
                    'fiscal_year': fin.fiscal_year if hasattr(fin, 'fiscal_year') else 'N/A',
                    'filing_date': fin.filing_date if hasattr(fin, 'filing_date') else 'N/A',
                }

                if hasattr(fin, 'financials'):
                    f = fin.financials

                    # Income statement
                    if hasattr(f, 'income_statement') and f.income_statement:
                        inc = f.income_statement
                        if hasattr(inc, 'revenues') and inc.revenues:
                            fin_data['revenue'] = inc.revenues.value
                        if hasattr(inc, 'net_income_loss') and inc.net_income_loss:
                            fin_data['net_income'] = inc.net_income_loss.value
                        if hasattr(inc, 'gross_profit') and inc.gross_profit:
                            fin_data['gross_profit'] = inc.gross_profit.value

                    # Balance sheet
                    if hasattr(f, 'balance_sheet') and f.balance_sheet:
                        bs = f.balance_sheet
                        if hasattr(bs, 'assets') and bs.assets:
                            fin_data['total_assets'] = bs.assets.value
                        if hasattr(bs, 'liabilities') and bs.liabilities:
                            fin_data['total_liabilities'] = bs.liabilities.value
                        if hasattr(bs, 'equity') and bs.equity:
                            fin_data['equity'] = bs.equity.value

                    # Cash flow
                    if hasattr(f, 'cash_flow_statement') and f.cash_flow_statement:
                        cf = f.cash_flow_statement
                        if hasattr(cf, 'net_cash_flow_from_operating_activities') and cf.net_cash_flow_from_operating_activities:
                            fin_data['operating_cash_flow'] = cf.net_cash_flow_from_operating_activities.value

                financials.append(fin_data)

            self.data['financials'] = financials

            if financials:
                print(f"\n✓ Fetched {len(financials)} financial reports")
                latest = financials[0]
                print(f"\nLatest Report ({latest.get('fiscal_period', 'N/A')} {latest.get('fiscal_year', 'N/A')}):")
                if 'revenue' in latest:
                    print(f"  ✓ Revenue: ${latest['revenue']:,.0f}")
                if 'net_income' in latest:
                    print(f"  ✓ Net Income: ${latest['net_income']:,.0f}")
                    if 'revenue' in latest and latest['revenue'] > 0:
                        margin = (latest['net_income'] / latest['revenue']) * 100
                        print(f"  ✓ Net Margin: {margin:.2f}%")
                if 'total_assets' in latest:
                    print(f"  ✓ Total Assets: ${latest['total_assets']:,.0f}")
                if 'operating_cash_flow' in latest:
                    print(f"  ✓ Operating Cash Flow: ${latest['operating_cash_flow']:,.0f}")

        except Exception as e:
            print(f"\n✗ Error fetching financials: {e}")
            import traceback
            traceback.print_exc()

    def fetch_options_chain(self):
        """Fetch options chain data with detailed Greeks/IV for ITM options"""
        print(f"\n{'='*80}")
        print(f"6. FETCHING OPTIONS CHAIN DATA")
        print(f"{'='*80}")

        try:
            # Get current price to identify ITM options
            current_price = None
            if self.data['current_snapshot'] and self.data['current_snapshot']['current_price']:
                current_price = self.data['current_snapshot']['current_price']
            elif self.data['historical_bars']:
                current_price = self.data['historical_bars'][-1]['close']

            print(f"\nCurrent stock price: ${current_price:.2f}")
            print(f"Fetching options chain snapshot for {self.ticker}...")

            options_chain = []

            # First pass: Get bulk options data
            for snap in self.client.list_snapshot_options_chain(
                self.ticker,
                params={"limit": 250}
            ):
                option_data = {'ticker': snap.ticker if hasattr(snap, 'ticker') else None}

                # Get details from the snapshot
                if hasattr(snap, 'details') and snap.details:
                    d = snap.details
                    option_data['strike'] = d.strike_price if hasattr(d, 'strike_price') else None
                    option_data['expiry'] = d.expiration_date if hasattr(d, 'expiration_date') else None
                    option_data['type'] = d.contract_type.upper() if hasattr(d, 'contract_type') else None
                    option_data['exercise_style'] = d.exercise_style if hasattr(d, 'exercise_style') else None

                # Day stats (price data)
                if hasattr(snap, 'day') and snap.day:
                    day = snap.day
                    option_data['day_open'] = day.open if hasattr(day, 'open') else None
                    option_data['day_high'] = day.high if hasattr(day, 'high') else None
                    option_data['day_low'] = day.low if hasattr(day, 'low') else None
                    option_data['day_close'] = day.close if hasattr(day, 'close') else None
                    option_data['volume'] = day.volume if hasattr(day, 'volume') else None
                    option_data['vwap'] = day.vwap if hasattr(day, 'vwap') else None

                # Basic Greeks/IV (may be None for many contracts)
                if hasattr(snap, 'greeks') and snap.greeks:
                    g = snap.greeks
                    option_data['delta'] = g.delta if hasattr(g, 'delta') and g.delta else None
                    option_data['gamma'] = g.gamma if hasattr(g, 'gamma') and g.gamma else None
                    option_data['theta'] = g.theta if hasattr(g, 'theta') and g.theta else None
                    option_data['vega'] = g.vega if hasattr(g, 'vega') and g.vega else None

                if hasattr(snap, 'implied_volatility') and snap.implied_volatility:
                    option_data['implied_volatility'] = snap.implied_volatility

                if hasattr(snap, 'open_interest'):
                    option_data['open_interest'] = snap.open_interest

                options_chain.append(option_data)

            print(f"\n✓ Fetched {len(options_chain)} option contracts from bulk API")

            # Second pass: Get detailed Greeks/IV for ITM call options near the money
            # (within 30% of current price where Greeks are most relevant)
            if current_price:
                print(f"\nFetching detailed Greeks/IV for ITM calls near the money...")

                itm_near_money = [
                    o for o in options_chain
                    if o.get('type') == 'CALL'
                    and o.get('strike')
                    and o.get('strike') < current_price
                    and o.get('strike') >= current_price * 0.70  # Within 30% ITM
                    and o.get('ticker')
                ]

                print(f"   Found {len(itm_near_money)} ITM calls to enhance (strike ${current_price*0.70:.0f}-${current_price:.0f})")

                enhanced = 0
                for option in itm_near_money[:100]:  # Limit to avoid rate limits
                    try:
                        # Get detailed snapshot with Greeks
                        detailed_snap = self.client.get_snapshot_option(self.ticker, option['ticker'])

                        # Update Greeks if available
                        if hasattr(detailed_snap, 'greeks') and detailed_snap.greeks:
                            g = detailed_snap.greeks
                            if hasattr(g, 'delta') and g.delta is not None:
                                option['delta'] = g.delta
                            if hasattr(g, 'gamma') and g.gamma is not None:
                                option['gamma'] = g.gamma
                            if hasattr(g, 'theta') and g.theta is not None:
                                option['theta'] = g.theta
                            if hasattr(g, 'vega') and g.vega is not None:
                                option['vega'] = g.vega

                        # Update IV if available
                        if hasattr(detailed_snap, 'implied_volatility') and detailed_snap.implied_volatility is not None:
                            option['implied_volatility'] = detailed_snap.implied_volatility

                        enhanced += 1

                    except Exception as e:
                        # Skip if individual fetch fails
                        continue

                print(f"   ✓ Enhanced {enhanced} options with detailed Greeks/IV")

            self.data['options_chain'] = options_chain

            # Summary stats
            calls = [o for o in options_chain if o.get('type') == 'CALL']
            puts = [o for o in options_chain if o.get('type') == 'PUT']
            with_greeks = [o for o in options_chain if o.get('delta') is not None]
            with_iv = [o for o in options_chain if o.get('implied_volatility') is not None]

            print(f"\n✓ Final Summary:")
            print(f"   Total contracts: {len(options_chain)}")
            print(f"   Calls: {len(calls)}, Puts: {len(puts)}")
            print(f"   With Greeks: {len(with_greeks)}")
            print(f"   With IV: {len(with_iv)}")

        except Exception as e:
            print(f"\n✗ Error fetching options chain: {e}")
            import traceback
            traceback.print_exc()

    def analyze_itm_calls(self):
        """Analyze In-The-Money call options"""
        print(f"\n{'='*80}")
        print(f"7. ANALYZING ITM CALL OPTIONS")
        print(f"{'='*80}")

        if not self.data['options_chain']:
            print("\n✗ No options data available for ITM analysis")
            return

        # Get current price from options data or historical data
        current_price = None

        # Try to get from first option's underlying price
        if self.data['options_chain'] and self.data['options_chain'][0].get('underlying_price'):
            current_price = self.data['options_chain'][0]['underlying_price']

        # Fallback to last historical bar
        if not current_price and self.data['historical_bars']:
            current_price = self.data['historical_bars'][-1]['close']

        if not current_price:
            print("\n✗ Cannot determine current stock price")
            return

        print(f"\nStock Price (reference): ${current_price:.2f}")

        # All options should be calls from our fetch
        calls = self.data['options_chain']

        # Filter for ITM calls (strike < current price) with valid data
        itm_calls = []
        for call in calls:
            strike = call.get('strike')
            # Try multiple sources for option price
            option_price = call.get('last_price') or call.get('day_close') or call.get('mid_price') or call.get('day_open')

            if strike and option_price and strike < current_price:
                # Calculate intrinsic value
                intrinsic_value = current_price - strike
                call['intrinsic_value'] = intrinsic_value

                # Use the option price we found
                call['option_price'] = option_price

                # Calculate time value
                time_value = option_price - intrinsic_value
                call['time_value'] = time_value

                # Calculate % in the money
                call['percent_itm'] = ((current_price - strike) / strike) * 100

                # Calculate leverage ratio (% stock move / % option move potential)
                if option_price > 0:
                    call['leverage_ratio'] = (current_price / option_price)

                itm_calls.append(call)

        # Sort by strike price (descending - closest to current price first)
        itm_calls.sort(key=lambda x: x.get('strike', 0), reverse=True)

        self.data['itm_calls'] = itm_calls

        print(f"\n✓ Found {len(itm_calls)} ITM call options with pricing data")

        # Show top ITM calls with Greeks
        print(f"\nTop ITM Call Options (closest to current price):")
        print(f"\n{'Expiry':<12} {'Strike':<10} {'Price':<10} {'Delta':<8} {'IV':<8} {'%ITM':<8} {'Vol':<8} {'OI':<8}")
        print(f"{'-'*85}")

        for i, call in enumerate(itm_calls[:25], 1):
            expiry = call.get('expiry', 'N/A')[:10]
            strike = call.get('strike', 0)
            price = call.get('option_price', 0)
            delta = call.get('delta')
            iv = call.get('implied_volatility')
            pct_itm = call.get('percent_itm', 0)
            volume = call.get('volume', 0) or 0
            oi = call.get('open_interest', 0) or 0

            delta_str = f"{delta:.3f}" if delta is not None else "N/A"
            iv_str = f"{iv:.2f}" if iv is not None else "N/A"

            print(f"{expiry:<12} ${strike:<9.2f} ${price:<9.2f} {delta_str:<8} {iv_str:<8} {pct_itm:<7.1f}% {volume:<7} {oi:<7}")

        # Show statistics about the ITM calls
        if itm_calls:
            print(f"\n{'='*95}")
            print("ITM CALL OPTIONS SUMMARY")
            print(f"{'='*95}")

            # Group by expiration
            from collections import defaultdict
            by_expiry = defaultdict(list)
            for call in itm_calls:
                by_expiry[call.get('expiry', 'Unknown')].append(call)

            print(f"\nOptions by Expiration Date:")
            for expiry in sorted(by_expiry.keys())[:10]:
                count = len(by_expiry[expiry])
                avg_strike = sum(c.get('strike', 0) for c in by_expiry[expiry]) / count if count > 0 else 0
                total_oi = sum(c.get('open_interest', 0) or 0 for c in by_expiry[expiry])
                print(f"  {expiry[:10]}: {count:3d} contracts, Avg Strike: ${avg_strike:6.2f}, Total OI: {total_oi:,}")

            # Recommended strikes
            print(f"\nRECOMMENDED ITM STRIKES (10-15% ITM):")
            print(f"{'Strike':<10} {'Expiry':<12} {'Price':<10} {'Intrinsic':<11} {'%ITM':<8} {'OI':<8}")
            print(f"{'-'*70}")

            # Filter for 10-15% ITM
            recommended = [c for c in itm_calls if 10 <= c.get('percent_itm', 0) <= 15]
            # Sort by expiry, then by open interest
            recommended.sort(key=lambda x: (x.get('expiry', ''), -(x.get('open_interest', 0) or 0)))

            for call in recommended[:15]:
                strike = call.get('strike', 0)
                expiry = call.get('expiry', 'N/A')[:10]
                price = call.get('option_price', 0)
                intrinsic = call.get('intrinsic_value', 0)
                pct_itm = call.get('percent_itm', 0)
                oi = call.get('open_interest', 0) or 0

                print(f"${strike:<9.2f} {expiry:<12} ${price:<9.2f} ${intrinsic:<10.2f} {pct_itm:<7.1f}% {oi:<7,}")

    def save_data(self):
        """Save all collected data to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/Users/zheyuanzhao/workspace/quantlab/results/goog_analysis_{timestamp}.json"

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)

        print(f"\n✓ Data saved to: {filename}")
        return filename

    def run_full_analysis(self):
        """Run complete analysis"""
        print("\n" + "="*80)
        print("GOOGLE (GOOG) COMPREHENSIVE STOCK & OPTIONS ANALYSIS")
        print("="*80)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.fetch_ticker_details()
        self.fetch_current_snapshot()
        self.fetch_historical_data(days=90)
        self.fetch_technical_indicators()
        self.fetch_financials()
        self.fetch_options_chain()
        self.analyze_itm_calls()

        data_file = self.save_data()

        print(f"\n{'='*80}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*80}")

        return data_file


if __name__ == "__main__":
    import os
    api_key = os.getenv('POLYGON_API_KEY', 'vDr8GDaQ87Z9Mwe5IiCKzGcRP9pnO8TW')
    analyzer = GOOGAnalyzer(api_key=api_key)
    data_file = analyzer.run_full_analysis()
    print(f"\nData file: {data_file}")
    print("\nNext: Run the report generator to create a detailed research report.")
