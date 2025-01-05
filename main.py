from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetAssetsRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.live import StockDataStream
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import asyncio
import logging

class ArgentinaTrader:
    def __init__(self, api_key, secret_key, initial_investment=13000, paper=True):
        self.trading_client = TradingClient(api_key, secret_key, paper=paper)
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
        self.stream_client = StockDataStream(api_key, secret_key)
        self.initial_investment = initial_investment

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Core Holdings (70-75%)
        # Asymmetric stop-loss and take-profit levels:
        # Due to research showing that momentum strategies have frequent small losses but larger potential gains
        self.core_symbols = {
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

        # Trading Component (25-30%) with tighter stops
        # Research indicates mean reversion strategies benefit from tighter stops
        # due to their higher-frequency nature
        self.trading_candidates = {
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

        self.trading_symbols = {}  # Will be populated dynamically

        # Strategy parameters based on research
        self.params = {
            'momentum_window': 20,        # Time series momentum window 【1】
            'mean_rev_window': 5,         # Mean reversion lookback period 【2】
            'volatility_window': 10,      # Volatility calculation window
            'min_daily_volume': 500000,   # Minimum daily volume in USD
            'max_position_increase': 1.5,  # Maximum position size multiplier
            'risk_multiplier': 1.2,       # YPF risk multiplier during uptrends
            'zscore_entry': -1.5,         # Mean reversion entry threshold 【3】
            'zscore_exit': 1.0,           # Mean reversion exit threshold
            'momentum_threshold': 0.02,    # Minimum momentum signal strength 【4】
            'max_sector_exposure': 0.40,   # Maximum exposure to any sector
            'rebalance_threshold': 0.10    # Minimum deviation to trigger rebalance
        }

    def calculate_hurst_exponent(self, data, lags=range(2, 21)):
        """Calculate Hurst exponent to determine trend strength"""
        tau = []
        std = []
        for lag in lags:
            tau.append(lag)
            std.append(np.std(np.subtract(data[lag:], data[:-lag])))
        return np.polyfit(np.log(tau), np.log(std), 1)[0] / 2

    def get_historical_data(self, symbol, days=30):
        """Get historical bar data with enhanced error handling"""
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Hour,
                start=(datetime.now() - timedelta(days=days)),
                end=datetime.now()
            )
            bars = self.data_client.get_stock_bars(request)
            return bars.df
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def check_liquidity(self, symbol):
        """Enhanced liquidity check using volume and spread"""
        try:
            data = self.get_historical_data(symbol, days=5)
            if data is None:
                return False

            avg_daily_volume = data['volume'].mean() * data['close'].mean()

            quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self.data_client.get_stock_latest_quote(quote_request)
            spread = (quote[symbol].ask_price - quote[symbol].bid_price) / quote[symbol].ask_price

            return (avg_daily_volume > self.params['min_daily_volume'] and 
                   spread < 0.02)
        except Exception as e:
            self.logger.error(f"Liquidity check failed for {symbol}: {e}")
            return False

    def select_trading_component(self):
        """Dynamically select trading component stocks"""
        scores = {}
        sector_counts = {}

        for symbol in self.trading_candidates.keys():
            if not self.check_liquidity(symbol):
                continue

            data = self.get_historical_data(symbol, days=30)
            if data is None:
                continue

            # Calculate multiple metrics
            returns = data['close'].pct_change()
            volatility = returns.std() * np.sqrt(252)
            momentum = returns.rolling(self.params['momentum_window']).mean().iloc[-1]
            hurst = self.calculate_hurst_exponent(data['close'])

            # Combine metrics into a single score
            score = (0.4 * momentum / volatility +  # Risk-adjusted momentum
                    0.3 * (hurst - 0.5) +          # Trend strength
                    0.3 * (1/volatility))          # Liquidity preference

            scores[symbol] = score
            sector_counts[self.trading_candidates[symbol]['sector']] = \
                sector_counts.get(self.trading_candidates[symbol]['sector'], 0) + 1

        # Select top stocks while maintaining sector diversity
        selected_symbols = []
        selected_sectors = set()

        for symbol in sorted(scores, key=scores.get, reverse=True):
            sector = self.trading_candidates[symbol]['sector']
            if len(selected_symbols) >= 3:
                break
            if sector not in selected_sectors or sector_counts[sector] <= 1:
                selected_symbols.append(symbol)
                selected_sectors.add(sector)

        # Update trading symbols with selected stocks
        self.trading_symbols = {
            # Trading Component (25-30%) with tighter stops
            # Research indicates mean reversion strategies benefit from tighter stops
            # due to their higher-frequency nature
            symbol: {
                'target_allocation': 0.08,
                'momentum_weight': 0.5,         # Equal weight as per research on combined strategies
                'mean_rev_weight': 0.5,
                'stop_loss': 0.08,              # Tighter stops for mean reversion component
                'take_profit': 0.15             # Still maintaining positive risk-reward ratio
            } for symbol in selected_symbols
        }

    def calculate_signals(self, symbol):
        """Calculate trading signals with enhanced momentum and mean reversion"""
        data = self.get_historical_data(symbol)
        if data is None:
            return 0

        # Time series momentum signal
        returns = data['close'].pct_change()
        momentum_signal = returns.rolling(self.params['momentum_window']).mean()

        # Mean reversion signal with dynamic thresholds
        price = data['close']
        ma = price.rolling(self.params['mean_rev_window']).mean()
        std = price.rolling(self.params['mean_rev_window']).std()
        zscore = (price - ma) / std

        # Calculate Hurst exponent for adaptive signal weighting
        hurst = self.calculate_hurst_exponent(price)

        # Adjust weights based on Hurst exponent
        if symbol in self.core_symbols:
            symbol_data = self.core_symbols[symbol]
        else:
            symbol_data = self.trading_symbols[symbol]

        momentum_weight = symbol_data['momentum_weight'] * (hurst if hurst > 0.5 else 1-hurst)
        mean_rev_weight = symbol_data['mean_rev_weight'] * (1-hurst if hurst > 0.5 else hurst)

        # Combine signals
        combined_signal = (momentum_weight * momentum_signal.iloc[-1] +
                         mean_rev_weight * (-zscore.iloc[-1]))

        # Apply YPF-specific adjustments
        if symbol == 'YPF' and momentum_signal.iloc[-1] > self.params['momentum_threshold']:
            combined_signal *= self.params['risk_multiplier']

        return combined_signal

    async def process_real_time_data(self, symbol, price):
        """
        Process real-time price updates and execute trades with research-based risk management

        Key insights from research:
        - Momentum strategies: Higher frequency of negative returns but larger positive returns
        - Mean reversion: More frequent but smaller positive returns
        - Combined approach: Better risk-adjusted returns than either strategy alone
        """
        try:
            position = self.trading_client.get_position(symbol)
            current_price = float(position.current_price)
            entry_price = float(position.avg_entry_price)

            # Check stop loss and take profit
            symbol_data = self.core_symbols.get(symbol) or self.trading_symbols.get(symbol)
            stop_loss = symbol_data['stop_loss']
            take_profit = symbol_data['take_profit']

            returns = (current_price - entry_price) / entry_price

            # Implement asymmetric stop-loss and take-profit based on strategy type
            if returns < -stop_loss:
                # Exit on stop-loss hit - research shows importance of strict risk management 【1】
                await self.execute_trade(symbol, 0)
                self.logger.info(f"Stop-loss triggered for {symbol} at {returns:.2%}")
                return
            elif returns > take_profit:
                # Take profit at larger gains for momentum positions
                await self.execute_trade(symbol, 0)
                self.logger.info(f"Take-profit triggered for {symbol} at {returns:.2%}")
                return

            # Calculate new position size based on combined signals
            signal = self.calculate_signals(symbol)
            target_position = self.calculate_position_size(symbol, signal)

            # Implement rebalancing threshold to avoid excessive trading
            if abs(float(position.qty) - target_position) / float(position.qty) > \
               self.params['rebalance_threshold']:
                await self.execute_trade(symbol, target_position)

        except Exception as e:
            self.logger.error(f"Error processing real-time data for {symbol}: {e}")

    async def execute_trade(self, symbol, target_position):
        """Execute trade with position sizing and risk management"""
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

                order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=order_side,
                    time_in_force=TimeInForce.DAY
                )

                self.trading_client.submit_order(order_data=order_data)
                self.logger.info(f"Executed {order_side} order for {symbol}: {qty} shares")

        except Exception as e:
            self.logger.error(f"Trade execution error for {symbol}: {e}")

    async def run_strategy(self):
        """Main strategy execution loop"""
        try:
            # Update trading component selection
            self.select_trading_component()

            # Start streaming quotes
            all_symbols = list(self.core_symbols.keys()) + list(self.trading_symbols.keys())

            async def quote_handler(data):
                symbol = data.symbol
                price = data.ask_price
                await self.process_real_time_data(symbol, price)

            self.stream_client.subscribe_quotes(quote_handler, all_symbols)
            await self.stream_client.run()

        except Exception as e:
            self.logger.error(f"Strategy execution error: {e}")
            raise

def main():
    """Main function to run the trading strategy"""
    api_key = "YOUR_API_KEY"
    secret_key = "YOUR_SECRET_KEY"

    trader = ArgentinaTrader(api_key, secret_key, initial_investment=13000)

    try:
        asyncio.run(trader.run_strategy())
    except KeyboardInterrupt:
        print("Strategy execution terminated by user")
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
