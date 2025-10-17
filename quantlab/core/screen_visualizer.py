"""
Screen Visualization Module

Provides interactive visualizations for screener features:
- Screen backtest results (cumulative returns, drawdown, metrics)
- Screen comparison results (Venn diagrams, consensus picks)
- Screening results (sector distribution, metric histograms)
- Watch mode alerts (timeline, frequency analysis)

All visualizations use plotly for interactivity and export to HTML.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

logger = logging.getLogger(__name__)


class ScreenBacktestVisualizer:
    """Visualize screen backtest results"""

    def __init__(self, backtest_data: Dict[str, Any]):
        """
        Initialize with backtest results JSON

        Args:
            backtest_data: JSON output from `quantlab screen backtest`
        """
        self.data = backtest_data
        self.results = backtest_data.get('results', {})
        self.period_results = pd.DataFrame(backtest_data.get('period_results', []))

    def create_cumulative_returns_chart(self) -> go.Figure:
        """Create cumulative returns chart comparing strategy vs benchmark"""
        if self.period_results.empty:
            return self._create_empty_figure("No period results available")

        # Calculate cumulative returns
        df = self.period_results.copy()
        try:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            # Drop rows with invalid dates
            df = df.dropna(subset=['date'])
            if df.empty:
                return self._create_empty_figure("No valid dates in period results")
        except Exception:
            return self._create_empty_figure("Invalid date format in period results")
        df['cumulative_return'] = (1 + df['avg_return'] / 100).cumprod() - 1

        # Create benchmark cumulative returns if available
        has_benchmark = 'benchmark_return' in df.columns
        if has_benchmark:
            df['benchmark_cumulative'] = (1 + df['benchmark_return'] / 100).cumprod() - 1

        fig = go.Figure()

        # Strategy returns
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['cumulative_return'] * 100,
            mode='lines',
            name='Strategy',
            line=dict(color='#2E86DE', width=2),
            hovertemplate='%{x|%Y-%m-%d}<br>Return: %{y:.2f}%<extra></extra>'
        ))

        # Benchmark returns
        if has_benchmark:
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['benchmark_cumulative'] * 100,
                mode='lines',
                name='Benchmark (SPY)',
                line=dict(color='#95A5A6', width=2, dash='dash'),
                hovertemplate='%{x|%Y-%m-%d}<br>Return: %{y:.2f}%<extra></extra>'
            ))

        fig.update_layout(
            title='Cumulative Returns: Strategy vs Benchmark',
            xaxis_title='Date',
            yaxis_title='Cumulative Return (%)',
            hovermode='x unified',
            template='plotly_white',
            height=500
        )

        return fig

    def create_drawdown_chart(self) -> go.Figure:
        """Create drawdown chart showing peak-to-trough declines"""
        if self.period_results.empty:
            return self._create_empty_figure("No period results available")

        df = self.period_results.copy()
        try:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
            if df.empty:
                return self._create_empty_figure("No valid dates in period results")
        except Exception:
            return self._create_empty_figure("Invalid date format in period results")
        df['cumulative_return'] = (1 + df['avg_return'] / 100).cumprod()

        # Calculate running maximum
        df['running_max'] = df['cumulative_return'].expanding().max()

        # Calculate drawdown
        df['drawdown'] = (df['cumulative_return'] / df['running_max'] - 1) * 100

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['drawdown'],
            mode='lines',
            name='Drawdown',
            fill='tozeroy',
            line=dict(color='#E74C3C', width=1),
            fillcolor='rgba(231, 76, 60, 0.2)',
            hovertemplate='%{x|%Y-%m-%d}<br>Drawdown: %{y:.2f}%<extra></extra>'
        ))

        # Add max drawdown line
        max_dd = self.results.get('max_drawdown', 0)
        fig.add_hline(
            y=max_dd,
            line_dash="dash",
            line_color="darkred",
            annotation_text=f"Max Drawdown: {max_dd:.2f}%",
            annotation_position="right"
        )

        fig.update_layout(
            title='Drawdown Over Time',
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )

        return fig

    def create_rolling_sharpe_chart(self) -> go.Figure:
        """Create rolling Sharpe ratio chart (30-day window)"""
        if self.period_results.empty or len(self.period_results) < 30:
            return self._create_empty_figure("Insufficient data for rolling Sharpe ratio")

        df = self.period_results.copy()
        try:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
            if df.empty or len(df) < 30:
                return self._create_empty_figure("Insufficient valid data for rolling Sharpe ratio")
        except Exception:
            return self._create_empty_figure("Invalid date format in period results")

        # Calculate rolling Sharpe (30-period window)
        window = min(30, len(df) // 3)  # Adaptive window
        df['rolling_sharpe'] = (
            df['avg_return'].rolling(window).mean() /
            df['avg_return'].rolling(window).std()
        ) * np.sqrt(252 / window)  # Annualize

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['rolling_sharpe'],
            mode='lines',
            name='Rolling Sharpe',
            line=dict(color='#9B59B6', width=2),
            hovertemplate='%{x|%Y-%m-%d}<br>Sharpe: %{y:.2f}<extra></extra>'
        ))

        # Add Sharpe = 0 line
        fig.add_hline(y=0, line_dash="dash", line_color="gray")

        # Add overall Sharpe line
        overall_sharpe = self.results.get('sharpe_ratio', 0)
        fig.add_hline(
            y=overall_sharpe,
            line_dash="dot",
            line_color="green",
            annotation_text=f"Overall: {overall_sharpe:.2f}",
            annotation_position="right"
        )

        fig.update_layout(
            title=f'Rolling Sharpe Ratio ({window}-Period Window)',
            xaxis_title='Date',
            yaxis_title='Sharpe Ratio',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )

        return fig

    def create_metrics_dashboard(self) -> go.Figure:
        """Create performance metrics dashboard with key statistics"""
        metrics = [
            ('Total Return', self.results.get('total_return', 0), '%'),
            ('Annualized Return', self.results.get('annualized_return', 0), '%'),
            ('Sharpe Ratio', self.results.get('sharpe_ratio', 0), ''),
            ('Max Drawdown', self.results.get('max_drawdown', 0), '%'),
            ('Win Rate', self.results.get('win_rate', 0), '%'),
            ('Alpha', self.results.get('alpha', 0), '%'),
        ]

        # Create table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['<b>Metric</b>', '<b>Value</b>'],
                fill_color='#2C3E50',
                font=dict(color='white', size=14),
                align='left'
            ),
            cells=dict(
                values=[
                    [m[0] for m in metrics],
                    [f"{m[1]:.2f}{m[2]}" for m in metrics]
                ],
                fill_color=[['#ECF0F1', '#D5DBDB'] * 3],
                font=dict(size=13),
                align='left',
                height=35
            )
        )])

        fig.update_layout(
            title='Performance Metrics Summary',
            height=350,
            margin=dict(l=20, r=20, t=50, b=20)
        )

        return fig

    def create_returns_distribution(self) -> go.Figure:
        """Create histogram of period returns"""
        if self.period_results.empty:
            return self._create_empty_figure("No period results available")

        returns = self.period_results['avg_return'].values

        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=returns,
            nbinsx=30,
            name='Returns',
            marker_color='#3498DB',
            opacity=0.7
        ))

        # Add mean line
        mean_return = returns.mean()
        fig.add_vline(
            x=mean_return,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mean: {mean_return:.2f}%",
            annotation_position="top"
        )

        fig.update_layout(
            title='Distribution of Period Returns',
            xaxis_title='Return (%)',
            yaxis_title='Frequency',
            template='plotly_white',
            height=400
        )

        return fig

    def create_win_rate_chart(self) -> go.Figure:
        """Create bar chart showing wins vs losses"""
        if self.period_results.empty:
            return self._create_empty_figure("No period results available")

        wins = (self.period_results['avg_return'] > 0).sum()
        losses = (self.period_results['avg_return'] <= 0).sum()

        fig = go.Figure(data=[
            go.Bar(
                x=['Winning Periods', 'Losing Periods'],
                y=[wins, losses],
                marker_color=['#27AE60', '#E74C3C'],
                text=[wins, losses],
                textposition='auto',
            )
        ])

        win_rate = self.results.get('win_rate', 0)

        fig.update_layout(
            title=f'Win Rate: {win_rate:.1f}%',
            yaxis_title='Number of Periods',
            template='plotly_white',
            height=400
        )

        return fig

    def create_full_report(self) -> go.Figure:
        """Create comprehensive multi-panel report"""
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Cumulative Returns',
                'Performance Metrics',
                'Drawdown',
                'Returns Distribution',
                'Rolling Sharpe Ratio',
                'Win/Loss Analysis'
            ),
            specs=[
                [{"type": "scatter"}, {"type": "table"}],
                [{"type": "scatter"}, {"type": "histogram"}],
                [{"type": "scatter"}, {"type": "bar"}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )

        # This is complex - for now, we'll generate individual charts
        # and let the CLI combine them or use create_html_report()
        return fig

    def create_html_report(self, output_path: str) -> None:
        """Create comprehensive HTML report with all charts"""
        charts = [
            ('cumulative_returns', self.create_cumulative_returns_chart()),
            ('metrics', self.create_metrics_dashboard()),
            ('drawdown', self.create_drawdown_chart()),
            ('rolling_sharpe', self.create_rolling_sharpe_chart()),
            ('returns_dist', self.create_returns_distribution()),
            ('win_rate', self.create_win_rate_chart()),
        ]

        # Generate HTML with all charts
        html_parts = [
            '<html><head><title>Screen Backtest Report</title>',
            '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>',
            '<style>',
            'body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }',
            '.header { background: #2C3E50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }',
            '.chart-container { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
            '</style></head><body>',
            '<div class="header">',
            '<h1>Screen Backtest Report</h1>',
            f'<p>Strategy: {self.data.get("criteria", {}).get("description", "Custom Screen")}</p>',
            f'<p>Period: {self.results.get("start_date")} to {self.results.get("end_date")}</p>',
            '</div>'
        ]

        for chart_id, fig in charts:
            html_parts.append(f'<div class="chart-container" id="{chart_id}"></div>')
            html_parts.append(f'<script>{fig.to_html(include_plotlyjs=False, div_id=chart_id)}</script>')

        html_parts.append('</body></html>')

        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(html_parts))

        logger.info(f"Backtest report saved to {output_path}")

    @staticmethod
    def _create_empty_figure(message: str) -> go.Figure:
        """Create empty figure with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            template='plotly_white',
            height=400
        )
        return fig


class ScreenComparisonVisualizer:
    """Visualize screen comparison results"""

    def __init__(self, comparison_data: Dict[str, Any]):
        """
        Initialize with comparison results JSON

        Args:
            comparison_data: JSON output from `quantlab screen compare-multi`
        """
        self.data = comparison_data
        self.screen_names = comparison_data.get('screen_names', [])
        self.individual_results = comparison_data.get('individual_results', {})
        self.overlap_analysis = pd.DataFrame(comparison_data.get('overlap_analysis', []))
        self.consensus_picks = pd.DataFrame(comparison_data.get('consensus_picks', []))
        self.comparison_metrics = pd.DataFrame(comparison_data.get('comparison_metrics', []))

    def create_overlap_venn(self) -> go.Figure:
        """Create Venn diagram showing screen overlaps (2-3 screens only)"""
        # Note: plotly doesn't have native Venn diagrams
        # For now, create a bar chart showing overlap counts
        # TODO: Consider matplotlib-venn for true Venn diagrams

        if self.overlap_analysis.empty:
            return self._create_empty_figure("No overlap data available")

        fig = go.Figure()

        # Create overlap summary
        overlap_summary = []
        for _, row in self.overlap_analysis.iterrows():
            screens_involved = row.get('screens', '')
            count = row.get('ticker_count', 0)
            overlap_summary.append((screens_involved, count))

        if overlap_summary:
            labels, values = zip(*overlap_summary)

            fig.add_trace(go.Bar(
                x=list(labels),
                y=list(values),
                marker_color='#3498DB',
                text=list(values),
                textposition='auto'
            ))

        fig.update_layout(
            title='Screen Overlap Analysis',
            xaxis_title='Screen Combination',
            yaxis_title='Number of Stocks',
            template='plotly_white',
            height=500
        )

        return fig

    def create_consensus_picks_table(self) -> go.Figure:
        """Create highlighted table of consensus picks"""
        if self.consensus_picks.empty:
            return self._create_empty_figure("No consensus picks found")

        # Get top 20 consensus picks
        df = self.consensus_picks.head(20)

        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['<b>Ticker</b>', '<b>Company</b>', '<b>Screens</b>', '<b>Score</b>'],
                fill_color='#2C3E50',
                font=dict(color='white', size=13),
                align='left'
            ),
            cells=dict(
                values=[
                    df.get('ticker', []),
                    df.get('company_name', []),
                    df.get('screen_count', []),
                    df.get('consensus_score', []),
                ],
                fill_color='#ECF0F1',
                font=dict(size=12),
                align='left',
                height=30
            )
        )])

        fig.update_layout(
            title=f'Top {len(df)} Consensus Picks (Found in Multiple Screens)',
            height=600,
            margin=dict(l=20, r=20, t=50, b=20)
        )

        return fig

    def create_sector_comparison(self) -> go.Figure:
        """Create grouped bar chart comparing sector distribution"""
        # Extract sector data from individual results
        sector_data = {}

        for screen_name, results_dict in self.individual_results.items():
            results_df = pd.DataFrame(results_dict.get('results', []))
            if not results_df.empty and 'sector' in results_df.columns:
                sector_counts = results_df['sector'].value_counts()
                sector_data[screen_name] = sector_counts

        if not sector_data:
            return self._create_empty_figure("No sector data available")

        # Create grouped bar chart
        fig = go.Figure()

        all_sectors = set()
        for counts in sector_data.values():
            all_sectors.update(counts.index)

        for screen_name, sector_counts in sector_data.items():
            fig.add_trace(go.Bar(
                name=screen_name,
                x=list(all_sectors),
                y=[sector_counts.get(s, 0) for s in all_sectors]
            ))

        fig.update_layout(
            title='Sector Distribution Across Screens',
            xaxis_title='Sector',
            yaxis_title='Number of Stocks',
            barmode='group',
            template='plotly_white',
            height=500
        )

        return fig

    def create_screen_size_comparison(self) -> go.Figure:
        """Create bar chart comparing number of stocks in each screen"""
        if self.comparison_metrics.empty:
            return self._create_empty_figure("No comparison metrics available")

        fig = go.Figure(data=[
            go.Bar(
                x=self.comparison_metrics['screen_name'],
                y=self.comparison_metrics['result_count'],
                marker_color='#9B59B6',
                text=self.comparison_metrics['result_count'],
                textposition='auto'
            )
        ])

        fig.update_layout(
            title='Number of Stocks per Screen',
            xaxis_title='Screen',
            yaxis_title='Number of Stocks',
            template='plotly_white',
            height=400
        )

        return fig

    def create_html_report(self, output_path: str) -> None:
        """Create comprehensive HTML report"""
        charts = [
            ('screen_sizes', self.create_screen_size_comparison()),
            ('overlap', self.create_overlap_venn()),
            ('sectors', self.create_sector_comparison()),
            ('consensus', self.create_consensus_picks_table()),
        ]

        html_parts = [
            '<html><head><title>Screen Comparison Report</title>',
            '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>',
            '<style>',
            'body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }',
            '.header { background: #8E44AD; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }',
            '.chart-container { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
            '</style></head><body>',
            '<div class="header">',
            '<h1>Screen Comparison Report</h1>',
            f'<p>Screens Compared: {", ".join(self.screen_names)}</p>',
            f'<p>Consensus Picks: {len(self.consensus_picks)}</p>',
            '</div>'
        ]

        for chart_id, fig in charts:
            html_parts.append(f'<div class="chart-container" id="{chart_id}"></div>')
            html_parts.append(f'<script>{fig.to_html(include_plotlyjs=False, div_id=chart_id)}</script>')

        html_parts.append('</body></html>')

        with open(output_path, 'w') as f:
            f.write('\n'.join(html_parts))

        logger.info(f"Comparison report saved to {output_path}")

    @staticmethod
    def _create_empty_figure(message: str) -> go.Figure:
        """Create empty figure with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            template='plotly_white'
        )
        return fig


class ScreenResultsVisualizer:
    """Visualize screening results"""

    def __init__(self, screening_data: Dict[str, Any]):
        """
        Initialize with screening results JSON

        Args:
            screening_data: JSON output from `quantlab screen run`
        """
        self.data = screening_data
        self.results = pd.DataFrame(screening_data.get('results', []))
        self.criteria = screening_data.get('criteria', {})

    def create_sector_pie_chart(self) -> go.Figure:
        """Create pie chart of sector distribution"""
        if self.results.empty or 'sector' not in self.results.columns:
            return self._create_empty_figure("No sector data available")

        sector_counts = self.results['sector'].value_counts()

        fig = go.Figure(data=[go.Pie(
            labels=sector_counts.index,
            values=sector_counts.values,
            hole=0.3,
            marker=dict(colors=px.colors.qualitative.Set3)
        )])

        fig.update_layout(
            title='Sector Distribution',
            template='plotly_white',
            height=500
        )

        return fig

    def create_industry_bar_chart(self) -> go.Figure:
        """Create bar chart of top industries"""
        if self.results.empty or 'industry' not in self.results.columns:
            return self._create_empty_figure("No industry data available")

        industry_counts = self.results['industry'].value_counts().head(15)

        fig = go.Figure(data=[
            go.Bar(
                x=industry_counts.values,
                y=industry_counts.index,
                orientation='h',
                marker_color='#3498DB'
            )
        ])

        fig.update_layout(
            title='Top 15 Industries',
            xaxis_title='Number of Stocks',
            yaxis_title='Industry',
            template='plotly_white',
            height=600
        )

        return fig

    def create_metric_histograms(self) -> go.Figure:
        """Create histograms for key metrics"""
        if self.results.empty:
            return self._create_empty_figure("No results available")

        # Select numeric columns
        numeric_cols = self.results.select_dtypes(include=[np.number]).columns
        metric_cols = [c for c in numeric_cols if c in ['pe_ratio', 'rsi', 'volume', 'price', 'market_cap']]

        if not metric_cols:
            return self._create_empty_figure("No numeric metrics available")

        # Create subplots
        n_metrics = len(metric_cols)
        rows = (n_metrics + 1) // 2

        fig = make_subplots(
            rows=rows, cols=2,
            subplot_titles=metric_cols,
            vertical_spacing=0.15
        )

        for idx, col in enumerate(metric_cols):
            row = idx // 2 + 1
            col_pos = idx % 2 + 1

            fig.add_trace(
                go.Histogram(x=self.results[col], name=col, showlegend=False),
                row=row, col=col_pos
            )

        fig.update_layout(
            title='Distribution of Key Metrics',
            template='plotly_white',
            height=400 * rows
        )

        return fig

    def create_price_volume_scatter(self) -> go.Figure:
        """Create scatter plot of price vs volume"""
        if self.results.empty or 'price' not in self.results.columns or 'volume' not in self.results.columns:
            return self._create_empty_figure("Price/volume data not available")

        fig = go.Figure(data=[
            go.Scatter(
                x=self.results['volume'],
                y=self.results['price'],
                mode='markers',
                text=self.results.get('ticker', ''),
                marker=dict(
                    size=8,
                    color=self.results.get('rsi', 50),
                    colorscale='RdYlGn_r',
                    showscale=True,
                    colorbar=dict(title="RSI")
                ),
                hovertemplate='<b>%{text}</b><br>Volume: %{x:,.0f}<br>Price: $%{y:.2f}<extra></extra>'
            )
        ])

        fig.update_layout(
            title='Price vs Volume',
            xaxis_title='Volume',
            yaxis_title='Price ($)',
            xaxis_type='log',
            template='plotly_white',
            height=500
        )

        return fig

    def create_html_report(self, output_path: str) -> None:
        """Create comprehensive HTML report"""
        charts = [
            ('sector', self.create_sector_pie_chart()),
            ('industry', self.create_industry_bar_chart()),
            ('price_volume', self.create_price_volume_scatter()),
            ('metrics', self.create_metric_histograms()),
        ]

        html_parts = [
            '<html><head><title>Screening Results Report</title>',
            '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>',
            '<style>',
            'body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }',
            '.header { background: #16A085; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }',
            '.chart-container { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
            '</style></head><body>',
            '<div class="header">',
            '<h1>Screening Results Report</h1>',
            f'<p>Total Stocks Found: {len(self.results)}</p>',
            '</div>'
        ]

        for chart_id, fig in charts:
            html_parts.append(f'<div class="chart-container" id="{chart_id}"></div>')
            html_parts.append(f'<script>{fig.to_html(include_plotlyjs=False, div_id=chart_id)}</script>')

        html_parts.append('</body></html>')

        with open(output_path, 'w') as f:
            f.write('\n'.join(html_parts))

        logger.info(f"Screening results report saved to {output_path}")

    @staticmethod
    def _create_empty_figure(message: str) -> go.Figure:
        """Create empty figure with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            template='plotly_white'
        )
        return fig


class ScreenAlertsVisualizer:
    """Visualize watch mode alerts"""

    def __init__(self, alerts_data: Dict[str, Any]):
        """
        Initialize with alerts JSON

        Args:
            alerts_data: JSON export from watch mode alerts
        """
        self.data = alerts_data
        self.alerts = pd.DataFrame(alerts_data.get('alerts', []))

        if not self.alerts.empty and 'alert_time' in self.alerts.columns:
            self.alerts['alert_time'] = pd.to_datetime(self.alerts['alert_time'])

    def create_alert_timeline(self) -> go.Figure:
        """Create timeline chart of alerts"""
        if self.alerts.empty:
            return self._create_empty_figure("No alerts available")

        fig = go.Figure()

        # Group by alert type
        for alert_type in self.alerts['alert_type'].unique():
            type_alerts = self.alerts[self.alerts['alert_type'] == alert_type]

            fig.add_trace(go.Scatter(
                x=type_alerts['alert_time'],
                y=[alert_type] * len(type_alerts),
                mode='markers',
                name=alert_type,
                text=type_alerts['ticker'],
                marker=dict(size=10),
                hovertemplate='%{text}<br>%{x|%Y-%m-%d %H:%M}<extra></extra>'
            ))

        fig.update_layout(
            title='Alert Timeline',
            xaxis_title='Time',
            yaxis_title='Alert Type',
            template='plotly_white',
            height=500,
            hovermode='closest'
        )

        return fig

    def create_alert_type_breakdown(self) -> go.Figure:
        """Create pie chart of alert types"""
        if self.alerts.empty:
            return self._create_empty_figure("No alerts available")

        type_counts = self.alerts['alert_type'].value_counts()

        fig = go.Figure(data=[go.Pie(
            labels=type_counts.index,
            values=type_counts.values,
            hole=0.3
        )])

        fig.update_layout(
            title='Alert Type Distribution',
            template='plotly_white',
            height=400
        )

        return fig

    def create_ticker_frequency_heatmap(self) -> go.Figure:
        """Create heatmap of which tickers alert most"""
        if self.alerts.empty:
            return self._create_empty_figure("No alerts available")

        # Get top 20 most alerting tickers
        ticker_counts = self.alerts['ticker'].value_counts().head(20)

        fig = go.Figure(data=[
            go.Bar(
                x=ticker_counts.index,
                y=ticker_counts.values,
                marker_color='#E74C3C',
                text=ticker_counts.values,
                textposition='auto'
            )
        ])

        fig.update_layout(
            title='Top 20 Most Active Tickers',
            xaxis_title='Ticker',
            yaxis_title='Alert Count',
            template='plotly_white',
            height=500
        )

        return fig

    def create_daily_alert_count(self) -> go.Figure:
        """Create line chart of alerts per day"""
        if self.alerts.empty:
            return self._create_empty_figure("No alerts available")

        # Group by date
        self.alerts['date'] = self.alerts['alert_time'].dt.date
        daily_counts = self.alerts.groupby('date').size()

        fig = go.Figure(data=[
            go.Scatter(
                x=daily_counts.index,
                y=daily_counts.values,
                mode='lines+markers',
                marker=dict(size=8),
                line=dict(width=2, color='#E67E22')
            )
        ])

        fig.update_layout(
            title='Alerts Per Day',
            xaxis_title='Date',
            yaxis_title='Number of Alerts',
            template='plotly_white',
            height=400
        )

        return fig

    def create_html_report(self, output_path: str) -> None:
        """Create comprehensive HTML report"""
        charts = [
            ('timeline', self.create_alert_timeline()),
            ('type_breakdown', self.create_alert_type_breakdown()),
            ('ticker_frequency', self.create_ticker_frequency_heatmap()),
            ('daily_counts', self.create_daily_alert_count()),
        ]

        html_parts = [
            '<html><head><title>Watch Mode Alerts Report</title>',
            '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>',
            '<style>',
            'body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }',
            '.header { background: #C0392B; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }',
            '.chart-container { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
            '</style></head><body>',
            '<div class="header">',
            '<h1>Watch Mode Alerts Report</h1>',
            f'<p>Total Alerts: {len(self.alerts)}</p>',
            '</div>'
        ]

        for chart_id, fig in charts:
            html_parts.append(f'<div class="chart-container" id="{chart_id}"></div>')
            html_parts.append(f'<script>{fig.to_html(include_plotlyjs=False, div_id=chart_id)}</script>')

        html_parts.append('</body></html>')

        with open(output_path, 'w') as f:
            f.write('\n'.join(html_parts))

        logger.info(f"Alerts report saved to {output_path}")

    @staticmethod
    def _create_empty_figure(message: str) -> go.Figure:
        """Create empty figure with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            template='plotly_white'
        )
        return fig


# Utility functions for CLI usage

def visualize_backtest_from_file(input_path: str, output_path: str) -> None:
    """Load backtest JSON and create visualization report"""
    with open(input_path, 'r') as f:
        data = json.load(f)

    visualizer = ScreenBacktestVisualizer(data)
    visualizer.create_html_report(output_path)


def visualize_comparison_from_file(input_path: str, output_path: str) -> None:
    """Load comparison JSON and create visualization report"""
    with open(input_path, 'r') as f:
        data = json.load(f)

    visualizer = ScreenComparisonVisualizer(data)
    visualizer.create_html_report(output_path)


def visualize_results_from_file(input_path: str, output_path: str) -> None:
    """Load screening results JSON and create visualization report"""
    with open(input_path, 'r') as f:
        data = json.load(f)

    visualizer = ScreenResultsVisualizer(data)
    visualizer.create_html_report(output_path)


def visualize_alerts_from_file(input_path: str, output_path: str) -> None:
    """Load alerts JSON and create visualization report"""
    with open(input_path, 'r') as f:
        data = json.load(f)

    visualizer = ScreenAlertsVisualizer(data)
    visualizer.create_html_report(output_path)
