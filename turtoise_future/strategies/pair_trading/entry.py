"""Entry logic for pair trading"""

import pandas as pd
import json
from typing import List, Dict, Any
from ...config.settings import settings
from ...data.cache import get_candles_recent, get_contract_cn_name, is_rare_contract
from .cointegration import calculate_zscore
from ...execution.broker import BotAgent


def is_open_position(bot_agents: List[Dict], market: str) -> bool:
    """Check if a market already has an open position"""
    for bot_agent in bot_agents:
        if bot_agent["market_1"] == market or bot_agent["market_2"] == market:
            return True
    return False


def load_open_positions() -> List[Dict]:
    """Load open positions from JSON file"""
    try:
        with open("bot_agents.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_open_positions(bot_agents: List[Dict]) -> None:
    """Save open positions to JSON file"""
    with open("bot_agents.json", "w", encoding="utf-8") as f:
        json.dump(bot_agents, f, ensure_ascii=False)


def find_entry_signals() -> int:
    """
    Find and execute entry signals for cointegrated pairs.

    Returns:
        Number of new positions opened
    """
    # Load cointegrated pairs
    df_pairs = pd.read_csv("cointegrated_pairs.csv")

    # Load existing positions
    bot_agents = load_open_positions()

    new_positions = 0

    for _, row in df_pairs.iterrows():
        base_market = row["base_market"]
        quote_market = row["quote_market"]
        hedge_ratio = row["hedge_ratio"]
        half_life = row["half_life"]

        # Get prices
        series_1 = get_candles_recent(base_market)
        series_2 = get_candles_recent(quote_market)

        if len(series_1) > 0 and len(series_1) == len(series_2):
            spread = series_1 - (hedge_ratio * series_2)
            z_score = calculate_zscore(spread).values.tolist()[-1]

            # Check entry conditions
            if abs(z_score) >= settings.zscore_threshold and half_life <= settings.half_life_threshold:
                # Check if already open
                if (
                    not is_open_position(bot_agents, base_market)
                    and not is_open_position(bot_agents, quote_market)
                    and not is_rare_contract(base_market)
                    and not is_rare_contract(quote_market)
                ):
                    # Determine side
                    base_side = "BUY" if z_score < 0 else "SELL"
                    quote_side = "BUY" if z_score > 0 else "SELL"

                    # Get prices
                    base_price = series_1[-1]
                    quote_price = series_2[-1]

                    # Calculate size
                    base_quantity = 1 / base_price * settings.usd_per_trade
                    quote_quantity = 1 / quote_price * settings.usd_per_trade
                    base_size = int(base_quantity)
                    quote_size = int(quote_quantity)

                    if base_size >= 1 and quote_size >= 1:
                        bot_agent = BotAgent(
                            market_1=base_market,
                            market_2=quote_market,
                            base_side=base_side,
                            base_size=str(base_size),
                            base_price=base_price,
                            quote_side=quote_side,
                            quote_size=str(quote_size),
                            quote_price=quote_price,
                            accept_failsafe_base_price=base_price,
                            z_score=z_score,
                            half_life=half_life,
                            hedge_ratio=hedge_ratio,
                        )

                        bot_open_dict = bot_agent.open_trades()
                        if bot_open_dict["pair_status"] == "LIVE":
                            bot_agents.append(bot_open_dict)
                            new_positions += 1
                            print(f"Opened position: {base_market}/{quote_market}")

    # Save updated positions
    save_open_positions(bot_agents)
    print(f"Success: {new_positions} New Pairs LIVE")

    return new_positions
