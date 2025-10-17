"""
Screen Comparison Module

Compare multiple screening strategies side-by-side to find overlaps,
consensus picks, and evaluate which strategies work best together.
"""

import logging
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass

import pandas as pd
import numpy as np

from .screener import ScreenCriteria, StockScreener

logger = logging.getLogger(__name__)


@dataclass
class ComparisonResults:
    """Results from comparing multiple screens"""
    screen_names: List[str]
    individual_results: Dict[str, pd.DataFrame]
    overlap_analysis: pd.DataFrame
    consensus_picks: pd.DataFrame
    comparison_metrics: pd.DataFrame


class ScreenComparator:
    """Compare multiple screening strategies"""

    def __init__(self, screener: StockScreener):
        """
        Initialize comparator

        Args:
            screener: StockScreener instance
        """
        self.screener = screener
        logger.info("✓ Screen comparator initialized")

    def compare_screens(
        self,
        screens: Dict[str, ScreenCriteria],
        limit_per_screen: int = 50,
        workers: int = 4,
        include_scores: bool = True
    ) -> ComparisonResults:
        """
        Compare multiple screening strategies

        Args:
            screens: Dict mapping screen names to ScreenCriteria
            limit_per_screen: Maximum results per screen
            workers: Number of parallel workers
            include_scores: Whether to include composite scores

        Returns:
            ComparisonResults with detailed analysis
        """
        try:
            logger.info(f"🔍 Comparing {len(screens)} screening strategies")

            # Run all screens
            individual_results = {}
            for name, criteria in screens.items():
                logger.info(f"   Running screen: {name}")
                results = self.screener.screen(
                    criteria,
                    limit=limit_per_screen,
                    workers=workers,
                    include_score=include_scores
                )
                individual_results[name] = results

            # Analyze overlaps
            overlap_analysis = self._analyze_overlaps(individual_results)

            # Find consensus picks (stocks in multiple screens)
            consensus_picks = self._find_consensus_picks(individual_results, include_scores)

            # Calculate comparison metrics
            comparison_metrics = self._calculate_comparison_metrics(individual_results)

            comparison = ComparisonResults(
                screen_names=list(screens.keys()),
                individual_results=individual_results,
                overlap_analysis=overlap_analysis,
                consensus_picks=consensus_picks,
                comparison_metrics=comparison_metrics
            )

            logger.info(f"✅ Comparison complete:")
            logger.info(f"   Total unique stocks: {overlap_analysis['total_unique'].iloc[0]}")
            logger.info(f"   Consensus picks: {len(consensus_picks)}")

            return comparison

        except Exception as e:
            logger.error(f"Screen comparison failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _analyze_overlaps(
        self,
        results: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Analyze ticker overlaps between screens

        Returns DataFrame with:
        - Total stocks per screen
        - Unique stocks (not in any other screen)
        - Overlap counts
        - Total unique stocks across all screens
        """
        try:
            screen_names = list(results.keys())
            ticker_sets = {name: set(df['ticker'].tolist()) for name, df in results.items()}

            # Calculate metrics for each screen
            overlap_data = []

            for name in screen_names:
                tickers = ticker_sets[name]
                total = len(tickers)

                # Find unique stocks (only in this screen)
                unique = tickers.copy()
                for other_name, other_tickers in ticker_sets.items():
                    if other_name != name:
                        unique -= other_tickers

                # Find overlaps with other screens
                overlaps = {}
                for other_name in screen_names:
                    if other_name != name:
                        overlap = len(tickers & ticker_sets[other_name])
                        overlaps[f'overlap_with_{other_name}'] = overlap

                overlap_data.append({
                    'screen': name,
                    'total_stocks': total,
                    'unique_stocks': len(unique),
                    'in_multiple_screens': total - len(unique),
                    **overlaps
                })

            df = pd.DataFrame(overlap_data)

            # Add summary row
            all_tickers = set()
            for tickers in ticker_sets.values():
                all_tickers.update(tickers)

            summary = {
                'screen': 'TOTAL',
                'total_stocks': sum(len(t) for t in ticker_sets.values()),
                'unique_stocks': len(all_tickers),
                'in_multiple_screens': sum(len(t) for t in ticker_sets.values()) - len(all_tickers),
                'total_unique': len(all_tickers)
            }

            # Add summary row
            df = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)

            return df

        except Exception as e:
            logger.error(f"Error analyzing overlaps: {e}")
            return pd.DataFrame()

    def _find_consensus_picks(
        self,
        results: Dict[str, pd.DataFrame],
        include_scores: bool = True
    ) -> pd.DataFrame:
        """
        Find stocks that appear in multiple screens (consensus picks)

        Returns DataFrame with:
        - ticker
        - appearances (number of screens containing this stock)
        - screens (list of screen names)
        - avg_score (if scores available)
        - stock metadata from first screen
        """
        try:
            # Build ticker -> screens mapping
            ticker_screens = {}

            for screen_name, df in results.items():
                for _, row in df.iterrows():
                    ticker = row['ticker']
                    if ticker not in ticker_screens:
                        ticker_screens[ticker] = {
                            'screens': [],
                            'scores': [],
                            'metadata': row.to_dict()
                        }
                    ticker_screens[ticker]['screens'].append(screen_name)
                    if include_scores and 'composite_score' in df.columns:
                        ticker_screens[ticker]['scores'].append(row['composite_score'])

            # Filter to stocks in multiple screens
            consensus = []
            for ticker, data in ticker_screens.items():
                if len(data['screens']) >= 2:  # In at least 2 screens
                    consensus.append({
                        'ticker': ticker,
                        'appearances': len(data['screens']),
                        'screens': ', '.join(data['screens']),
                        'avg_score': np.mean(data['scores']) if data['scores'] else None,
                        'name': data['metadata'].get('name', ''),
                        'sector': data['metadata'].get('sector', ''),
                        'industry': data['metadata'].get('industry', ''),
                        'price': data['metadata'].get('price'),
                        'market_cap': data['metadata'].get('market_cap')
                    })

            df = pd.DataFrame(consensus)

            if not df.empty:
                # Sort by number of appearances and score
                sort_cols = ['appearances']
                if include_scores and 'avg_score' in df.columns:
                    sort_cols.append('avg_score')
                df = df.sort_values(sort_cols, ascending=[False, False])

            return df

        except Exception as e:
            logger.error(f"Error finding consensus picks: {e}")
            return pd.DataFrame()

    def _calculate_comparison_metrics(
        self,
        results: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Calculate metrics for each screen to compare effectiveness

        Returns DataFrame with:
        - screen name
        - num_stocks
        - avg_score
        - avg_price
        - avg_volume
        - avg_market_cap
        - sector_diversity (number of unique sectors)
        """
        try:
            metrics = []

            for name, df in results.items():
                if df.empty:
                    continue

                metric = {
                    'screen': name,
                    'num_stocks': len(df),
                    'avg_score': df['composite_score'].mean() if 'composite_score' in df.columns else None,
                    'avg_price': df['price'].mean() if 'price' in df.columns else None,
                    'avg_volume': df['volume'].mean() if 'volume' in df.columns else None,
                    'avg_market_cap': df['market_cap'].mean() if 'market_cap' in df.columns else None,
                    'sector_diversity': df['sector'].nunique() if 'sector' in df.columns else 0,
                    'avg_rsi': df['rsi'].mean() if 'rsi' in df.columns else None,
                    'avg_pe_ratio': df['pe_ratio'].mean() if 'pe_ratio' in df.columns else None
                }

                metrics.append(metric)

            return pd.DataFrame(metrics)

        except Exception as e:
            logger.error(f"Error calculating comparison metrics: {e}")
            return pd.DataFrame()

    def export_comparison_report(
        self,
        comparison: ComparisonResults,
        output_path: str
    ) -> bool:
        """
        Export comparison results to multi-sheet Excel file

        Args:
            comparison: ComparisonResults object
            output_path: Path to save Excel file

        Returns:
            True if successful
        """
        try:
            from pathlib import Path
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Sheet 1: Summary metrics
                comparison.comparison_metrics.to_excel(
                    writer,
                    sheet_name='Summary',
                    index=False
                )

                # Sheet 2: Overlap analysis
                comparison.overlap_analysis.to_excel(
                    writer,
                    sheet_name='Overlap Analysis',
                    index=False
                )

                # Sheet 3: Consensus picks
                if not comparison.consensus_picks.empty:
                    comparison.consensus_picks.to_excel(
                        writer,
                        sheet_name='Consensus Picks',
                        index=False
                    )

                # Individual screen results (one sheet per screen)
                for name, df in comparison.individual_results.items():
                    # Truncate sheet name to 31 chars (Excel limit)
                    sheet_name = name[:27] + '...' if len(name) > 31 else name
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            logger.info(f"✅ Comparison report exported to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export comparison report: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def export_comparison_json(
        self,
        comparison: ComparisonResults,
        output_path: str
    ) -> bool:
        """
        Export comparison results to JSON file

        Args:
            comparison: ComparisonResults object
            output_path: Path to save JSON file

        Returns:
            True if successful
        """
        try:
            from pathlib import Path
            import json

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            report = {
                'screens': comparison.screen_names,
                'comparison_metrics': comparison.comparison_metrics.to_dict('records'),
                'overlap_analysis': comparison.overlap_analysis.to_dict('records'),
                'consensus_picks': comparison.consensus_picks.to_dict('records'),
                'individual_results': {
                    name: df.to_dict('records')
                    for name, df in comparison.individual_results.items()
                }
            }

            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"✅ Comparison JSON exported to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export comparison JSON: {e}")
            return False
