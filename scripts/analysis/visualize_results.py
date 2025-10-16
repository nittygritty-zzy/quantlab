#!/usr/bin/env python3
"""Visualize qlib backtest results

Usage:
    cd /path/to/quantlab
    uv run python scripts/analysis/visualize_results.py

Make sure to update EXP_DIR to point to your experiment run.
"""
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import os

# Change to project root directory
os.chdir(Path(__file__).parent.parent.parent)
sys.path.insert(0, str(Path("qlib_repo")))

# Import qlib
import qlib

# Set style
sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (14, 10)

# Latest experiment run - LIQUID UNIVERSE VERSION
# Update this path to the experiment run you want to visualize
EXP_DIR = Path("qlib_repo/examples/mlruns/178155917691905103/c20b6cfbfe56463ebc1769fd624e5cac/artifacts")

def load_pickle(filepath):
    """Load pickle file"""
    with open(filepath, 'rb') as f:
        return pickle.load(f)

# Load data
print("Loading data...")
import sys
sys.path.insert(0, str(Path("qlib_repo")))
import qlib

ic_data = load_pickle(EXP_DIR / "sig_analysis/ic.pkl")
ric_data = load_pickle(EXP_DIR / "sig_analysis/ric.pkl")
report = load_pickle(EXP_DIR / "portfolio_analysis/report_normal_1day.pkl")
pred = load_pickle(EXP_DIR / "pred.pkl")

# Create figure with subplots
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# 1. IC over time
ax1 = fig.add_subplot(gs[0, 0])
ic_series = ic_data  # Already a Series
ic_series.plot(ax=ax1, color='steelblue', linewidth=1.5, alpha=0.7)
ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
ax1.axhline(y=ic_series.mean(), color='green', linestyle='--', alpha=0.5,
            label=f'Mean IC: {ic_series.mean():.4f}')
ax1.set_title('Information Coefficient (IC) Over Time', fontsize=12, fontweight='bold')
ax1.set_xlabel('Date')
ax1.set_ylabel('IC')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. Rank IC over time
ax2 = fig.add_subplot(gs[0, 1])
ric_series = ric_data  # Already a Series
ric_series.plot(ax=ax2, color='coral', linewidth=1.5, alpha=0.7)
ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)
ax2.axhline(y=ric_series.mean(), color='green', linestyle='--', alpha=0.5,
            label=f'Mean Rank IC: {ric_series.mean():.4f}')
ax2.set_title('Rank IC Over Time', fontsize=12, fontweight='bold')
ax2.set_xlabel('Date')
ax2.set_ylabel('Rank IC')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. Cumulative Returns
ax3 = fig.add_subplot(gs[1, :])
returns = report['return']
benchmark_returns = report.get('bench', pd.Series(0, index=returns.index))
cum_returns = (1 + returns).cumprod()
cum_bench = (1 + benchmark_returns).cumprod()

ax3.plot(cum_returns.index, cum_returns.values, label='Strategy',
         linewidth=2, color='darkgreen')
ax3.plot(cum_bench.index, cum_bench.values, label='Benchmark (SPY)',
         linewidth=2, color='gray', alpha=0.7)
ax3.fill_between(cum_returns.index, cum_bench.values, cum_returns.values,
                  where=(cum_returns.values >= cum_bench.values),
                  alpha=0.2, color='green', label='Outperformance')
ax3.fill_between(cum_returns.index, cum_bench.values, cum_returns.values,
                  where=(cum_returns.values < cum_bench.values),
                  alpha=0.2, color='red', label='Underperformance')
ax3.set_title('Cumulative Returns: Strategy vs Benchmark', fontsize=12, fontweight='bold')
ax3.set_xlabel('Date')
ax3.set_ylabel('Cumulative Return')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. Daily Returns Distribution
ax4 = fig.add_subplot(gs[2, 0])
returns.hist(bins=50, ax=ax4, color='steelblue', alpha=0.7, edgecolor='black')
ax4.axvline(x=returns.mean(), color='red', linestyle='--', linewidth=2,
            label=f'Mean: {returns.mean():.4f}')
ax4.axvline(x=returns.median(), color='green', linestyle='--', linewidth=2,
            label=f'Median: {returns.median():.4f}')
ax4.set_title('Daily Returns Distribution', fontsize=12, fontweight='bold')
ax4.set_xlabel('Daily Return')
ax4.set_ylabel('Frequency')
ax4.legend()
ax4.grid(True, alpha=0.3)

# 5. Drawdown
ax5 = fig.add_subplot(gs[2, 1])
cum_max = cum_returns.cummax()
drawdown = (cum_returns - cum_max) / cum_max
drawdown.plot(ax=ax5, color='darkred', linewidth=1.5, alpha=0.8)
ax5.fill_between(drawdown.index, 0, drawdown.values, alpha=0.3, color='red')
ax5.set_title(f'Drawdown (Max: {drawdown.min():.2%})', fontsize=12, fontweight='bold')
ax5.set_xlabel('Date')
ax5.set_ylabel('Drawdown')
ax5.grid(True, alpha=0.3)

plt.suptitle('LightGBM Model - Backtest Results Analysis',
             fontsize=16, fontweight='bold', y=0.995)

# Save figure
output_path = Path("results/visualizations/backtest_visualization.png")
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"\n✓ Visualization saved to: {output_path.absolute()}")

# Print summary statistics
print("\n" + "="*60)
print("PERFORMANCE SUMMARY")
print("="*60)
print(f"Total Return: {(cum_returns.iloc[-1] - 1):.2%}")
print(f"Benchmark Return: {(cum_bench.iloc[-1] - 1):.2%}")
print(f"Excess Return: {((cum_returns.iloc[-1] - 1) - (cum_bench.iloc[-1] - 1)):.2%}")
print(f"Sharpe Ratio: {(returns.mean() / returns.std() * (252**0.5)):.2f}")
print(f"Max Drawdown: {drawdown.min():.2%}")
print(f"Win Rate: {(returns > 0).sum() / len(returns):.2%}")
print(f"Mean IC: {ic_series.mean():.4f}")
print(f"Mean Rank IC: {ric_series.mean():.4f}")
print("="*60)

# plt.show()  # Skip interactive display
