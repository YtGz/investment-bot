from alpaca.trading.client import TradingClient
import logging
import pandas as pd
from typing import Dict
import asyncio
import signal
from contextlib import AsyncExitStack
from datetime import datetime

from market_data.historical import HistoricalDataClient
from market_data.streaming import MarketDataStream
from portfolio.core import CorePortfolio
from portfolio.dynamic import TradingCandidates
from portfolio.trading_config import TradingConfig
from analysis.momentum import MomentumAnalyzer
from analysis.mean_reversion import MeanReversionAnalyzer
from analysis.signal_combiner import SignalCombiner
from trading.execution import TradeExecutor
from risk_management.position_sizing import PositionSizer
from risk_management.stop_loss import StopLossChecker
from metrics.performance import PerformanceMetrics

class TradingSystem:
    def __init__(self, api_key: str, secret_key: str, paper_trading: bool, initial_investment: float = 0):
        self.config = TradingConfig()
        
        # Initialize clients
        self.trading_client = TradingClient(api_key, secret_key, paper=paper_trading)
        self.historical_data = HistoricalDataClient(api_key, secret_key)
        self.market_stream = MarketDataStream(api_key, secret_key)
        
        # Initialize components
        self.core_portfolio = CorePortfolio()
        self.trading_candidates = TradingCandidates()
        self.momentum = MomentumAnalyzer(
            momentum_window=self.config.momentum_window,
            volatility_window=self.config.volatility_window
        )
        self.mean_reversion = MeanReversionAnalyzer(window=self.config.mean_rev_window)
        self.signal_combiner = SignalCombiner(self.momentum, self.mean_reversion)
        self.trade_executor = TradeExecutor(self.trading_client)
        self.position_sizer = PositionSizer(initial_investment)
        self.stop_loss_checker = StopLossChecker()
        self.metrics = PerformanceMetrics()
        
        PerformanceMetrics.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.trading_symbols = {}
        self.is_running = False
        self._exit_stack = AsyncExitStack()

    def _select_top_symbols(self, scores: Dict[str, float], sector_counts: Dict[str, int]) -> Dict[str, Dict]:
        selected_symbols = []
        selected_sectors = set()

        for symbol in sorted(scores, key=scores.get, reverse=True):
            sector = self.trading_candidates.candidates[symbol]['sector']
            if len(selected_symbols) >= 3:
                break
            if sector not in selected_sectors or sector_counts[sector] <= 1:
                selected_symbols.append(symbol)
                selected_sectors.add(sector)

        return self.trading_candidates.create_trading_config(selected_symbols)

    def select_trading_component(self):
        scores = {}
        sector_counts = {}
        
        for symbol in self.trading_candidates.candidates.keys():
            if not self.historical_data.check_liquidity(symbol):
                continue
                
            data = self.historical_data.get_bars(symbol)
            if data is None:
                continue
                
            momentum_signal, vol, hurst = self.momentum.calculate_signal(data['close'])
            score = (0.4 * momentum_signal / vol +
                    0.3 * (hurst - 0.5) +
                    0.3 * (1/vol))
                    
            scores[symbol] = score
            sector = self.trading_candidates.candidates[symbol]['sector']
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
            
        self.trading_symbols = self._select_top_symbols(scores, sector_counts)

    async def process_market_data(self, symbol: str, price: float):
        try:
            position = self.trading_client.get_position(symbol)
            current_price = float(position.current_price)
            entry_price = float(position.avg_entry_price)
            
            # Update position metrics
            self.metrics.update_position(symbol, current_price, float(position.qty))
            
            symbol_data = (self.core_portfolio.holdings.get(symbol) or 
                         self.trading_symbols.get(symbol))
            
            # Check stop loss and take profit
            exit_signal = self.stop_loss_checker.check_exits(
                current_price, 
                entry_price,
                symbol_data['stop_loss'],
                symbol_data['take_profit']
            )
            
            if exit_signal:
                await self.trade_executor.execute_trade(symbol, 0)
                self.metrics.log_trade(symbol, entry_price, current_price, 
                                     float(position.qty), datetime.now(), exit_signal)
                self.logger.info(f"{exit_signal} triggered for {symbol}")
                return
                
            # Calculate new position based on combined signals
            data = self.historical_data.get_bars(symbol)
            signal = self.signal_combiner.calculate_combined_signal(
                data['close'], 
                symbol, 
                symbol_data
            )
            
            target_position = self.position_sizer.calculate_position_size(
                symbol, 
                signal, 
                symbol_data
            )
            
            # Check if rebalance is needed
            current_position = float(position.qty)
            if abs(target_position - current_position) / current_position > 0.10:  # rebalance threshold
                await self.trade_executor.execute_trade(symbol, target_position)
            
        except Exception as e:
            self.logger.error(f"Error processing data for {symbol}: {e}")

    def setup_signal_handlers(self):
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._handle_shutdown)
            
    def _handle_shutdown(self, signum, frame):
        self.logger.info(f"Received shutdown signal {signum}")
        self.is_running = False
        
    async def cleanup(self):
        self.logger.info("Starting graceful shutdown...")
        await self.market_stream.close()
        await self._exit_stack.aclose()
        self.logger.info("Shutdown complete")

    async def run(self):
        """Main strategy execution loop"""
        try:
            self.setup_signal_handlers()
            self.is_running = True
            self.select_trading_component()
            all_symbols = list(self.core_portfolio.holdings.keys()) + list(self.trading_symbols.keys())
            
            async def quote_handler(data):
                if self.is_running:
                    await self.process_market_data(data.symbol, data.ask_price)
            
            async with self._exit_stack:
                await self._exit_stack.enter_async_context(self.market_stream)
                await self.market_stream.start_streaming(all_symbols, quote_handler)
                
                while self.is_running:
                    await asyncio.sleep(1)
                    
                    # Log daily performance
                    if self._is_end_of_day():
                        metrics = self.metrics.calculate_metrics()
                        self.logger.info(f"Daily performance metrics: {metrics}")
                    
        except Exception as e:
            self.logger.error(f"Strategy execution error: {e}")
            raise
        finally:
            await self.cleanup()

if __name__ == "__main__":
    initial_investment = 13000 # the initial investement in USD
    api_key = os.environ.get("API_KEY")
    secret_key = os.environ.get("API_SECRET")
    
    if not api_key or not secret_key:
        raise ValueError("API_KEY and API_SECRET environment variables must be set")
    
    is_dev = os.getenv('ENV', 'dev') == 'dev'
    trading_system = TradingSystem(api_key, secret_key, is_dev, initial_investment)
    
    try:
        asyncio.run(trading_system.run())
    except KeyboardInterrupt:
        print("Strategy execution terminated by user")
    except Exception as e:
        print(f"Fatal error: {e}")
