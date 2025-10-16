QuantLab Documentation
======================

.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/github/license/nittygritty-zzy/quantlab
   :target: https://github.com/nittygritty-zzy/quantlab/blob/main/LICENSE
   :alt: License

.. image:: https://readthedocs.org/projects/quantlab/badge/?version=latest
   :target: https://quantlab.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

🚀 Professional quantitative trading research platform with ML-powered backtesting, multi-source options analysis, portfolio management, and interactive Plotly visualizations. Built on qlib with CLI interface.

Features
--------

📊 **Interactive Visualizations**
   - Price charts (candlestick, line) with technical indicators
   - Multi-ticker comparison (normalized & absolute)
   - Options payoff diagrams with Greeks analysis
   - Portfolio performance dashboards
   - Backtest results visualization

📈 **Quantitative Research**
   - ML-powered stock ranking (LightGBM, XGBoost, TabNet, HIST)
   - Alpha158 technical factors
   - Custom factor engineering with qlib
   - Backtesting with realistic trading simulation

📉 **Options Analysis**
   - Multi-source options data (Polygon, yfinance, Alpha Vantage)
   - 15+ strategy builders (spreads, condors, butterflies)
   - Advanced Greeks (delta, gamma, theta, vega, vanna, charm, vomma)
   - IV surface analysis
   - Intraday options tracking

💼 **Portfolio Management**
   - Multi-portfolio tracking
   - Position management with cost basis
   - Comprehensive analysis (fundamentals, technicals, options, sentiment)
   - Risk metrics and recommendations

🎯 **Data Infrastructure**
   - DuckDB for fast analytics
   - Parquet-based qlib data (20+ years daily history)
   - Real-time and historical options data
   - Market holidays and extended hours filtering

Quick Links
-----------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart
   cli_overview

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/visualization
   user_guide/backtesting
   user_guide/options
   user_guide/portfolio
   user_guide/data_management

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/data
   api/visualization
   api/analysis
   api/cli

.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics

   advanced/custom_factors
   advanced/strategy_development
   advanced/performance_optimization
   advanced/extending_quantlab

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources

   examples
   faq
   changelog
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
