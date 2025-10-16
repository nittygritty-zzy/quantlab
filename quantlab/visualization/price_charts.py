"""
Price chart visualizations using Plotly.

Provides interactive price charts including:
- Candlestick charts
- OHLCV charts with volume
- Multi-ticker comparison
- Price with moving averages
"""

from typing import Optional, List, Dict
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quantlab.visualization.base import (
    create_base_figure,
    COLORS,
    add_range_selector,
    apply_quantlab_theme,
    get_chart_config,
    get_market_rangebreaks
)


def create_candlestick_chart(
    df: pd.DataFrame,
    ticker: str,
    show_volume: bool = True,
    show_range_selector: bool = True,
    height: int = 600,
    intraday: bool = False
) -> go.Figure:
    """
    Create interactive OHLC candlestick chart with optional volume.

    Args:
        df: DataFrame with columns: date, open, high, low, close, volume
        ticker: Stock ticker symbol
        show_volume: Include volume subplot
        show_range_selector: Add date range selector buttons
        height: Chart height in pixels

    Returns:
        Plotly figure object

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     'date': pd.date_range('2024-01-01', periods=30),
        ...     'open': np.random.randn(30).cumsum() + 100,
        ...     'high': np.random.randn(30).cumsum() + 102,
        ...     'low': np.random.randn(30).cumsum() + 98,
        ...     'close': np.random.randn(30).cumsum() + 100,
        ...     'volume': np.random.randint(1000000, 5000000, 30)
        ... })
        >>> fig = create_candlestick_chart(df, ticker="AAPL")
        >>> fig.show()
    """
    # Validate required columns
    required_cols = ['date', 'open', 'high', 'low', 'close']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    if show_volume and 'volume' not in df.columns:
        raise ValueError("'volume' column required when show_volume=True")

    # Get chart config
    config = get_chart_config('candlestick')

    # Format x-axis labels for intraday charts
    if intraday:
        # Use consistent format: "2025-09-16 09:30 AM"
        x_values = df['date'].dt.strftime('%Y-%m-%d %I:%M %p')
    else:
        x_values = df['date']

    # Create subplots if volume is shown
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{ticker} Price', 'Volume')
        )

        # Add candlestick
        fig.add_trace(
            go.Candlestick(
                x=x_values,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='OHLC',
                increasing_line_color=config.get('increasing_line_color', COLORS['bullish']),
                decreasing_line_color=config.get('decreasing_line_color', COLORS['bearish']),
                increasing_fillcolor=config.get('increasing_fillcolor', COLORS['bullish']),
                decreasing_fillcolor=config.get('decreasing_fillcolor', COLORS['bearish'])
            ),
            row=1, col=1
        )

        # Add volume bars with colors
        colors = []
        for i in range(len(df)):
            if i == 0:
                colors.append(COLORS['neutral'])
            else:
                if df.iloc[i]['close'] >= df.iloc[i]['open']:
                    colors.append(COLORS['bullish'])
                else:
                    colors.append(COLORS['bearish'])

        fig.add_trace(
            go.Bar(
                x=x_values,
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                showlegend=False,
                opacity=0.7
            ),
            row=2, col=1
        )

        # Update y-axes
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)

    else:
        # Single candlestick chart without volume
        fig = go.Figure()

        fig.add_trace(
            go.Candlestick(
                x=x_values,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='OHLC',
                increasing_line_color=config.get('increasing_line_color', COLORS['bullish']),
                decreasing_line_color=config.get('decreasing_line_color', COLORS['bearish'])
            )
        )

        fig.update_yaxes(title_text="Price ($)")

    # Update layout
    layout_config = {
        'title': f'{ticker} - Candlestick Chart',
        'xaxis_title': "Date",
        'height': height,
        'hovermode': 'x unified',
        'xaxis_rangeslider_visible': False
    }

    # For intraday charts, use categorical x-axis to avoid gaps
    # For daily charts, use rangebreaks to hide weekends/holidays
    if intraday:
        layout_config['xaxis'] = dict(type='category')
    else:
        layout_config['xaxis'] = dict(rangebreaks=get_market_rangebreaks(intraday=False))

    fig.update_layout(**layout_config)

    # Add range selector
    if show_range_selector:
        fig = add_range_selector(fig)

    fig = apply_quantlab_theme(fig)

    return fig


def create_price_line_chart(
    df: pd.DataFrame,
    ticker: str,
    price_column: str = 'close',
    show_volume: bool = False,
    moving_averages: Optional[List[int]] = None,
    height: int = 600,
    intraday: bool = False
) -> go.Figure:
    """
    Create line chart for price with optional moving averages.

    Args:
        df: DataFrame with columns: date, price_column, (optional) volume
        ticker: Stock ticker symbol
        price_column: Column to use for price (default: 'close')
        show_volume: Include volume subplot
        moving_averages: List of MA periods (e.g., [20, 50, 200])
        height: Chart height in pixels

    Returns:
        Plotly figure object

    Example:
        >>> fig = create_price_line_chart(
        ...     df,
        ...     ticker="AAPL",
        ...     moving_averages=[20, 50, 200]
        ... )
        >>> fig.show()
    """
    if price_column not in df.columns:
        raise ValueError(f"Column '{price_column}' not found in DataFrame")

    # Create subplots if volume is shown
    if show_volume:
        if 'volume' not in df.columns:
            raise ValueError("'volume' column required when show_volume=True")

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{ticker} Price', 'Volume')
        )
        price_row = 1
    else:
        fig = go.Figure()
        price_row = None

    # Format x-axis labels for intraday charts
    if intraday:
        # Use consistent format: "2025-09-16 09:30 AM"
        x_values = df['date'].dt.strftime('%Y-%m-%d %I:%M %p')
    else:
        x_values = df['date']

    # Add price line
    trace_price = go.Scatter(
        x=x_values,
        y=df[price_column],
        mode='lines',
        name='Price',
        line=dict(color=COLORS['primary'], width=2),
        hovertemplate='Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
    )

    if price_row:
        fig.add_trace(trace_price, row=price_row, col=1)
    else:
        fig.add_trace(trace_price)

    # Add moving averages
    if moving_averages:
        ma_colors = [COLORS['warning'], COLORS['info'], COLORS['danger']]
        for i, period in enumerate(moving_averages):
            ma_col = f'ma_{period}'
            if ma_col not in df.columns:
                # Calculate MA if not present
                df[ma_col] = df[price_column].rolling(window=period).mean()

            trace_ma = go.Scatter(
                x=x_values,
                y=df[ma_col],
                mode='lines',
                name=f'MA({period})',
                line=dict(
                    color=ma_colors[i % len(ma_colors)],
                    width=1,
                    dash='dash'
                ),
                hovertemplate=f'MA({period}): $%{{y:.2f}}<extra></extra>'
            )

            if price_row:
                fig.add_trace(trace_ma, row=price_row, col=1)
            else:
                fig.add_trace(trace_ma)

    # Add volume if requested
    if show_volume:
        colors = []
        for i in range(len(df)):
            if i == 0:
                colors.append(COLORS['neutral'])
            else:
                if df.iloc[i][price_column] >= df.iloc[i - 1][price_column]:
                    colors.append(COLORS['bullish'])
                else:
                    colors.append(COLORS['bearish'])

        fig.add_trace(
            go.Bar(
                x=x_values,
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                showlegend=False,
                opacity=0.7
            ),
            row=2, col=1
        )

        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)

    # Update layout
    layout_config = {
        'title': f'{ticker} - Price Chart',
        'xaxis_title': "Date",
        'yaxis_title': "Price ($)" if not show_volume else None,
        'height': height,
        'hovermode': 'x unified',
        'legend': dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    }

    # For intraday charts, use categorical x-axis to avoid gaps
    # For daily charts, use rangebreaks to hide weekends/holidays
    if intraday:
        layout_config['xaxis'] = dict(type='category')
    else:
        layout_config['xaxis'] = dict(rangebreaks=get_market_rangebreaks(intraday=False))

    fig.update_layout(**layout_config)

    fig = add_range_selector(fig)
    fig = apply_quantlab_theme(fig)

    return fig


def create_multi_ticker_comparison(
    data_dict: Dict[str, pd.DataFrame],
    price_column: str = 'close',
    normalize: bool = True,
    height: int = 600
) -> go.Figure:
    """
    Create comparison chart for multiple tickers.

    Args:
        data_dict: Dict mapping ticker -> DataFrame with date and price columns
        price_column: Column to use for price
        normalize: Normalize to percentage change from first date
        height: Chart height in pixels

    Returns:
        Plotly figure object

    Example:
        >>> data = {
        ...     'AAPL': df_aapl,
        ...     'GOOGL': df_googl,
        ...     'MSFT': df_msft
        ... }
        >>> fig = create_multi_ticker_comparison(data, normalize=True)
        >>> fig.show()
    """
    if not data_dict:
        raise ValueError("No ticker data provided")

    fig = go.Figure()

    colors = [COLORS['primary'], COLORS['success'], COLORS['warning'],
              COLORS['danger'], COLORS['info']]

    for i, (ticker, df) in enumerate(data_dict.items()):
        if 'date' not in df.columns or price_column not in df.columns:
            raise ValueError(f"Missing required columns for {ticker}")

        y_values = df[price_column]

        if normalize:
            # Normalize to percentage change
            first_value = y_values.iloc[0]
            y_values = ((y_values / first_value) - 1) * 100
            y_label = "% Change"
        else:
            y_label = "Price ($)"

        fig.add_trace(go.Scatter(
            x=df['date'],
            y=y_values,
            mode='lines',
            name=ticker,
            line=dict(color=colors[i % len(colors)], width=2),
            hovertemplate=f'{ticker}: %{{y:.2f}}<extra></extra>'
        ))

    # Update layout
    fig.update_layout(
        title='Multi-Ticker Comparison',
        xaxis_title="Date",
        yaxis_title=y_label,
        height=height,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            rangebreaks=get_market_rangebreaks()  # Hide weekends and holidays
        )
    )

    fig = add_range_selector(fig)
    fig = apply_quantlab_theme(fig)

    return fig
