
from dataclasses import dataclass, asdict
import datetime
import re
from typing import Dict, List

# Defining Dataclass in order for me to be organized
@dataclass
class FeeDetails:
    maker_fee_asset: float
    taker_fee_usdt: float
    withdrawal_fee_asset: float

@dataclass
class QuantityDetails:
    bought_qty: float
    after_fees: float
    after_withdrawal: float

@dataclass
class PriceDetails:
    current: float
    average: float
    end: float

@dataclass
class TradeSimulation:
    timestamp: str
    asset_pair: str
    initial_budget: float
    adjusted_budget: float
    buy_exchange: str
    sell_exchange: str
    network_used: str
    fees: FeeDetails
    quantities: QuantityDetails
    buy_prices: PriceDetails
    sell_prices: PriceDetails
    net_profit: float
    net_profit_percentage: float


# Fixed Taker Maker fee from both exchange
TRADING_FEES = {"Binance": 0.001, "OKX": 0.001}

# Helper function for identifying network name
MANUAL_NETWORK_MAPPING = {
    "the open network": "ton",
    "binance smart chain": "bsc"
}


def get_canonical(name: str):
    """
    Helper function to normalize network name
    """
    name = re.sub(r'[^\w\s]', '', name.lower().strip())
    return MANUAL_NETWORK_MAPPING.get(name, name)


def select_common_network(buy_networks: list, sell_networks: list):
    """
    Finding the same network and take their attributes.
    Compare them and return the cheapest network
    """
    common_networks = []
    for bn in buy_networks:
        canon_bn = set(get_canonical(bn["name"]).split())
        for sn in sell_networks:
            canon_sn = set(get_canonical(sn["name"]).split())
            if canon_bn & canon_sn:
                common_networks.append({
                    "network": " ".join(canon_bn & canon_sn),
                    "buy_withdrawal_fee": bn["fee"],
                    "sell_withdrawal_fee": sn["fee"],
                    "total_withdrawal_fee": bn["fee"] + sn["fee"]
                })
    return min(common_networks, key=lambda x: x["total_withdrawal_fee"]) if common_networks else None


def simulate_buy_with_usdt_limit(ask_levels, max_usdt):
    """
    Simulate selling the asset pair by using the entire quantities
    that available for the trade
    """
    total_qty, spent = 0, 0
    for price, qty in ask_levels:
        cost = price * qty
        if spent + cost <= max_usdt:
            spent += cost
            total_qty += qty
        else:
            qty_fit = (max_usdt - spent) / price
            spent += qty_fit * price
            total_qty += qty_fit
            break
    return total_qty, spent / total_qty if total_qty else 0, price


def simulate_sell_max_qty(bid_levels, max_qty):
    """
    Simulate buying the asset pair by using the entire quantities
    that available for the trade
    """
    earned, sold = 0, 0
    for price, qty in bid_levels:
        if sold + qty <= max_qty:
            earned += qty * price
            sold += qty
        else:
            qty_fit = max_qty - sold
            earned += qty_fit * price
            sold += qty_fit
            break
    return earned, earned / sold if sold else 0, price


def simulate_arbitrage_full(
    buy_asks, sell_bids, initial_usdt_budget,
    buy_exchange_name, sell_exchange_name,
    buy_network_fee, sell_taker_fee = 0.001, buy_maker_fee = 0.001,
    asset_pair = "UNKNOWN/USDT", network_name = "UNKNOWN"):

    """ 
    Simulates a full arbitrage cycle, from buying to selling an asset across two exchanges, 
    while accounting for trading and withdrawal fees.
    """

    # Order book calculation for adjusting the budget
    current_buy_price = buy_asks[0][0]
    current_sell_price = sell_bids[0][0]
    total_ask_value = sum(p * q for p, q in buy_asks)
    total_sell_qty = sum(q for p, q in sell_bids)

    # If there's no enough liquidity it will adjust the budget according to available ask orderbook
    if total_ask_value < initial_usdt_budget:
        adjusted_budget = total_ask_value
    else:
        usdt_needed, bought_qty = 0, 0
        for price, qty in buy_asks:
            if bought_qty + qty <= total_sell_qty:
                usdt_needed += qty * price
                bought_qty += qty
            else:
                qty_fit = total_sell_qty - bought_qty
                usdt_needed += qty_fit * price
                break
        adjusted_budget = min(initial_usdt_budget, usdt_needed)

    # Simulate Buying the asset with buy order book and available budget
    bought_qty, avg_buy_price, end_buy_price = simulate_buy_with_usdt_limit(buy_asks, adjusted_budget)
    maker_fee_amount = bought_qty * buy_maker_fee
    qty_after_fees = bought_qty - maker_fee_amount
    qty_after_withdrawal = qty_after_fees - buy_network_fee

    # Simulate Selling the asset with sell order book and available budget
    usdt_earned_gross, avg_sell_price, end_sell_price = simulate_sell_max_qty(sell_bids, qty_after_withdrawal)
    taker_fee_amount = usdt_earned_gross * sell_taker_fee
    usdt_earned = usdt_earned_gross - taker_fee_amount

    # Calculate the net profit and the percentage
    net_profit = usdt_earned - adjusted_budget
    net_profit_pct = (net_profit / adjusted_budget) * 100 if adjusted_budget else 0


    # All of the details when executing the simulation trade
    return TradeSimulation(
        timestamp = datetime.datetime.now().isoformat(),
        asset_pair = asset_pair,
        initial_budget = initial_usdt_budget,
        adjusted_budget = adjusted_budget,
        buy_exchange = buy_exchange_name,
        sell_exchange = sell_exchange_name,
        network_used = network_name,
        fees = FeeDetails(
            maker_fee_asset = maker_fee_amount,
            taker_fee_usdt = taker_fee_amount,
            withdrawal_fee_asset = buy_network_fee
            ),
        quantities = QuantityDetails(
            bought_qty = bought_qty, 
            after_fees = qty_after_fees, 
            after_withdrawal = qty_after_withdrawal
            ),
        buy_prices = PriceDetails(
            current = current_buy_price, 
            average = avg_buy_price, 
            end = end_buy_price
            ),
        sell_prices = PriceDetails(
            current = current_sell_price, 
            average = avg_sell_price, 
            end = end_sell_price
            ),
        net_profit = net_profit,
        net_profit_percentage = net_profit_pct
    )


def traditional_arbitrage(symbol, exchange_data, budget):
    """
    This function simulates a traditional arbitrage opportunity for a given trading symbol.comparing the current market prices of the 
    asset on both exchanges and determining where the asset is cheaper to buy and where it can be sold 
    at a higher price. The function also takes into account the trading fees and withdrawal fees that 
    apply when moving the asset from one exchange to another.
    """

    bin_price = exchange_data["Binance"]["price"]
    ok_price = exchange_data["OKX"]["price"]
    bin_nets = exchange_data["Binance"]["network"]
    ok_nets = exchange_data["OKX"]["network"]

    # Determining Direction:
    # Binance -> OKX
    if bin_price < ok_price:
        buy_ex, sell_ex = "Binance", "OKX"
        buy_asks = exchange_data["Binance"]["ask"]
        sell_bids = exchange_data["OKX"]["bid"]
        buy_nets, sell_nets = bin_nets, ok_nets

    # OKX -> Binance
    else:
        buy_ex, sell_ex = "OKX", "Binance"
        buy_asks = exchange_data["OKX"]["ask"]
        sell_bids = exchange_data["Binance"]["bid"]
        buy_nets, sell_nets = ok_nets, bin_nets

    # Finding the cheapest network available for both exchange
    net_info = select_common_network(buy_nets, sell_nets)

    # Skipping empty metadata
    if not net_info or not buy_asks or not sell_bids:
        return None, None, None

    # Simulate trading
    simulation = simulate_arbitrage_full(
        buy_asks = buy_asks,
        sell_bids = sell_bids,
        initial_usdt_budget = budget,
        buy_exchange_name = buy_ex,
        sell_exchange_name = sell_ex,
        buy_network_fee = net_info["buy_withdrawal_fee"],
        sell_taker_fee = TRADING_FEES[sell_ex],
        buy_maker_fee = TRADING_FEES[buy_ex],
        asset_pair = symbol,
        network_name = net_info["network"]
    )
    return simulation.net_profit, simulation.net_profit_percentage, simulation


def arbitrage_checker(group_symbols, budget, profit_threshold):

    opportunities = []

    # Cycling through every asset pairs available in the in-memory metadata symbol_price
    for symbol, exchange_data in group_symbols.items():

        if "Binance" not in exchange_data or "OKX" not in exchange_data:
            continue

        # Checking profitbale traditional arbitrage
        profit, percentage, details = traditional_arbitrage(symbol, exchange_data, budget)

        # Checking the profit and it's greater than the threshold percentage
        if profit is not None and percentage is not None and percentage > profit_threshold:
            opportunities.append(details)

    return opportunities
