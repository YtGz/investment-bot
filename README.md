# Argentina Investment Bot

An automated trading system focused on Argentine stocks using momentum and mean reversion strategies.

## Project Structure

```
src/
├── portfolio/
│   ├── core.py              # The main stocks we always want to hold (like YPF, BBVA) with their target percentages
│   └── dynamic.py           # Stocks we trade in and out of based on market conditions
├── risk_management/
│   ├── position_sizing.py   # How much money to put in each stock
│   └── stop_loss.py         # When to sell to prevent big losses
├── market_data/
│   ├── historical.py        # Gets past price data to make decisions
│   └── streaming.py         # Gets real-time price updates
├── analysis/
│   ├── momentum.py          # Finds stocks that are trending up strongly
│   └── mean_reversion.py    # Finds stocks that have temporarily moved away from their average price
└── trading/
    ├── execution.py         # Handles the actual buying and selling
    └── orders.py            # Creates the buy/sell orders with specific quantities
```

## Components Explained

### Portfolio Management
- **Core Holdings**: Main stocks that form the foundation of the portfolio (70-75% allocation)
- **Dynamic Trading**: Additional stocks traded based on market opportunities (25-30% allocation)

### Risk Management
- Position sizing rules to determine investment amounts
- Stop-loss mechanisms to protect against significant losses

### Market Data
- Historical price data analysis
- Real-time price streaming and monitoring

### Analysis
- Momentum strategy: Identifies stocks in strong upward trends
- Mean reversion strategy: Spots stocks that have temporarily deviated from their average price

### Trading
- Order execution system
- Position management and rebalancing
