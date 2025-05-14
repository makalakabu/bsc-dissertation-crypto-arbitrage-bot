import asyncio
import time
import hmac
import hashlib
import requests
from modules.core.group_symbols import symbol_prices, known_quotes_global, USDT_Network
from crypto_arbitrage_bot.config import BINANCE_API_KEY, BINANCE_API_SECRET

# Use known quotes from group_symbols.
KNOWN_QUOTES = list(known_quotes_global)

def extract_base_asset(symbol):
    """
    Given a trading pair (e.g., "BTCUSDT" or "BTCUSDC"), return the base asset (e.g., "BTC").
    """
    for quote in sorted(KNOWN_QUOTES, key=len, reverse=True):
        if symbol.endswith(quote):
            return symbol[:-len(quote)]
    return symbol



async def update_binance_withdrawal_fees():
    """
    Periodically fetch withdrawal fee info from Binance's REST endpoint (/sapi/v1/capital/config/getall)
    and update the "network" field for the "Binance" side in symbol_prices.
    """

    while True:

        # GET Request for Authenticated Rest Api call
        try:
            timestamp = int(time.time() * 1000)
            params = {"timestamp": timestamp}
            query_string = '&'.join(f"{k}={params[k]}" for k in sorted(params))
            signature = hmac.new(BINANCE_API_SECRET.encode('utf-8'),
                                 query_string.encode('utf-8'),
                                 hashlib.sha256).hexdigest()
            params["signature"] = signature

            headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
            url = "https://api.binance.com/sapi/v1/capital/config/getall"
            response = requests.get(url, params=params, headers=headers)
            fee_data = response.json()


            # Processing the data from Rest Api
            fee_mapping = {}
            if isinstance(fee_data, list):
                for asset in fee_data:
                    coin = asset.get("coin")
                    if not coin:
                        continue
                    if asset.get("networkList"):
                        networks = []
                        for net in asset["networkList"]:
                            network_display = net.get("name")#retriving the network name 
                            withdraw_fee = net.get("withdrawFee") #retriving the network fee 
                            withdraw_min = net.get("withdrawMin")#retriving the Minimum Withdrawal


                            # Append this network info to a list for the asset.
                            if network_display and withdraw_fee is not None and withdraw_min is not None:
                                try:
                                    fee_value = float(withdraw_fee)
                                except Exception:
                                    fee_value = 0.0
                                try:
                                    minWd_value = float(withdraw_min)
                                except Exception:
                                    minWd_value = 0.0
                                networks.append({
                                    "name": network_display,
                                    "fee": fee_value,
                                    "minWd": minWd_value
                                })
                        fee_mapping[coin] = networks
                    else:
                        try:
                            default_fee = float(asset.get("withdrawFee", 0))
                        except Exception:
                            default_fee = 0.0
                        fee_mapping[coin] = [{
                            "name": "default",
                            "fee": default_fee,
                            "minWd": 0
                        }]

            # Update the OKX network info for each symbol in in-memory metadata symbol_price.
            for symbol in symbol_prices:
                base_asset = extract_base_asset(symbol)
                if base_asset in fee_mapping:
                    symbol_prices[symbol]["Binance"]["network"] = fee_mapping[base_asset]
                else:
                    symbol_prices[symbol]["Binance"]["network"] = []

            # Update dedicated USDT_Network for Binance using the new structure.
            USDT_Network["Binance"] = fee_mapping.get("USDT", [])

            print("Updated Binance withdrawal network info (including USDT_Network).")
        except Exception as e:
            print("Error updating Binance withdrawal fees:", e)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(update_binance_withdrawal_fees())
