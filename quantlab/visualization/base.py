"""
Base utilities and themes for Plotly visualizations.

This module provides common configuration, themes, and utility functions
used across all visualization modules.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import lru_cache
import plotly.graph_objects as go
import plotly.io as pio

from quantlab.data.api_clients import PolygonClient
from quantlab.utils.config import load_config


# ============================================================================
# THEME CONFIGURATION
# ============================================================================

QUANTLAB_THEME = {
    "layout": {
        "template": "plotly_white",
        "font": {
            "family": "Arial, sans-serif",
            "size": 12,
            "color": "#2c3e50"
        },
        "title": {
            "font": {
                "size": 18,
                "color": "#2c3e50"
            },
            "x": 0.5,
            "xanchor": "center"
        },
        "xaxis": {
            "showgrid": True,
            "gridcolor": "#ecf0f1",
            "linecolor": "#bdc3c7",
            "linewidth": 1
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": "#ecf0f1",
            "linecolor": "#bdc3c7",
            "linewidth": 1
        },
        "hovermode": "closest",
        "plot_bgcolor": "white",
        "paper_bgcolor": "white"
    }
}

# Color palette for consistent styling
COLORS = {
    "primary": "#3498db",      # Blue
    "success": "#2ecc71",      # Green
    "danger": "#e74c3c",       # Red
    "warning": "#f39c12",      # Orange
    "info": "#1abc9c",         # Teal
    "dark": "#34495e",         # Dark gray
    "light": "#ecf0f1",        # Light gray
    "bullish": "#2ecc71",      # Green (for price increases)
    "bearish": "#e74c3c",      # Red (for price decreases)
    "neutral": "#95a5a6"       # Gray
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def apply_quantlab_theme(fig: go.Figure) -> go.Figure:
    """
    Apply QuantLab custom theme to a Plotly figure.

    Args:
        fig: Plotly figure object

    Returns:
        Updated figure with theme applied
    """
    fig.update_layout(**QUANTLAB_THEME["layout"])
    return fig


def save_figure(
    fig: go.Figure,
    output_path: str,
    format: str = "html",
    include_plotlyjs: str = "cdn",
    **kwargs
) -> None:
    """
    Save Plotly figure to file.

    Args:
        fig: Plotly figure object
        output_path: Path to save file
        format: Output format ('html', 'png', 'jpg', 'pdf', 'svg')
        include_plotlyjs: How to include plotly.js ('cdn', 'inline', True, False)
        **kwargs: Additional arguments passed to write_html or write_image
    """
    if format == "html":
        fig.write_html(
            output_path,
            include_plotlyjs=include_plotlyjs,
            **kwargs
        )
    else:
        # Requires kaleido package for static image export
        fig.write_image(output_path, format=format, **kwargs)


def create_base_figure(
    title: Optional[str] = None,
    xaxis_title: Optional[str] = None,
    yaxis_title: Optional[str] = None,
    height: int = 600,
    width: Optional[int] = None,
    **kwargs
) -> go.Figure:
    """
    Create a base Plotly figure with QuantLab theme.

    Args:
        title: Chart title
        xaxis_title: X-axis label
        yaxis_title: Y-axis label
        height: Chart height in pixels
        width: Chart width in pixels (None for responsive)
        **kwargs: Additional layout arguments

    Returns:
        Configured Plotly figure
    """
    fig = go.Figure()

    # Apply theme
    fig = apply_quantlab_theme(fig)

    # Update layout with provided arguments
    layout_updates = {
        "height": height,
        "title": title,
        "xaxis_title": xaxis_title,
        "yaxis_title": yaxis_title,
    }

    if width is not None:
        layout_updates["width"] = width

    # Merge with additional kwargs
    layout_updates.update(kwargs)

    fig.update_layout(**layout_updates)

    return fig


def format_currency(value: float, decimals: int = 2) -> str:
    """
    Format number as currency string.

    Args:
        value: Numeric value
        decimals: Number of decimal places

    Returns:
        Formatted currency string
    """
    return f"${value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format number as percentage string.

    Args:
        value: Numeric value (0.15 for 15%)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def add_range_selector(
    fig: go.Figure,
    buttons: Optional[list] = None
) -> go.Figure:
    """
    Add date range selector to time-series charts.

    Args:
        fig: Plotly figure object
        buttons: List of button configs (default: standard time periods)

    Returns:
        Updated figure with range selector
    """
    if buttons is None:
        buttons = [
            dict(count=1, label="1M", step="month", stepmode="backward"),
            dict(count=3, label="3M", step="month", stepmode="backward"),
            dict(count=6, label="6M", step="month", stepmode="backward"),
            dict(count=1, label="YTD", step="year", stepmode="todate"),
            dict(count=1, label="1Y", step="year", stepmode="backward"),
            dict(step="all", label="ALL")
        ]

    fig.update_xaxes(
        rangeselector=dict(buttons=buttons),
        rangeslider=dict(visible=False)
    )

    return fig


@lru_cache(maxsize=1)
def _get_cached_market_holidays() -> List[str]:
    """
    Get market holidays from Polygon API with caching.

    Cached for the session to avoid repeated API calls.

    Returns:
        List of holiday dates in YYYY-MM-DD format
    """
    try:
        config = load_config()
        polygon_api_key = config.polygon_api_key

        if not polygon_api_key:
            # No API key available, use default weekends only
            return []

        client = PolygonClient(api_key=polygon_api_key)

        # Get holidays for current year through next year
        start_date = f"{datetime.now().year}-01-01"
        end_date = f"{datetime.now().year + 1}-12-31"

        holidays = client.get_market_holidays(start_date=start_date, end_date=end_date)
        return holidays

    except Exception as e:
        # If anything fails, return empty list to fall back to weekends only
        return []


def get_market_rangebreaks(intraday: bool = False) -> List[Dict[str, Any]]:
    """
    Get Plotly rangebreaks for non-trading days/hours.

    Uses Polygon API to fetch actual market holidays and combines them with
    weekend rangebreaks. For intraday charts, only weekends are hidden since
    non-market hours are filtered from the data itself.
    Results are cached to minimize API calls.

    Args:
        intraday: If True, only hide weekends (hours are filtered in data)
                 If False, hide weekends and market holidays

    Returns:
        List of rangebreak dictionaries for Plotly xaxis configuration

    Example:
        >>> # For daily charts
        >>> fig.update_layout(
        ...     xaxis=dict(rangebreaks=get_market_rangebreaks())
        ... )
        >>> # For intraday charts
        >>> fig.update_layout(
        ...     xaxis=dict(rangebreaks=get_market_rangebreaks(intraday=True))
        ... )
    """
    rangebreaks = []

    # Always hide weekends
    rangebreaks.append(dict(bounds=["sat", "mon"]))

    # For daily data, also hide market holidays
    if not intraday:
        # Get market holidays from Polygon API
        holidays = _get_cached_market_holidays()

        # Add each holiday as a rangebreak
        for holiday in holidays:
            rangebreaks.append(dict(values=[holiday]))

    return rangebreaks


def add_watermark(
    fig: go.Figure,
    text: str = "QuantLab",
    opacity: float = 0.1
) -> go.Figure:
    """
    Add watermark to chart.

    Args:
        fig: Plotly figure object
        text: Watermark text
        opacity: Text opacity (0-1)

    Returns:
        Updated figure with watermark
    """
    fig.add_annotation(
        text=text,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=60, color="gray"),
        opacity=opacity,
        xanchor="center",
        yanchor="middle"
    )

    return fig


# ============================================================================
# CHART CONFIGURATION PRESETS
# ============================================================================

CHART_CONFIGS = {
    "candlestick": {
        "increasing_line_color": COLORS["bullish"],
        "decreasing_line_color": COLORS["bearish"],
        "increasing_fillcolor": COLORS["bullish"],
        "decreasing_fillcolor": COLORS["bearish"],
    },
    "volume_bars": {
        "opacity": 0.7,
    },
    "payoff_diagram": {
        "line_width": 3,
        "profit_color": COLORS["success"],
        "loss_color": COLORS["danger"],
        "breakeven_color": COLORS["warning"],
    }
}


def get_chart_config(chart_type: str) -> Dict[str, Any]:
    """
    Get predefined configuration for chart type.

    Args:
        chart_type: Type of chart (e.g., 'candlestick', 'payoff_diagram')

    Returns:
        Configuration dictionary
    """
    return CHART_CONFIGS.get(chart_type, {})
