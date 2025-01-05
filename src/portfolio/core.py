from dataclasses import dataclass
from typing import Dict

@dataclass
class CorePortfolio:
    """Core holdings representing 70-75% of the portfolio"""
    holdings: Dict[str, dict] = None

    def __post_init__(self):
        # Asymmetric stop-loss and take-profit levels:
        # Due to research showing that momentum strategies have frequent small losses but larger potential gains
        self.holdings = {
            'YPF': {
                'target_allocation': 0.35,
                'sector': 'energy',
                'momentum_weight': 0.8,  # Higher momentum weight for YPF
                'mean_rev_weight': 0.2,
                'stop_loss': 0.15,       # Wider stop for core position
                'take_profit': 0.30      # 2:1 reward-risk ratio based on momentum characteristics
            },
            'BBVA': {
                'target_allocation': 0.25,
                'sector': 'banking',
                'momentum_weight': 0.7,  # Balanced but momentum-leaning
                'mean_rev_weight': 0.3,
                'stop_loss': 0.12,       # Slightly tighter than YPF due to lower conviction
                'take_profit': 0.25
            },
            'CRESY': {
                'target_allocation': 0.08,
                'sector': 'agriculture',
                'momentum_weight': 0.6,
                'mean_rev_weight': 0.4,
                'stop_loss': 0.10,
                'take_profit': 0.20
            },
            'PAM': {
                'target_allocation': 0.07,
                'sector': 'energy',
                'momentum_weight': 0.6,
                'mean_rev_weight': 0.4,
                'stop_loss': 0.10,
                'take_profit': 0.20
            }
        }
