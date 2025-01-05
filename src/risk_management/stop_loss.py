from dataclasses import dataclass
from typing import Optional

@dataclass
class StopLossChecker:
    def check_exits(self, current_price: float, entry_price: float, 
                   stop_loss: float, take_profit: float) -> Optional[str]:
        returns = (current_price - entry_price) / entry_price
        
        if returns < -stop_loss:
            return "stop_loss"
        elif returns > take_profit:
            return "take_profit"
        
        return None
