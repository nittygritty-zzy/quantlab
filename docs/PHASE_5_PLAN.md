# Phase 5: Screener Visualization Suite

**Status:** 🚧 In Progress
**Start Date:** October 16, 2025
**Estimated Completion:** 6-8 hours

---

## Executive Summary

Phase 5 adds comprehensive interactive visualizations for all Phase 4 screener features, transforming raw data outputs into actionable visual insights. This phase extends the existing `quantlab visualize` CLI with screener-specific visualization commands.

---

## Goals

### Primary Goal
Add interactive plotly-based visualizations for all Phase 4 screener features:
1. Screen backtest results visualization
2. Screen comparison visualization
3. Screening results visualization
4. Watch mode alerts visualization

### Secondary Goals
- Integrate seamlessly with existing visualization infrastructure
- Generate HTML reports that can be shared
- Support both CLI and programmatic usage
- Provide export options (HTML, PNG, JSON)

---

## Component Breakdown

### 1. Screen Backtest Visualizations

**Command:** `quantlab visualize screen-backtest`

**Required Visualizations:**
- **Cumulative Returns Chart** - Line chart showing strategy returns vs benchmark over time
- **Drawdown Chart** - Area chart showing peak-to-trough declines
- **Rolling Sharpe Ratio** - Line chart showing risk-adjusted returns over time
- **Performance Metrics Dashboard** - Card layout with key metrics
- **Period Returns Distribution** - Histogram of period-by-period returns
- **Win Rate Bar Chart** - Wins vs losses visualization

**Input:** JSON file from `quantlab screen backtest --output file.json`

**Example Usage:**
```bash
quantlab screen backtest --saved-id my_oversold \
    --start-date 2025-01-01 --end-date 2025-10-01 \
    --output backtest.json

quantlab visualize screen-backtest --input backtest.json \
    --output backtest_report.html
```

---

### 2. Screen Comparison Visualizations

**Command:** `quantlab visualize screen-comparison`

**Required Visualizations:**
- **Overlap Venn Diagram** - Interactive Venn showing screen overlaps (2-5 screens)
- **Consensus Picks Table** - Highlighted table of stocks in multiple screens
- **Sector Distribution Comparison** - Grouped bar chart comparing sector allocations
- **Metric Distribution Comparison** - Box plots comparing key metrics across screens
- **Screen Size Bar Chart** - Number of stocks in each screen

**Input:** JSON file from `quantlab screen compare-multi --output file.json`

**Example Usage:**
```bash
quantlab screen compare-multi \
    --saved my_oversold --saved my_momentum --saved my_value \
    --output comparison.json

quantlab visualize screen-comparison --input comparison.json \
    --output comparison_report.html
```

---

### 3. Screening Results Visualizations

**Command:** `quantlab visualize screen-results`

**Required Visualizations:**
- **Sector Distribution Pie Chart** - Breakdown by sector
- **Industry Distribution Bar Chart** - Top industries represented
- **Metric Distribution Histograms** - Distribution of key metrics (P/E, RSI, etc.)
- **Price vs Volume Scatter Plot** - Identify outliers
- **Top Picks Summary Cards** - Visual cards for top 5-10 stocks
- **Market Cap Distribution** - Large/Mid/Small cap breakdown

**Input:** JSON file from `quantlab screen run --output file.json`

**Example Usage:**
```bash
quantlab screen run --rsi-max 30 --volume-min 1000000 \
    --output screening.json

quantlab visualize screen-results --input screening.json \
    --output screening_report.html
```

---

### 4. Watch Mode Alert Visualizations

**Command:** `quantlab visualize screen-alerts`

**Required Visualizations:**
- **Alert Timeline** - Gantt-style chart showing alerts over time
- **Alert Type Breakdown** - Pie chart of alert types (entry, exit, price_change, volume_spike)
- **Ticker Alert Frequency Heatmap** - Which tickers alert most often
- **Daily Alert Count Chart** - Line chart of alerts per day
- **Alert Status Table** - Interactive table of recent alerts

**Input:** JSON export from watch mode alerts

**Example Usage:**
```bash
quantlab screen watch-monitor alerts --since-hours 168 \
    --output alerts.json

quantlab visualize screen-alerts --input alerts.json \
    --output alerts_report.html
```

---

## Technical Architecture

### Module Structure

```
quantlab/core/
├── screen_visualizer.py      # New: Core visualization logic for screeners
    ├── ScreenBacktestVisualizer
    ├── ScreenComparisonVisualizer
    ├── ScreenResultsVisualizer
    └── ScreenAlertsVisualizer

quantlab/cli/
└── visualize.py              # Extended: Add screener commands
    ├── @visualize.command('screen-backtest')
    ├── @visualize.command('screen-comparison')
    ├── @visualize.command('screen-results')
    └── @visualize.command('screen-alerts')
```

### Design Principles

1. **Reuse Existing Infrastructure**
   - Leverage existing plotly setup from `quantlab/cli/visualize.py`
   - Use consistent color schemes and styling
   - Follow existing HTML export patterns

2. **Modular Visualizer Classes**
   - Each screener feature gets its own visualizer class
   - Classes take JSON input and return plotly figures
   - Easy to test and maintain

3. **Rich HTML Reports**
   - Combine multiple charts into comprehensive HTML reports
   - Include summary statistics and insights
   - Make reports shareable and self-contained

4. **CLI-First Design**
   - All visualizations accessible via CLI
   - Support for batch processing
   - Pipeline-friendly (read JSON, output HTML)

### Data Flow

```
Screen Command → JSON Output → Visualization Command → HTML Report
     ↓                           ↓
  Database              plotly figures → Interactive Charts
```

---

## Implementation Plan

### Phase 5.1: Core Visualizer Module (2 hours)
- Create `quantlab/core/screen_visualizer.py`
- Implement `ScreenBacktestVisualizer` class
- Implement `ScreenComparisonVisualizer` class
- Implement `ScreenResultsVisualizer` class
- Implement `ScreenAlertsVisualizer` class

### Phase 5.2: CLI Integration (1.5 hours)
- Extend `quantlab/cli/visualize.py`
- Add `screen-backtest` command
- Add `screen-comparison` command
- Add `screen-results` command
- Add `screen-alerts` command

### Phase 5.3: Testing (1.5 hours)
- Generate sample data from Phase 4 commands
- Test all visualization commands
- Verify HTML output quality
- Test edge cases (empty data, single data point)

### Phase 5.4: Documentation (1 hour)
- Update SCREENER_GUIDE.md with visualization examples
- Create PHASE_5_COMPLETE.md summary
- Add visualization workflow examples
- Document best practices

---

## Success Criteria

- ✅ All 4 screener features have interactive visualizations
- ✅ CLI commands generate HTML reports successfully
- ✅ Reports are shareable and self-contained
- ✅ Visualizations provide actionable insights
- ✅ Integration with existing visualization infrastructure
- ✅ Comprehensive documentation with examples

---

## Dependencies

**External Libraries:**
- plotly (already installed)
- pandas (already installed)
- numpy (already installed)

**Internal Dependencies:**
- Phase 4 screener commands must be functional
- JSON output from Phase 4 commands

---

## Example Workflows

### Workflow 1: Backtest and Visualize
```bash
# Step 1: Backtest a strategy
quantlab screen backtest --saved-id momentum_quality \
    --start-date 2024-01-01 --end-date 2025-10-01 \
    --output results/backtest.json

# Step 2: Visualize results
quantlab visualize screen-backtest \
    --input results/backtest.json \
    --output results/backtest_report.html

# Step 3: Open in browser
open results/backtest_report.html
```

### Workflow 2: Compare Strategies with Visualization
```bash
# Step 1: Compare multiple screens
quantlab screen compare-multi \
    --saved oversold --saved momentum --saved value \
    --output results/comparison.json

# Step 2: Visualize comparison
quantlab visualize screen-comparison \
    --input results/comparison.json \
    --output results/comparison_report.html

# Step 3: Review consensus picks visually
open results/comparison_report.html
```

### Workflow 3: Screen and Analyze Results
```bash
# Step 1: Run screening
quantlab screen run --rsi-max 30 --volume-min 1000000 \
    --pe-max 15 --output results/oversold.json

# Step 2: Visualize screening results
quantlab visualize screen-results \
    --input results/oversold.json \
    --output results/oversold_report.html

# Step 3: Explore sector distribution and metrics
open results/oversold_report.html
```

### Workflow 4: Monitor and Visualize Alerts
```bash
# Step 1: Get recent alerts
quantlab screen watch-monitor alerts --since-hours 168 \
    --output results/alerts.json

# Step 2: Visualize alert patterns
quantlab visualize screen-alerts \
    --input results/alerts.json \
    --output results/alerts_report.html

# Step 3: Identify patterns
open results/alerts_report.html
```

---

## Future Enhancements (Phase 6?)

### High Priority
1. **Interactive Filtering** - Drill down into data points
2. **Real-Time Updates** - Live refreshing dashboards
3. **Custom Themes** - Light/dark mode support
4. **Export to PNG** - Static image exports for presentations

### Medium Priority
5. **Comparison Overlays** - Overlay multiple backtests
6. **Statistical Annotations** - Highlight significant events
7. **Mobile-Responsive** - Better mobile viewing
8. **Dashboard Mode** - Multi-panel overview page

### Low Priority
9. **3D Visualizations** - 3D scatter plots for multi-dimensional analysis
10. **Animation** - Animated time-series visualizations
11. **PDF Export** - Generate PDF reports
12. **Email Integration** - Email reports automatically

---

## Known Limitations

1. **Static HTML Output**
   - Not a real-time dashboard (yet)
   - Requires regeneration to update
   - No server-side interactivity

2. **Venn Diagram Complexity**
   - Venn diagrams with 5+ screens become hard to read
   - May need alternative visualization (UpSet plots)

3. **Large Dataset Performance**
   - HTML files can get large with thousands of data points
   - May need data sampling for very large screens

4. **No Persistent State**
   - Visualizations don't remember user interactions
   - Each visualization is independent

---

## Risk Assessment

**Low Risk:**
- Using proven plotly library
- Building on existing visualization infrastructure
- JSON input/output is well-tested

**Medium Risk:**
- Venn diagram implementation may be complex
- Performance with large datasets unknown

**Mitigation:**
- Use plotly-venn or matplotlib-venn for Venn diagrams
- Implement data sampling for large datasets
- Test with realistic data sizes early

---

## Estimated Effort

| Component | Estimated Time |
|-----------|----------------|
| Core Visualizer Module | 2 hours |
| CLI Integration | 1.5 hours |
| Testing | 1.5 hours |
| Documentation | 1 hour |
| **Total** | **6 hours** |

---

## Deliverables

1. **Code:**
   - `quantlab/core/screen_visualizer.py` (~600 lines)
   - Extended `quantlab/cli/visualize.py` (~200 lines added)

2. **Documentation:**
   - `docs/PHASE_5_COMPLETE.md`
   - Updated `docs/SCREENER_GUIDE.md`
   - Example HTML reports in `docs/examples/`

3. **Tests:**
   - `tests/core/test_screen_visualizer.py`
   - Sample data files for testing

---

**Next Steps:**
1. Create core visualizer module
2. Implement backtest visualizations first (most important)
3. Test with real data from Phase 4
4. Iterate based on visual quality

---

**Last Updated:** October 16, 2025
**Status:** 🚧 Starting Implementation
