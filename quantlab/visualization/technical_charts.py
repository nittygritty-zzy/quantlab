"""
Technical indicator visualization charts using Plotly.

Provides interactive visualizations for technical analysis including:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Multi-indicator dashboards
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quantlab.visualization.base import (
    create_base_figure,
    COLORS,
    add_range_selector,
    apply_quantlab_theme,
)


def create_rsi_chart(
    df: pd.DataFrame,
    ticker: str,
    rsi_column: str = 'rsi',
    overbought: float = 70,
    oversold: float = 30,
    show_price: bool = True,
    height: int = 600
) -> go.Figure:
    """
    Create RSI chart with overbought/oversold zones.

    Args:
        df: DataFrame with columns: date, rsi, (optional) close
        ticker: Stock ticker symbol
        rsi_column: Name of RSI column (default: 'rsi')
        overbought: Overbought threshold (default: 70)
        oversold: Oversold threshold (default: 30)
        show_price: Show price subplot above RSI
        height: Chart height in pixels

    Returns:
        Plotly figure object

    Example:
        >>> df = pd.DataFrame({
        ...     'date': pd.date_range('2024-01-01', periods=90),
        ...     'close': np.random.randn(90).cumsum() + 100,
        ...     'rsi': 50 + np.random.randn(90).cumsum()
        ... })
        >>> fig = create_rsi_chart(df, ticker="AAPL")
        >>> fig.show()
    """
    if 'date' not in df.columns or rsi_column not in df.columns:
        raise ValueError(f"DataFrame must contain 'date' and '{rsi_column}' columns")

    if show_price and 'close' not in df.columns:
        raise ValueError("'close' column required when show_price=True")

    # Create subplots
    if show_price:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.4],
            subplot_titles=(f'{ticker} Price', 'RSI (14)')
        )
        price_row = 1
        rsi_row = 2
    else:
        fig = go.Figure()
        price_row = None
        rsi_row = None

    # Add price line if requested
    if show_price:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['close'],
                mode='lines',
                name='Price',
                line=dict(color=COLORS['primary'], width=2),
                hovertemplate='Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
            ),
            row=price_row, col=1
        )

    # Add RSI line
    trace_rsi = go.Scatter(
        x=df['date'],
        y=df[rsi_column],
        mode='lines',
        name='RSI',
        line=dict(color=COLORS['primary'], width=2),
        hovertemplate='Date: %{x}<br>RSI: %{y:.2f}<extra></extra>'
    )

    if rsi_row:
        fig.add_trace(trace_rsi, row=rsi_row, col=1)
    else:
        fig.add_trace(trace_rsi)

    # Add overbought zone (shaded red)
    shape_row = rsi_row if rsi_row else None

    if rsi_row:
        # Overbought zone
        fig.add_hrect(
            y0=overbought, y1=100,
            fillcolor=COLORS['danger'],
            opacity=0.1,
            line_width=0,
            row=rsi_row, col=1
        )
        # Oversold zone
        fig.add_hrect(
            y0=0, y1=oversold,
            fillcolor=COLORS['success'],
            opacity=0.1,
            line_width=0,
            row=rsi_row, col=1
        )
        # Overbought line
        fig.add_hline(
            y=overbought,
            line_dash="dash",
            line_color=COLORS['danger'],
            line_width=1,
            annotation_text="Overbought",
            annotation_position="right",
            row=rsi_row, col=1
        )
        # Oversold line
        fig.add_hline(
            y=oversold,
            line_dash="dash",
            line_color=COLORS['success'],
            line_width=1,
            annotation_text="Oversold",
            annotation_position="right",
            row=rsi_row, col=1
        )
        # Midline (50)
        fig.add_hline(
            y=50,
            line_dash="dot",
            line_color="gray",
            line_width=1,
            row=rsi_row, col=1
        )
    else:
        # Single chart without subplots
        fig.add_hrect(y0=overbought, y1=100, fillcolor=COLORS['danger'], opacity=0.1, line_width=0)
        fig.add_hrect(y0=0, y1=oversold, fillcolor=COLORS['success'], opacity=0.1, line_width=0)
        fig.add_hline(y=overbought, line_dash="dash", line_color=COLORS['danger'])
        fig.add_hline(y=oversold, line_dash="dash", line_color=COLORS['success'])
        fig.add_hline(y=50, line_dash="dot", line_color="gray")

    # Update axes
    if show_price:
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)
    else:
        fig.update_yaxes(title_text="RSI", range=[0, 100])

    # Update layout
    fig.update_layout(
        title=f'{ticker} - RSI Analysis',
        xaxis_title="Date",
        height=height,
        hovermode='x unified',
        showlegend=True
    )

    fig = add_range_selector(fig)
    fig = apply_quantlab_theme(fig)

    return fig


def create_macd_chart(
    df: pd.DataFrame,
    ticker: str,
    macd_column: str = 'macd',
    signal_column: str = 'macd_signal',
    histogram_column: str = 'macd_histogram',
    show_price: bool = True,
    height: int = 600
) -> go.Figure:
    """
    Create MACD chart with signal line and histogram.

    Args:
        df: DataFrame with columns: date, macd, macd_signal, macd_histogram, (optional) close
        ticker: Stock ticker symbol
        macd_column: Name of MACD column (default: 'macd')
        signal_column: Name of signal line column (default: 'macd_signal')
        histogram_column: Name of histogram column (default: 'macd_histogram')
        show_price: Show price subplot above MACD
        height: Chart height in pixels

    Returns:
        Plotly figure object

    Example:
        >>> df = pd.DataFrame({
        ...     'date': pd.date_range('2024-01-01', periods=90),
        ...     'close': np.random.randn(90).cumsum() + 100,
        ...     'macd': np.random.randn(90).cumsum(),
        ...     'macd_signal': np.random.randn(90).cumsum(),
        ...     'macd_histogram': np.random.randn(90)
        ... })
        >>> fig = create_macd_chart(df, ticker="AAPL")
        >>> fig.show()
    """
    required_cols = ['date', macd_column, signal_column, histogram_column]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    if show_price and 'close' not in df.columns:
        raise ValueError("'close' column required when show_price=True")

    # Create subplots
    if show_price:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.4],
            subplot_titles=(f'{ticker} Price', 'MACD')
        )
        price_row = 1
        macd_row = 2
    else:
        fig = go.Figure()
        price_row = None
        macd_row = None

    # Add price line if requested
    if show_price:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['close'],
                mode='lines',
                name='Price',
                line=dict(color=COLORS['primary'], width=2),
                hovertemplate='Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
            ),
            row=price_row, col=1
        )

    # Add histogram (as bars)
    histogram_colors = [COLORS['success'] if val >= 0 else COLORS['danger']
                       for val in df[histogram_column]]

    trace_hist = go.Bar(
        x=df['date'],
        y=df[histogram_column],
        name='Histogram',
        marker_color=histogram_colors,
        opacity=0.5,
        hovertemplate='Date: %{x}<br>Histogram: %{y:.3f}<extra></extra>'
    )

    # Add MACD line
    trace_macd = go.Scatter(
        x=df['date'],
        y=df[macd_column],
        mode='lines',
        name='MACD',
        line=dict(color=COLORS['primary'], width=2),
        hovertemplate='Date: %{x}<br>MACD: %{y:.3f}<extra></extra>'
    )

    # Add signal line
    trace_signal = go.Scatter(
        x=df['date'],
        y=df[signal_column],
        mode='lines',
        name='Signal',
        line=dict(color=COLORS['danger'], width=2, dash='dash'),
        hovertemplate='Date: %{x}<br>Signal: %{y:.3f}<extra></extra>'
    )

    if macd_row:
        fig.add_trace(trace_hist, row=macd_row, col=1)
        fig.add_trace(trace_macd, row=macd_row, col=1)
        fig.add_trace(trace_signal, row=macd_row, col=1)

        # Add zero line
        fig.add_hline(
            y=0,
            line_dash="solid",
            line_color="black",
            line_width=1,
            row=macd_row, col=1
        )

        # Update axes
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="MACD", row=2, col=1)
    else:
        fig.add_trace(trace_hist)
        fig.add_trace(trace_macd)
        fig.add_trace(trace_signal)
        fig.add_hline(y=0, line_dash="solid", line_color="black")
        fig.update_yaxes(title_text="MACD")

    # Update layout
    fig.update_layout(
        title=f'{ticker} - MACD Analysis',
        xaxis_title="Date",
        height=height,
        hovermode='x unified',
        showlegend=True
    )

    fig = add_range_selector(fig)
    fig = apply_quantlab_theme(fig)

    return fig


def create_bollinger_bands_chart(
    df: pd.DataFrame,
    ticker: str,
    price_column: str = 'close',
    bb_upper_column: str = 'bb_upper',
    bb_middle_column: str = 'bb_middle',
    bb_lower_column: str = 'bb_lower',
    show_volume: bool = False,
    height: int = 600
) -> go.Figure:
    """
    Create Bollinger Bands chart with price overlay.

    Args:
        df: DataFrame with columns: date, close, bb_upper, bb_middle, bb_lower, (optional) volume
        ticker: Stock ticker symbol
        price_column: Name of price column (default: 'close')
        bb_upper_column: Name of upper band column (default: 'bb_upper')
        bb_middle_column: Name of middle band column (default: 'bb_middle')
        bb_lower_column: Name of lower band column (default: 'bb_lower')
        show_volume: Show volume subplot
        height: Chart height in pixels

    Returns:
        Plotly figure object

    Example:
        >>> df = pd.DataFrame({
        ...     'date': pd.date_range('2024-01-01', periods=90),
        ...     'close': np.random.randn(90).cumsum() + 100,
        ...     'bb_upper': np.random.randn(90).cumsum() + 105,
        ...     'bb_middle': np.random.randn(90).cumsum() + 100,
        ...     'bb_lower': np.random.randn(90).cumsum() + 95
        ... })
        >>> fig = create_bollinger_bands_chart(df, ticker="AAPL")
        >>> fig.show()
    """
    required_cols = ['date', price_column, bb_upper_column, bb_middle_column, bb_lower_column]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    if show_volume and 'volume' not in df.columns:
        raise ValueError("'volume' column required when show_volume=True")

    # Create subplots
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{ticker} Price with Bollinger Bands', 'Volume')
        )
        price_row = 1
        volume_row = 2
    else:
        fig = go.Figure()
        price_row = None
        volume_row = None

    # Add upper band
    trace_upper = go.Scatter(
        x=df['date'],
        y=df[bb_upper_column],
        mode='lines',
        name='BB Upper',
        line=dict(color=COLORS['neutral'], width=1, dash='dot'),
        hovertemplate='Date: %{x}<br>Upper: $%{y:.2f}<extra></extra>'
    )

    # Add lower band (with fill to upper)
    trace_lower = go.Scatter(
        x=df['date'],
        y=df[bb_lower_column],
        mode='lines',
        name='BB Lower',
        line=dict(color=COLORS['neutral'], width=1, dash='dot'),
        fill='tonexty',
        fillcolor='rgba(149, 165, 166, 0.1)',
        hovertemplate='Date: %{x}<br>Lower: $%{y:.2f}<extra></extra>'
    )

    # Add middle band (SMA)
    trace_middle = go.Scatter(
        x=df['date'],
        y=df[bb_middle_column],
        mode='lines',
        name='BB Middle (SMA)',
        line=dict(color=COLORS['warning'], width=1, dash='dash'),
        hovertemplate='Date: %{x}<br>SMA: $%{y:.2f}<extra></extra>'
    )

    # Add price line
    trace_price = go.Scatter(
        x=df['date'],
        y=df[price_column],
        mode='lines',
        name='Price',
        line=dict(color=COLORS['primary'], width=2),
        hovertemplate='Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
    )

    if price_row:
        fig.add_trace(trace_upper, row=price_row, col=1)
        fig.add_trace(trace_lower, row=price_row, col=1)
        fig.add_trace(trace_middle, row=price_row, col=1)
        fig.add_trace(trace_price, row=price_row, col=1)
    else:
        fig.add_trace(trace_upper)
        fig.add_trace(trace_lower)
        fig.add_trace(trace_middle)
        fig.add_trace(trace_price)

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
                x=df['date'],
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                showlegend=False,
                opacity=0.7
            ),
            row=volume_row, col=1
        )

        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
    else:
        fig.update_yaxes(title_text="Price ($)")

    # Update layout
    fig.update_layout(
        title=f'{ticker} - Bollinger Bands',
        xaxis_title="Date",
        height=height,
        hovermode='x unified',
        showlegend=True
    )

    fig = add_range_selector(fig)
    fig = apply_quantlab_theme(fig)

    return fig


def create_technical_dashboard(
    df: pd.DataFrame,
    ticker: str,
    height: int = 900
) -> go.Figure:
    """
    Create comprehensive technical analysis dashboard with multiple indicators.

    Args:
        df: DataFrame with columns: date, close, volume, rsi, macd, macd_signal,
            macd_histogram, bb_upper, bb_middle, bb_lower
        ticker: Stock ticker symbol
        height: Chart height in pixels

    Returns:
        Plotly figure with subplots

    Example:
        >>> df = pd.DataFrame({
        ...     'date': pd.date_range('2024-01-01', periods=90),
        ...     'close': np.random.randn(90).cumsum() + 100,
        ...     'volume': np.random.randint(1000000, 5000000, 90),
        ...     'rsi': 50 + np.random.randn(90).cumsum(),
        ...     'macd': np.random.randn(90).cumsum(),
        ...     'macd_signal': np.random.randn(90).cumsum(),
        ...     'macd_histogram': np.random.randn(90),
        ...     'bb_upper': np.random.randn(90).cumsum() + 105,
        ...     'bb_middle': np.random.randn(90).cumsum() + 100,
        ...     'bb_lower': np.random.randn(90).cumsum() + 95
        ... })
        >>> fig = create_technical_dashboard(df, ticker="AAPL")
        >>> fig.show()
    """
    # Create subplots: 4 rows
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.4, 0.2, 0.2, 0.2],
        subplot_titles=(
            f'{ticker} - Price with Bollinger Bands',
            'Volume',
            'RSI (14)',
            'MACD'
        )
    )

    # Row 1: Price with Bollinger Bands
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['bb_upper'],
            mode='lines',
            name='BB Upper',
            line=dict(color=COLORS['neutral'], width=1, dash='dot'),
            showlegend=True
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['bb_lower'],
            mode='lines',
            name='BB Lower',
            line=dict(color=COLORS['neutral'], width=1, dash='dot'),
            fill='tonexty',
            fillcolor='rgba(149, 165, 166, 0.1)',
            showlegend=True
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['bb_middle'],
            mode='lines',
            name='SMA(20)',
            line=dict(color=COLORS['warning'], width=1, dash='dash'),
            showlegend=True
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['close'],
            mode='lines',
            name='Price',
            line=dict(color=COLORS['primary'], width=2),
            showlegend=True
        ),
        row=1, col=1
    )

    # Row 2: Volume
    colors = []
    for i in range(len(df)):
        if i == 0:
            colors.append(COLORS['neutral'])
        else:
            if df.iloc[i]['close'] >= df.iloc[i - 1]['close']:
                colors.append(COLORS['bullish'])
            else:
                colors.append(COLORS['bearish'])

    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False,
            opacity=0.7
        ),
        row=2, col=1
    )

    # Row 3: RSI
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['rsi'],
            mode='lines',
            name='RSI',
            line=dict(color=COLORS['primary'], width=2),
            showlegend=True
        ),
        row=3, col=1
    )

    # RSI zones
    fig.add_hrect(y0=70, y1=100, fillcolor=COLORS['danger'], opacity=0.1, line_width=0, row=3, col=1)
    fig.add_hrect(y0=0, y1=30, fillcolor=COLORS['success'], opacity=0.1, line_width=0, row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS['danger'], line_width=1, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS['success'], line_width=1, row=3, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="gray", line_width=1, row=3, col=1)

    # Row 4: MACD
    histogram_colors = [COLORS['success'] if val >= 0 else COLORS['danger']
                       for val in df['macd_histogram']]

    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['macd_histogram'],
            name='Histogram',
            marker_color=histogram_colors,
            opacity=0.5,
            showlegend=True
        ),
        row=4, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['macd'],
            mode='lines',
            name='MACD',
            line=dict(color=COLORS['primary'], width=2),
            showlegend=True
        ),
        row=4, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['macd_signal'],
            mode='lines',
            name='Signal',
            line=dict(color=COLORS['danger'], width=2, dash='dash'),
            showlegend=True
        ),
        row=4, col=1
    )

    fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1, row=4, col=1)

    # Update axes
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
    fig.update_yaxes(title_text="MACD", row=4, col=1)
    fig.update_xaxes(title_text="Date", row=4, col=1)

    # Update layout
    fig.update_layout(
        title=f'{ticker} - Technical Analysis Dashboard',
        height=height,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig = add_range_selector(fig)
    fig = apply_quantlab_theme(fig)

    return fig
