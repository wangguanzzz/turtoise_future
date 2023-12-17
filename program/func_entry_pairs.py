from constants import ZSCORE_THRESH, USD_PER_TRADE, USD_MIN_COLLATERAL,HALF_LIFE_THRESH
from func_utils import format_number
from func_public import get_candles_recent,get_contract_cn_name
from func_cointegration import calculate_zscore
from func_private import is_open_positions
from func_bot_agent import BotAgent
import pandas as pd
import json

from pprint import pprint

#open positions

def open_positions():
    """
    manage finding triggers for trade entry
    store trades for managing later on exit function
    """
    
    # load integrated pairs
    df = pd.read_csv("cointegrated_pairs.csv")
    
    # get markets from referencing of min order size, tick size etc.
    #TODO
    
    # initialize container for botagent results
    
    #open json file
    bot_agents = []
    try:
        open_positions_file = open('bot_agents.json')
        open_positions_dict = json.load(open_positions_file)
        for p in open_positions_dict:
            bot_agents.append(p)
        
    except:
        bot_agents = []
    
    # find Zscore triggers
    for index,row in df.iterrows():
        # extract variables
        base_market = row['base_market']
        quote_market = row['quote_market']
        hedge_ratio = row['hedge_ratio']
        half_life = row['half_life']
        

        # get prices
        series_1  = get_candles_recent(base_market)
        series_2  = get_candles_recent(quote_market)
        

        # get zscore
        if len(series_1) > 0 and len(series_1) == len(series_2):
            spread = series_1 - (hedge_ratio * series_2)
            # get the last one
            z_score = calculate_zscore(spread).values.tolist()[-1]
            
            # establish if protential trade
            if abs(z_score) >= ZSCORE_THRESH and half_life <= HALF_LIFE_THRESH:

                # enable like-by-like not already open ( diversify trading )
                is_base_open = is_open_positions(bot_agents,base_market)
                is_quote_open = is_open_positions(bot_agents,quote_market)
                
                # place trade
                if not is_base_open and not is_quote_open:
                    # determine the side
                    base_side = "BUY" if z_score < 0 else "SELL"
                    quote_side = "BUY" if z_score >0 else "SELL"
                    
                    # get acceptable price in string format with correct number of decimals
                    base_price =series_1[-1]
                    quote_price = series_2[-1]
                    accept_base_price = base_price
                    accept_quote_price = quote_price
                    failsafe_base_price = base_price
                    base_tick_size = 1
                    quote_tick_size = 1
                    

                    # format prices
                    accept_base_price = base_price
                    accept_quote_price = quote_price
                    accept_failsafe_base_price = base_price
                    
                    # get size
                    base_quantity = 1/base_price * USD_PER_TRADE
                    quote_quantity = 1/quote_price * USD_PER_TRADE
                    #base_step_size = markets["markets"][base_market]["stepSize"]
                    #quote_step_size = markets["markets"][quote_market]["stepSize"]
                    
                    
                    # format sizes
                    base_size = format_number(base_quantity,0.1)
                    quote_size = format_number(quote_quantity,0.1)
                    
                    
                    # ensure size
                    # base_min_order_size = markets["markets"][base_market]["minOrderSize"]
                    # quote_min_order_size = markets["markets"][quote_market]["minOrderSize"]
                    # check_base = float(base_quantity) > float(base_min_order_size)
                    # check_quote = float(quote_quantity) > float(quote_min_order_size)
                    check_base = True
                    check_quote= True
                    
                    # get cn contract name
                    base_market_cn = get_contract_cn_name(base_market)
                    quote_market_cn = get_contract_cn_name(quote_market)
                    
                    # if checks pass, place trades
                    if check_base and check_quote:
                        
                        # check account balance
                        # account = client.private.get_account()
                        # free_collateral  = float(account.data["account"]["freeCollateral"])
                        # print(f"Balance: {free_collateral} and minimum at {USD_MIN_COLLATERAL}")
                        
                        # # ensure collateral
                        # if free_collateral < USD_MIN_COLLATERAL:
                        #     break
                        
                        # create bot Agent
                        
                        bot_agent = BotAgent(
                            market_1=base_market,
                            market_2=quote_market,
                            base_side=base_side,
                            base_size=base_size,
                            base_price=accept_base_price,
                            quote_side=quote_side,
                            quote_size=quote_size,
                            quote_price=accept_quote_price,
                            accept_failsafe_base_price=accept_failsafe_base_price,
                            z_score=z_score,
                            half_life=half_life,
                            hedge_ratio=hedge_ratio                            
                        )
                        
                        # open trades
                        bot_open_dict = bot_agent.open_trades()
                        print(bot_open_dict)
                        # handle success in opening trades
                        if bot_open_dict["pair_status"] == 'LIVE':
                            
                            # append to list of bot agents
                            bot_agents.append(bot_open_dict)
                            del(bot_open_dict)
                            
                            #confirm live status in print
                            print("Trade status: Live")
                            print("---")

                    
    # Save agents
    print(f"Success: {len(bot_agents)} New Pairs LIVE")
    if len(bot_agents) > 0:
        with open("bot_agents.json","w",encoding='utf-8') as f:
            json.dump(bot_agents,f,ensure_ascii=False)
    
    