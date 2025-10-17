"""
Find Small Cap AI Stocks with Profitability

This script identifies small-cap AI/tech companies that are currently profitable.
Uses Polygon API for ticker data and financial information.
"""

import os
import requests
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
import time

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class ProfitableSmallCapAIFinder:
    """Find profitable small-cap AI stocks"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError("Polygon API key not found.")

        self.base_url = "https://api.polygon.io"

        # Define small cap range: $300M - $2B market cap
        self.min_market_cap = 300_000_000  # $300M
        self.max_market_cap = 2_000_000_000  # $2B

    def get_all_tickers(self, market_cap_min=None, market_cap_max=None, limit=1000):
        """
        Get all stock tickers with market cap filtering

        Args:
            market_cap_min: Minimum market cap
            market_cap_max: Maximum market cap
            limit: Number of results per page

        Returns:
            List of ticker data
        """
        endpoint = f"{self.base_url}/v3/reference/tickers"

        params = {
            'apiKey': self.api_key,
            'market': 'stocks',
            'active': 'true',
            'limit': limit,
            'sort': 'market_cap',
            'order': 'desc'
        }

        if market_cap_min:
            params['market_cap.gte'] = market_cap_min
        if market_cap_max:
            params['market_cap.lte'] = market_cap_max

        all_results = []
        next_url = None

        try:
            while True:
                if next_url:
                    response = requests.get(next_url, params={'apiKey': self.api_key})
                else:
                    response = requests.get(endpoint, params=params)

                response.raise_for_status()
                data = response.json()

                results = data.get('results', [])
                all_results.extend(results)

                print(f"Fetched {len(results)} tickers... (Total: {len(all_results)})")

                # Check for next page
                next_url = data.get('next_url')
                if not next_url:
                    break

                # Rate limiting - be conservative
                time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching tickers: {e}")

        return all_results

    def get_ticker_details(self, ticker: str) -> Dict:
        """Get detailed information about a ticker"""
        endpoint = f"{self.base_url}/v3/reference/tickers/{ticker.upper()}"
        params = {'apiKey': self.api_key}

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json().get('results', {})
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {ticker} details: {e}")
            return {}

    def is_ai_related(self, ticker_data: Dict) -> bool:
        """
        Check if company is AI-related based on name, description, and industry

        Args:
            ticker_data: Ticker information dictionary

        Returns:
            True if AI-related, False otherwise
        """
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning',
            'neural network', 'computer vision', 'nlp', 'natural language',
            'robotics', 'automation', 'intelligent', 'cognitive', 'data analytics',
            'predictive analytics', 'big data', 'cloud ai', 'ai platform',
            'conversational ai', 'chatbot', 'llm', 'generative ai', 'genai'
        ]

        # Check name
        name = ticker_data.get('name', '').lower()

        # Check description (if available)
        description = ticker_data.get('description', '').lower()

        # Check SIC description
        sic_desc = ticker_data.get('sic_description', '').lower()

        # Combined text to search
        search_text = f"{name} {description} {sic_desc}"

        # Check for AI keywords
        for keyword in ai_keywords:
            if keyword in search_text:
                return True

        return False

    def get_financials(self, ticker: str) -> Dict:
        """
        Get financial data for a ticker
        Note: This endpoint may require higher tier Polygon subscription
        """
        endpoint = f"{self.base_url}/vX/reference/financials"
        params = {
            'apiKey': self.api_key,
            'ticker': ticker.upper(),
            'limit': 1,
            'sort': 'period_of_report_date',
            'order': 'desc'
        }

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            results = response.json().get('results', [])
            return results[0] if results else {}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching financials for {ticker}: {e}")
            return {}

    def is_profitable(self, ticker: str, ticker_data: Dict) -> Optional[bool]:
        """
        Check if company is profitable

        For free tier, we'll use available data from ticker details.
        Premium tier can use get_financials() for detailed P&L data.
        """
        # Try to get financial data (may not be available on free tier)
        financials = self.get_financials(ticker)

        if financials:
            income_statement = financials.get('financials', {}).get('income_statement', {})
            net_income = income_statement.get('net_income_loss', {}).get('value')

            if net_income is not None:
                return net_income > 0

        # Fallback: We can't determine profitability without financial data
        # Return None to indicate unknown
        return None

    def find_profitable_smallcap_ai_stocks(self, max_results=50):
        """
        Main function to find profitable small-cap AI stocks

        Args:
            max_results: Maximum number of results to return

        Returns:
            List of matching stocks with details
        """
        print("\n" + "="*70)
        print("Searching for Profitable Small-Cap AI Stocks")
        print("="*70)
        print(f"Market Cap Range: ${self.min_market_cap/1e6:.0f}M - ${self.max_market_cap/1e9:.1f}B")
        print("="*70 + "\n")

        # Step 1: Get small-cap stocks
        print("Step 1: Fetching small-cap stocks...")
        small_cap_stocks = self.get_all_tickers(
            market_cap_min=self.min_market_cap,
            market_cap_max=self.max_market_cap
        )

        print(f"\nFound {len(small_cap_stocks)} small-cap stocks")

        # Step 2: Filter for AI-related companies
        print("\nStep 2: Filtering for AI-related companies...")
        ai_stocks = []

        for stock in small_cap_stocks:
            if self.is_ai_related(stock):
                ai_stocks.append(stock)

        print(f"Found {len(ai_stocks)} AI-related small-cap stocks")

        # Step 3: Check profitability (limited by API tier)
        print("\nStep 3: Checking profitability (may be limited by API tier)...")

        results = []
        for stock in ai_stocks[:max_results]:  # Limit to avoid rate limits
            ticker = stock.get('ticker')

            # Check profitability
            is_prof = self.is_profitable(ticker, stock)

            stock_info = {
                'ticker': ticker,
                'name': stock.get('name'),
                'market_cap': stock.get('market_cap'),
                'primary_exchange': stock.get('primary_exchange'),
                'sic_description': stock.get('sic_description'),
                'description': stock.get('description', 'N/A')[:200] + '...' if stock.get('description', '') else 'N/A',
                'profitable': is_prof,
                'currency': stock.get('currency_name', 'USD')
            }

            # Only include if profitable or profitability unknown
            if is_prof is True:
                results.append(stock_info)
                print(f"✓ {ticker} - {stock.get('name')[:40]} (Profitable)")
            elif is_prof is None:
                # Include but mark as unknown
                stock_info['profitable'] = 'Unknown'
                results.append(stock_info)
                print(f"? {ticker} - {stock.get('name')[:40]} (Profitability Unknown)")
            else:
                print(f"✗ {ticker} - {stock.get('name')[:40]} (Not Profitable)")

            # Rate limiting
            time.sleep(0.3)

        return results

    def print_results(self, results: List[Dict]):
        """Print results in a formatted way"""

        print("\n" + "="*70)
        print("PROFITABLE SMALL-CAP AI STOCKS")
        print("="*70 + "\n")

        if not results:
            print("No profitable small-cap AI stocks found with current criteria.")
            print("\nNote: Financial data may be limited on free tier API.")
            return

        for i, stock in enumerate(results, 1):
            market_cap_b = stock['market_cap'] / 1e9
            market_cap_m = stock['market_cap'] / 1e6

            if market_cap_b >= 1:
                cap_str = f"${market_cap_b:.2f}B"
            else:
                cap_str = f"${market_cap_m:.0f}M"

            profitable_status = "✓ Profitable" if stock['profitable'] is True else "? Unknown"

            print(f"{i}. {stock['ticker']} - {stock['name']}")
            print(f"   Market Cap: {cap_str}")
            print(f"   Exchange: {stock['primary_exchange']}")
            print(f"   Industry: {stock['sic_description']}")
            print(f"   Status: {profitable_status}")
            print(f"   Description: {stock['description']}")
            print()


def main():
    """Main execution"""

    finder = ProfitableSmallCapAIFinder()

    # Find profitable small-cap AI stocks
    results = finder.find_profitable_smallcap_ai_stocks(max_results=50)

    # Print formatted results
    finder.print_results(results)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total AI-related small-cap stocks analyzed: {len(results)}")

    profitable_count = sum(1 for r in results if r['profitable'] is True)
    unknown_count = sum(1 for r in results if r['profitable'] == 'Unknown')

    print(f"Confirmed profitable: {profitable_count}")
    print(f"Profitability unknown (need premium tier): {unknown_count}")

    print("\n" + "="*70)
    print("NOTE: Free tier Polygon API has limited financial data access.")
    print("For complete profitability analysis, consider:")
    print("1. Upgrade to Polygon Premium tier for financial statements")
    print("2. Use alternative APIs (Alpha Vantage, Yahoo Finance)")
    print("3. Manual verification via financial statements (10-K, 10-Q)")
    print("="*70)


if __name__ == "__main__":
    main()
