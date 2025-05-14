import requests
import json

# Global set to store quote currencies encountered during denormalization.
known_quotes_global = set()

def get_all_binance_spot_symbols():
    """
    Get all of the traiding pair available in the Binance spot exchagen using 
    unauthenticated rest api
    """
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    data = response.json()
    symbols = [item['symbol'] for item in data.get('symbols', [])]
    return symbols


def get_all_okx_spot_symbols():
    """
    Get all of the traiding pair available in the OKX spot exchagen using 
    unauthenticated rest api
    """
    url = "https://www.okx.com/api/v5/public/instruments?instType=SPOT"
    response = requests.get(url)
    data = response.json()
    instruments = data.get("data", [])
    # Convert from normalized "BTC-USDT" to denormalized "BTCUSDT"
    symbols = [denormalize_symbol(inst["instId"]) for inst in instruments]
    return symbols


def denormalize_symbol(symbol):
    """
    Converts a symbol from the normalized format (e.g. "BTC-USDT-SWAP" or "BTC-USDT")
    to the denormalized format (e.g. "BTCUSDT").
    If the symbol ends with "-SWAP", that portion is removed.
    Also adds the quote currency to the known_quotes_global set.
    """
    global known_quotes_global
    if symbol.endswith("-SWAP"):
        symbol = symbol[:-5]
    if '-' in symbol:
        parts = symbol.split('-', 1)
        if len(parts) == 2:
            base, quote = parts
            known_quotes_global.add(quote)
            return base + quote
    return symbol

def normalize_symbol(symbol):
    """
    Converts a denormalized symbol (e.g. "BTCUSDT") to the normalized format (e.g. "BTC-USDT")
    using the known_quotes_global set.
    """
    global known_quotes_global
    for quote in sorted(known_quotes_global, key=len, reverse=True):
        if symbol.endswith(quote):
            base = symbol[:-len(quote)]
            return f"{base}-{quote}"
    return symbol

def group_symbols():
    """
    Fetch symbols from Binance and OKX (both spot and futures) and build a dictionary mapping
    each denormalized symbol to a dictionary of exchanges, each having a default structure:
      {
        "price": -1,
        "network": {},
        "bid":[],
        "ask":[]
      }
    
    Only symbols present on both exchanges are kept.
    """
    exchange_symbols = {}

    try:
        binance_spot = set(get_all_binance_spot_symbols())
        exchange_symbols["Binance"] = binance_spot
    except Exception as e:
        print("Error fetching Binance symbols:", e)
        exchange_symbols["Binance"] = set()

    try:
        okx_spot = set(get_all_okx_spot_symbols())
        exchange_symbols["OKX"] = okx_spot
    except Exception as e:
        print("Error fetching OKX symbols:", e)
        exchange_symbols["OKX"] = set()

    # Default nested structure for each exchange.
    default_structure = {
        "price": -1,
        "bid":[],
        "ask":[],
        "network": []
    }

    # Build a dictionary mapping each symbol to its exchanges.
    symbol_dict = {}
    for exchange, symbols in exchange_symbols.items():
        for sym in symbols:
            if sym not in symbol_dict:
                symbol_dict[sym] = {}
            symbol_dict[sym][exchange] = {
                "price": default_structure["price"],
                "bid":[],
                "ask":[],
                "network": {}
            }
    # Only keep symbols that appear on both exchanges.
    filtered = {sym: exch for sym, exch in symbol_dict.items() if len(exch) >= 2}
    return filtered

def save_grouped_symbols(symbol_dict, filename="symbols_output.json"):
    """
    Save a json file only for debugin and data visualization
    """
    with open(filename, "w") as f:
        json.dump(symbol_dict, f, indent=2)
    print(f"Saved symbols to {filename}")

def save_known_quotes(filename="known_quotes.json"):
    """
    Save a json file only for debugin and data visualization
    """
    with open(filename, "w") as f:
        json.dump(list(known_quotes_global), f, indent=2)
    print(f"Saved known quotes to {filename}")

def get_known_quotes():
    """
    Getter for the known quote currencies.
    """
    return list(known_quotes_global)

# Initialize the symbol_prices global variable.
symbol_prices = group_symbols()


# This structure holds only the network metadata for USDT for each exchange.
# Networks are initialized empty and will be updated via REST APIs.
USDT_Network = {
    "Binance": {},
    "OKX": {}
}

