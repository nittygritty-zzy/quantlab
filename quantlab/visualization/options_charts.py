"""
Options strategy visualization charts using Plotly.

Provides interactive visualizations for options including:
- Payoff diagrams
- Greeks surface plots (2D and 3D)
- Options chain heatmaps
- Greeks timeline projections
"""

from typing import Optional, Tuple, List, Dict, Any
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quantlab.visualization.base import (
    create_base_figure,
    COLORS,
    format_currency,
    apply_quantlab_theme,
    get_chart_config
)


def create_payoff_diagram(
    prices: np.ndarray,
    pnls: np.ndarray,
    strategy_name: str,
    current_price: float,
    breakeven_points: Optional[List[float]] = None,
    max_profit: Optional[float] = None,
    max_loss: Optional[float] = None,
    height: int = 600
) -> go.Figure:
    """
    Create interactive options strategy payoff diagram.

    Args:
        prices: Array of underlying prices
        pnls: Array of corresponding P&L values
        strategy_name: Name of options strategy
        current_price: Current underlying price
        breakeven_points: List of breakeven prices
        max_profit: Maximum profit value
        max_loss: Maximum loss value
        height: Chart height in pixels

    Returns:
        Plotly figure object

    Example:
        >>> prices = np.linspace(90, 110, 100)
        >>> pnls = np.maximum(prices - 100, 0) - 5  # Long call at 100, premium 5
        >>> fig = create_payoff_diagram(
        ...     prices, pnls,
        ...     strategy_name="Long Call",
        ...     current_price=100,
        ...     breakeven_points=[105],
        ...     max_profit=None,  # Unlimited
        ...     max_loss=-500
        ... )
        >>> fig.show()
    """
    config = get_chart_config('payoff_diagram')

    fig = go.Figure()

    # Add payoff curve with fill
    fig.add_trace(go.Scatter(
        x=prices,
        y=pnls,
        mode='lines',
        name='P&L at Expiration',
        line=dict(
            color=COLORS['primary'],
            width=config.get('line_width', 3)
        ),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.2)',
        hovertemplate='Price: $%{x:.2f}<br>P&L: $%{y:,.0f}<extra></extra>'
    ))

    # Add zero line
    fig.add_hline(
        y=0,
        line_dash="solid",
        line_color="black",
        line_width=1,
        annotation_text="Breakeven"
    )

    # Add current stock price marker
    fig.add_vline(
        x=current_price,
        line_dash="dash",
        line_color=COLORS['success'],
        line_width=2,
        annotation_text=f"Current: ${current_price:.2f}",
        annotation_position="top"
    )

    # Add breakeven points
    if breakeven_points:
        for i, be in enumerate(breakeven_points):
            fig.add_vline(
                x=be,
                line_dash="dot",
                line_color=config.get('breakeven_color', COLORS['warning']),
                line_width=2,
                annotation_text=f"BE: ${be:.2f}",
                annotation_position="bottom" if i % 2 == 0 else "top"
            )

    # Add max profit line
    if max_profit is not None:
        fig.add_hline(
            y=max_profit,
            line_dash="dash",
            line_color=config.get('profit_color', COLORS['success']),
            line_width=1,
            annotation_text=f"Max Profit: {format_currency(max_profit)}",
            annotation_position="right"
        )

    # Add max loss line
    if max_loss is not None:
        fig.add_hline(
            y=max_loss,
            line_dash="dash",
            line_color=config.get('loss_color', COLORS['danger']),
            line_width=1,
            annotation_text=f"Max Loss: {format_currency(max_loss)}",
            annotation_position="right"
        )

    # Color profit/loss regions
    profit_mask = pnls >= 0
    loss_mask = pnls < 0

    if np.any(profit_mask):
        fig.add_trace(go.Scatter(
            x=prices[profit_mask],
            y=pnls[profit_mask],
            fill='tozeroy',
            fillcolor='rgba(46, 204, 113, 0.1)',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))

    if np.any(loss_mask):
        fig.add_trace(go.Scatter(
            x=prices[loss_mask],
            y=pnls[loss_mask],
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.1)',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))

    # Update layout
    fig.update_layout(
        title=f'{strategy_name} - Payoff Diagram',
        xaxis_title='Underlying Price at Expiration ($)',
        yaxis_title='Profit / Loss ($)',
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

    fig = apply_quantlab_theme(fig)

    return fig


def create_greeks_heatmap(
    greeks_data: pd.DataFrame,
    greek_name: str = 'delta',
    height: int = 600
) -> go.Figure:
    """
    Create heatmap showing Greek values across strikes and expirations.

    Args:
        greeks_data: DataFrame with columns: strike, expiration, greek_value
        greek_name: Name of Greek to display (delta, gamma, theta, vega, etc.)
        height: Chart height in pixels

    Returns:
        Plotly figure object

    Example:
        >>> df = pd.DataFrame({
        ...     'strike': [95, 100, 105] * 3,
        ...     'expiration': ['2024-01-01'] * 3 + ['2024-02-01'] * 3 + ['2024-03-01'] * 3,
        ...     'delta': [0.8, 0.5, 0.2, 0.7, 0.5, 0.3, 0.6, 0.5, 0.4]
        ... })
        >>> fig = create_greeks_heatmap(df, greek_name='delta')
        >>> fig.show()
    """
    # Pivot data for heatmap
    pivot = greeks_data.pivot_table(
        index='strike',
        columns='expiration',
        values=greek_name,
        aggfunc='mean'
    )

    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='RdYlGn',
        hovertemplate='Strike: $%{y:.2f}<br>' +
                      'Expiration: %{x}<br>' +
                      f'{greek_name.capitalize()}: %{{z:.4f}}<br>' +
                      '<extra></extra>',
        colorbar=dict(title=greek_name.capitalize())
    ))

    fig.update_layout(
        title=f'Options {greek_name.capitalize()} - Heatmap',
        xaxis_title='Expiration Date',
        yaxis_title='Strike Price ($)',
        height=height
    )

    fig = apply_quantlab_theme(fig)

    return fig


def create_greeks_timeline(
    timeline_data: pd.DataFrame,
    strategy_name: str,
    greeks_to_show: Optional[List[str]] = None,
    height: int = 700
) -> go.Figure:
    """
    Create timeline showing Greeks evolution over time.

    Args:
        timeline_data: DataFrame with columns: days_forward, delta, gamma, theta, vega, etc.
        strategy_name: Name of options strategy
        greeks_to_show: List of Greeks to display (default: all first-order)
        height: Chart height in pixels

    Returns:
        Plotly figure object with subplots

    Example:
        >>> df = pd.DataFrame({
        ...     'days_forward': range(0, 30),
        ...     'delta': np.random.randn(30).cumsum() + 50,
        ...     'gamma': np.random.randn(30).cumsum() + 5,
        ...     'theta': np.random.randn(30).cumsum() - 10,
        ...     'vega': np.random.randn(30).cumsum() + 20
        ... })
        >>> fig = create_greeks_timeline(df, strategy_name="Long Call")
        >>> fig.show()
    """
    if greeks_to_show is None:
        greeks_to_show = ['delta', 'gamma', 'theta', 'vega']

    # Filter to available Greeks
    available_greeks = [g for g in greeks_to_show if g in timeline_data.columns]

    if not available_greeks:
        raise ValueError(f"No Greeks found in data. Available columns: {timeline_data.columns.tolist()}")

    n_greeks = len(available_greeks)

    # Create subplots
    fig = make_subplots(
        rows=n_greeks,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=[f'{g.capitalize()} Evolution' for g in available_greeks]
    )

    colors = [COLORS['primary'], COLORS['success'], COLORS['danger'], COLORS['warning']]

    for i, greek in enumerate(available_greeks):
        fig.add_trace(
            go.Scatter(
                x=timeline_data['days_forward'],
                y=timeline_data[greek],
                mode='lines+markers',
                name=greek.capitalize(),
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=4),
                hovertemplate=f'Days Forward: %{{x}}<br>{greek.capitalize()}: %{{y:.4f}}<extra></extra>'
            ),
            row=i + 1,
            col=1
        )

        # Add zero line for reference
        fig.add_hline(
            y=0,
            line_dash="dot",
            line_color="gray",
            line_width=1,
            row=i + 1,
            col=1
        )

        # Update y-axis title
        fig.update_yaxes(title_text=greek.capitalize(), row=i + 1, col=1)

    # Update x-axis title (only bottom)
    fig.update_xaxes(title_text="Days Forward", row=n_greeks, col=1)

    # Update layout
    fig.update_layout(
        title=f'{strategy_name} - Greeks Timeline Projection',
        height=height,
        hovermode='x unified',
        showlegend=False
    )

    fig = apply_quantlab_theme(fig)

    return fig


def create_greeks_3d_surface(
    price_range: np.ndarray,
    time_range: np.ndarray,
    greek_values: np.ndarray,
    greek_name: str,
    strategy_name: str,
    current_price: float,
    height: int = 700
) -> go.Figure:
    """
    Create 3D surface plot showing Greek sensitivity to price and time.

    Args:
        price_range: Array of underlying prices
        time_range: Array of days forward
        greek_values: 2D array of Greek values (time × price)
        greek_name: Name of Greek (delta, gamma, theta, vega)
        strategy_name: Name of options strategy
        current_price: Current underlying price
        height: Chart height in pixels

    Returns:
        Plotly figure object

    Example:
        >>> prices = np.linspace(90, 110, 50)
        >>> days = np.linspace(0, 30, 30)
        >>> P, D = np.meshgrid(prices, days)
        >>> delta_values = 0.5 * np.exp(-(P - 100)**2 / 100) * (1 - D / 30)
        >>> fig = create_greeks_3d_surface(
        ...     prices, days, delta_values,
        ...     greek_name='delta',
        ...     strategy_name='Long Call',
        ...     current_price=100
        ... )
        >>> fig.show()
    """
    fig = go.Figure()

    fig.add_trace(go.Surface(
        x=price_range,
        y=time_range,
        z=greek_values,
        colorscale='Viridis',
        hovertemplate='Price: $%{x:.2f}<br>' +
                      'Days Fwd: %{y:.0f}<br>' +
                      f'{greek_name.capitalize()}: %{{z:.4f}}<br>' +
                      '<extra></extra>',
        colorbar=dict(title=greek_name.capitalize())
    ))

    # Add marker for current price
    # Find the closest price index
    current_idx = np.argmin(np.abs(price_range - current_price))
    fig.add_trace(go.Scatter3d(
        x=[price_range[current_idx]] * len(time_range),
        y=time_range,
        z=greek_values[:, current_idx],
        mode='lines',
        line=dict(color='red', width=4),
        name='Current Price',
        hoverinfo='skip'
    ))

    fig.update_layout(
        title=f'{strategy_name} - {greek_name.capitalize()} Surface',
        scene=dict(
            xaxis_title='Underlying Price ($)',
            yaxis_title='Days Forward',
            zaxis_title=greek_name.capitalize(),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.3)
            )
        ),
        height=height
    )

    fig = apply_quantlab_theme(fig)

    return fig


def create_strategy_comparison(
    comparison_data: Dict[str, Tuple[np.ndarray, np.ndarray]],
    current_price: float,
    height: int = 600
) -> go.Figure:
    """
    Create comparison chart for multiple options strategies.

    Args:
        comparison_data: Dict mapping strategy_name -> (prices, pnls)
        current_price: Current underlying price
        height: Chart height in pixels

    Returns:
        Plotly figure object

    Example:
        >>> prices = np.linspace(90, 110, 100)
        >>> data = {
        ...     'Long Call': (prices, np.maximum(prices - 100, 0) - 5),
        ...     'Long Put': (prices, np.maximum(100 - prices, 0) - 5),
        ...     'Straddle': (prices, np.abs(prices - 100) - 10)
        ... }
        >>> fig = create_strategy_comparison(data, current_price=100)
        >>> fig.show()
    """
    if not comparison_data:
        raise ValueError("No strategies provided")

    fig = go.Figure()

    colors = [COLORS['primary'], COLORS['success'], COLORS['danger'],
              COLORS['warning'], COLORS['info']]

    for i, (strategy_name, (prices, pnls)) in enumerate(comparison_data.items()):
        fig.add_trace(go.Scatter(
            x=prices,
            y=pnls,
            mode='lines',
            name=strategy_name,
            line=dict(color=colors[i % len(colors)], width=2),
            hovertemplate=f'{strategy_name}<br>Price: $%{{x:.2f}}<br>P&L: $%{{y:,.0f}}<extra></extra>'
        ))

    # Add zero line
    fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)

    # Add current price marker
    fig.add_vline(
        x=current_price,
        line_dash="dash",
        line_color=COLORS['neutral'],
        line_width=2,
        annotation_text=f"Current: ${current_price:.2f}"
    )

    fig.update_layout(
        title='Options Strategy Comparison',
        xaxis_title='Underlying Price at Expiration ($)',
        yaxis_title='Profit / Loss ($)',
        height=height,
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    fig = apply_quantlab_theme(fig)

    return fig
