from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import pandas as pd
from pathlib import Path

@dataclass
class PerformanceMetrics:
    """
    This implementation tracks key performance metrics including:

        - Trade-level P&L
        - Win rate
        - Average win/loss
        - Sharpe ratio
        - Maximum drawdown
        - Position tracking

    The metrics are logged daily and can be used for strategy evaluation and optimization.
    """
    trades: List[Dict] = field(default_factory=list)
    daily_returns: Dict[datetime, float] = field(default_factory=dict)
    positions: Dict[str, Dict] = field(default_factory=dict)

    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)

    def log_trade(self, symbol: str, entry_price: float, exit_price: float, 
                  quantity: float, timestamp: datetime, exit_reason: str):
        trade = {
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'pnl': (exit_price - entry_price) * quantity,
            'timestamp': timestamp,
            'exit_reason': exit_reason
        }
        self.trades.append(trade)

    def update_position(self, symbol: str, price: float, quantity: float):
        self.positions[symbol] = {
            'price': price,
            'quantity': quantity,
            'timestamp': datetime.now()
        }

    def calculate_metrics(self) -> Dict:
        df = pd.DataFrame(self.trades)
        return {
            'total_pnl': df['pnl'].sum(),
            'win_rate': len(df[df['pnl'] > 0]) / len(df) if len(df) > 0 else 0,
            'avg_win': df[df['pnl'] > 0]['pnl'].mean(),
            'avg_loss': df[df['pnl'] < 0]['pnl'].mean(),
            'sharpe_ratio': self._calculate_sharpe_ratio(),
            'max_drawdown': self._calculate_max_drawdown()
        }

    def _calculate_sharpe_ratio(self) -> float:
        returns = pd.Series(self.daily_returns)
        return returns.mean() / returns.std() * (252 ** 0.5) if len(returns) > 0 else 0

    def _calculate_max_drawdown(self) -> float:
        cumulative = pd.Series(self.daily_returns).cumsum()
        rolling_max = cumulative.expanding().max()
        drawdowns = cumulative - rolling_max
        return drawdowns.min()

    @staticmethod
    def setup_logging():
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"logs/trading_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler()
            ]
        )
