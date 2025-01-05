from dataclasses import dataclass
from typing import Dict

@dataclass
class TradingCandidates:
    """Trading component representing 25-30% of the portfolio"""
    candidates: Dict[str, dict] = None

    def __post_init__(self):
        self.candidates = {
            # Banking & Financial Services
            'GGAL': {'sector': 'banking'},     # Grupo Financiero Galicia
            'BMA': {'sector': 'banking'},      # Banco Macro
            'SUPV': {'sector': 'banking'},     # Grupo Supervielle
            'BBAR': {'sector': 'banking'},     # BBVA Banco Francés

            # Technology & Telecommunications
            'TEO': {'sector': 'technology'},   # Telecom Argentina
            'GLOB': {'sector': 'technology'},  # Globant

            # Energy & Utilities
            'CEPU': {'sector': 'energy'},      # Central Puerto
            'EDN': {'sector': 'energy'},       # Edenor
            'TGS': {'sector': 'energy'},       # Transportadora de Gas del Sur

            # Agriculture & Commodities
            'AGRO': {'sector': 'agriculture'}, # Adecoagro

            # Real Estate & Construction
            'IRCP': {'sector': 'real_estate'}, # IRSA Propiedades Comerciales
            'IRS': {'sector': 'real_estate'},  # IRSA Inversiones

            # Industrial & Manufacturing
            'LOMA': {'sector': 'industrial'},  # Loma Negra
            'TS': {'sector': 'industrial'},    # Tenaris

            # Consumer & Retail
            'ARCO': {'sector': 'consumer'},    # Arcos Dorados
            'MELI': {'sector': 'consumer'}     # MercadoLibre
        }

    def create_trading_config(self, selected_symbols: list) -> Dict[str, Dict]:
        # Trading Component (25-30%) with tighter stops
        # Research indicates mean reversion strategies benefit from tighter stops
        # due to their higher-frequency nature
        return {
            symbol: {
                'target_allocation': 0.08,
                'momentum_weight': 0.5,         # Equal weight as per research on combined strategies
                'mean_rev_weight': 0.5,
                'stop_loss': 0.08,              # Tighter stops for mean reversion component
                'take_profit': 0.15             # Still maintaining positive risk-reward ratio
            } for symbol in selected_symbols
        }