"""
Portfolio visualization charts using Plotly.

Provides interactive visualizations for portfolio management including:
- Allocation pie charts
- Position P&L analysis
- Sector composition
"""

from typing import List, Optional, Dict, Any
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quantlab.visualization.base import (
    create_base_figure,
    COLORS,
    format_currency,
    format_percentage,
    apply_quantlab_theme
)


def create_portfolio_pie_chart(
    positions: List[Dict[str, Any]],
    portfolio_name: str = "Portfolio",
    value_type: str = "weight",
    show_percentages: bool = True,
    hole_size: float = 0.3
) -> go.Figure:
    """
    Create interactive pie chart showing portfolio allocation.

    Args:
        positions: List of position dicts with keys: ticker, weight, value, shares
        portfolio_name: Name of portfolio for title
        value_type: Type of value to display ('weight' or 'value')
        show_percentages: Show percentage labels on slices
        hole_size: Size of center hole (0 = pie, >0 = donut)

    Returns:
        Plotly figure object

    Example:
        >>> positions = [
        ...     {"ticker": "AAPL", "weight": 0.35, "value": 35000},
        ...     {"ticker": "GOOGL", "weight": 0.25, "value": 25000},
        ...     {"ticker": "MSFT", "weight": 0.40, "value": 40000}
        ... ]
        >>> fig = create_portfolio_pie_chart(positions)
        >>> fig.show()
    """
    if not positions:
        raise ValueError("No positions provided")

    # Extract data
    tickers = [p.get("ticker", "UNKNOWN") for p in positions]

    if value_type == "weight":
        values = [p.get("weight", 0) for p in positions]
        value_suffix = "%"
        value_multiplier = 100
    else:  # value
        values = [p.get("value", 0) for p in positions]
        value_suffix = ""
        value_multiplier = 1

    # Create figure
    fig = go.Figure()

    # Add pie chart
    fig.add_trace(go.Pie(
        labels=tickers,
        values=values,
        hole=hole_size,
        textinfo='label+percent' if show_percentages else 'label',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>' +
                      'Value: %{value:.2f}' + value_suffix + '<br>' +
                      'Percentage: %{percent}<br>' +
                      '<extra></extra>',
        marker=dict(
            line=dict(color='white', width=2)
        )
    ))

    # Update layout
    fig.update_layout(
        title=f"{portfolio_name} - Allocation",
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02
        ),
        height=500,
        annotations=[
            dict(
                text=portfolio_name,
                x=0.5,
                y=0.5,
                font_size=20,
                showarrow=False
            )
        ] if hole_size > 0 else None
    )

    fig = apply_quantlab_theme(fig)

    return fig


def create_position_pnl_chart(
    positions: List[Dict[str, Any]],
    portfolio_name: str = "Portfolio"
) -> go.Figure:
    """
    Create horizontal bar chart showing P&L for each position.

    Args:
        positions: List of position dicts with keys: ticker, pnl, pnl_percent
        portfolio_name: Name of portfolio for title

    Returns:
        Plotly figure object

    Example:
        >>> positions = [
        ...     {"ticker": "AAPL", "pnl": 5000, "pnl_percent": 0.15},
        ...     {"ticker": "GOOGL", "pnl": -2000, "pnl_percent": -0.08},
        ...     {"ticker": "MSFT", "pnl": 3000, "pnl_percent": 0.10}
        ... ]
        >>> fig = create_position_pnl_chart(positions)
        >>> fig.show()
    """
    if not positions:
        raise ValueError("No positions provided")

    # Extract and sort by P&L
    df = pd.DataFrame(positions)
    df = df.sort_values('pnl', ascending=True)

    tickers = df['ticker'].tolist()
    pnls = df['pnl'].tolist()
    pnl_percents = df.get('pnl_percent', [0] * len(df)).tolist()

    # Color bars based on profit/loss
    colors = [COLORS["success"] if pnl >= 0 else COLORS["danger"] for pnl in pnls]

    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=tickers,
        x=pnls,
        orientation='h',
        marker=dict(color=colors),
        text=[format_currency(pnl) for pnl in pnls],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>' +
                      'P&L: %{x:,.0f}<br>' +
                      'P&L %: %{customdata:.2f}%<br>' +
                      '<extra></extra>',
        customdata=[p * 100 for p in pnl_percents]
    ))

    # Add zero line
    fig.add_vline(x=0, line_dash="solid", line_color="black", line_width=1)

    # Update layout
    fig.update_layout(
        title=f"{portfolio_name} - Position P&L",
        xaxis_title="Profit / Loss ($)",
        yaxis_title="Ticker",
        showlegend=False,
        height=max(400, len(positions) * 40),
        hovermode='closest'
    )

    fig = apply_quantlab_theme(fig)

    return fig


def create_portfolio_summary_dashboard(
    portfolio_data: Dict[str, Any],
    positions: List[Dict[str, Any]]
) -> go.Figure:
    """
    Create comprehensive portfolio dashboard with multiple subplots.

    Args:
        portfolio_data: Dict with portfolio metrics (total_value, total_pnl, etc.)
        positions: List of position dicts

    Returns:
        Plotly figure with subplots

    Example:
        >>> portfolio_data = {
        ...     "name": "Tech Portfolio",
        ...     "total_value": 100000,
        ...     "total_pnl": 8000,
        ...     "total_pnl_percent": 0.08
        ... }
        >>> positions = [
        ...     {"ticker": "AAPL", "weight": 0.35, "value": 35000, "pnl": 5000},
        ...     {"ticker": "GOOGL", "weight": 0.25, "value": 25000, "pnl": -2000},
        ...     {"ticker": "MSFT", "weight": 0.40, "value": 40000, "pnl": 5000}
        ... ]
        >>> fig = create_portfolio_summary_dashboard(portfolio_data, positions)
        >>> fig.show()
    """
    if not positions:
        raise ValueError("No positions provided")

    # Create subplots: 2 rows, 2 columns
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Portfolio Allocation",
            "Position P&L",
            "Top Winners",
            "Top Losers"
        ),
        specs=[
            [{"type": "pie"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "bar"}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.15
    )

    # 1. Portfolio Allocation (Pie Chart)
    tickers = [p.get("ticker", "UNKNOWN") for p in positions]
    weights = [p.get("weight", 0) for p in positions]

    fig.add_trace(
        go.Pie(
            labels=tickers,
            values=weights,
            hole=0.3,
            textinfo='label+percent',
            showlegend=False
        ),
        row=1, col=1
    )

    # 2. Position P&L (Horizontal Bar)
    df = pd.DataFrame(positions)
    df = df.sort_values('pnl', ascending=True)

    pnls = df['pnl'].tolist()
    colors = [COLORS["success"] if pnl >= 0 else COLORS["danger"] for pnl in pnls]

    fig.add_trace(
        go.Bar(
            y=df['ticker'].tolist(),
            x=pnls,
            orientation='h',
            marker=dict(color=colors),
            showlegend=False
        ),
        row=1, col=2
    )

    # 3. Top Winners
    winners = df.nlargest(5, 'pnl')
    fig.add_trace(
        go.Bar(
            x=winners['ticker'].tolist(),
            y=winners['pnl'].tolist(),
            marker=dict(color=COLORS["success"]),
            showlegend=False
        ),
        row=2, col=1
    )

    # 4. Top Losers
    losers = df.nsmallest(5, 'pnl')
    fig.add_trace(
        go.Bar(
            x=losers['ticker'].tolist(),
            y=losers['pnl'].tolist(),
            marker=dict(color=COLORS["danger"]),
            showlegend=False
        ),
        row=2, col=2
    )

    # Update layout
    portfolio_name = portfolio_data.get("name", "Portfolio")
    total_value = portfolio_data.get("total_value", 0)
    total_pnl = portfolio_data.get("total_pnl", 0)
    total_pnl_pct = portfolio_data.get("total_pnl_percent", 0)

    fig.update_layout(
        title=f"{portfolio_name} Dashboard<br>" +
              f"<sub>Total Value: {format_currency(total_value)} | " +
              f"P&L: {format_currency(total_pnl)} ({format_percentage(total_pnl_pct)})</sub>",
        height=800,
        showlegend=False
    )

    # Update axes
    fig.update_xaxes(title_text="P&L ($)", row=1, col=2)
    fig.update_xaxes(title_text="Ticker", row=2, col=1)
    fig.update_xaxes(title_text="Ticker", row=2, col=2)
    fig.update_yaxes(title_text="P&L ($)", row=2, col=1)
    fig.update_yaxes(title_text="P&L ($)", row=2, col=2)

    fig = apply_quantlab_theme(fig)

    return fig
