"""
Screen Backtesting Module

Test historical performance of screening criteria to validate effectiveness.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import pandas as pd
import numpy as np

from ..data.parquet_reader import ParquetReader
from ..data.database import DatabaseManager
from .screener import ScreenCriteria, StockScreener


logger = logging.getLogger(__name__)


@dataclass
class BacktestResults:
    """Results from a backtest run"""
    criteria: ScreenCriteria
    start_date: date
    end_date: date
    rebalance_frequency: str
    total_periods: int
    avg_stocks_per_period: float

    # Performance metrics
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    avg_holding_return: float

    # Period-by-period results
    period_results: pd.DataFrame

    # Benchmark comparison
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None


class ScreenBacktester:
    """Backtest screening criteria over historical periods"""

    def __init__(
        self,
        db: DatabaseManager,
        parquet_reader: ParquetReader,
        screener: StockScreener
    ):
        """
        Initialize backtester

        Args:
            db: Database manager
            parquet_reader: Historical data reader
            screener: Stock screener instance
        """
        self.db = db
        self.parquet = parquet_reader
        self.screener = screener

        logger.info("✓ Screen backtester initialized")

    def backtest_criteria(
        self,
        criteria: ScreenCriteria,
        start_date: date,
        end_date: date,
        rebalance_frequency: str = 'weekly',
        holding_periods: List[int] = [5, 20],
        benchmark: str = 'SPY'
    ) -> BacktestResults:
        """
        Backtest screening criteria over a date range

        Args:
            criteria: Screening criteria to test
            start_date: Start date for backtest
            end_date: End date for backtest
            rebalance_frequency: 'daily', 'weekly', or 'monthly'
            holding_periods: Days to hold (e.g., [5, 20] for 1-week and 1-month)
            benchmark: Benchmark ticker for comparison

        Returns:
            BacktestResults with performance metrics
        """
        try:
            logger.info(f"🔍 Starting backtest from {start_date} to {end_date}")
            logger.info(f"   Rebalance: {rebalance_frequency}, Holding periods: {holding_periods}")

            # Generate rebalance dates
            rebal_dates = self._generate_rebalance_dates(
                start_date, end_date, rebalance_frequency
            )

            logger.info(f"   Generated {len(rebal_dates)} rebalance periods")

            # Run screening at each rebalance date
            period_results = []

            for i, rebal_date in enumerate(rebal_dates, 1):
                if i % 10 == 0:
                    logger.info(f"   Progress: {i}/{len(rebal_dates)} periods")

                result = self._backtest_single_period(
                    criteria, rebal_date, holding_periods
                )

                if result:
                    period_results.append(result)

            if not period_results:
                logger.warning("⚠️  No results from backtest")
                return self._empty_backtest_results(criteria, start_date, end_date, rebalance_frequency)

            # Convert to DataFrame
            results_df = pd.DataFrame(period_results)

            # Calculate aggregate metrics
            metrics = self._calculate_backtest_metrics(results_df, holding_periods)

            # Get benchmark performance
            benchmark_return = self._calculate_benchmark_return(
                benchmark, start_date, end_date
            )

            # Calculate alpha/beta
            if benchmark_return is not None:
                alpha, beta = self._calculate_alpha_beta(
                    results_df, benchmark_return, start_date, end_date
                )
            else:
                alpha, beta = None, None

            backtest = BacktestResults(
                criteria=criteria,
                start_date=start_date,
                end_date=end_date,
                rebalance_frequency=rebalance_frequency,
                total_periods=len(results_df),
                avg_stocks_per_period=results_df['num_stocks'].mean(),
                total_return=metrics['total_return'],
                annualized_return=metrics['annualized_return'],
                sharpe_ratio=metrics['sharpe_ratio'],
                max_drawdown=metrics['max_drawdown'],
                win_rate=metrics['win_rate'],
                avg_holding_return=metrics['avg_return'],
                period_results=results_df,
                benchmark_return=benchmark_return,
                alpha=alpha,
                beta=beta
            )

            logger.info(f"✅ Backtest complete:")
            logger.info(f"   Total Return: {metrics['total_return']:.2f}%")
            logger.info(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            logger.info(f"   Win Rate: {metrics['win_rate']:.1f}%")

            return backtest

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._empty_backtest_results(criteria, start_date, end_date, rebalance_frequency)

    def _generate_rebalance_dates(
        self,
        start_date: date,
        end_date: date,
        frequency: str
    ) -> List[date]:
        """Generate list of rebalance dates"""
        dates = []
        current = start_date

        if frequency == 'daily':
            delta = timedelta(days=1)
        elif frequency == 'weekly':
            delta = timedelta(days=7)
        elif frequency == 'monthly':
            delta = timedelta(days=30)
        else:
            raise ValueError(f"Unknown frequency: {frequency}")

        while current <= end_date:
            dates.append(current)
            current += delta

        return dates

    def _backtest_single_period(
        self,
        criteria: ScreenCriteria,
        screen_date: date,
        holding_periods: List[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Backtest a single screening period

        Returns dict with:
        - date: Screening date
        - num_stocks: Number of stocks found
        - returns_5d, returns_20d, etc.: Average returns for each holding period
        """
        try:
            # Run screen as of this date (using data up to this date)
            # Note: This is simplified - in production would need point-in-time data
            results = self.screener.screen(
                criteria,
                limit=50,
                workers=2,
                include_score=True
            )

            if results.empty:
                return None

            tickers = results['ticker'].tolist()

            # Calculate forward returns for each holding period
            returns = {}
            for period in holding_periods:
                avg_return = self._calculate_forward_returns(
                    tickers, screen_date, period
                )
                returns[f'return_{period}d'] = avg_return

            return {
                'date': screen_date,
                'num_stocks': len(tickers),
                **returns
            }

        except Exception as e:
            logger.debug(f"Error in period {screen_date}: {e}")
            return None

    def _calculate_forward_returns(
        self,
        tickers: List[str],
        entry_date: date,
        holding_days: int
    ) -> Optional[float]:
        """Calculate average forward return for a list of tickers"""
        try:
            exit_date = entry_date + timedelta(days=holding_days + 5)  # Buffer for weekends

            returns = []

            for ticker in tickers:
                # Get price data around entry and exit
                df = self.parquet.get_stock_daily(
                    tickers=[ticker],
                    start_date=entry_date,
                    end_date=exit_date
                )

                if df is None or len(df) < 2:
                    continue

                # Get entry price (close on entry date or next available)
                entry_prices = df[df['date'] >= pd.Timestamp(entry_date)]
                if entry_prices.empty:
                    continue
                entry_price = float(entry_prices.iloc[0]['close'])

                # Get exit price (close around holding_days later)
                target_exit = entry_date + timedelta(days=holding_days)
                exit_prices = df[df['date'] >= pd.Timestamp(target_exit)]
                if exit_prices.empty:
                    exit_price = float(df.iloc[-1]['close'])  # Use last available
                else:
                    exit_price = float(exit_prices.iloc[0]['close'])

                # Calculate return
                ret = ((exit_price - entry_price) / entry_price) * 100
                returns.append(ret)

            if not returns:
                return None

            return np.mean(returns)

        except Exception as e:
            logger.debug(f"Error calculating returns: {e}")
            return None

    def _calculate_backtest_metrics(
        self,
        results_df: pd.DataFrame,
        holding_periods: List[int]
    ) -> Dict[str, float]:
        """Calculate aggregate backtest metrics"""

        # Use the longest holding period for main metrics
        main_period = max(holding_periods)
        return_col = f'return_{main_period}d'

        if return_col not in results_df.columns:
            return self._empty_metrics()

        returns = results_df[return_col].dropna()

        if returns.empty:
            return self._empty_metrics()

        # Total and annualized return
        total_return = returns.sum()
        num_periods = len(returns)
        periods_per_year = 252 / main_period  # Trading days
        annualized_return = ((1 + total_return/100) ** (periods_per_year / num_periods) - 1) * 100

        # Sharpe ratio (simplified - assumes risk-free rate = 0)
        avg_return = returns.mean()
        std_return = returns.std()
        sharpe_ratio = (avg_return / std_return * np.sqrt(periods_per_year)) if std_return > 0 else 0

        # Max drawdown
        cumulative = (1 + returns/100).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        max_drawdown = drawdown.min()

        # Win rate
        win_rate = (returns > 0).sum() / len(returns) * 100

        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'avg_return': avg_return
        }

    def _calculate_benchmark_return(
        self,
        benchmark: str,
        start_date: date,
        end_date: date
    ) -> Optional[float]:
        """Calculate benchmark total return over period"""
        try:
            df = self.parquet.get_stock_daily(
                tickers=[benchmark],
                start_date=start_date,
                end_date=end_date
            )

            if df is None or df.empty or len(df) < 2:
                return None

            start_price = float(df.iloc[0]['close'])
            end_price = float(df.iloc[-1]['close'])

            return ((end_price - start_price) / start_price) * 100

        except Exception as e:
            logger.debug(f"Error calculating benchmark return: {e}")
            return None

    def _calculate_alpha_beta(
        self,
        results_df: pd.DataFrame,
        benchmark_return: float,
        start_date: date,
        end_date: date
    ) -> tuple:
        """Calculate alpha and beta vs benchmark"""
        # Simplified calculation - would need period-by-period benchmark returns for proper beta
        # For now, just calculate alpha as excess return

        total_return = results_df['return_20d'].sum() if 'return_20d' in results_df.columns else 0
        alpha = total_return - benchmark_return if benchmark_return else None
        beta = 1.0  # Placeholder - proper beta requires covariance calculation

        return alpha, beta

    def _empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics dict"""
        return {
            'total_return': 0.0,
            'annualized_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'avg_return': 0.0
        }

    def _empty_backtest_results(
        self,
        criteria: ScreenCriteria,
        start_date: date,
        end_date: date,
        rebalance_frequency: str
    ) -> BacktestResults:
        """Return empty backtest results"""
        return BacktestResults(
            criteria=criteria,
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency=rebalance_frequency,
            total_periods=0,
            avg_stocks_per_period=0.0,
            total_return=0.0,
            annualized_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            avg_holding_return=0.0,
            period_results=pd.DataFrame()
        )

    def export_backtest_report(
        self,
        backtest: BacktestResults,
        output_path: str
    ) -> bool:
        """
        Export backtest results to JSON file

        Args:
            backtest: BacktestResults object
            output_path: Path to save JSON file

        Returns:
            True if successful
        """
        try:
            from pathlib import Path
            import json

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            report = {
                'backtest_info': {
                    'start_date': str(backtest.start_date),
                    'end_date': str(backtest.end_date),
                    'rebalance_frequency': backtest.rebalance_frequency,
                    'total_periods': backtest.total_periods,
                    'avg_stocks_per_period': backtest.avg_stocks_per_period
                },
                'performance': {
                    'total_return': backtest.total_return,
                    'annualized_return': backtest.annualized_return,
                    'sharpe_ratio': backtest.sharpe_ratio,
                    'max_drawdown': backtest.max_drawdown,
                    'win_rate': backtest.win_rate,
                    'avg_holding_return': backtest.avg_holding_return
                },
                'benchmark_comparison': {
                    'benchmark_return': backtest.benchmark_return,
                    'alpha': backtest.alpha,
                    'beta': backtest.beta
                } if backtest.benchmark_return else None,
                'period_results': backtest.period_results.to_dict('records')
            }

            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"✅ Backtest report exported to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return False
