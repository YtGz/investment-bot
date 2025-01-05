from alpaca.data.live import StockDataStream
import logging
from typing import Callable, List

class MarketDataStream:
    def __init__(self, api_key: str, secret_key: str):
        self.stream_client = StockDataStream(api_key, secret_key)
        self.logger = logging.getLogger(__name__)

    async def start_streaming(self, symbols: List[str], handler: Callable):
        try:
            self.stream_client.subscribe_quotes(handler, symbols)
            await self.stream_client.run()
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
            raise
