"""
Optimized Programmatic Stock Screener for Profitable Small-Cap AI Stocks

Optimizations:
1. Uses Polygon API filtering to reduce API calls
2. Filters invalid tickers (warrants, units, preferred shares)
3. Parallel processing for faster screening
4. Better error handling and validation
"""

import os
import requests
import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class OptimizedAIScreener:
    """Optimized programmatic screener"""

    def __init__(self, min_cap=300_000_000, max_cap=5_000_000_000):
        self.min_market_cap = min_cap
        self.max_market_cap = max_cap
        self.polygon_api_key = os.getenv('POLYGON_API_KEY')
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)

    def is_valid_ticker(self, ticker: str) -> bool:
        """
        Filter out invalid tickers that don't represent common stocks

        Excludes:
        - Warrants (.WS, .W, etc.)
        - Units (.U)
        - Preferred shares (ending in letters like PD, PE, PF, etc.)
        - Class shares with dots (A.B, etc.)
        """
        ticker = ticker.upper()

        # Exclude warrants
        if '.WS' in ticker or '.W' in ticker or ticker.endswith('W'):
            return False

        # Exclude units
        if '.U' in ticker:
            return False

        # Exclude preferred shares (usually ticker + P + letter)
        # Examples: ABRPD, ABRPE, AGMPD, etc.
        if len(ticker) > 4:
            # Check for pattern like ABCPD, ABCPE (ticker + P + letter)
            if ticker[-2] == 'P' and ticker[-1].isalpha():
                return False

            # Check for pattern like AHLPD (ticker ends with P + letter)
            if ticker.endswith('PA') or ticker.endswith('PB') or ticker.endswith('PC') or \
               ticker.endswith('PD') or ticker.endswith('PE') or ticker.endswith('PF') or \
               ticker.endswith('PG') or ticker.endswith('PH') or ticker.endswith('PI') or \
               ticker.endswith('PJ') or ticker.endswith('PK') or ticker.endswith('PL'):
                return False

        # Exclude tickers with dots (class shares, foreign listings)
        if '.' in ticker:
            return False

        # Exclude tickers with hyphens (some preferred shares)
        if '-' in ticker and ticker.split('-')[1].startswith('P'):
            return False

        return True

    def discover_ai_tickers_optimized(self) -> List[str]:
        """
        Optimized discovery using Polygon API with market cap filtering

        Since you have unlimited API access, we can:
        1. Filter by market cap directly in API
        2. Use type='CS' for common stocks only
        3. Paginate efficiently
        """
        if not self.polygon_api_key:
            print("⚠️  Polygon API key not found.")
            return []

        print("\n🔍 Discovering AI stocks from Polygon API (OPTIMIZED)...")

        # AI-related SIC codes
        ai_sic_codes = [
            '7370',  # Computer Programming, Data Processing
            '7371',  # Computer Programming Services
            '7372',  # Prepackaged Software
            '7373',  # Computer Integrated Systems Design
            '7374',  # Computer Processing And Data Preparation
            '3674',  # Semiconductors And Related Devices
            '3577',  # Computer Peripheral Equipment
            '8731',  # Commercial Physical And Biological Research
        ]

        all_tickers = set()

        for sic in ai_sic_codes:
            print(f"  Fetching SIC {sic}...", end=" ")
            tickers = self._get_tickers_by_sic_optimized(sic)

            # Filter invalid tickers
            valid_tickers = [t for t in tickers if self.is_valid_ticker(t)]
            all_tickers.update(valid_tickers)

            print(f"✅ {len(valid_tickers)} valid tickers (filtered {len(tickers) - len(valid_tickers)} invalid)")

        print(f"\n✅ Total unique valid tickers discovered: {len(all_tickers)}")
        return list(all_tickers)

    def _get_tickers_by_sic_optimized(self, sic_code: str) -> List[str]:
        """
        Optimized ticker fetch with market cap filtering at API level

        Uses Polygon API parameters:
        - type: 'CS' (Common Stock only)
        - market_cap.gte/lte: Filter by market cap
        - active: true
        """
        endpoint = "https://api.polygon.io/v3/reference/tickers"

        params = {
            'sic_code': sic_code,
            'type': 'CS',  # Common Stock only (excludes warrants, units, etc.)
            'market': 'stocks',
            'active': 'true',
            'market_cap.gte': self.min_market_cap,
            'market_cap.lte': self.max_market_cap,
            'limit': 1000,
            'apiKey': self.polygon_api_key
        }

        tickers = []

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get('results', [])
            tickers = [r['ticker'] for r in results if 'ticker' in r]

            # Handle pagination if next_url exists
            next_url = data.get('next_url')
            while next_url and len(tickers) < 1000:  # Limit to prevent infinite loops
                response = requests.get(next_url, params={'apiKey': self.polygon_api_key})
                response.raise_for_status()
                data = response.json()

                results = data.get('results', [])
                tickers.extend([r['ticker'] for r in results if 'ticker' in r])

                next_url = data.get('next_url')

        except Exception as e:
            print(f"Error: {str(e)[:50]}")

        return tickers

    def check_profitability_from_financials(self, ticker: str) -> Dict:
        """Check profitability using actual financial statements"""
        try:
            stock = yf.Ticker(ticker)
            income_stmt = stock.income_stmt

            if income_stmt is None or income_stmt.empty:
                return {
                    'is_profitable': None,
                    'reason': 'No financial data',
                    'net_income': None,
                    'net_margin': None
                }

            # Get Net Income
            if 'Net Income' in income_stmt.index:
                latest_net_income = income_stmt.loc['Net Income'].iloc[0]
            elif 'Net Income From Continuing Operations' in income_stmt.index:
                latest_net_income = income_stmt.loc['Net Income From Continuing Operations'].iloc[0]
            else:
                return {
                    'is_profitable': None,
                    'reason': 'Net Income not found',
                    'net_income': None,
                    'net_margin': None
                }

            # Get Revenue
            if 'Total Revenue' in income_stmt.index:
                revenue = income_stmt.loc['Total Revenue'].iloc[0]
                net_margin = (latest_net_income / revenue) * 100 if revenue else None
            else:
                net_margin = None

            is_profitable = latest_net_income > 0 if latest_net_income is not None else None

            return {
                'is_profitable': is_profitable,
                'net_income': float(latest_net_income) if latest_net_income is not None else None,
                'net_margin': float(net_margin) if net_margin is not None else None,
                'reason': f'Net Income: ${latest_net_income:,.0f}' if latest_net_income is not None else 'Unknown'
            }

        except Exception as e:
            return {
                'is_profitable': None,
                'reason': f'Error: {str(e)[:30]}',
                'net_income': None,
                'net_margin': None
            }

    def get_stock_fundamentals(self, ticker: str) -> Optional[Dict]:
        """Get stock fundamentals with profitability check"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            market_cap = info.get('marketCap', 0)
            if market_cap == 0:
                return None

            # Get profitability from financials
            profitability = self.check_profitability_from_financials(ticker)

            return {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', ticker)),
                'market_cap': market_cap,
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'is_profitable': profitability['is_profitable'],
                'net_income': profitability['net_income'],
                'net_margin': profitability['net_margin'],
                'profitability_reason': profitability['reason'],
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'pe_ratio': info.get('trailingPE'),
                'revenue': info.get('totalRevenue'),
                'revenue_growth': info.get('revenueGrowth'),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return None

    def screen_ticker(self, ticker: str, verbose: bool = True) -> Optional[Dict]:
        """Screen a single ticker (for parallel processing)"""
        if verbose:
            print(f"Screening {ticker:6s}...", end=" ", flush=True)

        data = self.get_stock_fundamentals(ticker)

        if not data:
            if verbose:
                print("❌ No data")
            return None

        market_cap = data['market_cap']

        # Market cap already filtered at API level, but double-check
        if market_cap < self.min_market_cap or market_cap > self.max_market_cap:
            if verbose:
                print(f"❌ Out of range")
            return None

        # Check profitability
        if data['is_profitable'] is None:
            if verbose:
                print(f"⚠️  No financial data")
            return None

        if not data['is_profitable']:
            if verbose:
                net_income = data['net_income']
                print(f"❌ Not profitable (Net Income: ${net_income/1e6:.1f}M)")
            return None

        # Passed all filters
        cap_str = f"${market_cap/1e9:.2f}B" if market_cap >= 1e9 else f"${market_cap/1e6:.0f}M"
        margin_str = f" | Margin: {data['net_margin']:.1f}%" if data['net_margin'] else ""
        if verbose:
            print(f"✅ {cap_str}{margin_str}")

        return data

    def screen_parallel(self, tickers: List[str], max_workers: int = 10, verbose: bool = True) -> pd.DataFrame:
        """
        Screen tickers in parallel for better performance

        Args:
            tickers: List of tickers to screen
            max_workers: Number of parallel threads (default 10)
            verbose: Print progress
        """
        print(f"\n📊 Screening {len(tickers)} tickers (parallel with {max_workers} workers)...")
        print("="*80 + "\n")

        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(self.screen_ticker, ticker, verbose): ticker
                for ticker in sorted(tickers)
            }

            # Collect results as they complete
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result()
                    if data:
                        results.append(data)
                except Exception as e:
                    if verbose:
                        print(f"Error screening {ticker}: {str(e)[:50]}")

        df = pd.DataFrame(results)

        if not df.empty:
            df = df.sort_values('market_cap', ascending=False)

            # Save results
            output_file = self.data_dir / f"screened_stocks_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(output_file, index=False)

            print(f"\n✅ Found {len(df)} profitable small-cap AI stocks")
            print(f"✅ Saved to: {output_file}")

        return df

    def screen(self, max_workers: int = 10, verbose: bool = True) -> pd.DataFrame:
        """
        Run optimized screening

        Args:
            max_workers: Number of parallel threads (increase for faster processing)
            verbose: Print progress
        """
        if verbose:
            print("\n" + "="*80)
            print("OPTIMIZED PROGRAMMATIC AI STOCK SCREENER")
            print("="*80)
            print(f"Market Cap Range: ${self.min_market_cap/1e6:.0f}M - ${self.max_market_cap/1e9:.1f}B")
            print(f"Parallel Workers: {max_workers}")
            print("="*80)

        # Discover tickers (already filtered by market cap at API level)
        tickers = self.discover_ai_tickers_optimized()

        if not tickers:
            print("\n❌ No tickers discovered. Check API access.")
            return pd.DataFrame()

        # Screen in parallel
        df = self.screen_parallel(tickers, max_workers=max_workers, verbose=verbose)

        return df

    def get_summary_stats(self, df: pd.DataFrame) -> Dict:
        """Get summary statistics"""
        if df.empty:
            return {}

        return {
            'total_stocks': len(df),
            'avg_market_cap': df['market_cap'].mean(),
            'median_market_cap': df['market_cap'].median(),
            'avg_net_margin': df[df['net_margin'].notna()]['net_margin'].mean(),
            'avg_pe_ratio': df[df['pe_ratio'].notna()]['pe_ratio'].mean(),
            'sectors': df['sector'].value_counts().to_dict(),
            'industries': df['industry'].value_counts().to_dict()
        }


def main():
    """Run optimized screener"""
    screener = OptimizedAIScreener(
        min_cap=300_000_000,   # $300M
        max_cap=5_000_000_000  # $5B
    )

    # Run screening with parallel processing (20 workers for unlimited API)
    df = screener.screen(max_workers=20, verbose=True)

    if not df.empty:
        stats = screener.get_summary_stats(df)

        print("\n" + "="*80)
        print("SUMMARY STATISTICS")
        print("="*80)
        print(f"Total stocks found: {stats['total_stocks']}")
        print(f"Average market cap: ${stats['avg_market_cap']/1e9:.2f}B")
        print(f"Median market cap: ${stats['median_market_cap']/1e9:.2f}B")

        if stats['avg_net_margin']:
            print(f"Average net margin: {stats['avg_net_margin']:.2f}%")
        if stats['avg_pe_ratio']:
            print(f"Average P/E ratio: {stats['avg_pe_ratio']:.1f}")

        print("\nTop Sectors:")
        for sector, count in list(stats['sectors'].items())[:5]:
            print(f"  - {sector}: {count}")

        print("="*80)

        # Display top stocks
        print("\n" + "="*80)
        print("TOP PROFITABLE STOCKS (by Market Cap)")
        print("="*80)
        top_stocks = df.head(10)[['ticker', 'name', 'market_cap', 'net_margin', 'pe_ratio']]

        for idx, row in top_stocks.iterrows():
            cap_str = f"${row['market_cap']/1e9:.2f}B" if row['market_cap'] >= 1e9 else f"${row['market_cap']/1e6:.0f}M"
            margin_str = f"{row['net_margin']:.1f}%" if pd.notna(row['net_margin']) else "N/A"
            pe_str = f"{row['pe_ratio']:.1f}" if pd.notna(row['pe_ratio']) else "N/A"

            print(f"\n{row['ticker']:6s} - {row['name'][:50]}")
            print(f"        Market Cap: {cap_str} | Net Margin: {margin_str} | P/E: {pe_str}")


if __name__ == "__main__":
    main()
