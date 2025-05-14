# Crypto Arbitrage Bot

This project implements a cryptocurrency arbitrage trading bot that exploits price differences between exchanges to generate potential profit. The bot monitors selected trading pairs and identifies arbitrage opportunities in real time.


## Academic Context
This project was developed as part of the completion of the BSc degree at the University of Sussex. The accompanying dissertation is included in this repository and provides a comprehensive explanation of the system.

## Dissertation Coverage
For a deeper understanding of the project, please refer to the attached `Final_Report.pdf`, which includes:
- Bot architecture and design
- Implementation details
- Outputs
- Limitations and challenges
- Suggestions for further development



## Project Structure

```
.
├── arbitrage_finder.py        # Core arbitrage simulation logic
├── binance_rest.py            # Periodic Binance REST fee updater
├── binance_websocket.py       # Binance WebSocket handler
├── email_notification.py      # Sends email alerts for profitable trades
├── group_symbols.py           # Symbol mapping, grouping, and formatting
├── okx_rest.py                # Periodic OKX REST fee updater
├── okx_websocket.py           # OKX WebSocket handler
├── price_updater.py           # Main orchestration of all processes
├── symbols_updated.json       # Live symbol metadata (auto-saved)
├── usdt_network.json          # Withdrawal fee data for USDT (auto-saved)
├── arbitrage_opportunities.csv# Log of arbitrage opportunities found
```

## Features

- **Live Order Book & Price Updates**  
  Uses Binance and OKX WebSockets for real-time price and order depth data.

-  **Arbitrage Simulation Engine**  
  Considers:
  - Maker/taker trading fees  
  - Withdrawal network costs  
  - Order book liquidity  
  - Budget constraints  

- **Email Alerts**  
  Notifies the user with details of the most profitable trade opportunity.

- **Smart Network Selection**  
  Finds the cheapest common network between exchanges for transfers.

- **Daily Symbol Refresh**  
  Automatically updates symbol lists and mappings every UK midnight.

- **CSV Logging**  
  Stores all profitable trades in `arbitrage_opportunities.csv`.

## Getting Started

### 1. Clone and Install

```bash
git clone https://github.com/your/repo.git
cd your-repo
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` or set environment variables in `crypto_arbitrage_bot/config.py`:

```python
BINANCE_API_KEY = "your-binance-key"
BINANCE_API_SECRET = "your-binance-secret"
OKX_API_KEY = "your-okx-key"
OKX_API_SECRET = "your-okx-secret"
OKX_PASSPHRASE = "your-okx-passphrase"

EMAIL_SENDER = "you@yahoo.com"
EMAIL_PASSWORD = "your-yahoo-app-password"
EMAIL_RECEIVER = "recipient@example.com"

ARBITRAGE_BUDGET = 1000
ARBITRAGE_PROFIT_THRESHOLD = 0.5  # %
```

### 3. Run the Bot

```bash
python price_updater.py
```

## 📧 Email Format Example

Subject:  
```
Arbitrage Opportunity: BTCUSDT | Profit 2.75%
```

Body:
```
buy_exchange: Binance
sell_exchange: OKX
network_used: TRC20
net_profit: 27.5
net_profit_percentage: 2.75
...
```

## Security Notes

- Never share your API keys or credentials.
- Use separate sub-accounts with withdrawal limits if deploying to production.

## Future Ideas

- Auto-execution on both exchanges
- Web dashboard for monitoring
- Add more exchanges (e.g., KuCoin, Kraken)
- Fee caching to reduce API hits
