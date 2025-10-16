"""
Advanced Greeks Calculator using Black-Scholes Model
Calculates Vanna, Charm, and Vomma for options
"""

import numpy as np
from scipy.stats import norm
from datetime import datetime

class BlackScholesGreeks:
    """Calculate first and second order Greeks using Black-Scholes model"""

    @staticmethod
    def days_to_expiry(expiry_date_str):
        """Calculate days to expiry from date string"""
        try:
            expiry = datetime.strptime(expiry_date_str[:10], '%Y-%m-%d')
            today = datetime.now()
            days = (expiry - today).days
            return max(days, 1)  # At least 1 day
        except:
            return 30  # Default to 30 days if parsing fails

    @staticmethod
    def d1(S, K, T, r, sigma):
        """Calculate d1 in Black-Scholes formula"""
        return (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))

    @staticmethod
    def d2(S, K, T, r, sigma):
        """Calculate d2 in Black-Scholes formula"""
        return BlackScholesGreeks.d1(S, K, T, r, sigma) - sigma*np.sqrt(T)

    @staticmethod
    def delta_call(S, K, T, r, sigma):
        """Calculate Delta for call option"""
        return norm.cdf(BlackScholesGreeks.d1(S, K, T, r, sigma))

    @staticmethod
    def delta_put(S, K, T, r, sigma):
        """Calculate Delta for put option"""
        return BlackScholesGreeks.delta_call(S, K, T, r, sigma) - 1

    @staticmethod
    def gamma(S, K, T, r, sigma):
        """Calculate Gamma (same for call and put)"""
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))

    @staticmethod
    def vega(S, K, T, r, sigma):
        """Calculate Vega (same for call and put) - per 1% change in vol"""
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        return S * norm.pdf(d1) * np.sqrt(T) / 100

    @staticmethod
    def theta_call(S, K, T, r, sigma):
        """Calculate Theta for call option - per day"""
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        term2 = -r * K * np.exp(-r*T) * norm.cdf(d2)

        return (term1 + term2) / 365  # Convert to per day

    @staticmethod
    def theta_put(S, K, T, r, sigma):
        """Calculate Theta for put option - per day"""
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        term2 = r * K * np.exp(-r*T) * norm.cdf(-d2)

        return (term1 + term2) / 365  # Convert to per day

    # ===== ADVANCED GREEKS =====

    @staticmethod
    def vanna(S, K, T, r, sigma):
        """
        Calculate Vanna: ∂Delta/∂σ or ∂Vega/∂S
        Sensitivity of delta to changes in implied volatility
        Same for calls and puts
        """
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        vanna = -norm.pdf(d1) * d2 / sigma

        return vanna / 100  # Per 1% change in volatility

    @staticmethod
    def charm_call(S, K, T, r, sigma):
        """
        Calculate Charm for calls: ∂Delta/∂t
        Rate of change of delta over time (delta decay)
        Also known as DdeltaDtime
        """
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        charm = -norm.pdf(d1) * (2*r*T - d2*sigma*np.sqrt(T)) / (2*T*sigma*np.sqrt(T))

        return charm / 365  # Per day

    @staticmethod
    def charm_put(S, K, T, r, sigma):
        """
        Calculate Charm for puts: ∂Delta/∂t
        """
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        charm = norm.pdf(d1) * (2*r*T - d2*sigma*np.sqrt(T)) / (2*T*sigma*np.sqrt(T))

        return charm / 365  # Per day

    @staticmethod
    def vomma(S, K, T, r, sigma):
        """
        Calculate Vomma (Volga): ∂Vega/∂σ
        Sensitivity of vega to changes in implied volatility
        Same for calls and puts
        Also known as DvegaDvol
        """
        d1 = BlackScholesGreeks.d1(S, K, T, r, sigma)
        d2 = BlackScholesGreeks.d2(S, K, T, r, sigma)

        vomma = S * norm.pdf(d1) * np.sqrt(T) * d1 * d2 / sigma

        return vomma / 10000  # Per 1% change in volatility squared


def calculate_advanced_greeks_for_option(S, K, T_days, r, sigma, option_type='call'):
    """
    Calculate all Greeks including advanced ones for a single option

    Parameters:
    -----------
    S : float - Current stock price
    K : float - Strike price
    T_days : int - Days to expiration
    r : float - Risk-free rate (annualized)
    sigma : float - Implied volatility (as decimal, e.g., 0.40 for 40%)
    option_type : str - 'call' or 'put'

    Returns:
    --------
    dict with all Greeks
    """

    T = T_days / 365.0  # Convert to years
    bs = BlackScholesGreeks()

    greeks = {
        # First-order Greeks
        'delta': bs.delta_call(S, K, T, r, sigma) if option_type == 'call' else bs.delta_put(S, K, T, r, sigma),
        'gamma': bs.gamma(S, K, T, r, sigma),
        'vega': bs.vega(S, K, T, r, sigma),
        'theta': bs.theta_call(S, K, T, r, sigma) if option_type == 'call' else bs.theta_put(S, K, T, r, sigma),

        # Second-order Greeks (Advanced)
        'vanna': bs.vanna(S, K, T, r, sigma),
        'charm': bs.charm_call(S, K, T, r, sigma) if option_type == 'call' else bs.charm_put(S, K, T, r, sigma),
        'vomma': bs.vomma(S, K, T, r, sigma),
    }

    return greeks


if __name__ == "__main__":
    # Test with example option
    S = 251.71  # GOOG current price
    K = 250.00  # Strike
    T_days = 2  # Days to expiry
    r = 0.045  # Risk-free rate (4.5%)
    sigma = 0.42  # 42% IV

    print("="*80)
    print("TESTING ADVANCED GREEKS CALCULATOR")
    print("="*80)

    print(f"\nOption Details:")
    print(f"  Stock Price: ${S:.2f}")
    print(f"  Strike: ${K:.2f}")
    print(f"  Days to Expiry: {T_days}")
    print(f"  IV: {sigma*100:.1f}%")
    print(f"  Risk-free rate: {r*100:.2f}%")

    call_greeks = calculate_advanced_greeks_for_option(S, K, T_days, r, sigma, 'call')

    print(f"\n{'='*80}")
    print("CALL OPTION GREEKS")
    print("="*80)

    print(f"\nFirst-Order Greeks:")
    print(f"  Delta:  {call_greeks['delta']:.4f}")
    print(f"  Gamma:  {call_greeks['gamma']:.4f}")
    print(f"  Vega:   {call_greeks['vega']:.4f} (per 1% vol change)")
    print(f"  Theta:  {call_greeks['theta']:.4f} (per day)")

    print(f"\nAdvanced Greeks:")
    print(f"  Vanna:  {call_greeks['vanna']:.6f} (∂Delta/∂σ per 1%)")
    print(f"  Charm:  {call_greeks['charm']:.6f} (∂Delta/∂t per day)")
    print(f"  Vomma:  {call_greeks['vomma']:.6f} (∂Vega/∂σ)")

    print(f"\n{'='*80}")
    print("INTERPRETATION")
    print("="*80)

    print(f"\nVanna = {call_greeks['vanna']:.6f}")
    print(f"  → If IV increases by 1%, delta will change by {call_greeks['vanna']:.6f}")
    print(f"  → {'Positive' if call_greeks['vanna'] > 0 else 'Negative'} vanna means delta {'increases' if call_greeks['vanna'] > 0 else 'decreases'} when vol rises")

    print(f"\nCharm = {call_greeks['charm']:.6f}")
    print(f"  → Delta will change by {call_greeks['charm']:.6f} per day (time decay of delta)")
    print(f"  → Each day, delta moves {'toward' if call_greeks['charm'] < 0 else 'away from'} 0")

    print(f"\nVomma = {call_greeks['vomma']:.6f}")
    print(f"  → If IV increases by 1%, vega will change by {call_greeks['vomma']:.6f}")
    print(f"  → {'Positive' if call_greeks['vomma'] > 0 else 'Negative'} vomma means vega exposure {'increases' if call_greeks['vomma'] > 0 else 'decreases'} when vol rises")
