import asyncio
import json
import websockets
from modules.core.group_symbols import symbol_prices, denormalize_symbol, normalize_symbol

def generate_okx_subscriptions():
    """
    Generate OKX subscriptions for both ticker and order book.
    Converts normalized symbols like XRPEUR → XRP-EUR
    """
    subs = []
    for sym, exchanges in symbol_prices.items():
        if "OKX" in exchanges:
            okx_sym = normalize_symbol(sym)
            subs.append({"channel": "tickers", "instId": okx_sym})
            subs.append({"channel": "books5", "instId": okx_sym})
    return subs

def chunk_list(lst, size):
    """Split a list into chunks of size 'chunk_size'."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]

async def send_ping(ws):
    """Send a ping frame every 15 seconds to keep the connection alive."""
    while True:
        try:
            await ws.send(json.dumps({"op": "ping"}))
        except websockets.ConnectionClosed:
            print("OKX ping failed — connection closed.")
            break
        await asyncio.sleep(15)

async def _handle_ws_session(chunk):
    """
    Handle a WebSocket connection for a chunk of combined ticker + order book streams.
    """
    uri = "wss://ws.okx.com:8443/ws/v5/public"

    async with websockets.connect(uri) as ws:
        sub_msg = {
            "op": "subscribe",
            "args": chunk
        }
        await ws.send(json.dumps(sub_msg))
        asyncio.create_task(send_ping(ws))

        while True:
            try:
                message = await ws.recv()
                data = json.loads(message)

                # ignoring confirmation subs from websocket
                if "data" not in data or "arg" not in data:
                    continue
                # Skip subscription confirmations.
                if data.get("event") == "subscribe":
                    continue
                # Skip pong confirmation message
                if data.get("op") == "pong":
                    continue

                channel = data["arg"]["channel"]
                okx_inst_id = data["arg"]["instId"]
                sym_key = denormalize_symbol(okx_inst_id)

                # Check if the symbol exists in the in-memory structure
                if sym_key not in symbol_prices or "OKX" not in symbol_prices[sym_key]:
                    print(f"⚠️ Received update for unknown symbol: {okx_inst_id} → {sym_key}")
                    continue

                # Processing the price connection
                if channel == "tickers":
                    try:
                        price = float(data["data"][0]["last"])

                        # update price in in-memory metadata
                        symbol_prices[sym_key]["OKX"]["price"] = price
                    except Exception as e:
                        print(f"Ticker parse error for {sym_key}: {e}")

                # Processing the order book connection
                elif channel == "books5":
                    try:
                        bids_raw = data["data"][0].get("bids", [])[:5]
                        asks_raw = data["data"][0].get("asks", [])[:5]

                        bids = [[float(price), float(qty)] for price, qty, *_ in bids_raw]
                        asks = [[float(price), float(qty)] for price, qty, *_ in asks_raw]

                        # update the bid and ask in in-memory metadata
                        symbol_prices[sym_key]["OKX"]["bid"] = bids
                        symbol_prices[sym_key]["OKX"]["ask"] = asks
                    except Exception as e:
                        print(f"Order book parse error for {sym_key}: {e}")

            except Exception as e:
                print(f"⚠️ WebSocket error: {e}")
                await asyncio.sleep(5)

async def handle_okx_connection(chunk):
    """
    Persistent wrapper for handling reconnection logic if WebSocket session drops.
    """
    while True:
        try:
            await _handle_ws_session(chunk)
        except Exception as e:
            print(f"❌ Connection failed: {e} — Reconnecting in 5s")
            await asyncio.sleep(5)

async def okx_combined_connection():
    """
    Split all subscriptions into chunks and assign them to their own websocket session.
    """
    subs = generate_okx_subscriptions()
    sub_chunks = chunk_list(subs, 100) 
    tasks = [asyncio.create_task(handle_okx_connection(chunk)) for chunk in sub_chunks]
    await asyncio.gather(*tasks)

async def main():
    await okx_combined_connection()

if __name__ == "__main__":
    asyncio.run(main())
