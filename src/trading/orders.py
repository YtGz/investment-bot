from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class OrderCreator:
    def __init__(self):
        self.fee_calculator = FeeCalculator()
        
    def create_market_order(self, symbol: str, qty: float, side: OrderSide, price: float) -> MarketOrderRequest:
        # Calculate fees for sell orders
        if side == OrderSide.SELL:
            fees = self.fee_calculator.calculate_sell_fees(price * qty, qty)
            # Adjust quantity to account for fees if needed
            qty = self._adjust_quantity_for_fees(qty, price, fees)
            
        return MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY)

