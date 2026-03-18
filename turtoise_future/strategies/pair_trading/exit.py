"""Exit logic for pair trading"""

import json
from typing import List, Dict
from ...config.settings import settings
from ...data.cache import get_candles_recent, get_contract_cn_name
from .cointegration import calculate_zscore
from ...execution.broker import place_market_order


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


def manage_trade_exits() -> str:
    """
    Manage exiting open positions based on exit rules.

    Returns:
        Status string
    """
    open_positions = load_open_positions()

    if len(open_positions) < 1:
        return "complete"

    save_output = []

    for position in open_positions:
        is_close = False

        position_market_m1 = position["market_1"]
        position_size_m1 = position["order_m1_size"]
        position_side_m1 = position["order_m1_side"]

        position_market_m2 = position["market_2"]
        position_size_m2 = position["order_m2_size"]
        position_side_m2 = position["order_m2_side"]

        series_1 = get_candles_recent(position_market_m1)
        series_2 = get_candles_recent(position_market_m2)

        if settings.close_at_zscore_cross:
            hedge_ratio = position["hedge_ratio"]
            z_score_traded = position["z_score"]

            if len(series_1) > 0 and len(series_1) == len(series_2):
                spread = series_1 - series_2 * hedge_ratio
                z_score_current = calculate_zscore(spread).values.tolist()[-1]

                z_score_level_check = abs(z_score_current) > settings.zscore_threshold
                z_score_cross_check = (z_score_current < 0 and z_score_traded > 0) or (
                    z_score_current > 0 and z_score_traded < 0
                )

                if z_score_level_check and z_score_cross_check:
                    is_close = True

        if is_close:
            side_m1 = "SELL" if position_side_m1 == "BUY" else "BUY"
            side_m2 = "SELL" if position_side_m2 == "BUY" else "BUY"

            accept_price_1 = series_1[-1]
            accept_price_2 = series_2[-1]

            try:
                print(f"Closing market 1: {get_contract_cn_name(position_market_m1)}")
                place_market_order(
                    market=position_market_m1,
                    side=side_m1,
                    size=position_size_m1,
                    price=accept_price_1,
                    reduce_only=True,
                )

                print(f"Closing market 2: {get_contract_cn_name(position_market_m2)}")
                place_market_order(
                    market=position_market_m2,
                    side=side_m2,
                    size=position_size_m2,
                    price=accept_price_2,
                    reduce_only=True,
                )
            except Exception as e:
                print(f"Exit failed: {e}")
        else:
            save_output.append(position)

    print(f"{len(save_output)} Items remaining. Saving file ...")
    save_open_positions(save_output)

    return "complete"
