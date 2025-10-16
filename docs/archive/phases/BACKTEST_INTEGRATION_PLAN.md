# Backtesting Framework Integration Plan

**Created**: 2025-10-15
**Status**: Planning Phase
**Goal**: Bridge QuantLab CLI features with existing Qlib backtest infrastructure

---

## Executive Summary

QuantLab already has a **mature backtesting system** built on Microsoft's Qlib framework. The integration plan focuses on:
1. **Connecting** new CLI features (technical indicators, options analysis) to existing backtest engine
2. **Creating** new trading strategies that leverage real-time data sources
3. **Extending** the Alpha158 feature set with Polygon API indicators
4. **Building** a unified workflow from research → backtest → live trading

---

## Current State Assessment

### ✅ What Already Exists

**Qlib Backtest Infrastructure** (`qlib_repo/qlib/backtest/`):
- Event-driven backtest engine with daily execution loop
- Portfolio metrics tracking (IC, ICIR, Sharpe, drawdown)
- Multiple strategy implementations (TopK, WeightBased, EnhancedIndexing)
- MLflow experiment tracking
- 30+ ML models (LightGBM, XGBoost, HIST, LSTM, etc.)

**Data Infrastructure**:
- 19 months of US stocks daily OHLCV (2024-2025)
- 13,187 liquid stocks (filtered from 14,310 total)
- 984 delisted stocks included (survivorship bias fix)
- Alpha158 feature handler (158 technical indicators)

**Analysis Tools**:
- Visualization scripts (6-panel charts)
- Data quality validation
- Comprehensive documentation

### 🆕 New CLI Capabilities (To Integrate)

**Real-Time Data Sources**:
- ✅ Polygon API: Unlimited calls, technical indicators (SMA, EMA, MACD, RSI)
- ✅ Alpha Vantage: News sentiment, treasury rates
- ✅ yfinance: Fundamentals, analyst recommendations
- ✅ Parquet warehouse: Historical OHLCV data

**Analysis Modules**:
- ✅ Technical Indicators: 9 indicators with signal interpretation
- ✅ Options Analysis: Advanced Greeks (Vanna, Charm, Vomma), ITM scoring
- ✅ Sentiment Analysis: News-based bullish/bearish signals
- ✅ Fundamental Analysis: P/E ratios, growth metrics, recommendations

**Infrastructure**:
- ✅ DataManager: Unified data routing with caching
- ✅ LookupTables: Slowly-changing data cache
- ✅ Portfolio Management: Position tracking, rebalancing

---

## Integration Architecture

### Phase 1: Feature Bridge (Weeks 1-2)

**Goal**: Make CLI data sources available to Qlib backtest engine

**Tasks**:
1. **Create QuantLabFeatureHandler** (extend Qlib's DataHandlerLP)
   ```python
   # Location: quantlab/backtest/handlers.py
   class QuantLabFeatureHandler(DataHandlerLP):
       """
       Feature handler that combines:
       - Qlib historical data
       - Polygon API technical indicators (via DataManager)
       - Fundamental data (via DataManager)
       - Sentiment scores (cached in LookupTables)
       """
   ```

2. **Implement Real-Time Indicator Fetcher**
   ```python
   # Location: quantlab/backtest/realtime_features.py
   class RealtimeIndicatorFetcher:
       """
       Fetch technical indicators from Polygon API
       Map to Qlib feature format
       Cache results for backtest performance
       """
   ```

3. **Create Feature Mapping Configuration**
   ```yaml
   # Location: configs/features/quantlab_features.yaml
   features:
     technical:
       - polygon_sma_20
       - polygon_ema_12
       - polygon_rsi_14
       - polygon_macd_histogram
     fundamental:
       - yf_pe_ratio
       - yf_forward_pe
       - yf_revenue_growth
     sentiment:
       - av_sentiment_score
       - av_articles_positive
   ```

**Deliverables**:
- ✅ New handler class in `quantlab/backtest/handlers.py`
- ✅ Feature fetcher in `quantlab/backtest/realtime_features.py`
- ✅ Configuration in `configs/features/quantlab_features.yaml`
- ✅ Unit tests for feature mapping

---

### Phase 2: Strategy Development (Weeks 3-4)

**Goal**: Create trading strategies that use new features

**Strategy 1: Technical + Fundamental Combo**
```python
# Location: quantlab/backtest/strategies/tech_fundamental_strategy.py
class TechFundamentalStrategy(TopkDropoutStrategy):
    """
    Long-only strategy combining:
    - Technical indicators (RSI, MACD) from Polygon
    - Fundamental filters (P/E < 30, Revenue Growth > 0)
    - Sentiment boost (multiply score by sentiment)

    Signal = (RSI_Score * 0.4) + (MACD_Score * 0.3) + (Fundamental_Score * 0.3)
    """
```

**Strategy 2: Mean Reversion with Options**
```python
# Location: quantlab/backtest/strategies/mean_reversion_options.py
class MeanReversionOptionsStrategy(BaseStrategy):
    """
    Identify oversold stocks (RSI < 30, Price < BB_lower)
    Backtest synthetic long call positions
    Use advanced Greeks for position sizing

    Entry: RSI < 30 AND Price < Bollinger Lower Band
    Exit: RSI > 70 OR Price > SMA(20)
    """
```

**Strategy 3: Sentiment-Driven Momentum**
```python
# Location: quantlab/backtest/strategies/sentiment_momentum_strategy.py
class SentimentMomentumStrategy(WeightStrategyBase):
    """
    Weight stocks by:
    - Price momentum (SMA crossovers)
    - News sentiment score (Alpha Vantage)
    - Analyst recommendations (yfinance)

    Weight = Momentum_Signal * (1 + Sentiment_Score) * Recommendation_Factor
    """
```

**Deliverables**:
- ✅ 3 new strategy implementations
- ✅ Strategy configuration YAMLs
- ✅ Backtest comparison notebook

---

### Phase 3: Backtest Execution (Weeks 5-6)

**Goal**: Run backtests with new strategies and validate results

**Task 1: Create Workflow Configs**
```yaml
# configs/backtest_quantlab_technical.yaml
qlib_init:
  provider_uri: "/Volumes/sandisk/quantmini-data/data/qlib/stocks_daily"
market: liquid_stocks
benchmark: SPY

task:
  model: LGBModel
  dataset:
    class: QuantLabFeatureHandler  # NEW: Use our handler
    kwargs:
      features:
        - polygon_rsi_14
        - polygon_macd_histogram
        - yf_pe_ratio
        - av_sentiment_score
    segments:
      train: [2024-01-02, 2024-06-30]
      valid: [2024-07-01, 2024-08-31]
      test: [2024-09-01, 2025-09-30]

port_analysis_config:
  strategy:
    class: TechFundamentalStrategy  # NEW: Our strategy
    kwargs:
      topk: 50
      rsi_oversold: 30
      rsi_overbought: 70
  backtest:
    start_time: 2024-09-01
    end_time: 2025-09-30
    account: 100000000
```

**Task 2: Run Experiment Suite**
```bash
# Run baseline (Alpha158)
uv run qrun configs/lightgbm_liquid_universe.yaml

# Run technical indicators strategy
uv run qrun configs/backtest_quantlab_technical.yaml

# Run sentiment momentum strategy
uv run qrun configs/backtest_sentiment_momentum.yaml

# Compare results
uv run python scripts/analysis/compare_strategies.py
```

**Task 3: Create Performance Dashboard**
```python
# scripts/analysis/strategy_dashboard.py
"""
Generate comprehensive comparison:
- IC/ICIR for each strategy
- Cumulative returns vs benchmark
- Drawdown comparison
- Feature importance analysis
- Transaction cost impact
"""
```

**Deliverables**:
- ✅ 3+ backtest configuration files
- ✅ Automated experiment runner script
- ✅ Strategy comparison dashboard
- ✅ Performance report with visualizations

---

### Phase 4: Live Integration Prep (Weeks 7-8)

**Goal**: Prepare for live trading integration

**Task 1: Create Signal Generator Service**
```python
# quantlab/live/signal_generator.py
class LiveSignalGenerator:
    """
    Generate trading signals in real-time:
    1. Fetch current indicators from Polygon API
    2. Apply trained model from backtest
    3. Rank stocks and generate top-K list
    4. Output signals with confidence scores
    """
```

**Task 2: Build Position Manager**
```python
# quantlab/live/position_manager.py
class PositionManager:
    """
    Manage live positions:
    - Track current holdings
    - Calculate target weights from signals
    - Generate rebalancing orders
    - Apply risk controls (max position size, sector limits)
    """
```

**Task 3: Create Paper Trading Mode**
```python
# quantlab/live/paper_trading.py
class PaperTradingEngine:
    """
    Simulate live trading without real money:
    - Execute signals in paper account
    - Track P&L in real-time
    - Compare to backtest results
    - Alert on significant deviations
    """
```

**Deliverables**:
- ✅ Live signal generation service
- ✅ Position management module
- ✅ Paper trading engine
- ✅ Monitoring dashboard

---

## Technical Specifications

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         QuantLab Backtest                        │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      QuantLabFeatureHandler                      │
│  Extends: Qlib DataHandlerLP                                    │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │   Polygon    │  │  yfinance    │  │AlphaVantage  │
         │  Technical   │  │ Fundamentals │  │  Sentiment   │
         │  Indicators  │  │              │  │              │
         └──────────────┘  └──────────────┘  └──────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
         ┌───────────────────────────────────────────────┐
         │          DataManager (existing)                │
         │  - API routing                                 │
         │  - Caching (15min prices, 24hr fundamentals)  │
         │  - Fallback logic                             │
         └───────────────────────────────────────────────┘
                                    │
                                    ▼
         ┌───────────────────────────────────────────────┐
         │       LookupTables (existing)                  │
         │  - Company info                                │
         │  - Analyst ratings                            │
         │  - Treasury rates                             │
         └───────────────────────────────────────────────┘
```

### Feature Schema

**Technical Indicators** (from Polygon API):
```python
{
    "polygon_sma_20": float,      # 20-day Simple Moving Average
    "polygon_sma_50": float,      # 50-day Simple Moving Average
    "polygon_ema_12": float,      # 12-day Exponential Moving Average
    "polygon_ema_26": float,      # 26-day Exponential Moving Average
    "polygon_rsi_14": float,      # 14-day RSI (0-100)
    "polygon_macd_line": float,   # MACD line
    "polygon_macd_signal": float, # MACD signal line
    "polygon_macd_hist": float,   # MACD histogram
}
```

**Fundamental Indicators** (from yfinance):
```python
{
    "yf_pe_ratio": float,         # Trailing P/E
    "yf_forward_pe": float,       # Forward P/E
    "yf_peg_ratio": float,        # PEG ratio
    "yf_profit_margin": float,    # Profit margin
    "yf_roe": float,              # Return on Equity
    "yf_revenue_growth": float,   # Revenue growth YoY
    "yf_target_price": float,     # Analyst target price
}
```

**Sentiment Indicators** (from Alpha Vantage):
```python
{
    "av_sentiment_score": float,     # -1 to 1 (bearish to bullish)
    "av_sentiment_label": str,       # "bullish", "bearish", "neutral"
    "av_articles_positive": int,     # Count of positive articles
    "av_articles_negative": int,     # Count of negative articles
}
```

---

## Implementation Priorities

### Must Have (MVP)
1. ✅ QuantLabFeatureHandler implementation
2. ✅ TechFundamentalStrategy (technical + fundamental combo)
3. ✅ Single backtest workflow config
4. ✅ Basic visualization of results

### Should Have (Full Integration)
5. ⏳ All 3 strategy implementations
6. ⏳ Strategy comparison dashboard
7. ⏳ Automated experiment runner
8. ⏳ Feature importance analysis

### Nice to Have (Future Enhancement)
9. ⏳ Live signal generation
10. ⏳ Paper trading mode
11. ⏳ Real-time monitoring
12. ⏳ Advanced risk controls

---

## Success Metrics

### Backtest Performance
- **IC Improvement**: Target IC > 0.10 (baseline: 0.08)
- **Rank IC**: Target Rank IC > 0.05 (baseline: -0.006)
- **Sharpe Ratio**: Target Sharpe > 2.0 (baseline: 3.94 but unrealistic)
- **Max Drawdown**: Target < 30% (baseline: 39-60%)

### Integration Quality
- **Feature Fetch Speed**: < 1 second per ticker
- **Cache Hit Rate**: > 80% for fundamentals
- **Backtest Runtime**: < 10 minutes for 9-month test period
- **Data Consistency**: 100% match between CLI and backtest features

### Code Quality
- **Test Coverage**: > 80% for new modules
- **Documentation**: Comprehensive docstrings + examples
- **Type Hints**: Full type annotations
- **Linting**: Pass flake8, mypy checks

---

## Risk Mitigation

### Data Quality Risks
**Risk**: API data may have gaps or errors
**Mitigation**:
- Implement comprehensive validation in QuantLabFeatureHandler
- Log all API failures and fallback events
- Compare features against Alpha158 for sanity checks

### Look-Ahead Bias
**Risk**: Using future data in backtest
**Mitigation**:
- Strict timestamp checks in feature handler
- Use point-in-time data from LookupTables
- Document data availability timing for each source

### Overfitting
**Risk**: Strategies optimized on test set
**Mitigation**:
- Use proper train/valid/test splits
- Cross-validation across multiple time periods
- Out-of-sample testing on 2025 data

### API Rate Limits
**Risk**: Exceeding API rate limits during backtest
**Mitigation**:
- Cache all API responses aggressively
- Use Parquet data as fallback
- Implement exponential backoff for retries

---

## File Structure

```
quantlab/
├── backtest/                          # NEW: Backtest integration
│   ├── __init__.py
│   ├── handlers.py                    # QuantLabFeatureHandler
│   ├── realtime_features.py           # API feature fetchers
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── tech_fundamental_strategy.py
│   │   ├── mean_reversion_options.py
│   │   └── sentiment_momentum_strategy.py
│   └── validators.py                  # Data quality checks
├── live/                              # NEW: Live trading prep
│   ├── __init__.py
│   ├── signal_generator.py
│   ├── position_manager.py
│   └── paper_trading.py
├── configs/
│   ├── backtest_quantlab_technical.yaml      # NEW
│   ├── backtest_sentiment_momentum.yaml      # NEW
│   └── features/
│       └── quantlab_features.yaml            # NEW
├── scripts/
│   ├── analysis/
│   │   ├── compare_strategies.py             # NEW
│   │   └── strategy_dashboard.py             # NEW
│   └── backtest/
│       └── run_experiment_suite.py           # NEW
├── tests/
│   └── backtest/                              # NEW
│       ├── test_quantlab_handler.py
│       ├── test_strategies.py
│       └── test_feature_consistency.py
└── docs/
    ├── BACKTEST_INTEGRATION_PLAN.md          # THIS FILE
    └── STRATEGY_GUIDE.md                     # NEW: Strategy documentation
```

---

## Timeline

### Week 1-2: Foundation
- [ ] Implement QuantLabFeatureHandler
- [ ] Create RealtimeIndicatorFetcher
- [ ] Write unit tests for feature mapping
- [ ] Document feature schema

### Week 3-4: Strategy Development
- [ ] Implement TechFundamentalStrategy
- [ ] Implement MeanReversionOptionsStrategy
- [ ] Implement SentimentMomentumStrategy
- [ ] Create strategy configs

### Week 5-6: Backtest Execution
- [ ] Run baseline experiments
- [ ] Run new strategy experiments
- [ ] Generate comparison visualizations
- [ ] Write performance report

### Week 7-8: Live Prep
- [ ] Build signal generator
- [ ] Create position manager
- [ ] Implement paper trading
- [ ] Deploy monitoring dashboard

---

## Dependencies

**Python Packages** (already installed):
- ✅ qlib - Backtest engine
- ✅ polygon - Polygon API client
- ✅ yfinance - Fundamentals data
- ✅ requests - Alpha Vantage API
- ✅ lightgbm/xgboost - ML models
- ✅ mlflow - Experiment tracking

**External Services** (already configured):
- ✅ Polygon API - Unlimited calls (Starter plan)
- ✅ Alpha Vantage API - 5 calls/min (free tier)
- ✅ yfinance - No rate limits

**Data Infrastructure** (already available):
- ✅ Parquet warehouse - 19 months OHLCV data
- ✅ DuckDB - Local caching
- ✅ LookupTables - Slowly-changing data

---

## References

**Existing Documentation**:
- `docs/BACKTEST_SUMMARY.md` - Overview of Qlib backtest system
- `docs/EXPERIMENT_SUMMARY.md` - Detailed experiment walkthroughs
- `docs/ALPHA158_EXPLAINED.md` - Feature engineering guide
- `docs/ANALYSIS_CAPABILITIES.md` - CLI features documentation

**Code References**:
- `qlib_repo/qlib/contrib/strategy/signal_strategy.py` - Strategy base class
- `qlib_repo/qlib/backtest/backtest.py` - Backtest engine
- `quantlab/data/data_manager.py` - Data routing and caching
- `quantlab/analysis/technical_indicators.py` - Indicator calculations

**Configuration Examples**:
- `configs/lightgbm_liquid_universe.yaml` - Working backtest config
- `configs/xgboost_liquid_universe.yaml` - Alternative model example

---

**Next Steps**: Review plan → Approve strategy priorities → Begin Phase 1 implementation
