# config.py
from dotenv import load_dotenv
import os

load_dotenv()

# Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")


# OKX
OKX_API_KEY = os.getenv("OKX_API_KEY")
OKX_API_SECRET = os.getenv("OKX_API_SECRET")
OKX_PASSPHRASE = os.getenv("OKX_PASSPHRASE")


# Email
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

# Arbitrage Config
ARBITRAGE_BUDGET = float(os.getenv("ARBITRAGE_BUDGET", "10000"))
ARBITRAGE_PROFIT_THRESHOLD = float(os.getenv("ARBITRAGE_PROFIT_THRESHOLD", "0"))#percentage in decimal