Installation
============

Requirements
------------

- Python 3.8 or higher
- `uv <https://github.com/astral-sh/uv>`_ (recommended) or pip
- 8GB+ RAM recommended for backtesting
- Polygon.io API key (for market data)

Install with uv (Recommended)
------------------------------

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/nittygritty-zzy/quantlab.git
   cd quantlab

   # Install with uv
   uv sync

   # Initialize the database and configuration
   uv run quantlab init

Install with pip
----------------

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/nittygritty-zzy/quantlab.git
   cd quantlab

   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -e .

   # Initialize
   quantlab init

Configuration
-------------

Create a configuration file at ``~/.quantlab/config.yaml``:

.. code-block:: yaml

   api_keys:
     polygon: "YOUR_POLYGON_API_KEY"
     alpha_vantage: "YOUR_ALPHA_VANTAGE_KEY"  # Optional

   data:
     qlib_data_path: "/path/to/qlib/data"  # Optional

   database:
     path: "~/.quantlab/quantlab.duckdb"

Get API Keys
~~~~~~~~~~~~

1. **Polygon.io** (Required)

   - Sign up at https://polygon.io
   - Free tier: 5 API calls/minute
   - Paid plans available for higher limits

2. **Alpha Vantage** (Optional)

   - Sign up at https://www.alphavantage.co
   - Free tier: 25 API calls/day

Data Setup
----------

QuantLab uses qlib's data format for historical stock prices.

Option 1: Download Pre-built Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Download US stock data (1998-present)
   uv run python -m qlib.run.get_data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region us

Option 2: Use Existing qlib Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have existing qlib data, configure the path in ``~/.quantlab/config.yaml``:

.. code-block:: yaml

   data:
     qlib_data_path: "/Volumes/sandisk/quantmini-data/data/qlib/stocks_daily/"

Verification
------------

Verify your installation:

.. code-block:: bash

   # Check CLI is working
   uv run quantlab --version

   # Check data availability
   uv run quantlab data check

   # List available tickers
   uv run quantlab data tickers | head -20

   # Test visualization
   uv run quantlab visualize price AAPL --period 30d --chart-type candlestick

Troubleshooting
---------------

Database Connection Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you see database errors:

.. code-block:: bash

   # Reinitialize the database
   rm ~/.quantlab/quantlab.duckdb
   uv run quantlab init

API Rate Limits
~~~~~~~~~~~~~~~

Polygon free tier: 5 calls/minute

- Use ``--from-date`` and ``--to-date`` to limit data ranges
- Consider upgrading for production use

Missing Data
~~~~~~~~~~~~

If tickers show no data:

.. code-block:: bash

   # Check data availability
   uv run quantlab data range AAPL

   # Download fresh data (requires qlib setup)
   # See qlib documentation for data updates

Next Steps
----------

Continue to :doc:`quickstart` to start using QuantLab!
