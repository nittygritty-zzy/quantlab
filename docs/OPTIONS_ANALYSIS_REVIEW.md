# QuantLab Options Analysis - Comprehensive Code Review

**Analysis Date:** 2025-10-16  
**Codebase Location:** `/Users/zheyuanzhao/workspace/quantlab`  
**Scope:** Medium-depth analysis of options-related functionality

---

## Executive Summary

QuantLab has a **robust options analysis framework** with:
- Multi-source data integration (Polygon, Alpha Vantage, yfinance)
- Complete Greeks calculation (first and second-order)
- ITM/OTM analysis capabilities
- Strategic options patterns (mean reversion with options)
- Minute-level data support (not yet exposed in CLI)

**Current Status:** Fully functional for daily options analysis with real market data.

---

## 1. CURRENT OPTIONS ANALYSIS CAPABILITIES

### 1.1 Main Analysis Module: `options_analyzer.py`
**Location:** `/Users/zheyuanzhao/workspace/quantlab/quantlab/analysis/options_analyzer.py`

**Key Class:** `OptionsAnalyzer`

**Primary Features:**
- ✅ ITM call analysis (`analyze_itm_calls()`)
- ✅ ITM put analysis (`analyze_itm_puts()`)
- ✅ Options scoring and ranking
- ✅ Liquidity assessment
- ✅ Time decay evaluation
- ✅ Volatility exposure analysis

**Scoring Algorithm:**
```python
# Call Option Scoring (100+ points possible)
- Delta score (0-30 pts): Prefers delta 0.7-0.9 (deep ITM)
- Theta score (0-25 pts): Lower absolute value is better
- Liquidity score (0-20 pts): Higher open interest better
- Charm score (0-15 pts): Positive charm valued
- Vanna/Vomma (0-10 pts): Volatility convexity

# Put Option Scoring (similar logic)
- Delta score (0-30 pts): Prefers delta -0.7 to -0.9
- Theta score (0-25 pts)
- Liquidity score (0-20 pts)
- Charm score (0-15 pts): Negative charm valued for puts
```

**Usage Example:**
```python
from quantlab.analysis.options_analyzer import OptionsAnalyzer

analyzer = OptionsAnalyzer(data_manager)

# Get top 10 ITM calls (5-20% ITM)
recommendations = analyzer.analyze_itm_calls(
    ticker="AAPL",
    min_itm_pct=5.0,
    max_itm_pct=20.0,
    min_open_interest=100,
    top_n=10
)

# Each recommendation includes:
# - contract: OptionContract object (full Greeks)
# - score: Float (0-100+)
# - analysis: Dict with liquidity/decay/volatility/greeks_summary
```

---

## 2. OPTIONS DATA STRUCTURES

### 2.1 Core Data Model: `OptionContract`
**Location:** `/Users/zheyuanzhao/workspace/quantlab/quantlab/models/ticker_data.py`

```python
@dataclass
class OptionContract:
    """Options contract data with Greeks"""
    # Required identifiers
    contract_ticker: str           # e.g., "AAPL240119C00175000"
    underlying_ticker: str         # e.g., "AAPL"
    strike_price: float
    expiration_date: date
    option_type: str              # 'call' or 'put'
    
    # Pricing data
    bid: Optional[float] = None
    ask: Optional[float] = None
    last_price: Optional[float] = None
    mark: Optional[float] = None
    
    # Volume metrics
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    
    # Volatility
    implied_volatility: Optional[float] = None
    
    # FIRST-ORDER GREEKS
    delta: Optional[float] = None    # ∂Price/∂S
    gamma: Optional[float] = None    # ∂Delta/∂S
    theta: Optional[float] = None    # ∂Price/∂t (per day)
    vega: Optional[float] = None     # ∂Price/∂IV (per 1%)
    rho: Optional[float] = None      # ∂Price/∂r
    
    # ADVANCED GREEKS (second-order + exotic)
    vanna: Optional[float] = None    # ∂Delta/∂IV
    charm: Optional[float] = None    # ∂Delta/∂t
    vomma: Optional[float] = None    # ∂Vega/∂IV
    
    # Analysis metrics
    itm_percentage: Optional[float] = None  # % in/out-of-money
    
    # Metadata
    data_source: Optional[str] = None  # "polygon", "parquet", etc.
    fetched_at: Optional[datetime] = None
```

### 2.2 Related Data Models

**TickerSnapshot:** Stock price data
```python
@dataclass
class TickerSnapshot:
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    change_percent: Optional[float] = None
```

**SentimentData:** News sentiment for strategy context
```python
@dataclass
class SentimentData:
    ticker: str
    sentiment_score: Optional[float]  # -1.0 to +1.0
    sentiment_label: Optional[str]    # 'bullish'/'neutral'/'bearish'
    articles_analyzed: Optional[int]
```

---

## 3. GREEKS CALCULATIONS

### 3.1 Black-Scholes Implementation
**Location:** `/Users/zheyuanzhao/workspace/quantlab/quantlab/analysis/greeks_calculator.py`

**Class:** `BlackScholesGreeks`

**Implemented Greeks:**

#### First-Order Greeks:
```python
# DELTA: Directional exposure
delta_call(S, K, T, r, sigma) -> float
delta_put(S, K, T, r, sigma) -> float
# Interpretation: How much option price changes per $1 move in stock
# Range: Call [0, 1], Put [-1, 0]

# GAMMA: Delta sensitivity
gamma(S, K, T, r, sigma) -> float
# Interpretation: How much delta changes per $1 move
# Peaks at-the-money, important for hedging

# THETA: Time decay
theta_call(S, K, T, r, sigma) -> float  # Per day
theta_put(S, K, T, r, sigma) -> float   # Per day
# Interpretation: How much option loses to time daily
# Negative for long options (you lose value)

# VEGA: Volatility sensitivity
vega(S, K, T, r, sigma) -> float  # Per 1% change
# Interpretation: How much option gains per 1% IV increase
# Higher for ATM, longer-dated options
```

#### Advanced Greeks:
```python
# VANNA: Delta's volatility sensitivity
vanna(S, K, T, r, sigma) -> float  # Per 1% IV change
# Interpretation: Delta changes by X when IV rises 1%
# Important for vol traders: Can help/hurt depending on view

# CHARM: Delta's time decay
charm_call(S, K, T, r, sigma) -> float  # Per day
charm_put(S, K, T, r, sigma) -> float   # Per day
# Interpretation: How much delta drifts daily from time decay
# Critical for short-term trading strategies

# VOMMA (Volga): Vega's volatility sensitivity
vomma(S, K, T, r, sigma) -> float  # Per 1% IV squared
# Interpretation: Vega changes by X when IV rises 1%
# Positive vomma: increased exposure to big vol moves
```

### 3.2 Main Calculation Function
```python
def calculate_advanced_greeks(
    stock_price: float,
    strike_price: float,
    days_to_expiry: int,
    risk_free_rate: float,
    implied_volatility: float,
    option_type: str = 'call'
) -> Dict[str, float]:
    """
    Returns dictionary with all 7 Greeks:
    {
        'delta': 0.6234,
        'gamma': 0.0089,
        'theta': -0.0234,
        'vega': 0.1567,
        'vanna': -0.0045,
        'charm': 0.0012,
        'vomma': 0.0156
    }
    """
```

### 3.3 Greeks Utility Functions
```python
days_to_expiry(expiry_date: str|date) -> int
# Safely converts expiry dates to days, min 1 day
```

---

## 4. MULTI-SOURCE OPTIONS ANALYSIS

### 4.1 Advanced Analysis Script
**Location:** `/Users/zheyuanzhao/workspace/quantlab/scripts/analysis/multi_source_options_analysis.py`

**Class:** `MultiSourceOptionsAnalysis`

**Data Integration:**

| Source | Data | Purpose |
|--------|------|---------|
| **Polygon** | Options chains, Greeks, bid/ask, volume, OI | Primary options data |
| **Alpha Vantage** | 3-month Treasury rate, news sentiment | Real risk-free rate, market context |
| **yfinance** | VIX, analyst recommendations, institutional holdings | Volatility environment, big picture |

**Workflow:**
```
1. fetch_from_polygon()
   ├─ Get current stock price
   ├─ Download all options chains
   ├─ Filter ITM calls (5-20% ITM range)
   └─ Collect Polygon Greeks

2. fetch_from_alpha_vantage()
   ├─ Get 3-month Treasury yield
   └─ Analyze news sentiment (bullish/neutral/bearish)

3. fetch_from_yfinance()
   ├─ VIX current + 5-day average
   ├─ Analyst recommendations
   └─ Institutional holdings

4. calculate_enhanced_greeks()
   ├─ Use REAL Treasury rate (not default 4.5%)
   ├─ Recalculate all Greeks with Black-Scholes
   └─ Add advanced Greeks (vanna, charm, vomma)

5. generate_comprehensive_report()
   ├─ Save JSON with raw data
   └─ Create Markdown with analysis + insights
```

**Output Example:**
```markdown
# AAPL MULTI-SOURCE OPTIONS ANALYSIS
Stock Price: $228.50
Risk-Free Rate: 4.256% (Real 3-month Treasury)
VIX: 18.5 (5-day avg: 19.2)

## TOP RECOMMENDATION
Strike: $225.00, Expires 2025-10-17
Position: 1.5% ITM
Delta: 0.7234 (captures 72% of moves)
Theta: -0.0145 (loses $1.45/day)
Vega: 0.1567 (gains $15.67 per 1% vol rise)
Vanna: -0.0056 (delta drops if IV rises)
News Sentiment: Bullish (+0.32 score)
```

---

## 5. DATA MANAGER INTEGRATION

### 5.1 DataManager Options Methods
**Location:** `/Users/zheyuanzhao/workspace/quantlab/quantlab/data/data_manager.py`

```python
class DataManager:
    def get_options_chain(
        self,
        ticker: str,
        expiration_date: Optional[date] = None,
        option_type: Optional[str] = None,
        min_itm_pct: float = 5.0,
        max_itm_pct: float = 20.0,
        use_cache: bool = True
    ) -> List[OptionContract]:
        """
        Get options with automatic Greeks calculation
        
        Strategy:
        1. Get current stock price
        2. Fetch from Polygon API
        3. Filter by ITM range
        4. Calculate/fetch advanced Greeks
        5. Return enriched OptionContract objects
        
        Returns list of 5-20% ITM options with all Greeks
        """
        
    def get_vix(self) -> Optional[Dict[str, float]]:
        """Get current VIX from yfinance"""
        
    def _get_risk_free_rate(self) -> float:
        """
        Smart risk-free rate retrieval:
        1. Try lookup table (cached daily)
        2. Fallback to Alpha Vantage API
        3. Default to 4.5%
        """
```

### 5.2 Data Flow
```
User Request
    ↓
DataManager.get_options_chain()
    ├─→ get_stock_price() [Polygon API or Parquet]
    ├─→ _get_risk_free_rate() [Lookup table or Alpha Vantage]
    ├─→ polygon.get_options_chain() [Polygon API]
    │
    ├─→ For each option:
    │   ├─ Calculate ITM percentage
    │   ├─ Calculate advanced_greeks() [Black-Scholes]
    │   └─ Create OptionContract object
    │
    └─→ Return filtered + enriched options list
```

---

## 6. STRATEGY PATTERNS

### 6.1 Mean Reversion Options Strategy
**Location:** `/Users/zheyuanzhao/workspace/quantlab/quantlab/backtest/strategies/mean_reversion_strategy.py`

**Class:** `MeanReversionOptionsStrategy(TopkDropoutStrategy)`

**Strategy Logic:**
```python
ENTRY CONDITIONS:
- RSI < oversold_threshold (default: 30)
- Price < Bollinger Band lower bound
- Volume trend positive (capitulation selling)

EXIT CONDITIONS:
- RSI > overbought_threshold (default: 70)
- Price > SMA(20)
- Stop loss triggered (default: -10%)

PARAMETERS:
- topk: 30 (max positions)
- n_drop: 3 (stocks to replace per period)
- min_hold_days: 2 (minimum holding period)
```

**How It Uses Options:**
```python
# Entry signal uses technical analysis to identify oversold
# Could be combined with:
# - Buying ITM calls at support (high delta ~0.8)
# - Synthetic long calls with low theta
# - Call spread with negative vanna hedge

# Greeks utilization:
# - Delta: High (0.7-0.9) for directional exposure
# - Theta: Low (minimize time decay)
# - Vega: Neutral or slightly positive
# - Charm: Watch for delta decay during hold
```

---

## 7. PARQUET-BASED OPTIONS DATA

### 7.1 Minute-Level Options Support
**Status:** Data exists but query not exposed in CLI

**Available Data:**
- Options minute data: 2024-01 through 2025-10
- ~2-5 GB per ticker per day (100+ contracts × 390 minutes)
- Full Greeks at each minute

**Implementation Plan (Not Yet Done):**
```python
# Would be added to parquet_reader.py:
def get_options_minute(
    self,
    underlying_tickers: List[str],
    start_datetime: Optional[datetime] = None,
    end_datetime: Optional[datetime] = None,
    option_type: Optional[str] = None,
    min_strike: Optional[float] = None,
    max_strike: Optional[float] = None,
    limit: Optional[int] = None
) -> pd.DataFrame:
    """
    Query minute-level options data
    WARNING: MASSIVE dataset - requires strict filtering
    """
```

**Use Cases (Future):**
- Intraday volatility analysis
- Options flow detection
- Market making research
- Greeks dynamics tracking

---

## 8. FILE STRUCTURE SUMMARY

```
quantlab/
├── quantlab/
│   ├── analysis/
│   │   ├── options_analyzer.py          [Main options analysis]
│   │   ├── greeks_calculator.py         [Black-Scholes implementation]
│   │   └── technical_indicators.py      [RSI, BB, SMA, etc.]
│   │
│   ├── data/
│   │   ├── data_manager.py              [Options chain fetching]
│   │   ├── api_clients.py               [Polygon/AlphaVantage/yfinance]
│   │   ├── parquet_reader.py            [Historical minute data]
│   │   └── lookup_tables.py             [Treasury rates cache]
│   │
│   ├── models/
│   │   └── ticker_data.py               [OptionContract dataclass]
│   │
│   └── backtest/
│       └── strategies/
│           ├── mean_reversion_strategy.py    [Options-aware strategy]
│           ├── sentiment_momentum_strategy.py
│           └── tech_fundamental_strategy.py
│
├── scripts/analysis/
│   ├── multi_source_options_analysis.py [End-to-end analysis]
│   └── advanced_greeks_calculator.py    [Standalone calculator]
│
└── docs/
    ├── OPTIONS_MINUTE_IMPLEMENTATION.md  [Implementation plan]
    └── ANALYSIS_CAPABILITIES.md          [Feature documentation]
```

---

## 9. KEY FEATURES & CAPABILITIES

### 9.1 What's Implemented
✅ Options chain retrieval (Polygon API)  
✅ All first-order Greeks (Delta, Gamma, Theta, Vega, Rho)  
✅ All advanced Greeks (Vanna, Charm, Vomma)  
✅ Black-Scholes calculations with real Treasury rates  
✅ ITM/OTM filtering and analysis  
✅ Options scoring/ranking system  
✅ Multi-source data integration  
✅ News sentiment analysis  
✅ VIX tracking  
✅ Institutional holdings data  
✅ Mean reversion strategy pattern  
✅ Caching with TTL  

### 9.2 What's NOT Yet Exposed
❌ CLI commands for options analysis  
❌ Minute-level options queries (data exists, code not finished)  
❌ Spread strategy builder (call spreads, straddles, etc.)  
❌ Greeks-based portfolio hedging  
❌ Live options flow detection  
❌ IV surface mapping  
❌ Skew analysis  

---

## 10. CONFIGURATION & USAGE

### 10.1 Required Environment Variables
```bash
POLYGON_API_KEY=vDr8GDaQ87Z9Mwe5IiCKzGcRP9pnO8TW
ALPHAVANTAGE_API_KEY=3NHDCBRE0IKFB8XW
# (yfinance needs no API key)
```

### 10.2 Example Usage Pattern
```python
from quantlab.data.data_manager import DataManager
from quantlab.analysis.options_analyzer import OptionsAnalyzer

# Initialize
dm = DataManager(config, db, parquet)

# Get options chain (auto-calculates Greeks)
options = dm.get_options_chain(
    ticker="AAPL",
    min_itm_pct=5.0,
    max_itm_pct=20.0
)  # Returns List[OptionContract]

# Analyze
analyzer = OptionsAnalyzer(dm)
recommendations = analyzer.analyze_itm_calls("AAPL", top_n=10)

# Access Greeks
for rec in recommendations:
    opt = rec['contract']
    print(f"Strike: ${opt.strike_price}")
    print(f"Delta: {opt.delta:.4f}")
    print(f"Vanna: {opt.vanna:.6f}")
    print(f"Charm: {opt.charm:.6f}")
```

---

## 11. IMPORTANT NOTES

### 11.1 Risk-Free Rate Handling
The system uses a **smart 3-tier approach**:
1. **Cached daily rate** (fastest) - from lookup tables
2. **API fetch** (slower) - from Alpha Vantage  
3. **Default 4.5%** (fallback) - when APIs unavailable

This is CRITICAL for accurate Greeks: Using wrong rate can throw off pricing significantly.

### 11.2 Greeks Limitations
- Black-Scholes assumes European options (simple)
- American options need binomial/trinomial model
- Real market Greeks (from Polygon) may differ (wider bids/asks)
- System stores both calculated + Polygon Greeks for comparison

### 11.3 Data Quality Issues
- Polygon sometimes missing Greeks data
- System auto-calculates when Polygon data absent
- Verification logic compares calculated vs Polygon (1% tolerance)
- Minute data very large - needs careful filtering

---

## 12. RECOMMENDED NEXT STEPS

### To Enhance Options Capabilities:
1. **Add CLI Commands**
   - `quantlab options analyze AAPL` - ITM analysis
   - `quantlab options chain AAPL --type call` - View full chain
   - `quantlab options minute AAPL --start "2025-10-15 09:30"` - Minute data

2. **Spread Strategies**
   - Call spread builder (bull/bear spreads)
   - Straddle/strangle constructor
   - Iron condor builder

3. **Greeks-Based Portfolio Management**
   - Portfolio Greeks aggregation (net delta, gamma, vega, theta)
   - Hedging suggestions
   - Greeks exposure limits

4. **Advanced Analytics**
   - IV surface visualization
   - Skew analysis
   - Vol term structure

---

## CONCLUSION

QuantLab has a **solid, production-ready options analysis foundation**:
- Complete Greeks calculations (Black-Scholes)
- Multi-source data integration
- ITM analysis and scoring
- Strategy integration patterns
- Extensive data available

The main gaps are **CLI exposure** and **strategy builders**, not the underlying engine.

