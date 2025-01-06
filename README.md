# Argentina Investment Bot

An automated trading system focused on Argentine stocks using momentum and mean reversion strategies.

## How to Use

### Development

Create a new token for the alpaca trading bot machine user in [Infisical](https://infisical.datawarp.dev/org/35374e20-0b45-4a16-afd4-7ea72161ab8a/identities/3879a90a-53df-4c01-894b-988c2a911cd5) (cf. step 2 of https://infisical.com/docs/documentation/platform/identities/token-auth#guide).

```fish
fish --private
set -gx INFISICAL_TOKEN_TRADING_BOT <token>
docker compose -f docker-compose.dev.yml watch
```

### Production

```
fish --private
set -gx INFISICAL_TOKEN_TRADING_BOT <token>
docker compose -f docker-compose.prod.yml up --build
```

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
