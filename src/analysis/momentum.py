import numpy as np
import pandas as pd
from typing import Tuple

class MomentumAnalyzer:
    def __init__(self, 
                 momentum_window: int = 20,
                 volatility_window: int = 10):
        self.momentum_window = momentum_window
        self.volatility_window = volatility_window

    def calculate_hurst_exponent(self, data: pd.Series, lags=range(2, 21)) -> float:
        """Calculate Hurst exponent to determine trend strength"""
        tau = []
        std = []
        for lag in lags:
            tau.append(lag)
            std.append(np.std(np.subtract(data[lag:], data[:-lag])))
        return np.polyfit(np.log(tau), np.log(std), 1)[0] / 2

    def calculate_signal(self, prices: pd.Series) -> Tuple[float, float, float]:
        """
        Calculate momentum signal with volatility adjustment and trend strength
        Returns: (momentum_signal, volatility, hurst_exponent)
        """
        returns = prices.pct_change()
        
        # Time series momentum
        momentum_signal = returns.rolling(self.momentum_window).mean()
        
        # Volatility calculation
        volatility = returns.rolling(self.volatility_window).std() * np.sqrt(252)
        
        # Trend strength
        hurst = self.calculate_hurst_exponent(prices)
        
        # Risk-adjusted momentum
        adjusted_signal = momentum_signal.iloc[-1] / volatility.iloc[-1]
        
        return adjusted_signal, volatility.iloc[-1], hurst

    def get_weighted_signal(self, 
                           prices: pd.Series, 
                           momentum_weight: float,
                           threshold: float = 0.02) -> float:
        """
        Get momentum signal weighted by trend strength and adjusted for risk
        """
        signal, vol, hurst = self.calculate_signal(prices)
        
        # Adjust weight based on Hurst exponent
        adjusted_weight = momentum_weight * (hurst if hurst > 0.5 else 1-hurst)
        
        # Apply threshold and weighting
        final_signal = adjusted_weight * signal if abs(signal) > threshold else 0
        
        return final_signal
