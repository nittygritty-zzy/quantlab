"""
QuantLab - Quantitative Trading Research Platform
Portfolio management and multi-source options analysis system
"""

__version__ = "0.1.0"
__author__ = "QuantLab Team"

from .core.portfolio_manager import PortfolioManager
from .core.analyzer import Analyzer

__all__ = ["PortfolioManager", "Analyzer", "__version__"]
