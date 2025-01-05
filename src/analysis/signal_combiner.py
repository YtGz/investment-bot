from typing import Dict
import pandas as pd
from .momentum import MomentumAnalyzer
from .mean_reversion import MeanReversionAnalyzer

class SignalCombiner:
    def __init__(self, momentum_analyzer: MomentumAnalyzer, mean_rev_analyzer: MeanReversionAnalyzer):
        self.momentum_analyzer = momentum_analyzer
        self.mean_rev_analyzer = mean_rev_analyzer

    def calculate_combined_signal(self, 
                                prices: pd.Series,
                                symbol: str,
                                symbol_data: Dict,
                                risk_multiplier: float = 1.2,
                                momentum_threshold: float = 0.02) -> float:
        """Combines momentum and mean reversion signals with YPF-specific adjustments"""
        
        # Get individual signals
        momentum_signal, _, hurst = self.momentum_analyzer.calculate_signal(prices)
        mean_rev_signal = self.mean_rev_analyzer.get_signal(prices)
        
        # Adjust weights based on Hurst exponent
        momentum_weight = symbol_data['momentum_weight'] * (hurst if hurst > 0.5 else 1-hurst)
        mean_rev_weight = symbol_data['mean_rev_weight'] * (1-hurst if hurst > 0.5 else hurst)
        
        # Combine signals
        combined_signal = (momentum_weight * momentum_signal +
                         mean_rev_weight * mean_rev_signal)
        
        # YPF-specific adjustment
        if symbol == 'YPF' and momentum_signal > momentum_threshold:
            combined_signal *= risk_multiplier
            
        return combined_signal
