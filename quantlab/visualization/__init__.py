"""
QuantLab Visualization Module

Interactive Plotly-based visualizations for:
- Portfolio analysis
- Price charts (candlesticks, OHLCV)
- Options payoff diagrams and Greeks
- Technical indicators
- Backtest performance

Usage:
    from quantlab.visualization import create_candlestick_chart
    fig = create_candlestick_chart(df, ticker="AAPL")
    fig.show()
"""

from quantlab.visualization.base import (
    apply_quantlab_theme,
    save_figure,
    create_base_figure,
    format_currency,
    format_percentage,
    add_range_selector,
    add_watermark,
    get_chart_config,
    COLORS,
    QUANTLAB_THEME,
)

from quantlab.visualization.portfolio_charts import (
    create_portfolio_pie_chart,
    create_position_pnl_chart,
    create_portfolio_summary_dashboard,
)

from quantlab.visualization.price_charts import (
    create_candlestick_chart,
    create_price_line_chart,
    create_multi_ticker_comparison,
)

from quantlab.visualization.options_charts import (
    create_payoff_diagram,
    create_greeks_heatmap,
    create_greeks_timeline,
    create_greeks_3d_surface,
    create_strategy_comparison,
)

from quantlab.visualization.technical_charts import (
    create_rsi_chart,
    create_macd_chart,
    create_bollinger_bands_chart,
    create_technical_dashboard,
)

from quantlab.visualization.backtest_charts import (
    create_cumulative_returns_chart,
    create_drawdown_chart,
    create_monthly_returns_heatmap,
    create_rolling_sharpe_chart,
    create_backtest_dashboard,
    load_backtest_report,
    calculate_backtest_metrics,
)

__all__ = [
    # Base utilities
    "apply_quantlab_theme",
    "save_figure",
    "create_base_figure",
    "format_currency",
    "format_percentage",
    "add_range_selector",
    "add_watermark",
    "get_chart_config",
    "COLORS",
    "QUANTLAB_THEME",
    # Portfolio charts
    "create_portfolio_pie_chart",
    "create_position_pnl_chart",
    "create_portfolio_summary_dashboard",
    # Price charts
    "create_candlestick_chart",
    "create_price_line_chart",
    "create_multi_ticker_comparison",
    # Options charts
    "create_payoff_diagram",
    "create_greeks_heatmap",
    "create_greeks_timeline",
    "create_greeks_3d_surface",
    "create_strategy_comparison",
    # Technical charts
    "create_rsi_chart",
    "create_macd_chart",
    "create_bollinger_bands_chart",
    "create_technical_dashboard",
    # Backtest charts
    "create_cumulative_returns_chart",
    "create_drawdown_chart",
    "create_monthly_returns_heatmap",
    "create_rolling_sharpe_chart",
    "create_backtest_dashboard",
    "load_backtest_report",
    "calculate_backtest_metrics",
]

__version__ = "0.1.0"
