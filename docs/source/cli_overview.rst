CLI Overview
============

QuantLab provides a comprehensive command-line interface for all trading research operations.

Command Structure
-----------------

.. code-block:: bash

   quantlab [COMMAND] [SUBCOMMAND] [OPTIONS] [ARGUMENTS]

Main Commands
-------------

Data Management
~~~~~~~~~~~~~~~

.. code-block:: bash

   quantlab data check              # Check data availability
   quantlab data tickers [--type]   # List available tickers
   quantlab data query TICKER       # Query price/options data
   quantlab data range TICKER       # Show date range

Analysis
~~~~~~~~

.. code-block:: bash

   quantlab analyze ticker TICKER [OPTIONS]     # Analyze single ticker
   quantlab analyze portfolio NAME [OPTIONS]    # Analyze portfolio

Portfolio Management
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   quantlab portfolio create NAME             # Create portfolio
   quantlab portfolio list                    # List portfolios
   quantlab portfolio show NAME               # Show portfolio details
   quantlab portfolio add NAME TICKER [OPTS]  # Add position
   quantlab portfolio remove NAME TICKER      # Remove position
   quantlab portfolio update NAME TICKER      # Update position

Visualization
~~~~~~~~~~~~~

.. code-block:: bash

   quantlab visualize price TICKER [OPTIONS]              # Price charts
   quantlab visualize compare TICKER1 TICKER2 ... [OPTS]  # Multi-ticker
   quantlab visualize options STRATEGY [OPTIONS]          # Options payoff
   quantlab visualize portfolio NAME [OPTIONS]            # Portfolio charts
   quantlab visualize backtest PATH [OPTIONS]             # Backtest results

Lookup Tables
~~~~~~~~~~~~~

.. code-block:: bash

   quantlab lookup init                    # Initialize lookup tables
   quantlab lookup stats                   # Show statistics
   quantlab lookup refresh [--type]        # Refresh data
   quantlab lookup get company TICKER      # Get company info
   quantlab lookup get ratings TICKER      # Get analyst ratings
   quantlab lookup get treasury [--maturity] # Get risk-free rate

Common Options
--------------

Price Charts
~~~~~~~~~~~~

.. code-block:: bash

   --period PERIOD          # Time period (e.g., 30d, 90d, 1year, ytd, max)
   --interval INTERVAL      # Intraday interval (1min, 5min, 15min, 1hour)
   --chart-type TYPE        # Chart type (candlestick, line)
   --output PATH            # Save chart to file
   --show-volume           # Include volume bars
   --mas MA_PERIODS        # Moving averages (e.g., 20,50,200)

Examples:

.. code-block:: bash

   # Daily candlestick with volume
   quantlab visualize price AAPL --period 90d --chart-type candlestick --show-volume

   # Intraday 5-minute chart
   quantlab visualize price AAPL --interval 5min --period 5d --chart-type line

   # With moving averages
   quantlab visualize price AAPL --period 1year --mas 50,200

Options Strategy
~~~~~~~~~~~~~~~~

.. code-block:: bash

   --current-price PRICE    # Current stock price
   --strike1, --strike2,    # Strike prices (strategy-dependent)
   --strike3, --strike4
   --premium PREMIUM        # Net premium paid/received
   --iv IV                  # Implied volatility (for Greeks)
   --dte DAYS              # Days to expiration
   --risk-free-rate RATE   # Risk-free rate (default: treasury)

Available strategies:

* Single leg: ``long_call``, ``long_put``, ``short_call``, ``short_put``
* Covered: ``covered_call``, ``protective_put``, ``collar``
* Spreads: ``bull_call_spread``, ``bear_put_spread``, ``bull_put_spread``, ``bear_call_spread``
* Volatility: ``long_straddle``, ``short_straddle``, ``long_strangle``, ``short_strangle``
* Complex: ``iron_condor``, ``iron_butterfly``, ``butterfly``, ``calendar_spread``

Analysis Options
~~~~~~~~~~~~~~~~

.. code-block:: bash

   --output PATH                # Save analysis to JSON file
   --no-fundamentals           # Skip fundamental analysis
   --no-options                # Skip options analysis
   --no-technicals             # Skip technical analysis
   --no-sentiment              # Skip sentiment analysis

Examples:

.. code-block:: bash

   # Full analysis
   quantlab analyze ticker AAPL --output results/aapl_analysis.json

   # Options-only analysis
   quantlab analyze ticker AAPL --no-fundamentals --no-technicals --no-sentiment

Environment Variables
---------------------

.. code-block:: bash

   QUANTLAB_CONFIG_PATH      # Custom config file path
   POLYGON_API_KEY          # Polygon.io API key
   ALPHA_VANTAGE_API_KEY    # Alpha Vantage API key
   QUANTLAB_DB_PATH         # Database file path

Configuration File
------------------

Default location: ``~/.quantlab/config.yaml``

.. code-block:: yaml

   # API Keys
   api_keys:
     polygon: "YOUR_API_KEY"
     alpha_vantage: "YOUR_API_KEY"

   # Data paths
   data:
     qlib_data_path: "/path/to/qlib/data"

   # Database
   database:
     path: "~/.quantlab/quantlab.duckdb"

   # Default settings
   defaults:
     period: "90d"
     chart_type: "candlestick"

Output Formats
--------------

JSON Output
~~~~~~~~~~~

Analysis commands support ``--output`` to save JSON:

.. code-block:: bash

   quantlab analyze ticker AAPL --output analysis.json

   # Pretty-print JSON
   cat analysis.json | python -m json.tool

HTML Charts
~~~~~~~~~~~

Visualization commands generate interactive HTML:

.. code-block:: bash

   quantlab visualize price AAPL --output chart.html

   # Open in browser
   open chart.html  # macOS
   xdg-open chart.html  # Linux
   start chart.html  # Windows

Piping and Integration
----------------------

Use with jq
~~~~~~~~~~~

.. code-block:: bash

   # Extract specific fields
   quantlab analyze ticker AAPL --output - | jq '.options.chain[] | select(.strike == 180)'

   # Count options contracts
   quantlab analyze ticker AAPL --output - | jq '.options.chain | length'

Use with grep
~~~~~~~~~~~~~

.. code-block:: bash

   # Filter tickers
   quantlab data tickers | grep "^AA"

   # Search in analysis
   quantlab analyze ticker AAPL --output - | grep -i "recommendation"

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Analyze multiple tickers
   for ticker in AAPL GOOGL MSFT; do
       quantlab analyze ticker $ticker --output results/${ticker}.json
   done

   # Parallel processing
   echo "AAPL GOOGL MSFT NVDA" | xargs -P 4 -n 1 bash -c '
       quantlab analyze ticker "$1" --output "results/$1.json"
   ' _

Error Handling
--------------

Return Codes
~~~~~~~~~~~~

- 0: Success
- 1: General error
- 2: Invalid arguments
- 3: Data not found
- 4: API error

Logging
~~~~~~~

Set log level:

.. code-block:: bash

   # Debug level
   QUANTLAB_LOG_LEVEL=DEBUG quantlab visualize price AAPL

   # Quiet mode
   QUANTLAB_LOG_LEVEL=ERROR quantlab analyze ticker AAPL

Advanced Usage
--------------

Custom Scripts
~~~~~~~~~~~~~~

Import QuantLab in your Python scripts:

.. code-block:: python

   from quantlab.core.analyzer import Analyzer
   from quantlab.visualization.price_charts import create_candlestick_chart

   # Initialize analyzer
   analyzer = Analyzer()

   # Get data and create chart
   df = analyzer.get_price_data("AAPL", period="90d")
   fig = create_candlestick_chart(df, "AAPL", show_volume=True)
   fig.write_html("aapl_chart.html")

Backtesting Integration
~~~~~~~~~~~~~~~~~~~~~~~~

Use ``qrun`` for backtesting:

.. code-block:: bash

   # Run backtest
   qrun configs/my_strategy.yaml

   # Visualize results
   quantlab visualize backtest results/mlruns/[exp_id]/[run_id]

Next Steps
----------

- :doc:`user_guide/visualization` - Detailed visualization guide
- :doc:`user_guide/options` - Options analysis guide
- :doc:`api/cli` - CLI API reference
- :doc:`examples` - More examples
