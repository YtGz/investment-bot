from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
import pandas as pd
import logging

class HistoricalDataClient:
    def __init__(self, api_key: str, secret_key: str):
        self.client = StockHistoricalDataClient(api_key, secret_key)
        self.logger = logging.getLogger(__name__)

    def get_bars(self, symbol: str, days: int = 30) -> pd.DataFrame:
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Hour,
            start=(datetime.now() - timedelta(days=days)),
            end=datetime.now()
        )
        try:
            bars = self.client.get_stock_bars(request)
            return bars.df
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def check_liquidity(self, symbol: str, min_volume: int) -> bool:
        try:
            data = self.get_bars(symbol, days=5)
            if data is None:
                return False

            avg_daily_volume = data['volume'].mean() * data['close'].mean()
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self.client.get_stock_latest_quote(quote_request)
            spread = (quote[symbol].ask_price - quote[symbol].bid_price) / quote[symbol].ask_price

            return avg_daily_volume > min_volume and spread < 0.02
        except Exception as e:
            self.logger.error(f"Liquidity check failed for {symbol}: {e}")
            return False
