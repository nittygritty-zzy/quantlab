"""
Find Related Stocks using Polygon API

This script demonstrates how to find stocks related to a given ticker
(e.g., NVDA -> AMD, TSMC, ASML, etc.) using Polygon's Related Companies endpoint.

The API analyzes news coverage and returns data to identify related tickers.
"""

import os
import requests
from typing import List, Dict, Optional
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class RelatedStocksFinder:
    """Find related stocks using Polygon API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the finder with Polygon API key

        Args:
            api_key: Polygon API key (if None, reads from POLYGON_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError("Polygon API key not found. Set POLYGON_API_KEY environment variable.")

        self.base_url = "https://api.polygon.io"

    def get_related_tickers(self, ticker: str) -> Dict:
        """
        Get related tickers for a given stock

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')

        Returns:
            Dictionary containing related tickers and metadata
        """
        endpoint = f"{self.base_url}/v1/related-companies/{ticker.upper()}"
        params = {'apiKey': self.api_key}

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching related tickers: {e}")
            return {}

    def get_related_tickers_list(self, ticker: str) -> List[str]:
        """
        Get list of related ticker symbols only

        Args:
            ticker: Stock ticker symbol

        Returns:
            List of related ticker symbols
        """
        data = self.get_related_tickers(ticker)
        results = data.get('results', [])
        return [item['ticker'] for item in results if 'ticker' in item]

    def get_ticker_details(self, ticker: str) -> Dict:
        """
        Get detailed information about a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with ticker details
        """
        endpoint = f"{self.base_url}/v3/reference/tickers/{ticker.upper()}"
        params = {'apiKey': self.api_key}

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json().get('results', {})
        except requests.exceptions.RequestException as e:
            print(f"Error fetching ticker details: {e}")
            return {}

    def get_related_with_details(self, ticker: str) -> List[Dict]:
        """
        Get related tickers with detailed company information

        Args:
            ticker: Stock ticker symbol

        Returns:
            List of dictionaries containing ticker and company details
        """
        related_tickers = self.get_related_tickers_list(ticker)
        detailed_info = []

        for rel_ticker in related_tickers:
            details = self.get_ticker_details(rel_ticker)
            if details:
                detailed_info.append({
                    'ticker': rel_ticker,
                    'name': details.get('name', 'N/A'),
                    'market': details.get('market', 'N/A'),
                    'locale': details.get('locale', 'N/A'),
                    'primary_exchange': details.get('primary_exchange', 'N/A'),
                    'type': details.get('type', 'N/A'),
                    'currency_name': details.get('currency_name', 'N/A'),
                    'market_cap': details.get('market_cap', 'N/A'),
                    'sic_description': details.get('sic_description', 'N/A'),
                })

        return detailed_info

    def print_related_stocks(self, ticker: str, show_details: bool = False):
        """
        Print related stocks in a formatted way

        Args:
            ticker: Stock ticker symbol
            show_details: If True, show detailed company information
        """
        print(f"\n{'='*60}")
        print(f"Related Stocks for {ticker.upper()}")
        print(f"{'='*60}\n")

        if show_details:
            related_stocks = self.get_related_with_details(ticker)

            if not related_stocks:
                print("No related stocks found.")
                return

            for i, stock in enumerate(related_stocks, 1):
                print(f"{i}. {stock['ticker']} - {stock['name']}")
                print(f"   Exchange: {stock['primary_exchange']}")
                print(f"   Industry: {stock['sic_description']}")
                print(f"   Market Cap: {stock['market_cap']}")
                print()
        else:
            related_tickers = self.get_related_tickers_list(ticker)

            if not related_tickers:
                print("No related stocks found.")
                return

            print("Related Tickers:", ", ".join(related_tickers))
            print()


def main():
    """Example usage"""

    # Initialize finder
    finder = RelatedStocksFinder()

    # Example 1: Find related stocks for NVDA
    print("\nExample 1: Simple related tickers list")
    finder.print_related_stocks('NVDA', show_details=False)

    # Example 2: Find related stocks with details
    print("\nExample 2: Related tickers with company details")
    finder.print_related_stocks('NVDA', show_details=True)

    # Example 3: Get related tickers as a list for further processing
    print("\nExample 3: Get related tickers for programmatic use")
    nvda_related = finder.get_related_tickers_list('NVDA')
    print(f"Found {len(nvda_related)} related tickers:")
    print(nvda_related)

    # Example 4: Compare multiple stocks
    print("\nExample 4: Compare related stocks for different tickers")
    tickers_to_check = ['NVDA', 'AMD', 'INTC']

    for ticker in tickers_to_check:
        related = finder.get_related_tickers_list(ticker)
        print(f"{ticker}: {', '.join(related[:5])}...")  # Show first 5

    # Example 5: Find common related stocks
    print("\nExample 5: Find stocks commonly related to both NVDA and AMD")
    nvda_related = set(finder.get_related_tickers_list('NVDA'))
    amd_related = set(finder.get_related_tickers_list('AMD'))
    common = nvda_related.intersection(amd_related)
    print(f"Common related stocks: {', '.join(common)}")


if __name__ == "__main__":
    main()
