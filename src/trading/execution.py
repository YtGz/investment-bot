from alpaca.trading.client import TradingClient
from .orders import OrderCreator
from alpaca.trading.enums import OrderSide
import logging

class TradeExecutor:
    def __init__(self, trading_client: TradingClient):
        self.trading_client = trading_client
        self.order_creator = OrderCreator()
        self.fee_calculator = FeeCalculator()
        self.logger = logging.getLogger(__name__)

    async def execute_trade(self, symbol: str, target_position: float):
        try:
            current_position = 0
            try:
                position = self.trading_client.get_position(symbol)
                current_position = float(position.qty)
            except:
                pass

            if target_position != current_position:
                order_side = OrderSide.BUY if target_position > current_position else OrderSide.SELL
                qty = abs(target_position - current_position)
                
                order = self.order_creator.create_market_order(symbol, qty, order_side)
                self.trading_client.submit_order(order_data=order)
                self.logger.info(f"Executed {order_side} order for {symbol}: {qty} shares")

        except Exception as e:
            self.logger.error(f"Trade execution error for {symbol}: {e}")
