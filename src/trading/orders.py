from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dataclasses import dataclass

@dataclass
class OrderCreator:
    def create_market_order(self, symbol: str, qty: float, side: OrderSide) -> MarketOrderRequest:
        return MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY
        )
