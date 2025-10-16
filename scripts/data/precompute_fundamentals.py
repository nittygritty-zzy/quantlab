#!/usr/bin/env python3
"""
Pre-fetch fundamental data for all stocks

This script fetches fundamental metrics from yfinance once and caches them.
This eliminates slow API calls during backtest runs.

Usage:
    uv run python scripts/data/precompute_fundamentals.py

Cache location: /Volumes/sandisk/quantmini-data/data/fundamentals_cache/

Run this:
- Daily before market open (to get latest fundamentals)
- After earnings releases (fundamentals change)
- When adding new tickers to universe
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quantlab.utils.logger import setup_logger

logger = setup_logger(__name__)

# Import yfinance
try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed")
    print("Install with: uv pip install yfinance")
    sys.exit(1)


def precompute_fundamentals(
    tickers: list,
    cache_dir: str = "/Volumes/sandisk/quantmini-data/data/fundamentals_cache"
):
    """
    Fetch fundamental data from yfinance and cache it

    Args:
        tickers: List of ticker symbols
        cache_dir: Directory to save cached fundamentals
    """
    print("=" * 70)
    print("PRECOMPUTING FUNDAMENTAL DATA")
    print("=" * 70)
    print(f"Tickers: {len(tickers)}")
    print(f"Cache directory: {cache_dir}")
    print()

    # Create cache directory
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    all_fundamentals = []
    successful = 0
    failed = 0

    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Fetching {ticker}...", end=" ")

        try:
            # Fetch data from yfinance
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract key fundamental metrics
            fundamental_data = {
                'ticker': ticker,
                'fetch_date': datetime.now().strftime('%Y-%m-%d'),
                'fetch_timestamp': datetime.now().isoformat(),

                # Valuation metrics
                'forward_pe': info.get('forwardPE'),
                'trailing_pe': info.get('trailingPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'enterprise_value': info.get('enterpriseValue'),
                'ev_to_revenue': info.get('enterpriseToRevenue'),
                'ev_to_ebitda': info.get('enterpriseToEbitda'),

                # Growth metrics
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'revenue_per_share': info.get('revenuePerShare'),

                # Profitability metrics
                'profit_margin': info.get('profitMargins'),
                'operating_margin': info.get('operatingMargins'),
                'gross_margin': info.get('grossMargins'),
                'roe': info.get('returnOnEquity'),
                'roa': info.get('returnOnAssets'),

                # Financial health
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'total_cash': info.get('totalCash'),
                'total_debt': info.get('totalDebt'),

                # Market data
                'market_cap': info.get('marketCap'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'float_shares': info.get('floatShares'),

                # Dividend data
                'dividend_yield': info.get('dividendYield'),
                'payout_ratio': info.get('payoutRatio'),

                # Analyst ratings
                'target_mean_price': info.get('targetMeanPrice'),
                'recommendation': info.get('recommendationKey'),
                'number_of_analyst_opinions': info.get('numberOfAnalystOpinions'),
            }

            all_fundamentals.append(fundamental_data)
            successful += 1

            # Count non-null metrics
            non_null_count = sum(1 for v in fundamental_data.values() if v is not None)
            print(f"✓ {non_null_count}/30 metrics")

            # Rate limiting: sleep briefly to avoid hitting yfinance limits
            time.sleep(0.5)

        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            failed += 1
            logger.error(f"Failed to fetch {ticker}: {e}")

    # Save to parquet
    if all_fundamentals:
        df = pd.DataFrame(all_fundamentals)

        # Save with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        cache_file = cache_path / f"fundamentals_{timestamp}.parquet"
        df.to_parquet(cache_file, index=False)

        # Also save as "latest" for easy access
        latest_file = cache_path / "fundamentals_latest.parquet"
        df.to_parquet(latest_file, index=False)

        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total: {len(tickers)}")
        print()
        print(f"Cache files:")
        print(f"  {cache_file}")
        print(f"  {latest_file}")
        print()

        # Show sample data
        print("Sample data (first 5 rows):")
        print(df[['ticker', 'forward_pe', 'revenue_growth', 'profit_margin', 'market_cap']].head())
        print()

        print("✓ Fundamentals pre-fetched successfully!")
        print()
        print("Next steps:")
        print("  1. Modify realtime_features.py to load from cache")
        print("  2. Run backtests with yfinance features (much faster!)")
        print("  3. Re-run this script daily to keep data fresh")

    else:
        print()
        print("✗ No fundamentals were fetched. Check errors above.")

    return successful, failed


if __name__ == "__main__":
    # Top 50 liquid US stocks
    TICKERS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "UNH", "XOM",
        "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "LLY", "ABBV", "MRK",
        "AVGO", "PEP", "COST", "KO", "ADBE", "WMT", "MCD", "CSCO", "CRM", "ACN",
        "TMO", "ABT", "NFLX", "DHR", "CMCSA", "VZ", "NKE", "DIS", "TXN", "INTC",
        "AMD", "QCOM", "UPS", "PM", "NEE", "RTX", "HON", "ORCL", "INTU", "AMGN"
    ]

    print("This will take ~30-60 seconds due to yfinance rate limiting...")
    print()

    # Run precomputation
    precompute_fundamentals(tickers=TICKERS)
