Quick Start
===========

This guide will help you get started with QuantLab in 5 minutes.

Initialize QuantLab
-------------------

.. code-block:: bash

   # Initialize database and configuration
   uv run quantlab init

Basic Commands
--------------

Price Data & Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # View daily candlestick chart (90 days)
   uv run quantlab visualize price AAPL --period 90d --chart-type candlestick

   # View intraday 5-minute chart (5 days, gap-free!)
   uv run quantlab visualize price AAPL --interval 5min --period 5d --chart-type line

   # Compare multiple tickers (normalized)
   uv run quantlab visualize compare AAPL GOOGL MSFT --period 90d --normalize

Options Analysis
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Analyze ticker with options data
   uv run quantlab analyze ticker AAPL

   # View bull call spread payoff
   uv run quantlab visualize options bull_call_spread \
       --current-price 180 --strike1 185 --strike2 195 --premium 1.70

   # Analyze iron condor
   uv run quantlab visualize options iron_condor \
       --current-price 180 --strike1 175 --strike2 180 --strike3 185 --strike4 190

Portfolio Management
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create a portfolio
   uv run quantlab portfolio create "Tech Portfolio" --description "Long-term tech holdings"

   # Add positions
   uv run quantlab portfolio add "Tech Portfolio" AAPL --shares 100 --cost-basis 150.00
   uv run quantlab portfolio add "Tech Portfolio" GOOGL --shares 50 --cost-basis 120.00

   # View portfolio
   uv run quantlab portfolio show "Tech Portfolio"

   # Analyze entire portfolio
   uv run quantlab analyze portfolio "Tech Portfolio"

   # Visualize portfolio performance
   uv run quantlab visualize portfolio "Tech Portfolio" --chart-type performance

Backtesting
~~~~~~~~~~~

.. code-block:: bash

   # Run a backtest
   uv run qrun configs/backtest_tech_momentum.yaml

   # View backtest results
   ls results/mlruns/

   # Visualize backtest performance
   uv run quantlab visualize backtest results/mlruns/[exp_id]/[run_id] --chart-type performance

Example Workflows
-----------------

Workflow 1: Stock Research
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Step 1: View price history
   uv run quantlab visualize price AAPL --period 1year --chart-type candlestick

   # Step 2: Get comprehensive analysis
   uv run quantlab analyze ticker AAPL --output results/aapl_analysis.json

   # Step 3: Compare to peers
   uv run quantlab visualize compare AAPL MSFT GOOGL --period 90d --normalize

Workflow 2: Options Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Step 1: Analyze underlying stock
   uv run quantlab analyze ticker AAPL

   # Step 2: View options chain
   uv run quantlab data query AAPL --type options --limit 50

   # Step 3: Visualize strategy payoff
   uv run quantlab visualize options bull_call_spread \
       --current-price 225 --strike1 230 --strike2 240 --premium 3.50 \
       --iv 0.25 --dte 30

Workflow 3: Portfolio Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Step 1: Create portfolio
   uv run quantlab portfolio create "My Portfolio"

   # Step 2: Add positions
   uv run quantlab portfolio add "My Portfolio" AAPL --shares 100
   uv run quantlab portfolio add "My Portfolio" GOOGL --shares 50

   # Step 3: Full analysis
   uv run quantlab analyze portfolio "My Portfolio" \
       --output results/portfolio_analysis.json

   # Step 4: Visualize
   uv run quantlab visualize portfolio "My Portfolio" --chart-type allocation

Workflow 4: Quantitative Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Step 1: Create config file (see examples in configs/)
   cp configs/backtest_tech_momentum.yaml configs/my_strategy.yaml

   # Step 2: Edit strategy parameters
   vim configs/my_strategy.yaml

   # Step 3: Run backtest
   uv run qrun configs/my_strategy.yaml

   # Step 4: Analyze results
   uv run quantlab visualize backtest results/mlruns/[exp_id]/[run_id]

Sample Charts
-------------

All visualizations are interactive Plotly charts that you can:

- Zoom and pan
- Hover for detailed information
- Save as images
- Customize with CLI options

Check out sample charts in ``docs/images/``:

- `price_candlestick_90d.html <../images/price_candlestick_90d.html>`_ - 90-day AAPL candlestick
- `price_intraday_5min.html <../images/price_intraday_5min.html>`_ - 5-minute intraday (gap-free!)
- `comparison_normalized.html <../images/comparison_normalized.html>`_ - AAPL vs GOOGL vs MSFT
- `options_bull_call_spread.html <../images/options_bull_call_spread.html>`_ - Options payoff

CLI Tips
--------

Get Help
~~~~~~~~

.. code-block:: bash

   # Main help
   uv run quantlab --help

   # Command-specific help
   uv run quantlab visualize --help
   uv run quantlab analyze --help
   uv run quantlab portfolio --help

Output Options
~~~~~~~~~~~~~~

Most commands support ``--output`` to save results:

.. code-block:: bash

   # Save analysis to JSON
   uv run quantlab analyze ticker AAPL --output results/aapl.json

   # Save chart to specific location
   uv run quantlab visualize price AAPL --output results/aapl_chart.html

Batch Processing
~~~~~~~~~~~~~~~~

Use shell loops for batch operations:

.. code-block:: bash

   # Analyze multiple tickers
   for ticker in AAPL GOOGL MSFT NVDA; do
       uv run quantlab analyze ticker $ticker --output results/${ticker}_analysis.json
   done

   # Generate multiple charts
   for ticker in AAPL GOOGL MSFT; do
       uv run quantlab visualize price $ticker --period 90d --output results/${ticker}.html
   done

Next Steps
----------

- :doc:`cli_overview` - Complete CLI reference
- :doc:`user_guide/visualization` - Advanced visualization guide
- :doc:`user_guide/options` - Options analysis in depth
- :doc:`user_guide/backtesting` - Strategy development guide
- :doc:`examples` - More detailed examples
