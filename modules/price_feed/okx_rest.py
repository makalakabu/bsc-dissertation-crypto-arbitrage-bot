import asyncio
import time
import hmac
import hashlib
import base64
import datetime
import requests
from modules.core.group_symbols import symbol_prices, known_quotes_global, USDT_Network
from crypto_arbitrage_bot.config import OKX_API_KEY, OKX_API_SECRET, OKX_PASSPHRASE

# Use known quotes from group_symbols (e.g., ["USDT", "USDC", "BUSD", "USD", "EUR"])
KNOWN_QUOTES = list(known_quotes_global)

def extract_base_asset(symbol):
    """
    Given a trading pair (e.g., "BTCUSDT" or "BTCUSDC"), return the base asset (e.g., "BTC").
    """
    for quote in sorted(KNOWN_QUOTES, key=len, reverse=True):
        if symbol.endswith(quote):
            return symbol[:-len(quote)]
    return symbol

def normalize_network_okx(raw_network_name, asset_symbol=None):
    """
    Normalize the network name for OKX.
    """
    if asset_symbol and raw_network_name.startswith(f"{asset_symbol}-"):
        return raw_network_name.split("-", 1)[1]
    return raw_network_name


def get_okx_timestamp():
    """
    Generate Timestamp for Signing to the Rest Api
    """
    return datetime.datetime.utcnow().isoformat("T", "milliseconds") + "Z"

def generate_okx_signature(timestamp, method, request_path, body, secret):
    message = timestamp + method.upper() + request_path + body
    mac = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

async def update_okx_withdrawal_fees():
    """
    Periodically fetch withdrawal fee info from OKX's REST API endpoint (/api/v5/asset/currencies)
    and update the "network" field for the "OKX" side in symbol_prices.
    """
    while True:

        # GET Request for Authenticated Rest Api call
        try:
            method = "GET"
            request_path = "/api/v5/asset/currencies"
            body = ""
            timestamp = get_okx_timestamp()
            signature = generate_okx_signature(timestamp, method, request_path, body, OKX_API_SECRET)
            headers = {
                "OK-ACCESS-KEY": OKX_API_KEY,
                "OK-ACCESS-SIGN": signature,
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": OKX_PASSPHRASE,
                "Content-Type": "application/json"
            }
            url = "https://www.okx.com" + request_path
            response = requests.get(url, headers=headers)
            fee_data = response.json()

            
            fee_mapping = {}
            if fee_data.get("code") == "0" and "data" in fee_data:
                for item in fee_data["data"]:
                    asset = item.get("ccy")
                    raw_chain = item.get("chain") #retriving network name for rest api
                    fee_str = item.get("maxFee")#retriving network fee for rest api
                    minWd_str = item.get("minWd")#retriving Minimum Withdrawwal for rest api

                    if asset and raw_chain and fee_str is not None and minWd_str is not None:
                        norm_chain = normalize_network_okx(raw_chain, asset_symbol=asset)
                        try:
                            fee_value = float(fee_str)
                        except Exception:
                            fee_value = 0.0
                        try:
                            minWd_value = float(minWd_str)
                        except Exception:
                            minWd_value = 0.0

                            
                        # Append this network info to a list for the asset.
                        if asset in fee_mapping:
                            fee_mapping[asset].append({
                                "name": norm_chain,
                                "fee": fee_value,
                                "minWd": minWd_value
                            })
                        else:
                            fee_mapping[asset] = [{
                                "name": norm_chain,
                                "fee": fee_value,
                                "minWd": minWd_value
                            }]

            # Update the OKX network info for each symbol in in-memory metadata symbol_price.
            for symbol in symbol_prices:
                base_asset = extract_base_asset(symbol)
                if base_asset in fee_mapping:
                    symbol_prices[symbol]["OKX"]["network"] = fee_mapping[base_asset]
                else:
                    symbol_prices[symbol]["OKX"]["network"] = []

            # Update dedicated USDT_Network for OKX 
            USDT_Network["OKX"] = fee_mapping.get("USDT", [])
        except Exception as e:
            print("Error updating OKX withdrawal fees:", e)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(update_okx_withdrawal_fees())
