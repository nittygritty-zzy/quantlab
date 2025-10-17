# Finding Related Stocks: Methods & Implementation Guide

## Overview
This guide covers multiple approaches to finding stocks related to a given ticker (e.g., NVDA → AMD, TSMC, ASML, INTC, etc.).

---

## Method 1: Polygon API - Related Companies Endpoint ✅ RECOMMENDED

### Description
Polygon's `/v1/related-companies/{ticker}` endpoint identifies related stocks through analysis of:
- News coverage patterns
- Returns correlation data

### Advantages
- ✅ Pre-computed relationships (fast)
- ✅ Based on multiple data sources
- ✅ Updated daily
- ✅ Simple API call

### Implementation
```python
from example.find_related_stocks import RelatedStocksFinder

finder = RelatedStocksFinder()
related = finder.get_related_tickers('NVDA')
# Returns: ['AMD', 'TSMC', 'ASML', 'INTC', ...]
```

### API Details
- **Endpoint**: `GET /v1/related-companies/{ticker}`
- **Rate Limits**: Depends on plan (Basic/Starter/Developer/Advanced)
- **Update Frequency**: Daily
- **Cost**: Available on all Stocks plans

### Use Cases
1. **Peer Analysis**: Compare NVDA with AMD, INTC
2. **Portfolio Diversification**: Find alternatives to current holdings
3. **Sector Research**: Identify key players in semiconductor space
4. **Pair Trading**: Find correlated stocks for statistical arbitrage

---

## Method 2: Ticker Details + Industry/Sector Filtering

### Description
Use Polygon's ticker details endpoint to get SIC codes, industry classifications, and filter by matching characteristics.

### Implementation Strategy
```python
# Step 1: Get target stock details
target_details = finder.get_ticker_details('NVDA')
target_sic = target_details.get('sic_code')
target_industry = target_details.get('sic_description')

# Step 2: Get all tickers in same industry
# /v3/reference/tickers?sic_code={sic_code}&market=stocks&active=true

# Step 3: Filter by market cap, exchange, etc.
```

### Advantages
- ✅ More control over filtering criteria
- ✅ Can customize similarity metrics
- ✅ Includes inactive/delisted companies if needed

### Disadvantages
- ❌ Requires multiple API calls
- ❌ Need to implement filtering logic
- ❌ May need additional data for ranking

### Data Points for Filtering
- **SIC Code**: Industry classification
- **Market Cap**: Company size similarity
- **Primary Exchange**: NYSE, NASDAQ, etc.
- **Locale**: US, international
- **Type**: Common stock, ETF, etc.

---

## Method 3: Correlation Analysis (Price Returns)

### Description
Calculate price return correlations to find stocks that move together.

### Implementation
```python
import pandas as pd
from polygon import RESTClient

def get_price_correlation(ticker1, ticker2, days=252):
    """Calculate correlation between two stocks"""
    # Fetch historical prices for both tickers
    # Calculate daily returns
    # Compute correlation coefficient
    pass

def find_correlated_stocks(target_ticker, universe, threshold=0.7):
    """Find stocks with correlation > threshold"""
    # Compare target with all stocks in universe
    # Return sorted by correlation
    pass
```

### Advantages
- ✅ Quantitative, objective measure
- ✅ Customizable timeframes
- ✅ Identifies actual trading relationships

### Disadvantages
- ❌ Computationally intensive
- ❌ Many API calls required
- ❌ Correlation changes over time
- ❌ Doesn't capture fundamental relationships

### Best Practices
- Use 1-year (252 days) for medium-term correlation
- Use 5-year for long-term relationships
- Consider rolling correlations
- Adjust for market regime changes

---

## Method 4: Fundamental Similarity

### Description
Compare fundamental metrics to find similar companies.

### Data Sources
1. **Polygon Ticker Details**: Basic company info
2. **Polygon Financials** (if available): Revenue, earnings, etc.
3. **External APIs**: For more detailed fundamentals

### Similarity Metrics
```python
def calculate_fundamental_similarity(stock1, stock2):
    """
    Compare companies based on:
    - Market cap (within 2x range)
    - Revenue growth rate
    - Profit margins
    - P/E ratio
    - Industry classification
    """
    similarity_score = 0
    # Implement weighted scoring
    return similarity_score
```

### Advantages
- ✅ Captures business model similarity
- ✅ More stable than price correlation
- ✅ Good for long-term analysis

### Disadvantages
- ❌ Requires fundamental data API
- ❌ Data may be delayed (quarterly)
- ❌ More complex to implement

---

## Method 5: News & Social Mention Co-occurrence

### Description
Identify stocks frequently mentioned together in news articles and social media.

### Data Sources
- **Polygon News API**: `/v2/reference/news`
- **Alpha Vantage News Sentiment**
- **Reddit/Twitter APIs**

### Implementation Concept
```python
def find_co_mentioned_stocks(ticker, num_articles=100):
    """
    1. Fetch recent news articles mentioning ticker
    2. Extract all other tickers mentioned in same articles
    3. Rank by co-occurrence frequency
    """
    # Get news articles
    # Parse for ticker symbols
    # Count co-occurrences
    # Return ranked list
    pass
```

### Advantages
- ✅ Captures market perception
- ✅ Real-time relationships
- ✅ Identifies emerging connections

### Disadvantages
- ❌ Requires NLP/text processing
- ❌ Can be noisy
- ❌ May reflect temporary events

---

## Method 6: ETF Holdings Analysis

### Description
Find stocks that appear together in same sector/thematic ETFs.

### Implementation
```python
def find_etf_peers(ticker):
    """
    1. Find ETFs that hold the target stock
    2. Get holdings of those ETFs
    3. Identify stocks with high overlap
    """
    # Example: NVDA appears in
    # - SMH (Semiconductors)
    # - XLK (Technology)
    # - QQQ (NASDAQ 100)
    # Other top holdings = related stocks
    pass
```

### Advantages
- ✅ Professional curation (ETF managers)
- ✅ Sector/theme based grouping
- ✅ Weighted by institutional preference

### Disadvantages
- ❌ Requires ETF holdings data
- ❌ May be delayed (13F filings)
- ❌ Limited to liquid, large-cap stocks

---

## Method 7: Supply Chain & Business Relationships

### Description
Identify companies in the same supply chain or with direct business relationships.

### For NVDA Example
```
Suppliers → NVDA → Customers

Suppliers:
- TSMC (chip manufacturing)
- ASML (lithography equipment)
- Synopsys (design tools)

Customers:
- Cloud providers (MSFT, GOOGL, AMZN)
- OEMs (Dell, HP)
- Automotive (TSLA)

Competitors:
- AMD (GPUs)
- INTC (CPUs, attempting GPUs)
- QCOM (mobile chips)
```

### Data Sources
- **Bloomberg Supply Chain data**
- **FactSet Revere**
- **Manual research** (10-K filings, investor presentations)

### Advantages
- ✅ Captures true business relationships
- ✅ Useful for fundamental analysis
- ✅ Identifies value chain opportunities

### Disadvantages
- ❌ Expensive data sources
- ❌ Manual research required
- ❌ Not easily automated

---

## Recommended Approach: Hybrid Method

### Strategy
Combine multiple methods for best results:

```python
class HybridRelatedStocksFinder:
    def find_related_stocks(self, ticker, methods='all'):
        """
        1. Get Polygon Related Companies (base list)
        2. Filter by same SIC code/industry
        3. Calculate price correlations for top candidates
        4. Score by multiple factors
        5. Return ranked list
        """

        # Method 1: API Related Companies
        api_related = self.get_polygon_related(ticker)

        # Method 2: Industry Filter
        industry_peers = self.get_industry_peers(ticker)

        # Method 3: Correlation (for top candidates only)
        correlated = self.get_correlated_stocks(ticker,
                                                 universe=api_related + industry_peers)

        # Combine and score
        final_scores = self.calculate_composite_score(
            api_related, industry_peers, correlated
        )

        return sorted(final_scores, key=lambda x: x['score'], reverse=True)
```

### Scoring Example
```python
def calculate_composite_score(ticker, candidate):
    score = 0

    # Weight: 40% - API says they're related
    if candidate in api_related:
        score += 40

    # Weight: 30% - Same industry/sector
    if same_sic_code(ticker, candidate):
        score += 30

    # Weight: 20% - High price correlation (>0.7)
    correlation = get_correlation(ticker, candidate)
    if correlation > 0.7:
        score += 20 * (correlation / 1.0)

    # Weight: 10% - Similar market cap
    if similar_market_cap(ticker, candidate, tolerance=2.0):
        score += 10

    return score
```

---

## Practical Use Cases & Examples

### Use Case 1: Build a Sector Watchlist
```python
# Start with sector leader
leader = 'NVDA'

# Get related stocks
finder = RelatedStocksFinder()
related = finder.get_related_tickers_list(leader)

# Create watchlist
watchlist = [leader] + related[:10]  # Top 10 related

# Monitor for trading opportunities
for ticker in watchlist:
    # Run technical analysis
    # Check for entry/exit signals
    pass
```

### Use Case 2: Pairs Trading
```python
# Find highly correlated pairs
nvda_related = finder.get_related_tickers_list('NVDA')

for candidate in nvda_related:
    correlation = calculate_correlation('NVDA', candidate)

    if correlation > 0.85:
        # Check for divergence
        spread = get_price_spread('NVDA', candidate)

        if spread > 2_std_devs:
            # Trading opportunity: mean reversion
            print(f"Pairs trade opportunity: NVDA vs {candidate}")
```

### Use Case 3: Portfolio Diversification Check
```python
# Check if your portfolio is too concentrated
portfolio = ['NVDA', 'AMD', 'INTC', 'QCOM']

# Build relationship matrix
for stock1 in portfolio:
    related_to_stock1 = finder.get_related_tickers_list(stock1)

    for stock2 in portfolio:
        if stock2 in related_to_stock1:
            print(f"Warning: {stock1} and {stock2} are related!")
            print("Consider diversifying into different sectors")
```

### Use Case 4: Event-Driven Trading
```python
# NVDA announces earnings beat
# Trade related stocks on sympathy move

nvda_related = finder.get_related_tickers_list('NVDA')

# Filter for highly correlated stocks
sympathy_plays = []
for ticker in nvda_related:
    if calculate_correlation('NVDA', ticker) > 0.75:
        sympathy_plays.append(ticker)

print(f"Watch these for sympathy moves: {sympathy_plays}")
# Expected: AMD, INTC, SMCI, etc.
```

---

## Implementation Roadmap

### Phase 1: Basic Implementation (Week 1)
- ✅ Implement Polygon Related Companies API
- ✅ Create simple ticker list fetcher
- ✅ Add basic error handling

### Phase 2: Enhanced Features (Week 2)
- ⬜ Add ticker details enrichment
- ⬜ Implement industry/sector filtering
- ⬜ Add caching for API responses

### Phase 3: Advanced Analysis (Week 3-4)
- ⬜ Implement correlation analysis
- ⬜ Create composite scoring system
- ⬜ Build relationship matrix visualization

### Phase 4: Integration (Week 5)
- ⬜ Integrate with existing QuantLab screeners
- ⬜ Add to watchlist management system
- ⬜ Create automated alerts for related stock movements

---

## Performance Considerations

### API Rate Limits
```python
# Polygon rate limits (varies by plan)
# Basic: 5 requests/minute
# Starter: 100 requests/minute
# Developer: 500 requests/minute

# Best practices:
# 1. Cache results (daily updates sufficient)
# 2. Batch requests when possible
# 3. Use exponential backoff on errors
```

### Caching Strategy
```python
import pickle
from datetime import datetime, timedelta

class CachedRelatedStocksFinder(RelatedStocksFinder):
    def __init__(self, cache_duration_hours=24):
        super().__init__()
        self.cache = {}
        self.cache_duration = timedelta(hours=cache_duration_hours)

    def get_related_tickers(self, ticker):
        # Check cache first
        if ticker in self.cache:
            cached_time, cached_data = self.cache[ticker]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data

        # Fetch from API
        data = super().get_related_tickers(ticker)
        self.cache[ticker] = (datetime.now(), data)
        return data
```

---

## Testing & Validation

### Test Cases
```python
def test_nvda_related_stocks():
    """Test that NVDA returns expected semiconductor peers"""
    finder = RelatedStocksFinder()
    related = finder.get_related_tickers_list('NVDA')

    expected_tickers = ['AMD', 'INTC']  # Minimum expected

    for ticker in expected_tickers:
        assert ticker in related, f"{ticker} should be related to NVDA"

    assert len(related) > 0, "Should return at least some related tickers"


def test_invalid_ticker():
    """Test handling of invalid ticker"""
    finder = RelatedStocksFinder()
    related = finder.get_related_tickers_list('INVALIDTICKER123')

    assert isinstance(related, list), "Should return empty list for invalid ticker"
```

---

## Resources

### Polygon API Documentation
- Related Companies: https://polygon.io/docs/stocks/get_v1_related-companies__ticker
- Ticker Details: https://polygon.io/docs/stocks/get_v3_reference_tickers__ticker
- News API: https://polygon.io/docs/stocks/get_v2_reference_news

### Alternative APIs (if needed)
- **Alpha Vantage**: Sector peers, fundamentals
- **IEX Cloud**: Related symbols, peer groups
- **Yahoo Finance**: Industry classification
- **SEC Edgar**: Business relationships (10-K filings)

### Academic Research
- "Stock Correlation Networks" (graph theory approach)
- "Supply Chain Network Analysis"
- "News-based Asset Pricing"
