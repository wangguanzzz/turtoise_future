# place market order
from datetime import datetime, timedelta
import time
from pprint import pprint
from func_utils import format_number

# get existing open positions
def is_open_positions(bot_agents,market):
    for bot_agent in bot_agents:
        if bot_agent['market_1'] == market or bot_agent['market_2'] == market:
            return True
    return False


# check order status
def check_order_status( order_id):
    return "live"
    # order = client.private.get_order_by_id(order_id)
    # if order.data:
    #     if "order" in order.data.keys():
    #         return order.data["order"]["status"]
    # return 'FAILED'

# place market order
def place_market_order( market, side ,size, price, reduce_only):

    print("place order ===")
    print(f"{market} {side} | side: {side} | size: {size} | price: {price} | close_order: {reduce_only}")
    
    #place an order
    # place_order = client.private.create_order(
    #     position_id = position_id,
    #     market = market,
    #     side = side,
    #     order_type = "MARKET",
    #     post_only = False,
    #     size = size,
    #     price = price,
    #     limit_fee = '0.015',
    #     expiration_epoch_seconds = expiration.timestamp(),
    #     time_in_force = 'FOK',
    #     reduce_only = reduce_only
    # )
    # return result
    #print(place_order.data)
    # return place_order.data
    return None


