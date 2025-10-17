# yfinance Data Field Mapping

## ✅ YES - yfinance provides ALL the data you requested!

Based on real test with SOUN ticker, here's the complete mapping:

---

## 📊 Your Requested Fields → yfinance Keys

| Your Field | yfinance Key | Available? | Example Value |
|------------|--------------|------------|---------------|
| **Previous Close** | `previousClose` | ✅ YES | 20.76 |
| **Open** | `open` | ✅ YES | 19.945 |
| **Bid** | `bid` | ✅ YES | 17.0 |
| **Bid Size** | `bidSize` | ✅ YES | 5 (×200 shares) |
| **Ask** | `ask` | ✅ YES | 24.05 |
| **Ask Size** | `askSize` | ✅ YES | 2 (×200 shares) |
| **Day's Range** | `dayLow`, `dayHigh` | ✅ YES | 18.6 - 20.4 |
| **52 Week Range** | `fiftyTwoWeekLow`, `fiftyTwoWeekHigh` | ✅ YES | 4.86 - 24.98 |
| **Volume** | `volume` | ✅ YES | 26,909,033 |
| **Avg. Volume** | `averageVolume` | ✅ YES | 61,635,446 |
| **Market Cap** | `marketCap` | ✅ YES | 7.79B |
| **Beta (5Y Monthly)** | `beta` | ✅ YES | 2.79 |
| **PE Ratio (TTM)** | `trailingPE` | ⚠️ Sometimes | null (if unprofitable) |
| **EPS (TTM)** | `trailingEps` | ✅ YES | -0.68 |
| **Earnings Date** | `earningsTimestamp` | ✅ YES | 1754596800 (timestamp) |
| **Forward Dividend & Yield** | `dividendYield` | ⚠️ If pays | null (if no dividend) |
| **Ex-Dividend Date** | `exDividendDate` | ⚠️ If pays | null (if no dividend) |
| **1y Target Est** | `targetMeanPrice` | ✅ YES | 16.56 |

---

## 💡 How to Access Each Field

```python
import yfinance as yf

stock = yf.Ticker("SOUN")
info = stock.info

# Your requested fields
previous_close = info.get('previousClose')        # 20.76
open_price = info.get('open')                     # 19.945
bid = info.get('bid')                             # 17.0
bid_size = info.get('bidSize')                    # 5
ask = info.get('ask')                             # 24.05
ask_size = info.get('askSize')                    # 2

# Day's Range
day_low = info.get('dayLow')                      # 18.6
day_high = info.get('dayHigh')                    # 20.4
day_range = f"{day_low} - {day_high}"             # "18.6 - 20.4"

# 52 Week Range
week_52_low = info.get('fiftyTwoWeekLow')         # 4.86
week_52_high = info.get('fiftyTwoWeekHigh')       # 24.98
week_52_range = f"{week_52_low} - {week_52_high}" # "4.86 - 24.98"

# Volume
volume = info.get('volume')                       # 26909033
avg_volume = info.get('averageVolume')            # 61635446

# Valuation
market_cap = info.get('marketCap')                # 7792923648
beta = info.get('beta')                           # 2.791
pe_ratio = info.get('trailingPE')                 # null (unprofitable)
eps = info.get('trailingEps')                     # -0.68

# Earnings & Dividends
earnings_date = info.get('earningsTimestamp')     # 1754596800
dividend_yield = info.get('dividendYield')        # null (no dividend)
ex_dividend = info.get('exDividendDate')          # null

# Analyst Target
target_price = info.get('targetMeanPrice')        # 16.5625
```

---

## 📈 BONUS: Additional Useful Fields (165 total!)

### Valuation Metrics
```python
forward_pe = info.get('forwardPE')                    # -95.575
peg_ratio = info.get('pegRatio')                      # null
price_to_book = info.get('priceToBook')               # 21.55
price_to_sales = info.get('priceToSalesTrailing12Months')  # 59.28
enterprise_value = info.get('enterpriseValue')        # 8.24B
```

### Profitability
```python
profit_margin = info.get('profitMargins')             # -171.28%
operating_margin = info.get('operatingMargins')       # -108.59%
return_on_assets = info.get('returnOnAssets')         # -23.47%
return_on_equity = info.get('returnOnEquity')         # -77.14%
gross_profit = info.get('grossProfits')               # 53.26M
ebitda = info.get('ebitda')                          # -137.26M
```

### Growth Metrics
```python
revenue_growth = info.get('revenueGrowth')            # 217.1% (quarterly)
earnings_growth = info.get('earningsGrowth')          # null
revenue = info.get('totalRevenue')                    # 131.45M
revenue_per_share = info.get('revenuePerShare')       # 0.344
```

### Balance Sheet
```python
total_cash = info.get('totalCash')                    # 230.34M
total_debt = info.get('totalDebt')                    # 4.39M
debt_to_equity = info.get('debtToEquity')             # 1.22
current_ratio = info.get('currentRatio')              # 4.84
quick_ratio = info.get('quickRatio')                  # 4.67
book_value = info.get('bookValue')                    # 0.887
```

### Cash Flow
```python
free_cashflow = info.get('freeCashflow')              # -4.85M
operating_cashflow = info.get('operatingCashflow')    # -112.12M
```

### Shares & Ownership
```python
shares_outstanding = info.get('sharesOutstanding')    # 375.15M
float_shares = info.get('floatShares')                # 365.55M
shares_short = info.get('sharesShort')                # 117.33M
short_ratio = info.get('shortRatio')                  # 1.55
short_percent_float = info.get('shortPercentOfFloat') # 31.47%
held_by_insiders = info.get('heldPercentInsiders')    # 1.36%
held_by_institutions = info.get('heldPercentInstitutions')  # 47.09%
```

### Technical Indicators
```python
fifty_day_avg = info.get('fiftyDayAverage')           # 15.53
two_hundred_day_avg = info.get('twoHundredDayAverage')  # 12.25
fifty_two_week_change = info.get('52WeekChange')      # 277.45%
sandp_52_week_change = info.get('SandP52WeekChange')  # 13.03%
```

### Analyst Recommendations
```python
target_mean_price = info.get('targetMeanPrice')       # 16.56
target_high_price = info.get('targetHighPrice')       # 26.0
target_low_price = info.get('targetLowPrice')         # 12.0
recommendation_mean = info.get('recommendationMean')  # 1.78 (buy)
recommendation_key = info.get('recommendationKey')    # "buy"
num_analyst_opinions = info.get('numberOfAnalystOpinions')  # 8
```

### Company Info
```python
company_name = info.get('longName')                   # "SoundHound AI, Inc."
industry = info.get('industry')                       # "Software"
sector = info.get('sector')                           # "Technology"
description = info.get('longBusinessSummary')         # Full description
website = info.get('website')                         # Company website
employees = info.get('fullTimeEmployees')             # Number of employees
```

---

## 🕐 Historical Data

```python
# Get historical price data
hist = stock.history(period="1mo")  # 1 month

# Available columns:
# - Open, High, Low, Close
# - Volume
# - Dividends, Stock Splits

# Example: Last 5 days
print(hist.tail())
```

---

## 📊 Real-Time vs Delayed Data

### Real-Time (with premium data)
- Current price, bid/ask
- Volume updates
- Intraday data

### Delayed (free tier)
- 15-minute delay typically
- Check: `info.get('exchangeDataDelayedBy')`  # 0 = real-time

---

## ⚠️ Important Notes

### Fields That May Be Null

1. **PE Ratio** (`trailingPE`):
   - `null` if company is unprofitable (negative earnings)
   - Example: SOUN has negative EPS, so no PE ratio

2. **Dividend Fields** (`dividendYield`, `exDividendDate`):
   - `null` if company doesn't pay dividends
   - Many growth/AI stocks don't pay dividends

3. **PEG Ratio** (`pegRatio`):
   - `null` if no earnings growth or negative earnings

4. **Earnings Growth** (`earningsGrowth`):
   - May be `null` for newer companies or unprofitable ones

### Always Use `.get()` with Default

```python
# BAD - will crash if key doesn't exist
pe_ratio = info['trailingPE']

# GOOD - returns None if not available
pe_ratio = info.get('trailingPE')

# BETTER - provide default value
pe_ratio = info.get('trailingPE', 'N/A')
```

---

## 🔧 Practical Screener Integration

### Add to Screener

```python
def get_stock_fundamentals(self, ticker: str) -> Optional[Dict]:
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        'ticker': ticker,
        'name': info.get('longName'),

        # Price Data
        'current_price': info.get('currentPrice'),
        'previous_close': info.get('previousClose'),
        'open': info.get('open'),
        'bid': info.get('bid'),
        'ask': info.get('ask'),
        'day_low': info.get('dayLow'),
        'day_high': info.get('dayHigh'),
        '52_week_low': info.get('fiftyTwoWeekLow'),
        '52_week_high': info.get('fiftyTwoWeekHigh'),

        # Volume
        'volume': info.get('volume'),
        'avg_volume': info.get('averageVolume'),

        # Valuation
        'market_cap': info.get('marketCap'),
        'pe_ratio': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'peg_ratio': info.get('pegRatio'),
        'price_to_book': info.get('priceToBook'),
        'price_to_sales': info.get('priceToSalesTrailing12Months'),

        # Profitability
        'profit_margin': info.get('profitMargins'),
        'operating_margin': info.get('operatingMargins'),
        'roe': info.get('returnOnEquity'),
        'roa': info.get('returnOnAssets'),

        # Growth
        'revenue_growth': info.get('revenueGrowth'),
        'earnings_growth': info.get('earningsGrowth'),

        # Technical
        'beta': info.get('beta'),
        'fifty_day_avg': info.get('fiftyDayAverage'),
        'two_hundred_day_avg': info.get('twoHundredDayAverage'),

        # Short Interest
        'short_ratio': info.get('shortRatio'),
        'short_percent_float': info.get('shortPercentOfFloat'),

        # Analyst Data
        'target_price': info.get('targetMeanPrice'),
        'recommendation': info.get('recommendationKey'),
        'num_analysts': info.get('numberOfAnalystOpinions'),
    }
```

---

## 📋 Summary

### ✅ What yfinance Provides

**ALL your requested fields:**
- ✅ Previous Close, Open, Bid, Ask (with sizes)
- ✅ Day's Range, 52 Week Range
- ✅ Volume, Average Volume
- ✅ Market Cap, Beta
- ✅ PE Ratio, EPS
- ✅ Earnings Date, Target Price

**PLUS 165+ additional fields:**
- Financial ratios (P/B, P/S, PEG, etc.)
- Profitability metrics (margins, ROE, ROA)
- Growth metrics (revenue, earnings growth)
- Balance sheet data (cash, debt, ratios)
- Cash flow data
- Short interest data
- Analyst recommendations
- Company information

### 📊 Data Quality

- ✅ **Free & No API Key Required**
- ✅ **Real company data from Yahoo Finance**
- ✅ **Historical price data**
- ✅ **Regular updates**
- ⚠️ **Some fields may be null** (handle with `.get()`)
- ⚠️ **15-minute delay on free tier** (check `exchangeDataDelayedBy`)

### 🚀 Ready to Use

The screener already uses yfinance - you have access to all this data! Just add the fields you need to the `get_stock_fundamentals()` function.

---

**Test it yourself:**
```bash
uv run python example/test_yfinance_data.py
```
