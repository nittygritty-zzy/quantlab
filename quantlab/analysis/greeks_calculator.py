"""
Advanced Greeks Calculator using Black-Scholes Model

Calculates first-order Greeks (Delta, Gamma, Theta, Vega) and
second-order Greeks (Vanna, Charm, Vomma) for options.
"""

import numpy as np
from scipy.stats import norm
from datetime import datetime, date
from typing import Dict, Union

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class BlackScholesGreeks:
    """Calculate first and second order Greeks using Black-Scholes model"""

    @staticmethod
    def days_to_expiry(expiry_date: Union[str, date]) -> int:
        """
        Calculate days to expiry from date

        Args:
            expiry_date: Expiration date as string (YYYY-MM-DD) or date object

        Returns:
            Number of days to expiry (minimum 1)
        """
        try:
            if isinstance(expiry_date, str):
                expiry = datetime.strptime(expiry_date[:10], '%Y-%m-%d').date()
            else:
                expiry = expiry_date

            today = datetime.now().date()
            days = (expiry - today).days
            return max(days, 1)  # At least 1 day
        except Exception as e:
            logger.warning(f"Failed to parse expiry date: {e}, using 30 days")
            return 30  # Default to 30 days if parsing fails

    @staticmethod
    def d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1 in Black-Scholes formula"""
        return (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))

    @staticmethod
    def d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d2 in Black-Scholes formula"""
        return BlackScholesGreeks.d1(S, K, T, r, sigma) - sigma*np.sqrt(T)

    @staticmethod
    def delta_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Delta for call option"""
        return norm.cdf(BlackScholesGreeks.d1(S, K, T, r, sigma))

    @staticmethod
    def delta_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Delta for put option"""
        return BlackScholesGreeks.delta_call(S, K, T, r, sigma) - 1

    @staticmethod
    def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Gamma (same for call and put)"""
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))

    @staticmethod
    def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Vega (same for call and put) - per 1% change in vol"""
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        return S * norm.pdf(d1) * np.sqrt(T) / 100

    @staticmethod
    def theta_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Theta for call option - per day"""
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        term2 = -r * K * np.exp(-r*T) * norm.cdf(d2)

        return (term1 + term2) / 365  # Convert to per day

    @staticmethod
    def theta_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Theta for put option - per day"""
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        term2 = r * K * np.exp(-r*T) * norm.cdf(-d2)

        return (term1 + term2) / 365  # Convert to per day

    # ===== ADVANCED GREEKS =====

    @staticmethod
    def vanna(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate Vanna: ∂Delta/∂σ or ∂Vega/∂S

        Sensitivity of delta to changes in implied volatility.
        Same for calls and puts.

        Returns: Vanna per 1% change in volatility
        """
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        vanna = -norm.pdf(d1) * d2 / sigma

        return vanna / 100  # Per 1% change in volatility

    @staticmethod
    def charm_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate Charm for calls: ∂Delta/∂t

        Rate of change of delta over time (delta decay).
        Also known as DdeltaDtime.

        Returns: Charm per day
        """
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        charm = -norm.pdf(d1) * (2*r*T - d2*sigma*np.sqrt(T)) / (2*T*sigma*np.sqrt(T))

        return charm / 365  # Per day

    @staticmethod
    def charm_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate Charm for puts: ∂Delta/∂t

        Returns: Charm per day
        """
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        charm = norm.pdf(d1) * (2*r*T - d2*sigma*np.sqrt(T)) / (2*T*sigma*np.sqrt(T))

        return charm / 365  # Per day

    @staticmethod
    def vomma(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate Vomma (Volga): ∂Vega/∂σ

        Sensitivity of vega to changes in implied volatility.
        Same for calls and puts. Also known as DvegaDvol.

        Returns: Vomma per 1% change in volatility squared
        """
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        vomma = S * norm.pdf(d1) * np.sqrt(T) * d1 * d2 / sigma

        return vomma / 10000  # Per 1% change in volatility squared


def calculate_advanced_greeks(
    stock_price: float,
    strike_price: float,
    days_to_expiry: int,
    risk_free_rate: float,
    implied_volatility: float,
    option_type: str = 'call'
) -> Dict[str, float]:
    """
    Calculate all Greeks including advanced ones for a single option

    Args:
        stock_price: Current stock price
        strike_price: Option strike price
        days_to_expiry: Days until expiration
        risk_free_rate: Risk-free rate (annualized, as decimal)
        implied_volatility: Implied volatility (as decimal, e.g., 0.40 for 40%)
        option_type: 'call' or 'put'

    Returns:
        Dictionary with all Greeks (delta, gamma, vega, theta, vanna, charm, vomma)
    """
    try:
        T = days_to_expiry / 365.0  # Convert to years
        bs = BlackScholesGreeks()

        greeks = {
            # First-order Greeks
            'delta': bs.delta_call(stock_price, strike_price, T, risk_free_rate, implied_volatility)
                     if option_type == 'call'
                     else bs.delta_put(stock_price, strike_price, T, risk_free_rate, implied_volatility),
            'gamma': bs.gamma(stock_price, strike_price, T, risk_free_rate, implied_volatility),
            'vega': bs.vega(stock_price, strike_price, T, risk_free_rate, implied_volatility),
            'theta': bs.theta_call(stock_price, strike_price, T, risk_free_rate, implied_volatility)
                     if option_type == 'call'
                     else bs.theta_put(stock_price, strike_price, T, risk_free_rate, implied_volatility),

            # Second-order Greeks (Advanced)
            'vanna': bs.vanna(stock_price, strike_price, T, risk_free_rate, implied_volatility),
            'charm': bs.charm_call(stock_price, strike_price, T, risk_free_rate, implied_volatility)
                     if option_type == 'call'
                     else bs.charm_put(stock_price, strike_price, T, risk_free_rate, implied_volatility),
            'vomma': bs.vomma(stock_price, strike_price, T, risk_free_rate, implied_volatility),
        }

        return greeks

    except Exception as e:
        logger.error(f"Failed to calculate Greeks: {e}")
        return {}
