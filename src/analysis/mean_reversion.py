import numpy as np
import pandas as pd

class MeanReversionAnalyzer:
    def __init__(self, window: int = 5):
        self.window = window

    def get_signal(self, prices: pd.Series, zscore_entry: float = -1.5) -> float:
        """Calculate mean reversion signal using z-score"""
        ma = prices.rolling(self.window).mean()
        std = prices.rolling(self.window).std()
        zscore = (prices - ma) / std
        
        return -zscore.iloc[-1]  # Negative zscore for mean reversion signal
