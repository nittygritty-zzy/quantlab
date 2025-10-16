#!/usr/bin/env python3
"""
Build stock2concept matrix for HIST model using Polygon API.

This script:
1. Loads liquid_stocks list from qlib
2. Fetches SIC codes for each stock from Polygon API
3. Maps SIC codes to GICS sectors
4. Builds stock2concept matrix
5. Saves stock2concept.npy and stock_index.npy
"""

import json
import time
import numpy as np
from polygon import RESTClient
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# SIC code to GICS sector mapping
# Based on: https://en.wikipedia.org/wiki/Standard_Industrial_Classification
# and GICS sector definitions
SIC_TO_SECTOR = {
    # Technology (SIC 3570-3579, 7370-7379)
    range(3570, 3580): 'Technology',
    range(7370, 7380): 'Technology',
    range(3600, 3700): 'Technology',  # Electronic equipment

    # Financials (SIC 6000-6799)
    range(6000, 6100): 'Financials',  # Banks
    range(6100, 6300): 'Financials',  # Credit agencies
    range(6300, 6400): 'Financials',  # Insurance
    range(6400, 6500): 'Financials',  # Insurance agents
    range(6500, 6600): 'Financials',  # Real estate
    range(6700, 6800): 'Financials',  # Holding companies

    # Healthcare (SIC 2830-2836, 3840-3860, 8000-8099)
    range(2830, 2837): 'Healthcare',  # Pharmaceuticals
    range(3840, 3861): 'Healthcare',  # Medical instruments
    range(8000, 8100): 'Healthcare',  # Health services

    # Consumer Discretionary (SIC 2300-2390, 3700-3720, 5200-5990)
    range(2300, 2391): 'Consumer Discretionary',  # Apparel
    range(3700, 3721): 'Consumer Discretionary',  # Transportation equipment (ex autos)
    range(3710, 3716): 'Consumer Discretionary',  # Motor vehicles
    range(5200, 5400): 'Consumer Discretionary',  # Retail - Building materials
    range(5500, 5600): 'Consumer Discretionary',  # Retail - Auto
    range(5700, 5800): 'Consumer Discretionary',  # Retail - Furniture
    range(5900, 6000): 'Consumer Discretionary',  # Retail - Miscellaneous
    range(7800, 7900): 'Consumer Discretionary',  # Entertainment

    # Communication Services (SIC 4800-4899, 7370-7379)
    range(4800, 4900): 'Communication Services',  # Telecommunications
    range(7370, 7380): 'Communication Services',  # Software/services

    # Industrials (SIC 1500-1799, 3400-3499, 3700-3799, 4000-4799)
    range(1500, 1800): 'Industrials',  # Construction
    range(3400, 3500): 'Industrials',  # Fabricated metal products
    range(3720, 3800): 'Industrials',  # Aircraft & aerospace
    range(4000, 4100): 'Industrials',  # Railroads
    range(4200, 4500): 'Industrials',  # Transportation
    range(5000, 5200): 'Industrials',  # Wholesale trade
    range(7300, 7400): 'Industrials',  # Business services

    # Consumer Staples (SIC 2000-2079, 2080-2099, 5400-5500)
    range(2000, 2080): 'Consumer Staples',  # Food products
    range(2080, 2100): 'Consumer Staples',  # Beverages
    range(2100, 2200): 'Consumer Staples',  # Tobacco
    range(5400, 5500): 'Consumer Staples',  # Grocery stores

    # Energy (SIC 1300-1399, 2900-2999)
    range(1300, 1400): 'Energy',  # Oil & gas extraction
    range(2900, 3000): 'Energy',  # Petroleum refining

    # Utilities (SIC 4900-4999)
    range(4900, 5000): 'Utilities',  # Electric, gas, sanitary services

    # Real Estate (SIC 6500-6599, 6700-6799)
    range(6500, 6600): 'Real Estate',  # Real estate

    # Materials (SIC 1000-1499, 2600-2699, 2800-2829)
    range(1000, 1500): 'Materials',  # Mining
    range(2600, 2700): 'Materials',  # Paper products
    range(2800, 2830): 'Materials',  # Chemicals
    range(3300, 3400): 'Materials',  # Primary metal industries
}

def sic_to_sector(sic_code):
    """Map SIC code to GICS sector."""
    if sic_code is None:
        return 'Unknown'

    try:
        sic_int = int(str(sic_code).strip())
        for sic_range, sector in SIC_TO_SECTOR.items():
            if sic_int in sic_range:
                return sector
        return 'Unknown'
    except:
        return 'Unknown'


def fetch_stock_sectors(stock_list, api_key, output_file='/tmp/stock_sectors.json',
                       resume=True, batch_size=500, max_workers=10):
    """
    Fetch SIC codes and sectors for all stocks using Polygon API in parallel.

    Args:
        stock_list: List of stock symbols
        api_key: Polygon API key
        output_file: JSON file to save/resume from
        resume: Whether to resume from previous run
        batch_size: Save progress every N stocks
        max_workers: Number of parallel threads
    """
    # Load existing data if resuming
    stock_sectors = {}
    if resume and Path(output_file).exists():
        with open(output_file, 'r') as f:
            stock_sectors = json.load(f)
        print(f"Resuming: Loaded {len(stock_sectors)} existing stock sectors")

    # Filter out already fetched stocks
    stocks_to_fetch = [s for s in stock_list if s not in stock_sectors]
    total = len(stock_list)
    remaining = len(stocks_to_fetch)

    print(f"Total stocks: {total}")
    print(f"Already fetched: {total - remaining}")
    print(f"Remaining: {remaining}")
    print(f"Using {max_workers} parallel workers")
    print("="*60)

    if remaining == 0:
        print("All stocks already fetched!")
        return stock_sectors

    # Thread-safe data structures
    lock = Lock()
    errors = []
    completed = 0

    def fetch_single_stock(symbol):
        """Fetch sector info for a single stock."""
        try:
            client = RESTClient(api_key=api_key)
            details = client.get_ticker_details(symbol)

            sic_code = getattr(details, 'sic_code', None)
            sic_description = getattr(details, 'sic_description', None)
            sector = sic_to_sector(sic_code)

            return symbol, {
                'sic_code': sic_code,
                'sic_description': sic_description,
                'sector': sector,
                'name': getattr(details, 'name', None),
            }

        except Exception as e:
            error_msg = f"{symbol}: {type(e).__name__}: {e}"
            return symbol, {
                'sic_code': None,
                'sic_description': None,
                'sector': 'Unknown',
                'name': None,
                'error': str(e)
            }, error_msg

    # Use ThreadPoolExecutor for parallel fetching
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_symbol = {
            executor.submit(fetch_single_stock, symbol): symbol
            for symbol in stocks_to_fetch
        }

        # Process completed tasks
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]

            try:
                result = future.result()

                if len(result) == 3:
                    # Error case
                    symbol, data, error_msg = result
                    errors.append(error_msg)
                    if len(errors) <= 10:
                        print(f"ERROR - {error_msg}")
                else:
                    # Success case
                    symbol, data = result

                # Thread-safe update
                with lock:
                    stock_sectors[symbol] = data
                    completed += 1

                    # Progress report
                    if completed % 100 == 0 or completed == remaining:
                        elapsed = time.time() - start_time
                        rate = completed / elapsed
                        eta = (remaining - completed) / rate if rate > 0 else 0

                        pct = 100 * (total - remaining + completed) / total
                        print(f"Progress: {completed}/{remaining} fetched "
                              f"({pct:.1f}% total) | "
                              f"{rate:.1f} req/sec | "
                              f"ETA: {eta/60:.1f} min")

                    # Save progress periodically
                    if completed % batch_size == 0:
                        with open(output_file, 'w') as f:
                            json.dump(stock_sectors, f, indent=2)
                        print(f"💾 Saved progress: {len(stock_sectors)} stocks")

            except Exception as e:
                print(f"ERROR processing {symbol}: {e}")

    # Final save
    with open(output_file, 'w') as f:
        json.dump(stock_sectors, f, indent=2)

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✓ Completed! Fetched sectors for {len(stock_sectors)} stocks")
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Rate: {completed/elapsed:.1f} requests/second")
    print(f"Errors: {len(errors)}")

    if errors:
        print(f"\nFirst 10 errors:")
        for err in errors[:10]:
            print(f"  - {err}")

    return stock_sectors


def build_stock2concept_matrix(stock_list, stock_sectors, output_dir='/Users/zheyuanzhao/workspace/quantlab/data'):
    """
    Build stock2concept matrix and stock_index mapping.

    Args:
        stock_list: Ordered list of stock symbols
        stock_sectors: Dict mapping symbol -> sector info
        output_dir: Directory to save .npy files
    """
    # Define sector list (GICS 11 sectors + Unknown)
    sectors = [
        'Technology',
        'Financials',
        'Healthcare',
        'Consumer Discretionary',
        'Communication Services',
        'Industrials',
        'Consumer Staples',
        'Energy',
        'Utilities',
        'Real Estate',
        'Materials',
        'Unknown'
    ]

    n_stocks = len(stock_list)
    n_concepts = len(sectors)

    # Initialize matrix
    stock2concept = np.zeros((n_stocks, n_concepts), dtype=np.float32)

    # Build stock_index mapping
    stock_index = {symbol: i for i, symbol in enumerate(stock_list)}

    # Fill matrix
    sector_counts = {sector: 0 for sector in sectors}

    for i, symbol in enumerate(stock_list):
        if symbol in stock_sectors:
            sector = stock_sectors[symbol]['sector']
        else:
            sector = 'Unknown'

        if sector in sectors:
            j = sectors.index(sector)
            stock2concept[i, j] = 1.0
            sector_counts[sector] += 1

    # Print statistics
    print("\n" + "="*60)
    print("Stock2Concept Matrix Statistics")
    print("="*60)
    print(f"Shape: ({n_stocks} stocks, {n_concepts} sectors)")
    print(f"\nSector distribution:")
    for sector in sectors:
        count = sector_counts[sector]
        pct = 100 * count / n_stocks
        print(f"  {sector:30s}: {count:5d} ({pct:5.1f}%)")

    # Save files
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    stock2concept_path = Path(output_dir) / 'stock2concept_liquid_stocks.npy'
    stock_index_path = Path(output_dir) / 'stock_index_liquid_stocks.npy'

    np.save(stock2concept_path, stock2concept)
    np.save(stock_index_path, stock_index)

    print(f"\n✓ Saved {stock2concept_path}")
    print(f"✓ Saved {stock_index_path}")

    return stock2concept, stock_index


def main():
    """Main execution."""
    print("="*60)
    print("Building stock2concept matrix for HIST model")
    print("="*60)

    # Load stock list
    stock_list_file = '/tmp/liquid_stocks_list.json'
    with open(stock_list_file, 'r') as f:
        stock_list = json.load(f)

    print(f"\nLoaded {len(stock_list)} stocks from {stock_list_file}")

    # Polygon API key
    api_key = 'vDr8GDaQ87Z9Mwe5IiCKzGcRP9pnO8TW'

    # Fetch sectors
    print("\n" + "="*60)
    print("Step 1: Fetching SIC codes and sectors from Polygon API (PARALLEL)")
    print("="*60)
    print("Using 10 parallel workers for fast fetching")
    print("Estimated time: ~10-20 minutes for 13K stocks")
    print("Progress is saved every 500 stocks and can be resumed\n")

    stock_sectors = fetch_stock_sectors(
        stock_list,
        api_key,
        output_file='/tmp/stock_sectors.json',
        resume=True,
        batch_size=500,
        max_workers=10  # 10 parallel threads
    )

    # Build matrix
    print("\n" + "="*60)
    print("Step 2: Building stock2concept matrix")
    print("="*60)

    stock2concept, stock_index = build_stock2concept_matrix(
        stock_list,
        stock_sectors,
        output_dir='/Users/zheyuanzhao/workspace/quantlab/data'
    )

    print("\n" + "="*60)
    print("✓ Complete! Ready to use with HIST model")
    print("="*60)


if __name__ == '__main__':
    main()
