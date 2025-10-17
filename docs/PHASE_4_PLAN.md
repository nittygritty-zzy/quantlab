# Phase 4: Advanced Screening Features

**Date:** October 16, 2025
**Status:** 🚧 In Progress
**Priority:** High

---

## Overview

Phase 4 focuses on advanced screening capabilities that enhance workflow efficiency, enable historical validation, and provide real-time monitoring. These features transform the screener from a static tool into a dynamic research platform.

---

## Goals

1. **Historical Validation** - Backtest screening criteria to measure effectiveness
2. **Saved Screens** - Reusable screening templates with named configurations
3. **Screen Comparison** - Side-by-side comparison of multiple screening strategies
4. **Watch Mode** - Real-time monitoring with alerts when stocks enter/exit screens

---

## Phase 4 Components

### 1. Screen Backtesting ⭐ (Priority: HIGH)

**Purpose:** Validate screening criteria by testing historical performance

**Features:**
- Backtest any screening criteria over historical periods
- Calculate forward returns (1-day, 5-day, 20-day, 60-day)
- Performance metrics (win rate, average return, Sharpe ratio)
- Sector-adjusted returns
- Statistical significance testing
- Comparison to benchmark (SPY)

**Implementation:**
```python
# quantlab/core/screen_backtest.py
class ScreenBacktester:
    def backtest_criteria(
        self,
        criteria: ScreenCriteria,
        start_date: date,
        end_date: date,
        rebalance_frequency: str = 'weekly'  # daily, weekly, monthly
    ) -> BacktestResults

    def calculate_forward_returns(
        self,
        tickers: List[str],
        entry_date: date,
        holding_periods: List[int] = [1, 5, 20, 60]
    ) -> pd.DataFrame

    def compare_to_benchmark(
        self,
        backtest_results: BacktestResults,
        benchmark: str = 'SPY'
    ) -> ComparisonMetrics
```

**CLI Commands:**
```bash
# Backtest oversold screen for last 6 months
quantlab screen backtest \
    --preset oversold \
    --start-date 2025-04-16 \
    --end-date 2025-10-16 \
    --rebalance weekly \
    --output results/oversold_backtest.json

# Backtest custom criteria
quantlab screen backtest \
    --rsi-max 30 \
    --volume-min 1000000 \
    --start-date 2025-01-01 \
    --holding-period 20 \
    --benchmark SPY
```

**Output:**
- Performance summary (total return, CAGR, Sharpe ratio, max drawdown)
- Monthly/weekly returns breakdown
- Win rate by sector
- Best/worst performers
- Comparison to benchmark

**Estimated Time:** 3-4 hours

---

### 2. Saved Screens (Priority: HIGH)

**Purpose:** Save and reuse screening criteria as named templates

**Features:**
- Save any screening criteria with a name
- List all saved screens
- Load and run saved screens
- Update/delete saved screens
- Share screens as JSON files
- Metadata (description, tags, creation date, last run)

**Implementation:**
```python
# quantlab/core/saved_screens.py
class SavedScreenManager:
    def save_screen(
        self,
        screen_id: str,
        name: str,
        criteria: ScreenCriteria,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool

    def load_screen(self, screen_id: str) -> Optional[ScreenCriteria]

    def list_screens(self) -> pd.DataFrame

    def run_saved_screen(
        self,
        screen_id: str,
        limit: int = 50
    ) -> pd.DataFrame

    def export_screen(self, screen_id: str, output_path: str) -> bool

    def import_screen(self, input_path: str) -> bool
```

**Database Schema:**
```sql
CREATE TABLE saved_screens (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR,
    criteria JSON NOT NULL,  -- ScreenCriteria as JSON
    tags JSON,  -- Array of tags
    created_date TIMESTAMP NOT NULL,
    last_modified TIMESTAMP NOT NULL,
    last_run TIMESTAMP,
    run_count INTEGER DEFAULT 0
)
```

**CLI Commands:**
```bash
# Save current criteria
quantlab screen save my_oversold \
    --name "My Oversold Strategy" \
    --description "RSI < 30 with high volume" \
    --rsi-max 30 \
    --volume-min 1000000 \
    --tags "oversold,technical"

# List saved screens
quantlab screen list-saved

# Run saved screen
quantlab screen run-saved my_oversold --limit 20

# Export screen for sharing
quantlab screen export-saved my_oversold --output my_screen.json

# Import screen from file
quantlab screen import-saved friend_screen.json
```

**Estimated Time:** 2-3 hours

---

### 3. Screen Comparison (Priority: MEDIUM)

**Purpose:** Compare multiple screening strategies side-by-side

**Features:**
- Run multiple screens simultaneously
- Compare results (overlap analysis)
- Side-by-side metrics comparison
- Venn diagram of ticker overlap
- Combined score across screens
- Export comparison report

**Implementation:**
```python
# quantlab/core/screen_comparison.py
class ScreenComparator:
    def compare_screens(
        self,
        screens: Dict[str, ScreenCriteria],
        limit_per_screen: int = 50
    ) -> ComparisonResults

    def find_overlap(
        self,
        results: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame  # Tickers found in multiple screens

    def calculate_consensus_score(
        self,
        results: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame  # Combined scores

    def create_comparison_report(
        self,
        comparison: ComparisonResults,
        output_path: str
    ) -> bool
```

**CLI Commands:**
```bash
# Compare two presets
quantlab screen compare \
    --screen1 oversold \
    --screen2 value-stocks \
    --output comparison_report.xlsx

# Compare saved screens
quantlab screen compare \
    --saved my_oversold \
    --saved my_momentum \
    --saved my_quality

# Find stocks in all screens (consensus picks)
quantlab screen compare \
    --screen1 oversold \
    --screen2 value-stocks \
    --screen3 quality \
    --show-overlap-only
```

**Output:**
- Multi-sheet Excel report
- Sheet 1: All screens side-by-side
- Sheet 2: Overlap analysis (Venn diagram data)
- Sheet 3: Consensus picks (stocks in multiple screens)
- Sheet 4: Performance comparison (if backtested)

**Estimated Time:** 2-3 hours

---

### 4. Watch Mode with Alerts (Priority: MEDIUM)

**Purpose:** Monitor screens continuously and alert when stocks qualify

**Features:**
- Run screen on schedule (every 15min, hourly, daily)
- Alert when new stocks enter screen
- Alert when tracked stocks exit screen
- Alert on significant changes (price, volume, RSI)
- Multiple notification channels (terminal, file, webhook)
- Alert history and statistics

**Implementation:**
```python
# quantlab/core/screen_watcher.py
class ScreenWatcher:
    def start_watch(
        self,
        screen_id: str,
        interval: str = '1h',  # 15m, 1h, 1d
        alert_on: List[str] = ['entry', 'exit']
    ) -> WatchSession

    def stop_watch(self, session_id: str) -> bool

    def get_active_watches(self) -> List[WatchSession]

    def configure_alerts(
        self,
        session_id: str,
        notification_type: str = 'terminal',  # terminal, file, webhook
        alert_threshold: Optional[Dict] = None
    ) -> bool
```

**Database Schema:**
```sql
CREATE TABLE screen_watch_sessions (
    id VARCHAR PRIMARY KEY,
    screen_id VARCHAR NOT NULL,
    interval VARCHAR NOT NULL,
    started_at TIMESTAMP NOT NULL,
    last_run TIMESTAMP,
    status VARCHAR NOT NULL,  -- active, paused, stopped
    alert_count INTEGER DEFAULT 0,
    FOREIGN KEY (screen_id) REFERENCES saved_screens(id)
)

CREATE TABLE screen_watch_alerts (
    id BIGINT PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    alert_type VARCHAR NOT NULL,  -- entry, exit, change
    ticker VARCHAR NOT NULL,
    alert_time TIMESTAMP NOT NULL,
    details JSON,
    acknowledged BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (session_id) REFERENCES screen_watch_sessions(id)
)
```

**CLI Commands:**
```bash
# Start watching oversold screen
quantlab screen watch start oversold \
    --interval 1h \
    --alert-on entry,exit

# List active watches
quantlab screen watch list

# Stop watch
quantlab screen watch stop <session_id>

# View alerts
quantlab screen watch alerts --last 24h

# Run in background (detached mode)
quantlab screen watch start momentum \
    --interval 15m \
    --output alerts.log \
    --daemon
```

**Estimated Time:** 3-4 hours

---

## Implementation Priority

### Week 1 (High Priority)
1. **Saved Screens** (2-3 hours)
   - Essential for workflow efficiency
   - Foundation for other features
   - Quick win with high user value

2. **Screen Backtesting** (3-4 hours)
   - Critical for strategy validation
   - Helps users understand screen effectiveness
   - Builds confidence in screening criteria

### Week 2 (Medium Priority)
3. **Screen Comparison** (2-3 hours)
   - Helps identify best strategies
   - Consensus picks are valuable
   - Complements backtesting

4. **Watch Mode** (3-4 hours)
   - Real-time monitoring capability
   - Reduces manual rerunning
   - Professional trading tool feature

**Total Estimated Time:** 10-14 hours

---

## Success Criteria

### Saved Screens
- ✅ Can save any screening criteria with metadata
- ✅ Can list/load/run saved screens
- ✅ Can export/import screens as JSON
- ✅ CLI commands work seamlessly

### Screen Backtesting
- ✅ Can backtest any criteria over date range
- ✅ Calculates forward returns (1d, 5d, 20d, 60d)
- ✅ Provides performance metrics (Sharpe, win rate, returns)
- ✅ Compares to benchmark
- ✅ Generates detailed backtest report

### Screen Comparison
- ✅ Can compare 2+ screens simultaneously
- ✅ Finds ticker overlap
- ✅ Calculates consensus scores
- ✅ Generates multi-sheet comparison report

### Watch Mode
- ✅ Can start/stop monitoring sessions
- ✅ Runs screens on schedule
- ✅ Alerts on entry/exit
- ✅ Tracks alert history
- ✅ Works in daemon mode

---

## Testing Strategy

### Unit Tests
- `tests/core/test_saved_screens.py` - SavedScreenManager (20 tests)
- `tests/core/test_screen_backtest.py` - ScreenBacktester (25 tests)
- `tests/core/test_screen_comparison.py` - ScreenComparator (15 tests)
- `tests/core/test_screen_watcher.py` - ScreenWatcher (20 tests)

### Integration Tests
- `tests/integration/test_phase4_integration.py`
  - Save → Run → Backtest workflow
  - Compare → Export workflow
  - Watch → Alert workflow
  - End-to-end scenarios

**Target:** 80 new tests, >90% coverage

---

## Documentation Updates

### Files to Create/Update
1. `docs/PHASE_4_COMPLETION_SUMMARY.md` - Comprehensive summary
2. `docs/SCREENER_GUIDE.md` - Update with Phase 4 features
3. `docs/BACKTEST_GUIDE.md` - New guide for backtesting screens
4. `docs/WATCH_MODE_GUIDE.md` - Guide for watch mode usage

---

## Dependencies

### New Python Packages
None required - all features use existing dependencies:
- pandas (data manipulation)
- DuckDB (storage)
- click (CLI)
- openpyxl (Excel export)

### Data Requirements
- Historical price data (already available in Parquet)
- Benchmark data (SPY) for comparison

---

## Future Enhancements (Phase 5+)

**Beyond Phase 4:**
1. **Options Screeners** - Screen by Greeks, volume, OI
2. **Sector Rotation** - Identify sector trends over time
3. **Relative Screening** - Find stocks relative to sector/index
4. **Machine Learning** - Predict screen effectiveness
5. **Web Dashboard** - Visual interface for all features

---

## Notes

### Design Decisions
1. **Saved screens use JSON serialization** - Flexible, human-readable
2. **Backtesting uses actual historical data** - No simulation assumptions
3. **Watch mode uses lightweight polling** - No websockets needed yet
4. **Comparison supports unlimited screens** - Dict-based architecture

### Performance Considerations
- Backtesting can be slow for long periods → Show progress
- Watch mode should be efficient → Use last known results as baseline
- Comparison runs screens in parallel → Use ThreadPoolExecutor
- Saved screens stored in DuckDB → Fast retrieval

---

**Ready to implement Phase 4! 🚀**

Let's start with **Saved Screens** as the foundation for all other features.
