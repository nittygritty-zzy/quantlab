"""
Backtest Performance Visualization Charts

Professional Plotly-based visualizations for analyzing backtest results from Qlib.
Includes cumulative returns, drawdowns, monthly heatmaps, and risk metrics.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Dict, Any
from datetime import datetime

from .base import apply_quantlab_theme, COLORS, get_market_rangebreaks


def create_cumulative_returns_chart(
    report_df: pd.DataFrame,
    title: str = "Cumulative Returns",
    benchmark_name: str = "Benchmark",
    height: int = 600
) -> go.Figure:
    """
    Create cumulative returns chart comparing portfolio to benchmark.

    Args:
        report_df: Backtest report DataFrame with columns: ['return', 'bench', 'account']
        title: Chart title
        benchmark_name: Name of benchmark for legend
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    # Calculate cumulative returns
    portfolio_cumret = (1 + report_df['return']).cumprod() - 1
    bench_cumret = (1 + report_df['bench']).cumprod() - 1

    # Create figure
    fig = go.Figure()

    # Add portfolio line
    fig.add_trace(go.Scatter(
        x=report_df.index,
        y=portfolio_cumret * 100,  # Convert to percentage
        name='Portfolio',
        line=dict(color=COLORS["primary"], width=2.5),
        hovertemplate='<b>Portfolio</b><br>Date: %{x}<br>Return: %{y:.2f}%<extra></extra>'
    ))

    # Add benchmark line
    fig.add_trace(go.Scatter(
        x=report_df.index,
        y=bench_cumret * 100,
        name=benchmark_name,
        line=dict(color=COLORS["neutral"], width=2, dash='dash'),
        hovertemplate=f'<b>{benchmark_name}</b><br>Date: %{{x}}<br>Return: %{{y:.2f}}%<extra></extra>'
    ))

    # Add zero line
    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)

    # Update layout
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#2c3e50'), x=0.5, xanchor='center'),
        xaxis_title='Date',
        yaxis_title='Cumulative Return (%)',
        height=height,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='#ecf0f1',
            linecolor='#bdc3c7',
            linewidth=1,
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(label="ALL", step="all")
                ]
            ),
            rangebreaks=get_market_rangebreaks()  # Hide weekends and holidays
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#ecf0f1',
            linecolor='#bdc3c7',
            linewidth=1,
            ticksuffix='%'
        )
    )

    apply_quantlab_theme(fig)

    return fig


def create_drawdown_chart(
    report_df: pd.DataFrame,
    title: str = "Portfolio Drawdown",
    height: int = 500
) -> go.Figure:
    """
    Create underwater drawdown chart showing peak-to-trough losses.

    Args:
        report_df: Backtest report DataFrame with 'account' column
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    # Calculate drawdown
    portfolio_value = report_df['account']
    cumulative_max = portfolio_value.cummax()
    drawdown = (portfolio_value - cumulative_max) / cumulative_max * 100

    # Create figure
    fig = go.Figure()

    # Add drawdown area
    fig.add_trace(go.Scatter(
        x=report_df.index,
        y=drawdown,
        fill='tozeroy',
        fillcolor='rgba(231, 76, 60, 0.3)',  # Red with transparency
        line=dict(color=COLORS["danger"], width=2),
        name='Drawdown',
        hovertemplate='<b>Drawdown</b><br>Date: %{x}<br>Drawdown: %{y:.2f}%<extra></extra>'
    ))

    # Add zero line
    fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.5)

    # Mark maximum drawdown
    max_dd = drawdown.min()
    max_dd_date = drawdown.idxmin()

    fig.add_annotation(
        x=max_dd_date,
        y=max_dd,
        text=f"Max DD: {max_dd:.2f}%",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor=COLORS["danger"],
        ax=50,
        ay=-40,
        bgcolor="white",
        bordercolor=COLORS["danger"],
        borderwidth=2
    )

    # Update layout
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#2c3e50'), x=0.5, xanchor='center'),
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        height=height,
        hovermode='x unified',
        showlegend=False,
        xaxis=dict(
            showgrid=True,
            gridcolor='#ecf0f1',
            linecolor='#bdc3c7',
            linewidth=1,
            rangebreaks=get_market_rangebreaks()  # Hide weekends and holidays
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#ecf0f1',
            linecolor='#bdc3c7',
            linewidth=1,
            ticksuffix='%'
        )
    )

    apply_quantlab_theme(fig)

    return fig


def create_monthly_returns_heatmap(
    report_df: pd.DataFrame,
    title: str = "Monthly Returns Heatmap",
    height: int = 500
) -> go.Figure:
    """
    Create calendar heatmap showing monthly returns.

    Args:
        report_df: Backtest report DataFrame with 'return' column
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    # Calculate monthly returns
    monthly_returns = (1 + report_df['return']).resample('ME').prod() - 1

    # Create pivot table for heatmap
    monthly_returns_pct = monthly_returns * 100
    monthly_returns_pct.index = pd.to_datetime(monthly_returns_pct.index)

    # Create year and month columns
    years = monthly_returns_pct.index.year.unique()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Create matrix
    matrix = []
    for year in sorted(years):
        year_data = []
        for month in range(1, 13):
            try:
                val = monthly_returns_pct[
                    (monthly_returns_pct.index.year == year) &
                    (monthly_returns_pct.index.month == month)
                ].iloc[0]
                year_data.append(val)
            except IndexError:
                year_data.append(np.nan)
        matrix.append(year_data)

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=months,
        y=[str(y) for y in sorted(years)],
        colorscale=[
            [0, '#d73027'],      # Red for losses
            [0.5, '#fee08b'],    # Yellow for neutral
            [1, '#1a9850']       # Green for gains
        ],
        zmid=0,
        text=[[f"{val:.1f}%" if not np.isnan(val) else "" for val in row] for row in matrix],
        texttemplate='%{text}',
        textfont=dict(size=10),
        hovertemplate='<b>%{y} %{x}</b><br>Return: %{z:.2f}%<extra></extra>',
        colorbar=dict(
            title=dict(text="Return (%)"),
            tickmode="linear",
            tick0=-20,
            dtick=10
        )
    ))

    # Update layout
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#2c3e50'), x=0.5, xanchor='center'),
        xaxis_title='',
        yaxis_title='',
        height=height,
        xaxis=dict(side='top'),
    )

    apply_quantlab_theme(fig)

    return fig


def create_rolling_sharpe_chart(
    report_df: pd.DataFrame,
    window: int = 60,
    risk_free_rate: float = 0.02,
    title: str = "Rolling Sharpe Ratio",
    height: int = 500
) -> go.Figure:
    """
    Create rolling Sharpe ratio chart showing risk-adjusted returns over time.

    Args:
        report_df: Backtest report DataFrame with 'return' column
        window: Rolling window size in days (default: 60)
        risk_free_rate: Annual risk-free rate (default: 0.02 = 2%)
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    # Calculate rolling Sharpe ratio
    daily_returns = report_df['return']
    daily_rf = risk_free_rate / 252  # Assuming 252 trading days

    excess_returns = daily_returns - daily_rf
    rolling_mean = excess_returns.rolling(window=window).mean()
    rolling_std = excess_returns.rolling(window=window).std()

    # Annualize
    rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252)

    # Create figure
    fig = go.Figure()

    # Add Sharpe ratio line
    fig.add_trace(go.Scatter(
        x=report_df.index,
        y=rolling_sharpe,
        name=f'{window}-Day Rolling Sharpe',
        line=dict(color="#9b59b6", width=2.5),
        hovertemplate='<b>Sharpe Ratio</b><br>Date: %{x}<br>Sharpe: %{y:.2f}<extra></extra>'
    ))

    # Add reference lines
    fig.add_hline(y=1, line_dash="dash", line_color="green", opacity=0.5,
                  annotation_text="Good (1.0)", annotation_position="right")
    fig.add_hline(y=2, line_dash="dash", line_color="darkgreen", opacity=0.5,
                  annotation_text="Excellent (2.0)", annotation_position="right")
    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)

    # Update layout
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#2c3e50'), x=0.5, xanchor='center'),
        xaxis_title='Date',
        yaxis_title='Sharpe Ratio',
        height=height,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='#ecf0f1',
            linecolor='#bdc3c7',
            linewidth=1,
            rangebreaks=get_market_rangebreaks()  # Hide weekends and holidays
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#ecf0f1',
            linecolor='#bdc3c7',
            linewidth=1
        )
    )

    apply_quantlab_theme(fig)

    return fig


def create_backtest_dashboard(
    report_df: pd.DataFrame,
    strategy_name: str = "Strategy",
    benchmark_name: str = "Benchmark",
    height: int = 1200
) -> go.Figure:
    """
    Create comprehensive backtest dashboard with multiple panels.

    Combines:
    - Cumulative returns (40% height)
    - Drawdown (30% height)
    - Rolling Sharpe ratio (30% height)

    Args:
        report_df: Backtest report DataFrame
        strategy_name: Name of strategy for title
        benchmark_name: Name of benchmark
        height: Total chart height in pixels

    Returns:
        Plotly Figure object
    """
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            'Cumulative Returns',
            'Drawdown',
            'Rolling Sharpe Ratio (60-Day)'
        ),
        row_heights=[0.4, 0.3, 0.3],
        vertical_spacing=0.08,
        shared_xaxes=True
    )

    # Panel 1: Cumulative Returns
    portfolio_cumret = (1 + report_df['return']).cumprod() - 1
    bench_cumret = (1 + report_df['bench']).cumprod() - 1

    fig.add_trace(go.Scatter(
        x=report_df.index,
        y=portfolio_cumret * 100,
        name='Portfolio',
        line=dict(color=COLORS["primary"], width=2.5),
        showlegend=True
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=report_df.index,
        y=bench_cumret * 100,
        name=benchmark_name,
        line=dict(color=COLORS["neutral"], width=2, dash='dash'),
        showlegend=True
    ), row=1, col=1)

    # Panel 2: Drawdown
    portfolio_value = report_df['account']
    cumulative_max = portfolio_value.cummax()
    drawdown = (portfolio_value - cumulative_max) / cumulative_max * 100

    fig.add_trace(go.Scatter(
        x=report_df.index,
        y=drawdown,
        fill='tozeroy',
        fillcolor='rgba(231, 76, 60, 0.3)',
        line=dict(color=COLORS["danger"], width=2),
        name='Drawdown',
        showlegend=False
    ), row=2, col=1)

    # Panel 3: Rolling Sharpe
    daily_returns = report_df['return']
    excess_returns = daily_returns - 0.02/252
    rolling_sharpe = (excess_returns.rolling(60).mean() / excess_returns.rolling(60).std()) * np.sqrt(252)

    fig.add_trace(go.Scatter(
        x=report_df.index,
        y=rolling_sharpe,
        name='Rolling Sharpe',
        line=dict(color="#9b59b6", width=2.5),
        showlegend=False
    ), row=3, col=1)

    # Add reference line for Sharpe = 1
    fig.add_hline(y=1, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)

    # Update axes
    fig.update_yaxes(title_text="Return (%)", row=1, col=1, ticksuffix='%')
    fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1, ticksuffix='%')
    fig.update_yaxes(title_text="Sharpe Ratio", row=3, col=1)
    fig.update_xaxes(
        title_text="Date",
        row=3, col=1,
        rangebreaks=get_market_rangebreaks()  # Hide weekends and holidays
    )

    # Update layout
    fig.update_layout(
        title=dict(
            text=f"{strategy_name} - Backtest Performance Dashboard",
            font=dict(size=20, color='#2c3e50'),
            x=0.5,
            xanchor='center'
        ),
        height=height,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.05,
            xanchor="right",
            x=1
        )
    )

    apply_quantlab_theme(fig)

    return fig


def load_backtest_report(mlflow_run_path: str) -> pd.DataFrame:
    """
    Load backtest report from MLflow run artifacts.

    Args:
        mlflow_run_path: Path to MLflow run directory
                        Example: 'results/mlruns/489214785307856385/2b374fe2956c4161a1bd2dcef7299bd2'

    Returns:
        DataFrame with backtest report data
    """
    import pickle
    from pathlib import Path

    report_path = Path(mlflow_run_path) / 'artifacts' / 'portfolio_analysis' / 'report_normal_1day.pkl'

    if not report_path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")

    with open(report_path, 'rb') as f:
        report_df = pickle.load(f)

    return report_df


def calculate_backtest_metrics(report_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate key backtest performance metrics.

    Args:
        report_df: Backtest report DataFrame

    Returns:
        Dictionary with performance metrics
    """
    # Total returns
    total_return = (1 + report_df['return']).prod() - 1
    bench_return = (1 + report_df['bench']).prod() - 1

    # Annualized returns (assuming daily data)
    n_days = len(report_df)
    n_years = n_days / 252
    annual_return = (1 + total_return) ** (1 / n_years) - 1

    # Volatility
    annual_vol = report_df['return'].std() * np.sqrt(252)

    # Sharpe ratio
    sharpe = (annual_return - 0.02) / annual_vol

    # Max drawdown
    portfolio_value = report_df['account']
    cumulative_max = portfolio_value.cummax()
    drawdown = (portfolio_value - cumulative_max) / cumulative_max
    max_drawdown = drawdown.min()

    # Win rate
    win_rate = (report_df['return'] > 0).mean()

    return {
        'total_return': total_return * 100,
        'annual_return': annual_return * 100,
        'bench_return': bench_return * 100,
        'annual_volatility': annual_vol * 100,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown * 100,
        'win_rate': win_rate * 100,
        'n_days': n_days
    }
