class PositionSizer:
    def __init__(self, initial_investment: float, max_position_increase: float = 1.5):
        self.initial_investment = initial_investment
        self.max_position_increase = max_position_increase

    def calculate_position_size(self, symbol: str, signal: float, symbol_data: dict) -> float:
        """
        Calculate position size based on:
        - Base allocation from symbol data
        - Signal strength
        - Maximum position size constraints
        """
        base_size = self.initial_investment * symbol_data['target_allocation']
        signal_adjustment = min(abs(signal), self.max_position_increase)
        
        return base_size * signal_adjustment
