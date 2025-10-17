# QuantLab - Comprehensive Plotly Visualization Master Plan

**Date:** October 16, 2025
**Technology Stack:** Plotly (primary charting library)
**Scope:** Complete visualization coverage for 75+ features
**Current Coverage:** ~10% → Target: 95%+

---

## EXECUTIVE SUMMARY

This master plan provides complete Plotly-based visualization implementation for the QuantLab platform, covering:
- **Portfolio Management** (7 charts)
- **Price Data & Candlesticks** (8 charts)
- **Technical Analysis** (12 charts)
- **Options Analysis** (15 charts including 3D)
- **Greeks Visualization** (10 charts)
- **Strategy Analysis** (8 charts)
- **Backtesting** (9 charts)
- **Fundamentals & Sentiment** (10 charts)

**Total:** 79 interactive Plotly visualizations organized in 4 implementation phases

---

## WHY PLOTLY?

### Advantages for QuantLab:
✅ **Interactive** - Zoom, pan, hover tooltips, range selection
✅ **Web-Ready** - Export to HTML (standalone, no server needed)
✅ **3D Capable** - Greeks surfaces, volatility surfaces
✅ **Professional** - Publication-quality charts
✅ **CLI-Friendly** - Save to file without browser
✅ **Versatile** - All chart types (line, bar, candlestick, heatmap, 3D)
✅ **Single Dependency** - One library for everything
✅ **Export Options** - HTML, PNG, SVG, PDF

### vs Other Libraries:
- **matplotlib/seaborn**: Static only, no interactivity
- **mplfinance**: Limited to candlesticks only
- **bokeh**: More complex API, similar results

---

## IMPLEMENTATION PHASES

### Phase 1: Foundation (Weeks 1-2) - 40-50 hours
**Priority 1 Features**: High impact, low complexity

### Phase 2: Options & Advanced (Weeks 3-4) - 50-60 hours
**Priority 2 Features**: Options-specific, 3D visualizations

### Phase 3: Dashboards (Weeks 5-6) - 30-40 hours
**Integration**: Multi-page dashboards, CLI integration

### Phase 4: Polish & Features (Week 7+) - 40+ hours
**Advanced**: Reports, alerts, optimization

**Total Effort:** ~200 hours over 7-8 weeks

---

## PHASE 1: FOUNDATION (Priority 1)

### 1.1 Portfolio Visualization Module

**File:** `quantlab/visualization/portfolio_charts.py`

#### Chart 1.1.1: Portfolio Pie Chart ⭐ CRITICAL
```python
import plotly.graph_objects as go

def create_portfolio_pie(positions: List[Position]) -> go.Figure:
    """
    Portfolio allocation pie chart

    Args:
        positions: List of Position objects with ticker, weight

    Returns:
        Interactive Plotly pie chart
    """
    fig = go.Figure(data=[go.Pie(
        labels=[p.ticker for p in positions],
        values=[p.weight * 100 for p in positions],
        hole=0.3,  # Donut chart
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Weight: %{value:.2f}%<br>Shares: %{customdata[0]}<extra></extra>',
        customdata=[[p.shares] for p in positions]
    )])

    fig.update_layout(
        title='Portfolio Allocation',
        showlegend=True,
        height=500
    )

    return fig

# CLI Integration:
# quantlab portfolio show PORTFOLIO_NAME --chart pie --output allocation.html
```

**Data Source:** `portfolio.positions` → ticker, weight, shares
**Complexity:** Low
**Impact:** Very High - instant allocation understanding

#### Chart 1.1.2: Position P&L Heatmap
```python
def create_pnl_heatmap(positions: List[Position], current_prices: Dict[str, float]) -> go.Figure:
    """
    Position winners/losers heatmap

    Args:
        positions: List with ticker, cost_basis, shares
        current_prices: Dict of ticker → current price
    """
    tickers = [p.ticker for p in positions]
    pnl_values = []
    pnl_pcts = []

    for p in positions:
        current = current_prices.get(p.ticker, p.cost_basis)
        pnl = (current - p.cost_basis) * p.shares
        pnl_pct = ((current / p.cost_basis) - 1) * 100
        pnl_values.append(pnl)
        pnl_pcts.append(pnl_pct)

    fig = go.Figure(data=go.Heatmap(
        y=tickers,
        z=[[pnl] for pnl in pnl_pcts],
        colorscale='RdYlGn',
        zmid=0,
        text=[[f'${pnl:,.0f}'] for pnl in pnl_values],
        texttemplate='%{text}',
        hovertemplate='<b>%{y}</b><br>P&L: %{text}<br>Return: %{z:.2f}%<extra></extra>'
    )])

    fig.update_layout(
        title='Position P&L Heatmap',
        xaxis_showticklabels=False,
        height=400 + len(tickers) * 30
    )

    return fig
```

**Data Source:** `position.cost_basis + current_price` → P&L
**Complexity:** Low
**Impact:** High - identify winners/losers quickly

---

### 1.2 Price Data Visualization Module

**File:** `quantlab/visualization/price_charts.py`

#### Chart 1.2.1: Candlestick Chart ⭐ CRITICAL
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_candlestick_chart(
    df: pd.DataFrame,
    ticker: str,
    show_volume: bool = True
) -> go.Figure:
    """
    Interactive OHLC candlestick chart with optional volume

    Args:
        df: DataFrame with columns: date, open, high, low, close, volume
        ticker: Stock ticker symbol
        show_volume: Include volume subplot
    """
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{ticker} Price', 'Volume')
        )

        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='OHLC'
            ),
            row=1, col=1
        )

        # Volume bars
        colors = ['red' if df.iloc[i]['close'] < df.iloc[i]['open'] else 'green'
                  for i in range(len(df))]

        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                showlegend=False
            ),
            row=2, col=1
        )

        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)

    else:
        fig = go.Figure(data=[go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])

        fig.update_layout(title=f'{ticker} Price Chart')

    fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(step="all", label="ALL")
            ])
        )
    )

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=600,
        hovermode='x unified'
    )

    return fig

# CLI Integration:
# quantlab data query AAPL --days 90 --chart candlestick --output price.html
```

**Data Source:** `data query` → OHLCV
**Complexity:** Low
**Impact:** Very High - industry standard

#### Chart 1.2.2: Multi-Ticker Comparison
```python
def create_comparison_chart(
    data_dict: Dict[str, pd.DataFrame],
    normalize: bool = True
) -> go.Figure:
    """
    Overlay multiple tickers for comparison

    Args:
        data_dict: {ticker: df with date, close}
        normalize: Normalize to 100 at start
    """
    fig = go.Figure()

    for ticker, df in data_dict.items():
        if normalize:
            base = df['close'].iloc[0]
            values = (df['close'] / base) * 100
            y_label = "Normalized (Base=100)"
        else:
            values = df['close']
            y_label = "Price ($)"

        fig.add_trace(go.Scatter(
            x=df['date'],
            y=values,
            mode='lines',
            name=ticker,
            hovertemplate='%{fullData.name}<br>%{y:.2f}<extra></extra>'
        ))

    fig.update_layout(
        title='Multi-Ticker Comparison',
        xaxis_title='Date',
        yaxis_title=y_label,
        hovermode='x unified',
        height=500
    )

    return fig
```

---

### 1.3 Technical Analysis Visualization Module

**File:** `quantlab/visualization/technical_charts.py`

#### Chart 1.3.1: Multi-Indicator Dashboard ⭐ CRITICAL
```python
def create_technical_dashboard(
    df: pd.DataFrame,
    ticker: str,
    indicators: Dict[str, pd.DataFrame]
) -> go.Figure:
    """
    Comprehensive technical analysis dashboard

    Args:
        df: Price data (date, open, high, low, close, volume)
        ticker: Stock symbol
        indicators: Dict of calculated indicators
            {
                'sma': df with SMA20, SMA50, SMA200
                'rsi': df with RSI values
                'macd': df with MACD, signal, histogram
                'bollinger': df with upper, middle, lower
            }
    """
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.4, 0.2, 0.2, 0.2],
        subplot_titles=(
            f'{ticker} Price + Moving Averages',
            'RSI (14)',
            'MACD (12,26,9)',
            'Bollinger Bands'
        )
    )

    # Row 1: Price + SMA
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price'
        ),
        row=1, col=1
    )

    if 'sma' in indicators:
        sma_df = indicators['sma']
        for col, color in [('SMA20', 'blue'), ('SMA50', 'orange'), ('SMA200', 'red')]:
            if col in sma_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=sma_df['date'],
                        y=sma_df[col],
                        name=col,
                        line=dict(color=color, width=1)
                    ),
                    row=1, col=1
                )

    # Row 2: RSI
    if 'rsi' in indicators:
        rsi_df = indicators['rsi']
        fig.add_trace(
            go.Scatter(
                x=rsi_df['date'],
                y=rsi_df['RSI'],
                name='RSI',
                line=dict(color='purple')
            ),
            row=2, col=1
        )
        # Overbought/Oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        fig.update_yaxes(range=[0, 100], row=2, col=1)

    # Row 3: MACD
    if 'macd' in indicators:
        macd_df = indicators['macd']
        fig.add_trace(
            go.Scatter(
                x=macd_df['date'],
                y=macd_df['MACD'],
                name='MACD',
                line=dict(color='blue')
            ),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=macd_df['date'],
                y=macd_df['Signal'],
                name='Signal',
                line=dict(color='orange')
            ),
            row=3, col=1
        )
        # Histogram
        colors = ['green' if val >= 0 else 'red' for val in macd_df['Histogram']]
        fig.add_trace(
            go.Bar(
                x=macd_df['date'],
                y=macd_df['Histogram'],
                name='Histogram',
                marker_color=colors
            ),
            row=3, col=1
        )

    # Row 4: Bollinger Bands
    if 'bollinger' in indicators:
        bb_df = indicators['bollinger']
        fig.add_trace(
            go.Scatter(
                x=bb_df['date'],
                y=bb_df['Upper'],
                name='BB Upper',
                line=dict(color='gray', width=1, dash='dash')
            ),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=bb_df['date'],
                y=bb_df['Middle'],
                name='BB Middle',
                line=dict(color='blue', width=1)
            ),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=bb_df['date'],
                y=bb_df['Lower'],
                name='BB Lower',
                line=dict(color='gray', width=1, dash='dash'),
                fill='tonexty',
                fillcolor='rgba(173, 216, 230, 0.3)'
            ),
            row=4, col=1
        )

    fig.update_layout(
        height=1000,
        showlegend=True,
        hovermode='x unified'
    )

    fig.update_xaxes(rangeslider_visible=False)

    return fig

# CLI Integration:
# quantlab analyze ticker AAPL --chart technical --output tech_dashboard.html
```

**Data Source:** `technical_indicators` module
**Complexity:** Low-Medium
**Impact:** Very High - comprehensive TA view

---

### 1.4 Options Strategy Visualization Module

**File:** `quantlab/visualization/options_charts.py`

#### Chart 1.4.1: Options Payoff Diagram ⭐ CRITICAL
```python
def create_payoff_diagram(
    strategy: OptionsStrategy,
    price_range: Tuple[float, float] = None,
    num_points: int = 100
) -> go.Figure:
    """
    Interactive options strategy payoff diagram

    Args:
        strategy: OptionsStrategy object
        price_range: (min, max) price range, or None for auto
        num_points: Resolution of payoff curve
    """
    # Generate payoff data
    if price_range is None:
        current = strategy.current_stock_price
        price_range = (current * 0.7, current * 1.3)

    prices = np.linspace(price_range[0], price_range[1], num_points)
    pnls = [strategy.pnl_at_price(p) for p in prices]

    fig = go.Figure()

    # Payoff curve
    fig.add_trace(go.Scatter(
        x=prices,
        y=pnls,
        mode='lines',
        name='P&L at Expiration',
        line=dict(color='blue', width=3),
        fill='tozeroy',
        fillcolor='rgba(0,100,255,0.2)',
        hovertemplate='Price: $%{x:.2f}<br>P&L: $%{y:,.0f}<extra></extra>'
    ))

    # Zero line
    fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)

    # Current stock price
    current_pnl = strategy.pnl_at_price(strategy.current_stock_price)
    fig.add_vline(
        x=strategy.current_stock_price,
        line_dash="dash",
        line_color="green",
        annotation_text="Current",
        annotation_position="top"
    )

    # Breakeven points
    breakevens = strategy.breakeven_points()
    for be in breakevens:
        fig.add_vline(
            x=be,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"BE: ${be:.2f}",
            annotation_position="bottom"
        )

    # Max profit/loss annotations
    max_profit = strategy.max_profit()
    max_loss = strategy.max_loss()

    fig.add_annotation(
        x=0.05, y=0.95,
        xref="paper", yref="paper",
        text=f"<b>Max Profit:</b> ${max_profit:,.0f}<br><b>Max Loss:</b> ${max_loss:,.0f}",
        showarrow=False,
        bgcolor="white",
        bordercolor="black",
        borderwidth=1
    )

    fig.update_layout(
        title=f'{strategy.name} - Payoff Diagram',
        xaxis_title='Underlying Price at Expiration ($)',
        yaxis_title='Profit / Loss ($)',
        height=500,
        hovermode='x'
    )

    return fig

# CLI Integration:
# quantlab strategy build iron_condor ... --chart payoff --output payoff.html
```

**Data Source:** `strategy.pnl_at_price()` + risk metrics
**Complexity:** Low
**Impact:** Very High - essential for options traders

---

### 1.5 Backtest Visualization Module

**File:** `quantlab/visualization/backtest_charts.py`

#### Chart 1.5.1: Cumulative Returns Chart ⭐ CRITICAL
```python
def create_cumulative_returns_chart(
    backtest_results: Dict[str, pd.DataFrame],
    benchmark: pd.DataFrame = None
) -> go.Figure:
    """
    Strategy cumulative returns vs benchmark

    Args:
        backtest_results: {strategy_name: df with date, returns}
        benchmark: Optional benchmark df (date, returns)
    """
    fig = go.Figure()

    # Strategy returns
    for name, df in backtest_results.items():
        cumulative = (1 + df['returns']).cumprod() * 100

        fig.add_trace(go.Scatter(
            x=df['date'],
            y=cumulative,
            mode='lines',
            name=name,
            hovertemplate='%{fullData.name}<br>%{y:.2f}%<extra></extra>'
        ))

    # Benchmark
    if benchmark is not None:
        benchmark_cumulative = (1 + benchmark['returns']).cumprod() * 100
        fig.add_trace(go.Scatter(
            x=benchmark['date'],
            y=benchmark_cumulative,
            mode='lines',
            name='Benchmark (SPY)',
            line=dict(dash='dash', color='gray'),
            hovertemplate='Benchmark<br>%{y:.2f}%<extra></extra>'
        ))

    # Base line
    fig.add_hline(y=100, line_dash="solid", line_color="black", line_width=1)

    fig.update_layout(
        title='Cumulative Returns',
        xaxis_title='Date',
        yaxis_title='Return (%)',
        hovermode='x unified',
        height=500
    )

    return fig
```

**Data Source:** Backtest results → daily returns
**Complexity:** Low
**Impact:** Very High - performance visualization

---

## PHASE 2: OPTIONS & ADVANCED (Priority 2)

### 2.1 Advanced Greeks Visualization

**File:** `quantlab/visualization/greeks_charts.py`

#### Chart 2.1.1: Greeks Timeline Forecast ⭐⭐ HIGH
```python
def create_greeks_timeline(
    forecast_points: List[GreeksForecastPoint]
) -> go.Figure:
    """
    Greeks evolution over time

    Args:
        forecast_points: List of forecast points with days_forward, greeks
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Delta', 'Theta', 'Vega', 'Vanna'),
        vertical_spacing=0.12
    )

    dates = [p.date for p in forecast_points]

    # Delta
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[p.greeks['delta'] for p in forecast_points],
            mode='lines+markers',
            name='Delta',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    fig.add_hline(y=0, line_dash="dash", row=1, col=1)

    # Theta
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[p.greeks['theta'] for p in forecast_points],
            mode='lines+markers',
            name='Theta',
            line=dict(color='red', width=2),
            marker=dict(size=6)
        ),
        row=1, col=2
    )

    # Vega
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[p.greeks['vega'] for p in forecast_points],
            mode='lines+markers',
            name='Vega',
            line=dict(color='green', width=2),
            marker=dict(size=6)
        ),
        row=2, col=1
    )

    # Vanna (advanced)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[p.greeks['vanna'] for p in forecast_points],
            mode='lines+markers',
            name='Vanna',
            line=dict(color='purple', width=2),
            marker=dict(size=6)
        ),
        row=2, col=2
    )

    fig.update_layout(
        title='Greeks Forecast Timeline',
        showlegend=False,
        height=700,
        hovermode='x unified'
    )

    return fig

# CLI Integration:
# quantlab strategy greeks-forecast strategy.json --chart timeline --output forecast.html
```

#### Chart 2.1.2: Greeks 3D Surface ⭐⭐⭐ ADVANCED
```python
def create_greeks_3d_surface(
    strategy: OptionsStrategy,
    greek_name: str = 'delta',
    price_range: Tuple[float, float] = None,
    time_range: Tuple[int, int] = (0, 30)
) -> go.Figure:
    """
    3D surface plot: stock price × time × Greek value

    Args:
        strategy: OptionsStrategy object
        greek_name: Which Greek to plot (delta, gamma, vega, etc.)
        price_range: (min, max) underlying prices
        time_range: (min_days, max_days) to expiration
    """
    if price_range is None:
        current = strategy.current_stock_price
        price_range = (current * 0.8, current * 1.2)

    # Generate grid
    prices = np.linspace(price_range[0], price_range[1], 50)
    days = np.linspace(time_range[0], time_range[1], 30)

    # Calculate Greeks at each (price, time) point
    Z = []
    for day in days:
        row = []
        for price in prices:
            # Simulate strategy at this price and time
            greeks = _calculate_greeks_at(strategy, price, days_forward=day)
            row.append(greeks.get(greek_name, 0))
        Z.append(row)

    fig = go.Figure(data=[go.Surface(
        x=prices,
        y=days,
        z=Z,
        colorscale='Viridis',
        hovertemplate='Price: $%{x:.2f}<br>Days Fwd: %{y:.0f}<br>%{fullData.name}: %{z:.4f}<extra></extra>'
    )])

    fig.update_layout(
        title=f'{strategy.name} - {greek_name.capitalize()} Surface',
        scene=dict(
            xaxis_title='Underlying Price ($)',
            yaxis_title='Days Forward',
            zaxis_title=greek_name.capitalize(),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.3))
        ),
        height=700
    )

    return fig
```

**Data Source:** Greeks calculator + time projection
**Complexity:** High (3D)
**Impact:** High - advanced analysis

---

### 2.2 Options Chain Visualization

#### Chart 2.2.1: Options Chain Heatmap ⭐⭐ MEDIUM
```python
def create_options_chain_heatmap(
    options_data: pd.DataFrame,
    metric: str = 'open_interest'
) -> go.Figure:
    """
    Strike × Expiration heatmap for calls/puts

    Args:
        options_data: DataFrame with strike, expiration, open_interest, iv, etc.
        metric: Column to visualize (open_interest, iv, volume)
    """
    # Pivot for calls
    calls = options_data[options_data['option_type'] == 'call']
    call_pivot = calls.pivot_table(
        values=metric,
        index='strike',
        columns='expiration',
        aggfunc='sum'
    )

    # Pivot for puts
    puts = options_data[options_data['option_type'] == 'put']
    put_pivot = puts.pivot_table(
        values=metric,
        index='strike',
        columns='expiration',
        aggfunc='sum'
    )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Calls', 'Puts'),
        horizontal_spacing=0.1
    )

    # Calls heatmap
    fig.add_trace(
        go.Heatmap(
            z=call_pivot.values,
            x=call_pivot.columns,
            y=call_pivot.index,
            colorscale='Greens',
            name='Calls',
            hovertemplate='Strike: %{y}<br>Exp: %{x}<br>%{customdata}: %{z:,.0f}<extra></extra>',
            customdata=[[metric]] * len(call_pivot)
        ),
        row=1, col=1
    )

    # Puts heatmap
    fig.add_trace(
        go.Heatmap(
            z=put_pivot.values,
            x=put_pivot.columns,
            y=put_pivot.index,
            colorscale='Reds',
            name='Puts',
            hovertemplate='Strike: %{y}<br>Exp: %{x}<br>%{customdata}: %{z:,.0f}<extra></extra>',
            customdata=[[metric]] * len(put_pivot)
        ),
        row=1, col=2
    )

    fig.update_layout(
        title=f'Options Chain - {metric.replace("_", " ").title()}',
        height=600
    )

    return fig
```

#### Chart 2.2.2: Volatility Surface (3D) ⭐⭐⭐ ADVANCED
```python
def create_volatility_surface_3d(
    options_data: pd.DataFrame
) -> go.Figure:
    """
    3D volatility surface: strike × expiration × IV

    Args:
        options_data: DataFrame with strike, days_to_expiration, iv
    """
    # Pivot data
    pivot = options_data.pivot_table(
        values='iv',
        index='strike',
        columns='days_to_expiration',
        aggfunc='mean'
    )

    fig = go.Figure(data=[go.Surface(
        x=pivot.columns,  # Days to expiration
        y=pivot.index,    # Strikes
        z=pivot.values,   # IV
        colorscale='Plasma',
        hovertemplate='Strike: $%{y:.2f}<br>DTE: %{x:.0f}<br>IV: %{z:.2f}%<extra></extra>'
    )])

    fig.update_layout(
        title='Implied Volatility Surface',
        scene=dict(
            xaxis_title='Days to Expiration',
            yaxis_title='Strike Price ($)',
            zaxis_title='Implied Volatility (%)',
            camera=dict(eye=dict(x=1.5, y=-1.5, z=1.3))
        ),
        height=700
    )

    return fig

# CLI Integration:
# quantlab analyze ticker AAPL --chart volatility-surface --output vol_surface.html
```

**Data Source:** Options chain → strike, expiration, IV
**Complexity:** High (3D)
**Impact:** High - vol skew analysis

---

## PHASE 3: DASHBOARDS & INTEGRATION

### 3.1 Multi-Page Dashboard Structure

**Framework:** Plotly Dash or Streamlit

#### Dashboard 1: Portfolio Dashboard
- Portfolio pie chart
- Position P&L heatmap
- Sector composition
- Historical value chart

#### Dashboard 2: Technical Analysis Dashboard
- Candlestick with indicators
- RSI, MACD, Bollinger subplots
- Signal strength heatmap
- Multi-ticker comparison

#### Dashboard 3: Options Analysis Dashboard
- Strategy payoff diagram
- Greeks timeline
- Greeks 3D surface
- Options chain heatmap
- Volatility surface

#### Dashboard 4: Backtest Dashboard
- Cumulative returns
- Drawdown chart
- Monthly returns heatmap
- Rolling Sharpe ratio
- Trade distribution

---

### 3.2 CLI Integration Pattern

```python
# Add --chart and --output flags to all relevant commands

@click.option('--chart', type=click.Choice([
    'pie', 'candlestick', 'payoff', 'greeks', 'heatmap', 'surface'
]), help='Generate interactive chart')
@click.option('--output', type=click.Path(), help='Save chart to HTML file')
def command(..., chart, output):
    # ... existing logic ...

    if chart:
        fig = create_chart(data, chart_type=chart)

        if output:
            fig.write_html(output)
            click.echo(f"📊 Chart saved to: {output}")
        else:
            # Auto-save to results/charts/
            auto_path = f"results/charts/{command_name}_{chart}_{timestamp}.html"
            fig.write_html(auto_path)
            click.echo(f"📊 Chart saved to: {auto_path}")
```

---

## PHASE 4: POLISH & ADVANCED FEATURES

### 4.1 Export & Reporting

```python
# Export to multiple formats
fig.write_html("chart.html")      # Interactive HTML
fig.write_image("chart.png")      # Static PNG
fig.write_image("chart.svg")      # Vector SVG
fig.write_image("chart.pdf")      # PDF

# Generate PDF report with multiple charts
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
# ... report generation logic
```

### 4.2 Performance Optimization

```python
# Use caching for expensive calculations
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_chart(ticker: str, chart_type: str) -> go.Figure:
    # ... chart generation
    pass

# Downsample for large datasets
if len(df) > 10000:
    df = df.iloc[::10]  # Take every 10th point
```

### 4.3 Real-Time Updates

```python
# Dash callback for live updates
@app.callback(
    Output('live-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_chart(n):
    # Fetch latest data
    # Update figure
    return fig
```

---

## COMPLETE FEATURE CHECKLIST

### Portfolio (7 charts)
- [ ] Portfolio pie chart
- [ ] Position P&L heatmap
- [ ] Sector composition bar chart
- [ ] Historical value line chart
- [ ] Cost basis vs current scatter
- [ ] Allocation gauge
- [ ] Sector performance comparison

### Price Data (8 charts)
- [ ] Candlestick chart with volume
- [ ] Intraday minute chart
- [ ] Multi-ticker comparison
- [ ] VWAP overlay
- [ ] Volume profile
- [ ] Bid-ask spread
- [ ] Price range heatmap
- [ ] Gap analysis

### Technical Analysis (12 charts)
- [ ] Multi-indicator dashboard (4 subplots)
- [ ] RSI with bands
- [ ] MACD histogram
- [ ] Bollinger Bands
- [ ] Stochastic oscillator
- [ ] ADX gauge
- [ ] Signal strength heatmap
- [ ] Moving average crossovers
- [ ] Volume OBV
- [ ] ATR volatility
- [ ] Ichimoku cloud
- [ ] Fibonacci retracements

### Options Strategies (8 charts)
- [ ] Payoff diagram
- [ ] Max profit/loss zones
- [ ] Breakeven lines
- [ ] Strategy comparison overlay
- [ ] Risk profile gauges
- [ ] Probability distribution
- [ ] Time decay animation
- [ ] Scenario analysis matrix

### Greeks (10 charts)
- [ ] Greeks timeline (2D)
- [ ] Delta surface (3D)
- [ ] Gamma surface (3D)
- [ ] Vega surface (3D)
- [ ] Greeks heatmap (time × price)
- [ ] Greeks gauge dashboard
- [ ] Charm decay chart
- [ ] Vanna sensitivity
- [ ] Vomma visualization
- [ ] Multi-Greek comparison

### Options Chain (7 charts)
- [ ] Options chain heatmap (OI)
- [ ] Volatility surface (3D)
- [ ] Put/call ratio timeline
- [ ] Strike concentration
- [ ] Expiration distribution
- [ ] Greeks by strike
- [ ] IV percentile

### Backtesting (9 charts)
- [ ] Cumulative returns
- [ ] Drawdown (underwater)
- [ ] Monthly returns heatmap
- [ ] Rolling Sharpe ratio
- [ ] Daily return distribution
- [ ] Trade entry/exit markers
- [ ] Portfolio weight evolution
- [ ] Correlation matrix
- [ ] Feature importance

### Fundamentals (6 charts)
- [ ] P/E ratio comparison
- [ ] Growth metrics bar chart
- [ ] Valuation heatmap
- [ ] Balance sheet gauges
- [ ] Margin trends
- [ ] ROE/ROA scatter

### Sentiment (4 charts)
- [ ] Sentiment gauge
- [ ] Article breakdown pie
- [ ] Sentiment timeline
- [ ] Buzz score trend

### Market Context (4 charts)
- [ ] VIX gauge
- [ ] Treasury yield curve
- [ ] Economic calendar
- [ ] Sector rotation heatmap

---

## DEPENDENCIES & SETUP

### Install Plotly
```bash
pip install plotly>=5.18.0
pip install kaleido  # For static image export
```

### Update pyproject.toml
```toml
dependencies = [
    # ... existing ...
    "plotly>=5.18.0",
    "kaleido>=0.2.1",  # For PNG/SVG/PDF export
]
```

---

## FILE STRUCTURE

```
quantlab/
├── visualization/
│   ├── __init__.py
│   ├── portfolio_charts.py       # Portfolio visualization
│   ├── price_charts.py            # Candlestick, OHLC
│   ├── technical_charts.py        # Technical indicators
│   ├── options_charts.py          # Payoff diagrams, chains
│   ├── greeks_charts.py           # Greeks surfaces, timelines
│   ├── backtest_charts.py         # Backtest performance
│   ├── fundamental_charts.py      # Fundamentals & ratios
│   ├── sentiment_charts.py        # Sentiment & news
│   ├── utils.py                   # Shared utilities
│   └── themes.py                  # Custom Plotly themes
├── cli/
│   └── ... (add --chart flags)
└── dashboard/                     # Optional: Dash/Streamlit apps
    ├── app.py
    ├── pages/
    │   ├── portfolio.py
    │   ├── technical.py
    │   ├── options.py
    │   └── backtest.py
    └── components/
        ├── charts.py
        └── layout.py
```

---

## SUCCESS METRICS

### Phase 1 (Weeks 1-2):
- ✅ 7 Priority 1 charts implemented
- ✅ CLI integration working
- ✅ HTML export functional
- ✅ User can generate portfolio pie, candlestick, payoff, technical, backtest charts

### Phase 2 (Weeks 3-4):
- ✅ 10 Priority 2 charts (including 3D)
- ✅ Greeks visualization complete
- ✅ Options chain analysis working
- ✅ 3D surfaces rendering correctly

### Phase 3 (Weeks 5-6):
- ✅ Multi-page dashboard deployed
- ✅ All charts integrated
- ✅ Navigation working
- ✅ Performance acceptable (<2s load)

### Phase 4 (Week 7+):
- ✅ PDF export working
- ✅ Real-time updates (if applicable)
- ✅ Mobile-responsive
- ✅ Documentation complete

---

## TIMELINE SUMMARY

| Week | Focus | Deliverable | Hours |
|------|-------|-------------|-------|
| 1-2 | Foundation | 7 Priority 1 charts | 40-50 |
| 3-4 | Options & 3D | Greeks & chains | 50-60 |
| 5-6 | Dashboards | Integrated UI | 30-40 |
| 7+ | Polish | Production ready | 40+ |
| **Total** | | **All 79 charts** | **~200** |

---

## CONCLUSION

This comprehensive plan provides:
- ✅ **79 Plotly visualizations** across all QuantLab features
- ✅ **4-phase implementation** (8 weeks total)
- ✅ **Complete code examples** for each chart type
- ✅ **CLI integration pattern** for all commands
- ✅ **3D visualization support** for advanced analytics
- ✅ **Export to HTML/PNG/SVG/PDF**
- ✅ **Dashboard framework** (optional Dash/Streamlit)

**Next Step:** Choose 2-3 Priority 1 charts to implement first (recommend: Portfolio Pie, Candlestick, Payoff Diagram).

---

**Ready to start Phase 1 implementation?** 🚀
