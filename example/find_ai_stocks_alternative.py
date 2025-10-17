"""
Find Small Cap Profitable AI Stocks - Alternative Approach

Uses a combination of:
1. Known AI-related tickers
2. Yahoo Finance for financial data (free, no API key needed)
3. Manual filtering for small-cap range
"""

import yfinance as yf
from typing import List, Dict
import pandas as pd


class AIStockScreener:
    """Screen for profitable small-cap AI stocks"""

    def __init__(self):
        # Small cap range: $300M - $2B
        self.min_market_cap = 300_000_000
        self.max_market_cap = 2_000_000_000

        # Curated list of AI/ML/Data Analytics companies
        # This includes known AI players across different market caps
        self.ai_tickers = [
            # AI Software & Platforms
            'AI', 'BBAI', 'SOUN', 'BFRG', 'PATH', 'UPST', 'LMND',
            'INTA', 'CWAN', 'ALTR', 'AMBA', 'EXLS', 'DT', 'SMCI',

            # Computer Vision & Imaging
            'AMBA', 'KOPN', 'VUZI', 'INVZ', 'OUST', 'LAZR', 'VLDR',

            # Robotics & Automation
            'IRBT', 'BLDE', 'ISRG', 'TER',

            # Data Analytics & Cloud AI
            'DOMO', 'ESTC', 'SUMO', 'FSLY', 'CFLT', 'NET', 'SNOW',
            'DDOG', 'S', 'MDB', 'FROG', 'DLO',

            # Semiconductor AI (edge AI, neural chips)
            'NVDA', 'AMD', 'INTC', 'QCOM', 'XLNX', 'LSCC', 'FORM',
            'LITE', 'RMBS', 'CRUS', 'SMTC',

            # Healthcare AI
            'TDOC', 'HIMS', 'DOCS', 'GDRX', 'SDGR', 'VCYT',

            # Cybersecurity AI
            'PANW', 'CRWD', 'ZS', 'FTNT', 'S', 'TENB', 'RPD',

            # Edge AI & IoT
            'SYNA', 'SWKS', 'QRVO', 'SLAB', 'ALKT',

            # Conversational AI / NLP
            'NICE', 'VEEV', 'TWLO', 'BAND',

            # MLOps & AI Infrastructure
            'ESTC', 'SPLK', 'DDOG', 'DT', 'GTLB',

            # Emerging AI Players
            'SOUN', 'AI', 'BBAI', 'BFRG', 'RSKD', 'EZFL'
        ]

        # Remove duplicates
        self.ai_tickers = list(set(self.ai_tickers))

    def get_stock_data(self, ticker: str) -> Dict:
        """Get stock data from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get financial data
            market_cap = info.get('marketCap', 0)

            # Profitability metrics
            net_income = info.get('netIncomeToCommon')
            profit_margin = info.get('profitMargins')
            trailing_eps = info.get('trailingEps')

            # Determine if profitable
            is_profitable = False
            if net_income and net_income > 0:
                is_profitable = True
            elif trailing_eps and trailing_eps > 0:
                is_profitable = True
            elif profit_margin and profit_margin > 0:
                is_profitable = True

            return {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', ticker)),
                'market_cap': market_cap,
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'net_income': net_income,
                'profit_margin': profit_margin,
                'trailing_eps': trailing_eps,
                'forward_eps': info.get('forwardEps'),
                'revenue_growth': info.get('revenueGrowth'),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'is_profitable': is_profitable,
                'description': info.get('longBusinessSummary', 'N/A')[:200] + '...' if info.get('longBusinessSummary') else 'N/A'
            }

        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def screen_stocks(self) -> List[Dict]:
        """Screen for profitable small-cap AI stocks"""
        print("\n" + "="*80)
        print("SCREENING FOR PROFITABLE SMALL-CAP AI STOCKS")
        print("="*80)
        print(f"Market Cap Range: ${self.min_market_cap/1e6:.0f}M - ${self.max_market_cap/1e9:.1f}B")
        print(f"Analyzing {len(self.ai_tickers)} AI-related tickers...")
        print("="*80 + "\n")

        results = []

        for ticker in self.ai_tickers:
            print(f"Checking {ticker}...", end=" ")

            data = self.get_stock_data(ticker)

            if not data:
                print("❌ Error")
                continue

            market_cap = data['market_cap']

            # Check if in small-cap range
            if market_cap < self.min_market_cap:
                print(f"❌ Too small (${market_cap/1e6:.0f}M)")
                continue

            if market_cap > self.max_market_cap:
                print(f"❌ Too large (${market_cap/1e9:.2f}B)")
                continue

            # Check if profitable
            if not data['is_profitable']:
                print(f"❌ Not profitable")
                continue

            print(f"✅ MATCH! ${market_cap/1e6:.0f}M")
            results.append(data)

        return results

    def print_results(self, results: List[Dict]):
        """Print results in formatted way"""
        print("\n" + "="*80)
        print("PROFITABLE SMALL-CAP AI STOCKS")
        print("="*80 + "\n")

        if not results:
            print("No profitable small-cap AI stocks found in the analyzed list.")
            print("\nTry expanding the market cap range or adding more tickers to the list.")
            return

        # Sort by market cap
        results = sorted(results, key=lambda x: x['market_cap'], reverse=True)

        for i, stock in enumerate(results, 1):
            market_cap_b = stock['market_cap'] / 1e9
            market_cap_m = stock['market_cap'] / 1e6

            if market_cap_b >= 1:
                cap_str = f"${market_cap_b:.2f}B"
            else:
                cap_str = f"${market_cap_m:.0f}M"

            print(f"\n{i}. {stock['ticker']} - {stock['name']}")
            print(f"   {'─'*76}")
            print(f"   Market Cap: {cap_str}")
            print(f"   Industry: {stock['industry']}")
            print(f"   Current Price: ${stock['current_price']:.2f}" if stock['current_price'] else "   Price: N/A")

            # Financial metrics
            if stock['profit_margin']:
                print(f"   Profit Margin: {stock['profit_margin']*100:.2f}%")
            if stock['trailing_eps']:
                print(f"   Trailing EPS: ${stock['trailing_eps']:.2f}")
            if stock['revenue_growth']:
                print(f"   Revenue Growth: {stock['revenue_growth']*100:.1f}%")

            print(f"   Description: {stock['description']}")

    def export_to_csv(self, results: List[Dict], filename='profitable_smallcap_ai.csv'):
        """Export results to CSV"""
        if not results:
            print("No results to export.")
            return

        df = pd.DataFrame(results)

        # Select and order columns
        columns = [
            'ticker', 'name', 'market_cap', 'current_price',
            'trailing_eps', 'profit_margin', 'revenue_growth',
            'industry', 'sector'
        ]

        df = df[columns]
        df.to_csv(filename, index=False)
        print(f"\n✅ Results exported to {filename}")


def main():
    """Main execution"""
    screener = AIStockScreener()

    # Screen for stocks
    results = screener.screen_stocks()

    # Print results
    screener.print_results(results)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total tickers analyzed: {len(screener.ai_tickers)}")
    print(f"Profitable small-cap AI stocks found: {len(results)}")

    if results:
        total_market_cap = sum(r['market_cap'] for r in results)
        avg_market_cap = total_market_cap / len(results)
        print(f"Average market cap: ${avg_market_cap/1e9:.2f}B")

        profitable_with_margin = [r for r in results if r['profit_margin'] and r['profit_margin'] > 0]
        if profitable_with_margin:
            avg_margin = sum(r['profit_margin'] for r in profitable_with_margin) / len(profitable_with_margin)
            print(f"Average profit margin: {avg_margin*100:.2f}%")

    print("="*80)

    # Export to CSV
    if results:
        screener.export_to_csv(results, 'example/profitable_smallcap_ai.csv')


if __name__ == "__main__":
    main()
