"""
Find Profitable AI Stocks - Expanded Search
Includes small to mid-cap range for better results
"""

import yfinance as yf
from typing import List, Dict
import pandas as pd


class ExpandedAIStockScreener:
    """Screen for profitable AI stocks with expanded criteria"""

    def __init__(self, min_cap=300_000_000, max_cap=5_000_000_000):
        self.min_market_cap = min_cap  # $300M default
        self.max_market_cap = max_cap  # $5B default (expanded from $2B)

        # Expanded list of AI companies
        self.ai_tickers = [
            # Pure-play AI platforms
            'AI', 'BBAI', 'SOUN', 'BFRG', 'RSKD',

            # AI Software & SaaS
            'PATH', 'UPST', 'LMND', 'INTA', 'CWAN', 'ALTR', 'DT', 'FROG',
            'DOMO', 'ESTC', 'SUMO', 'CFLT', 'S', 'DLO',

            # Computer Vision & Imaging
            'AMBA', 'KOPN', 'VUZI', 'INVZ', 'OUST', 'LAZR', 'VLDR', 'MGNI',

            # Robotics & Automation
            'IRBT', 'BLDE', 'TER', 'KRNT', 'PL', 'RNG',

            # Semiconductor AI
            'LSCC', 'FORM', 'LITE', 'RMBS', 'CRUS', 'SMTC', 'SYNA',
            'SWKS', 'QRVO', 'SLAB', 'ALKT', 'MCHP', 'NXPI',

            # Healthcare AI & Digital Health
            'TDOC', 'HIMS', 'DOCS', 'GDRX', 'SDGR', 'VCYT', 'PRCT',
            'ACCD', 'SDGR', 'PHR', 'ONEM', 'LFST',

            # Cybersecurity AI
            'PANW', 'CRWD', 'ZS', 'FTNT', 'TENB', 'RPD', 'QLYS',
            'VRNS', 'FSLY', 'AKAM', 'CHKP', 'CYBR', 'SAIL',

            # Edge AI & IoT
            'GRMN', 'WOLF', 'PSTG', 'SPLK',

            # Conversational AI / NLP
            'NICE', 'VEEV', 'TWLO', 'BAND', 'RNG', 'ASAN',

            # Data Analytics & Cloud
            'DDOG', 'SNOW', 'MDB', 'NET', 'GTLB', 'DBX',

            # MLOps & AI Infrastructure
            'ESTC', 'DDOG', 'PSTG', 'WK',

            # Marketing/Advertising AI
            'MGNI', 'TTD', 'APPS', 'PUBM', 'RAMP',

            # Voice/Audio AI
            'SOUN', 'LSCC', 'TTD',

            # Chip Design/EDA with AI
            'SNPS', 'CDNS', 'ANSS',

            # Enterprise AI
            'NOW', 'WDAY', 'CRM', 'TEAM', 'ZM',

            # Fintech AI
            'UPST', 'AFRM', 'SOFI', 'NU', 'HOOD',

            # Additional
            'EXLS', 'SMCI', 'WIX', 'YEXT', 'EPAM', 'GLOB', 'FICO',
            'APPN', 'PCTY', 'MNDY', 'ZI', 'BILL', 'SQ', 'DOCN',
            'APP', 'BRZE', 'FOUR', 'AYX', 'CLBT', 'ALIT'
        ]

        # Remove duplicates
        self.ai_tickers = list(set(self.ai_tickers))

    def get_stock_data(self, ticker: str) -> Dict:
        """Get stock data from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            market_cap = info.get('marketCap', 0)
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
                'fifty_day_avg': info.get('fiftyDayAverage'),
                'two_hundred_day_avg': info.get('twoHundredDayAverage'),
                'pe_ratio': info.get('trailingPE'),
                'is_profitable': is_profitable,
                'description': info.get('longBusinessSummary', 'N/A')[:250] + '...' if info.get('longBusinessSummary') else 'N/A'
            }

        except Exception as e:
            print(f"Error fetching {ticker}: {str(e)[:50]}")
            return None

    def screen_stocks(self) -> List[Dict]:
        """Screen for profitable AI stocks"""
        min_cap_str = f"${self.min_market_cap/1e6:.0f}M" if self.min_market_cap < 1e9 else f"${self.min_market_cap/1e9:.1f}B"
        max_cap_str = f"${self.max_market_cap/1e9:.1f}B"

        print("\n" + "="*80)
        print("SCREENING FOR PROFITABLE AI STOCKS")
        print("="*80)
        print(f"Market Cap Range: {min_cap_str} - {max_cap_str}")
        print(f"Analyzing {len(self.ai_tickers)} AI-related tickers...")
        print("="*80 + "\n")

        results = []

        for ticker in sorted(self.ai_tickers):
            print(f"Checking {ticker:6s}...", end=" ")

            data = self.get_stock_data(ticker)

            if not data:
                print("❌ Error")
                continue

            market_cap = data['market_cap']

            if market_cap < self.min_market_cap:
                print(f"❌ Too small (${market_cap/1e6:.0f}M)")
                continue

            if market_cap > self.max_market_cap:
                print(f"❌ Too large (${market_cap/1e9:.2f}B)")
                continue

            if not data['is_profitable']:
                print(f"❌ Not profitable")
                continue

            cap_str = f"${market_cap/1e9:.2f}B" if market_cap >= 1e9 else f"${market_cap/1e6:.0f}M"
            margin_str = f" | Margin: {data['profit_margin']*100:.1f}%" if data['profit_margin'] else ""
            print(f"✅ {cap_str}{margin_str}")
            results.append(data)

        return results

    def print_results(self, results: List[Dict], top_n=None):
        """Print results in formatted way"""
        print("\n" + "="*80)
        print("PROFITABLE AI STOCKS")
        print("="*80 + "\n")

        if not results:
            print("No profitable AI stocks found in the analyzed list.")
            return

        # Sort by market cap
        results = sorted(results, key=lambda x: x['market_cap'], reverse=True)

        display_results = results[:top_n] if top_n else results

        for i, stock in enumerate(display_results, 1):
            market_cap_b = stock['market_cap'] / 1e9
            market_cap_m = stock['market_cap'] / 1e6

            cap_str = f"${market_cap_b:.2f}B" if market_cap_b >= 1 else f"${market_cap_m:.0f}M"

            print(f"\n{i}. {stock['ticker']} - {stock['name']}")
            print(f"   {'─'*76}")
            print(f"   💰 Market Cap: {cap_str} | Industry: {stock['industry']}")

            if stock['current_price']:
                price_str = f"${stock['current_price']:.2f}"
                if stock['fifty_day_avg']:
                    vs_50d = ((stock['current_price'] / stock['fifty_day_avg']) - 1) * 100
                    price_str += f" (50-day: {vs_50d:+.1f}%)"
                print(f"   📈 Price: {price_str}")

            # Financial metrics
            metrics = []
            if stock['profit_margin']:
                metrics.append(f"Profit Margin: {stock['profit_margin']*100:.2f}%")
            if stock['trailing_eps']:
                metrics.append(f"EPS: ${stock['trailing_eps']:.2f}")
            if stock['pe_ratio']:
                metrics.append(f"P/E: {stock['pe_ratio']:.1f}")
            if stock['revenue_growth']:
                metrics.append(f"Rev Growth: {stock['revenue_growth']*100:.1f}%")

            if metrics:
                print(f"   📊 {' | '.join(metrics)}")

            # Trim description
            desc = stock['description']
            if len(desc) > 150:
                desc = desc[:150] + "..."
            print(f"   📝 {desc}")

    def export_to_csv(self, results: List[Dict], filename='example/profitable_ai_stocks.csv'):
        """Export results to CSV"""
        if not results:
            print("No results to export.")
            return

        df = pd.DataFrame(results)

        columns = [
            'ticker', 'name', 'market_cap', 'current_price',
            'trailing_eps', 'pe_ratio', 'profit_margin', 'revenue_growth',
            'industry', 'sector'
        ]

        df = df[[c for c in columns if c in df.columns]]
        df = df.sort_values('market_cap', ascending=False)
        df.to_csv(filename, index=False)
        print(f"\n✅ Results exported to {filename}")


def main():
    """Main execution"""

    # Create screener with expanded range: $300M - $5B
    screener = ExpandedAIStockScreener(
        min_cap=300_000_000,    # $300M
        max_cap=5_000_000_000   # $5B (includes mid-cap)
    )

    # Screen for stocks
    results = screener.screen_stocks()

    # Print results
    screener.print_results(results, top_n=20)  # Show top 20

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total tickers analyzed: {len(screener.ai_tickers)}")
    print(f"Profitable AI stocks found: {len(results)}")

    if results:
        total_market_cap = sum(r['market_cap'] for r in results)
        avg_market_cap = total_market_cap / len(results)
        print(f"Average market cap: ${avg_market_cap/1e9:.2f}B")

        profitable_with_margin = [r for r in results if r['profit_margin'] and r['profit_margin'] > 0]
        if profitable_with_margin:
            avg_margin = sum(r['profit_margin'] for r in profitable_with_margin) / len(profitable_with_margin)
            print(f"Average profit margin: {avg_margin*100:.2f}%")

        with_pe = [r for r in results if r['pe_ratio'] and r['pe_ratio'] > 0]
        if with_pe:
            avg_pe = sum(r['pe_ratio'] for r in with_pe) / len(with_pe)
            print(f"Average P/E ratio: {avg_pe:.1f}")

    print("="*80)

    # Export
    if results:
        screener.export_to_csv(results)


if __name__ == "__main__":
    main()
