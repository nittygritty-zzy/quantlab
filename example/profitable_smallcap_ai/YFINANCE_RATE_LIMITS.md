# yfinance Rate Limits Guide (2025)

**Last Updated**: October 2025

## ⚠️ Important Context

yfinance is an **unofficial library** that scrapes Yahoo Finance web pages. Yahoo Finance does **NOT** provide official API documentation or rate limits. All limits are informal, dynamically enforced, and subject to change.

---

## 📊 Rate Limit Summary by Data Type

| Data Type | Estimated Limit | Notes |
|-----------|----------------|-------|
| **Historical Price Data** (`download()`) | ~5 requests/minute | Most restrictive; Yahoo recently tightened |
| **Company Info** (`.info`) | ~5 requests/minute | Same backend as download |
| **Financial Statements** | ~5 requests/minute | Multiple API calls per ticker |
| **Intraday Data** (1m, 5m, 15m) | ~360 requests/hour | Heavy data load; ~950 tickers max reported |
| **Dividends & Splits** | ~5 requests/minute | Lightweight; included with history |
| **Options Chains** | ~5 requests/minute | Each expiration = separate request |
| **Analyst Data** | ~5 requests/minute | Part of info scraping |
| **News Articles** | ~5 requests/minute | Separate endpoint |

---

## 🚨 Known Rate Limits (2025)

### Official vs Observed Limits

**Official Yahoo API Documentation** (NOT yfinance-specific):
- **2,000 requests/hour** (general Yahoo API limit)
- **360 requests/hour** mentioned for specific endpoints

**Community-Observed Limits for yfinance**:
- ⚠️ **~5 requests per minute** (most conservative estimate)
- ⚠️ **Few hundred requests per day** before blocks occur
- ⚠️ **~950 tickers** for 7-day 1-minute intraday data (reported Nov 2024)
- ⚠️ Some users report limits after only **4-5 requests per day**

### Why Limits Vary

Yahoo's rate limiting is:
- **IP-based**: Multiple scripts from same IP compound the issue
- **Pattern-based**: Rapid sequential requests trigger faster blocks
- **Dynamic**: Limits tighten during high-traffic periods
- **Undocumented**: No official thresholds published

---

## 🔴 Common Rate Limit Errors

### YFRateLimitError
```python
YFRateLimitError('Too Many Requests. Rate limited. Try after a while.')
```

### HTTP 429 Error
```
HTTPError: 429 Client Error: Too Many Requests for url
```

### HTTP 999 Error
```
HTTPError: 999 (Request denied - often associated with rate limiting)
```

---

## ✅ Best Practices to Avoid Rate Limits

### 1. **Add Delays Between Requests** ⭐ MOST IMPORTANT

```python
import yfinance as yf
import time

tickers = ['AAPL', 'MSFT', 'GOOGL']

for ticker in tickers:
    stock = yf.Ticker(ticker)
    data = stock.info
    print(f"Fetched {ticker}")

    time.sleep(2)  # Wait 2-5 seconds between requests
```

**Recommended delays**:
- ✅ **2-5 seconds** for individual ticker requests
- ✅ **5-10 seconds** for heavy data (options chains, financials)
- ✅ **10-15 seconds** if you've already hit rate limits

### 2. **Use Batch Downloads**

```python
# BAD: Individual requests
for ticker in ['AAPL', 'MSFT', 'GOOGL']:
    data = yf.download(ticker, start='2023-01-01')  # 3 requests

# GOOD: Batch request
data = yf.download(['AAPL', 'MSFT', 'GOOGL'], start='2023-01-01')  # 1 request
```

### 3. **Implement Error Handling with Exponential Backoff**

```python
import time
from requests.exceptions import HTTPError

def fetch_with_retry(ticker, max_retries=3):
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            return stock.info
        except Exception as e:
            if '429' in str(e) or 'rate limit' in str(e).lower():
                wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    return None
```

### 4. **Cache Data Locally**

```python
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def get_data_cached(ticker, cache_days=1):
    cache_file = f"cache/{ticker}.csv"
    cache_path = Path(cache_file)

    # Check if cache exists and is fresh
    if cache_path.exists():
        mod_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mod_time < timedelta(days=cache_days):
            print(f"Loading {ticker} from cache")
            return pd.read_csv(cache_file)

    # Fetch fresh data
    print(f"Fetching {ticker} from Yahoo Finance")
    data = yf.download(ticker, period='1y', progress=False)
    data.to_csv(cache_file)
    time.sleep(2)  # Rate limit protection
    return data
```

### 5. **Limit Concurrent Requests**

```python
from concurrent.futures import ThreadPoolExecutor
import time

def fetch_ticker(ticker):
    time.sleep(2)  # Stagger requests
    stock = yf.Ticker(ticker)
    return stock.info

# Limit to 5 concurrent workers (not 20 or 50!)
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(fetch_ticker, tickers))
```

**⚠️ IMPORTANT**: For yfinance, use **max_workers=5** or less, NOT 20-50 workers like with Polygon API!

### 6. **Use Sessions for Connection Reuse**

```python
import requests_cache
import yfinance as yf

# Enable caching for requests
session = requests_cache.CachedSession('yfinance_cache', expire_after=3600)
yf.set_tz_cache_location(session)
```

---

## 📈 Rate Limit Strategy by Use Case

### Small-Scale Analysis (< 10 tickers)
```python
# Sequential with 2-second delays
for ticker in tickers:
    data = yf.Ticker(ticker).info
    time.sleep(2)
```
**Expected time**: ~20 seconds for 10 tickers
**Risk**: Low

### Medium-Scale Screening (10-100 tickers)
```python
# Batch download for price data
prices = yf.download(tickers, start='2023-01-01', group_by='ticker')

# Sequential with caching for fundamentals
for ticker in tickers:
    info = get_cached_info(ticker)
    time.sleep(3)
```
**Expected time**: ~5-10 minutes for 100 tickers
**Risk**: Medium

### Large-Scale Screening (100-1000+ tickers)
```python
# MUST use caching + aggressive delays
# Split into batches
batch_size = 50
for i in range(0, len(tickers), batch_size):
    batch = tickers[i:i+batch_size]

    # Batch download prices
    prices = yf.download(batch, period='1d', progress=False)

    # Long delay between batches
    time.sleep(60)  # Wait 1 minute between batches
```
**Expected time**: Several hours for 1000 tickers
**Risk**: High - **consider using Polygon API instead**

---

## 🔄 Comparison: yfinance vs Polygon API

| Feature | yfinance | Polygon API (Paid) |
|---------|----------|-------------------|
| **Rate Limit** | ~5 req/min (informal) | Unlimited with paid plan |
| **Reliability** | ⚠️ Can break anytime | ✅ Official, stable |
| **Cost** | Free | $49-299/month |
| **Data Coverage** | Historical + some real-time | Comprehensive |
| **Best For** | Small projects, testing | Production systems |
| **Concurrent Requests** | ❌ Not recommended | ✅ Supported (20-50 workers) |

---

## 🛠️ Recommended Workflow for Large-Scale Screening

### Phase 1: Discovery (Use Polygon API)
```python
# Use Polygon to discover tickers by criteria
# Polygon supports unlimited requests with paid plan
tickers = discover_tickers_via_polygon(
    market_cap_gte=300_000_000,
    market_cap_lte=5_000_000_000
)
```

### Phase 2: Historical Data (Use yfinance with caching)
```python
# Use yfinance for historical price data (Yahoo has better history)
# Implement aggressive caching (cache for 1 day)
for ticker in tickers:
    data = get_cached_price_data(ticker, cache_days=1)
    time.sleep(3)  # 3-second delay
```

### Phase 3: Fundamentals (Use Polygon or yfinance)
```python
# Option A: Polygon (faster, unlimited)
fundamentals = polygon_client.get_ticker_details(ticker)

# Option B: yfinance (free but slower)
fundamentals = yf.Ticker(ticker).info
time.sleep(2)
```

---

## 📝 Summary & Recommendations

### ✅ DO:
1. **Add 2-5 second delays** between every yfinance request
2. **Use batch downloads** with `yf.download(['AAPL', 'MSFT'])` when possible
3. **Implement caching** for repeated queries
4. **Use exponential backoff** when hitting rate limits
5. **Limit concurrent workers** to 5 or fewer
6. **Monitor for 429 errors** and adjust delays accordingly
7. **Consider Polygon API** for large-scale production systems

### ❌ DON'T:
1. ❌ Make rapid sequential requests without delays
2. ❌ Use 20-50 concurrent workers with yfinance
3. ❌ Fetch same data repeatedly without caching
4. ❌ Ignore 429 errors and retry immediately
5. ❌ Use yfinance for real-time trading systems
6. ❌ Rely on yfinance for mission-critical applications
7. ❌ Expect consistent rate limits (they change)

---

## 🔮 Future-Proofing

**Yahoo's Direction (2024-2025)**:
- Rate limits have **tightened significantly**
- More aggressive pattern detection
- Increased use of CAPTCHAs and blocks
- Possible move toward official paid API

**Recommendations**:
1. **For hobby projects**: yfinance is fine with proper delays
2. **For production**: Migrate to official APIs (Polygon, Alpha Vantage, IEX Cloud)
3. **For research**: Consider academic data sources (WRDS, CRSP)
4. **For trading**: Use broker APIs (Interactive Brokers, TD Ameritrade)

---

## 📚 References

- [yfinance GitHub Issues](https://github.com/ranaroussi/yfinance/issues)
- [Stack Overflow: yfinance rate limits](https://stackoverflow.com/questions/tagged/yfinance)
- Community reports from Medium, Reddit, GitHub (2024-2025)

---

**Bottom Line**: yfinance is **free but unreliable** for large-scale use. For the 125-stock screener we built, yfinance works, but for 1000+ stocks, **use Polygon API instead**.
