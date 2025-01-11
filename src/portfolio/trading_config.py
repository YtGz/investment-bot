from dataclasses import dataclass

@dataclass
class TradingConfig:
    initial_investment = 13000
    core_allocation = 0.75
    dynamic_allocation = 0.25
       
    # Liquidity requirements
    min_volume_multiplier = 20  # We want daily volume to be at least 20x our max position
    max_position_size = initial_investment * dynamic_allocation
    min_daily_volume = max_position_size * min_volume_multiplier # Minimum daily volume in USD

    # Time windows
    momentum_window: int = 20        # Time series momentum window
    mean_rev_window: int = 5         # Mean reversion lookback period
    volatility_window: int = 10      # Volatility calculation window
    
    # Trading thresholds
    max_position_increase: float = 1.5  # Maximum position size multiplier
    risk_multiplier: float = 1.2     # YPF risk multiplier during uptrends
    zscore_entry: float = -1.5       # Mean reversion entry threshold
    zscore_exit: float = 1.0         # Mean reversion exit threshold
    momentum_threshold: float = 0.02  # Minimum momentum signal strength
    
    # Portfolio constraints
    max_sector_exposure: float = 0.40  # Maximum exposure to any sector
    rebalance_threshold: float = 0.10  # Minimum deviation to trigger rebalance
