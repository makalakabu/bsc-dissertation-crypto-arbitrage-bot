from dataclasses import asdict
import random
import asyncio
import datetime
import pytz
import json
import sys
import os
import csv


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

#Load Env for Budget and Profit treshold
from crypto_arbitrage_bot.config import ARBITRAGE_BUDGET, ARBITRAGE_PROFIT_THRESHOLD

# WebSocket connections for live price updates.
from modules.price_feed.binance_websocket import binance_combined_connection
from modules.price_feed.okx_websocket import okx_combined_connection

# REST API fee updaters.
from modules.price_feed.binance_rest import update_binance_withdrawal_fees
from modules.price_feed.okx_rest import update_okx_withdrawal_fees

# Symbol grouping and shared data structures.
from modules.core.group_symbols import symbol_prices, save_grouped_symbols, group_symbols, USDT_Network

# Arbitrage checker from your arbitrage finder module.
from modules.core.arbitrage_finder import arbitrage_checker

#Email alert notification
from modules.alerts.email_notification import email_alert


async def periodic_save():
    """
    Save In-memory metadata (symbol_prices, USDT_Netwoork) to a json file only for debugging and visualization purposes for every 10 sec.
    """
    while True:
        await asyncio.sleep(10)  # Adjust interval as needed.
        save_grouped_symbols(symbol_prices, "data/symbols_updated.json")
        with open("data/usdt_network.json", "w") as f:
            json.dump(USDT_Network, f, indent=2)
        print("Saved symbols_updated.json and usdt_network.json")

async def recalc_symbols_daily():
    """
    Wait until the next UK midnight (Europe/London) and recalculate the symbol grouping.
    This keeps the dynamic symbol data fresh.
    """
    tz = pytz.timezone("Europe/London")
    while True:
        now = datetime.datetime.now(tz)
        next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        seconds_until_midnight = (next_midnight - now).total_seconds()
        await asyncio.sleep(seconds_until_midnight)
        new_groups = group_symbols()
        symbol_prices.clear()
        symbol_prices.update(new_groups)
        print("Recalculated symbol grouping at UK midnight.")

def log_arbitrage_opportunities(opportunities, file_path="data/arbitrage_opportunities.csv"):
    """
    Writing the profitable arbitrage details into a csv file
    """
    if not opportunities:
        return

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    write_header = not os.path.isfile(file_path)
    with open(file_path, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=asdict(opportunities[0]).keys())
        if write_header:
            writer.writeheader()
        for opp in opportunities:
            writer.writerow(asdict(opp))

    print(f"📁 Appended {len(opportunities)} opportunities to {file_path}")



async def arbitrage_loop(symbol_prices, budget, profit_threshold, check_interval=10):
    """
    Arbitrage Logic. This function will retrive the information from in-memory metadata symbol_price,
    and finding profitable arbitrage by simulating the trade. It will send email notification alert
    to the user for the best profitbale percentage in that cycle. This function also add random
    sleep time between 2-5 minutes for the network congestion simulation.
    """
    while True:
        # all details about profitable arbitrage in one cycle
        opportunities = arbitrage_checker(symbol_prices, budget, profit_threshold)

        if opportunities:
            # write to csv file
            log_arbitrage_opportunities(opportunities)

            # Send Email to the user about the best Arbitrage Execution
            best = max(opportunities, key=lambda x: x.net_profit_percentage)
            email_alert(best)

            # Simulate transfer delay
            wait_time = random.randint(120, 300)
            print(f"⏳ Sleeping {wait_time} seconds to simulate transfer...")
            await asyncio.sleep(wait_time)
        else:
            await asyncio.sleep(check_interval)

async def main():
    """
    Run all components concurrently:
      - Binance and OKX WebSocket connections for live price updates.
      - REST-based withdrawal fee updaters.
      - Periodic saving of symbol_prices and USDT_Network.
      - Daily recalculation of symbol grouping.
      - Periodic arbitrage checking.
    """

    await asyncio.gather(

        # Updating all of the atributes for the in-memory metadata
        binance_combined_connection(),
        okx_combined_connection(),
        update_binance_withdrawal_fees(),
        update_okx_withdrawal_fees(),
        periodic_save(),
        recalc_symbols_daily(), 

        # retriving attributes and cycle the arbitrage 
        arbitrage_loop(symbol_prices, ARBITRAGE_BUDGET, ARBITRAGE_PROFIT_THRESHOLD)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot manually stopped.")
    except Exception as e:
        print(f"Fatal error: {e}")
