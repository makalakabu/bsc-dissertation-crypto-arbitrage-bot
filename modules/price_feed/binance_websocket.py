import json
import asyncio
import websockets
from modules.core.group_symbols import symbol_prices

def generate_combined_streams(limit=20):
    """
    Generate a list of Binance subscription strings like:
    ['btcusdt@ticker', 'btcusdt@depth5@100ms']
    """
    streams = []
    for sym, exchanges in symbol_prices.items():
        if "Binance" in exchanges:
            base = sym.lower()
            streams.append(f"{base}@ticker")
            streams.append(f"{base}@depth{limit}@100ms")
    return streams

def chunk_list(lst, chunk_size):
    """Split a list into chunks of size 'chunk_size'."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

async def send_ping(ws):
    """Send a ping frame every 15 seconds to keep the connection alive."""
    while True:
        try:
            await ws.ping()
        except websockets.ConnectionClosed:
            print("Connection closed during ping.")
            break
        await asyncio.sleep(15)

async def handle_binance_combined_connection(chunk):
    """
    Handle a WebSocket connection for a chunk of combined ticker + order book streams.
    """
    stream_path = "/".join(chunk)
    uri = f"wss://stream.binance.com:9443/stream?streams={stream_path}"

    # Waiting for websocket connection
    async with websockets.connect(uri) as ws:

        # Send ping to keep the connection alive
        asyncio.create_task(send_ping(ws))

        async for message in ws:
            data = json.loads(message)
            stream = data.get("stream", "")
            payload = data.get("data", {})
    
            # Processing the price connectoin
            if stream.endswith("@ticker"):
                symbol = payload.get("s")
                try:
                    new_price = float(payload.get("c", 0))
                    # update price in in-memory metadata
                    symbol_prices[symbol]["Binance"]["price"] = new_price
                except Exception as e:
                    print(f"Error parsing price for {symbol}: {e}")

            # Processing the order book connection
            elif stream.endswith("@depth5@100ms"):
                symbol_key = stream.replace("@depth5@100ms", "").upper()
                bids_raw = payload.get("bids", [])
                asks_raw = payload.get("asks", [])

 
                bids = [[float(price), float(qty)] for price, qty in bids_raw]
                asks = [[float(price), float(qty)] for price, qty in asks_raw]

                #update the bid and ask in in-memory metadata
                if symbol_key in symbol_prices and "Binance" in symbol_prices[symbol_key]:
                    symbol_prices[symbol_key]["Binance"]["bid"] = bids
                    symbol_prices[symbol_key]["Binance"]["ask"] = asks


async def binance_combined_connection():
    streams = generate_combined_streams(limit=5)
    stream_chunks = chunk_list(streams, 100) 
    tasks = [asyncio.create_task(handle_binance_combined_connection(chunk)) for chunk in stream_chunks]
    await asyncio.gather(*tasks)

async def main():
    await binance_combined_connection()

if __name__ == "__main__":
    asyncio.run(main())
