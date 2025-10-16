# Stock2Concept Matrix Explained

## What is Stock2Concept?

**stock2concept** is a binary matrix that maps stocks to predefined "concepts" (categories/groups).

**Shape**: `[N_stocks, N_concepts]`
- Each row = 1 stock
- Each column = 1 concept
- Value = 1 if stock belongs to that concept, 0 otherwise

---

## Concrete Example

### Simple Example (5 stocks, 4 concepts)

```
Concepts: Tech, Finance, Energy, Healthcare

         Tech  Finance  Energy  Healthcare
AAPL     1.0    0.0     0.0      0.0
MSFT     1.0    0.0     0.0      0.0
JPM      0.0    1.0     0.0      0.0
XOM      0.0    0.0     1.0      0.0
JNJ      0.0    0.0     0.0      1.0
```

**Interpretation**:
- AAPL belongs to Tech sector
- MSFT belongs to Tech sector
- JPM belongs to Finance sector
- XOM belongs to Energy sector
- JNJ belongs to Healthcare sector

### Multi-Concept Example

Stocks can belong to MULTIPLE concepts:

```
Concepts: [Sector, Market Cap, Volatility]
          Tech  Finance  LargeCap  SmallCap  HighVol  LowVol

AAPL      1.0    0.0      1.0       0.0       0.0      1.0
MSFT      1.0    0.0      1.0       0.0       0.0      1.0
JPM       0.0    1.0      1.0       0.0       0.0      1.0
TSLA      1.0    0.0      1.0       0.0       1.0      0.0
GME       0.0    0.0      0.0       1.0       1.0      0.0
```

**Interpretation**:
- AAPL: Tech + Large Cap + Low Volatility
- MSLA: Tech + Large Cap + Low Volatility
- JPM: Finance + Large Cap + Low Volatility
- TSLA: Tech + Large Cap + High Volatility
- GME: Small Cap + High Volatility

---

## What are "Concepts"?

Concepts are **any groupings** that capture shared behavior:

### 1. Sector Classification (Most Common)

**GICS Sectors** (11 sectors):
```
1. Information Technology
2. Financials
3. Health Care
4. Consumer Discretionary
5. Communication Services
6. Industrials
7. Consumer Staples
8. Energy
9. Utilities
10. Real Estate
11. Materials
```

### 2. Industry Classification

**GICS Industry Groups** (24 industry groups):
```
Tech:
- Software & Services
- Technology Hardware & Equipment
- Semiconductors

Finance:
- Banks
- Diversified Financials
- Insurance

Healthcare:
- Pharma & Biotech
- Healthcare Equipment & Services
```

### 3. Market Cap Groups

```
- Large Cap (>$10B)
- Mid Cap ($2B-$10B)
- Small Cap (<$2B)
```

### 4. Style Factors

```
- Value stocks (low P/E, high dividend)
- Growth stocks (high P/E, high growth)
- Momentum stocks (recent outperformance)
```

### 5. Custom Concepts

```
- Volatility groups (high/medium/low vol)
- Liquidity groups (high/medium/low volume)
- Geographic exposure (domestic/international)
- ESG categories (high/medium/low ESG score)
```

---

## Why HIST Needs Stock2Concept

### The Problem HIST Solves

**XGBoost approach** (no concept information):
```python
# Predict each stock independently
predict(AAPL_features) → 0.02
predict(MSFT_features) → 0.01
predict(JPM_features) → 0.015

# Problem: No awareness that AAPL and MSFT should move together!
```

**HIST approach** (with stock2concept):
```python
# Step 1: Aggregate stocks into concepts
Tech_concept = average(AAPL_features, MSFT_features, GOOGL_features, ...)
Finance_concept = average(JPM_features, BAC_features, WFC_features, ...)

# Step 2: Learn concept-level patterns
"Tech sector is strong today" → +0.015 boost to all tech stocks

# Step 3: Apply concept influence to individual stocks
AAPL: +0.015 (Tech boost) + 0.005 (individual) = +0.020
MSFT: +0.015 (Tech boost) - 0.003 (individual) = +0.012
JPM:  +0.008 (Finance boost) + 0.007 (individual) = +0.015

# Now AAPL and MSFT move together (shared Tech boost)
# But individual patterns still matter
```

### Key Benefit: Cross-Sectional Consistency

**Without concepts**:
```
Day 1: AAPL > MSFT (random)
Day 2: MSFT > AAPL (random)
Day 3: AAPL > MSFT (random)

→ Inconsistent ranking → Rank IC ≈ 0
```

**With concepts**:
```
Day 1: Tech sector +2% → AAPL +2.5%, MSFT +1.8%
Day 2: Tech sector -1% → AAPL -0.8%, MSFT -1.2%
Day 3: Tech sector +1% → AAPL +1.3%, MSFT +0.9%

Consistent pattern: AAPL usually > MSFT within Tech
→ Stable ranking → Rank IC > 0!
```

---

## Real Example: Qlib CSI300

From the qlib HIST paper, CSI300 stock2concept has:

```
Shape: (300 stocks, 83 concepts)

Concepts include:
- GICS Sectors (11)
- GICS Industry Groups (24)
- Market Cap Groups (3)
- Other custom groupings (45)

Example:
Stock "000001.XSHE" (Ping An Bank):
- Belongs to: Finance sector
- Belongs to: Banks industry
- Belongs to: Large Cap
- Total: 3-5 active concepts

Stock "600519.XSHG" (Kweichow Moutai):
- Belongs to: Consumer Staples sector
- Belongs to: Food & Beverage industry
- Belongs to: Large Cap
- Total: 3-5 active concepts
```

---

## How to Create Stock2Concept for US Stocks

### Option 1: Use GICS Sectors (Simple)

**11 sectors** (easiest to start):

```python
import numpy as np
import pandas as pd

# Define sector mapping
sector_map = {
    'AAPL': 'Tech',
    'MSFT': 'Tech',
    'GOOGL': 'Communication',
    'META': 'Communication',
    'JPM': 'Finance',
    'BAC': 'Finance',
    'JNJ': 'Healthcare',
    'PFE': 'Healthcare',
    'XOM': 'Energy',
    'CVX': 'Energy',
    # ... all stocks
}

# Create unique concept list
concepts = ['Tech', 'Finance', 'Healthcare', 'Energy',
            'Communication', 'Consumer Discretionary', 'Consumer Staples',
            'Industrials', 'Materials', 'Real Estate', 'Utilities']

# Build matrix
stock_list = list(sector_map.keys())
stock2concept = np.zeros((len(stock_list), len(concepts)))

for i, stock in enumerate(stock_list):
    sector = sector_map[stock]
    j = concepts.index(sector)
    stock2concept[i, j] = 1.0

# Save
np.save('stock2concept_gics_sectors.npy', stock2concept)
```

**Result**:
```
Shape: (3000 stocks, 11 concepts)
Each stock belongs to exactly 1 sector
```

### Option 2: GICS Sectors + Industries (Better)

**11 sectors + 24 industry groups = 35 concepts**:

```python
# Each stock belongs to both sector AND industry
stock2concept = np.zeros((3000, 35))

# Example: AAPL
stock2concept[0, sector_tech] = 1.0           # Sector: Tech
stock2concept[0, industry_software] = 1.0     # Industry: Software

# Example: JPM
stock2concept[100, sector_finance] = 1.0      # Sector: Finance
stock2concept[100, industry_banks] = 1.0      # Industry: Banks
```

### Option 3: Full Featured (Best)

**Sectors + Industries + Market Cap + Volatility = ~50 concepts**:

```python
concepts = [
    # 11 GICS Sectors
    'Tech', 'Finance', 'Healthcare', ...,

    # 24 GICS Industries
    'Software', 'Banks', 'Pharma', ...,

    # 3 Market Cap groups
    'LargeCap', 'MidCap', 'SmallCap',

    # 3 Volatility groups
    'HighVol', 'MediumVol', 'LowVol',

    # 3 Liquidity groups
    'HighLiquidity', 'MediumLiquidity', 'LowLiquidity',

    # Other custom
    'Value', 'Growth', 'Momentum', ...
]

# Each stock belongs to ~5-8 concepts
```

---

## Where to Get Sector/Industry Data

### Option 1: yfinance (Free)

```python
import yfinance as yf

ticker = yf.Ticker("AAPL")
info = ticker.info

sector = info.get('sector')        # 'Technology'
industry = info.get('industry')    # 'Consumer Electronics'
market_cap = info.get('marketCap') # 3000000000000
```

### Option 2: pandas_datareader (Free)

```python
from pandas_datareader import data as pdr

# Get sector from Yahoo Finance
stock_info = pdr.get_quote_yahoo('AAPL')
```

### Option 3: Download CSV Mapping (Manual)

Many financial data sites provide sector/industry CSV files:
- Wikipedia: List of S&P 500 companies with sectors
- Kaggle: US stock sector datasets
- NASDAQ website: Company listings with industry

### Option 4: Use Qlib's Built-in (If Available)

```python
# Qlib might have US stock sector data
from qlib.data import D

# Check if sector data exists
instruments = D.instruments(market='sp500')
```

---

## Practical Example: Building stock2concept

Let's build one for liquid_stocks:

```python
import numpy as np
import pandas as pd
import qlib
from qlib.data import D
import yfinance as yf

# Step 1: Get stock list
qlib.init(provider_uri='...', region='cn')
instruments = D.instruments(market='liquid_stocks')
stock_list = instruments.get_level_values('instrument').unique().tolist()

print(f"Found {len(stock_list)} stocks")

# Step 2: Define concepts (start simple with GICS sectors)
sectors = [
    'Technology',
    'Financials',
    'Health Care',
    'Consumer Discretionary',
    'Communication Services',
    'Industrials',
    'Consumer Staples',
    'Energy',
    'Utilities',
    'Real Estate',
    'Materials'
]

# Step 3: Fetch sector for each stock
stock_to_sector = {}

for stock in stock_list:
    try:
        ticker = yf.Ticker(stock)
        sector = ticker.info.get('sector', 'Unknown')
        stock_to_sector[stock] = sector
        print(f"{stock}: {sector}")
    except:
        stock_to_sector[stock] = 'Unknown'

# Step 4: Build matrix
stock2concept = np.zeros((len(stock_list), len(sectors)))

for i, stock in enumerate(stock_list):
    sector = stock_to_sector[stock]
    if sector in sectors:
        j = sectors.index(sector)
        stock2concept[i, j] = 1.0

# Step 5: Save
np.save('stock2concept_liquid_stocks.npy', stock2concept)
print(f"Saved stock2concept matrix: {stock2concept.shape}")

# Step 6: Also save stock_index mapping
stock_index = {stock: i for i, stock in enumerate(stock_list)}
np.save('stock_index_liquid_stocks.npy', stock_index)
```

---

## Summary

**stock2concept** = Matrix mapping stocks to predefined groups

**Purpose**: Help HIST learn shared patterns across related stocks

**Key insight**:
- Stocks in same sector often move together
- By modeling this explicitly, HIST gets better ranking consistency
- Result: Higher Rank IC!

**To use HIST, you need**:
1. Create stock2concept matrix (stocks × sectors/industries)
2. Create stock_index dict (stock symbol → integer ID)
3. Save both as .npy files
4. Pass file paths to HIST config

**Simplest approach**: Start with 11 GICS sectors
- Use yfinance to fetch sector for each stock
- Build binary matrix
- Save and use in HIST

---

## Next Steps

1. **Fetch sector data** for liquid_stocks using yfinance
2. **Build stock2concept matrix** (3000 stocks × 11 sectors)
3. **Build stock_index mapping** (symbol → ID)
4. **Configure HIST** to use these files
5. **Train and compare** with XGBoost results

Expected improvement: Rank IC from 0 → 0.02-0.04
