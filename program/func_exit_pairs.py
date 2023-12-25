from constants import CLOSE_AT_ZSCORE_CROSS,ZSCORE_THRESH
from func_utils import format_number
from func_public import get_candles_recent,get_contract_cn_name
from func_cointegration import calculate_zscore
from func_private import place_market_order
from func_bot_agent import BotAgent
import time
import json
from pprint import pprint

# Close positions
def manage_trade_exits():
    """
        Manage exiting open positions
        
    """
    
    # Initialize saving output
    save_output =[]
    
    #open json file
    try:
        open_positions_file = open('bot_agents.json',encoding='utf-8')
        open_positions_dict = json.load(open_positions_file)
    except:
        return "complete"
    
    if len(open_positions_dict) < 1:
        return "complete"
    

        
    # check all saved positions matchh order record
    # exit trade according to any exit trade rules
    for position in open_positions_dict:
    # initialize is_close trigger
        is_close= False
        
        # extract position matching info from file - market 1
        position_market_m1 = position['market_1']

        position_size_m1 = position['order_m1_size']
        position_side_m1 = position['order_m1_side']

        # extract position matching info from file - market 2
        position_market_m2 = position['market_2']
        position_size_m2 = position['order_m2_size']
        position_side_m2 = position['order_m2_side']
        
      
        # get prices
        series_1 = get_candles_recent(position_market_m1)
        series_2 = get_candles_recent(position_market_m2)
        
       
        # trigger close based on z-sore
        if CLOSE_AT_ZSCORE_CROSS:
            hedge_ratio = position['hedge_ratio']
            z_score_traded = position['z_score']
            if len(series_1) > 0 and len(series_1) == len(series_2):
                spread = series_1 - series_2 * hedge_ratio
                z_score_current = calculate_zscore(spread).values.tolist()[-1]
            
            # determine trigger
            z_score_level_check = abs(z_score_current) > ZSCORE_THRESH
            z_score_cross_check = (z_score_current < 0  and z_score_traded > 0 ) or (z_score_current > 0  and z_score_traded < 0 )
            
            # close trade
            if z_score_level_check and z_score_cross_check:
                # initial close trigger
                is_close = True
        
        ###
        # add any other close logic you want here
        # trigger is is_close
        ###
        
        
        # Close positions if triggered
        if is_close:
            # determine side  - m1
            side_m1 = "SELL"
            if position_side_m1 == 'SELL':
                side_m1 = 'BUY'
            # determine side  - m2
            side_m2 = "SELL"
            if position_side_m2 == 'SELL':
                side_m2 = 'BUY'            
                
            # get and format price
            accept_price_1 = series_1[-1]
            accept_price_2 = series_2[-1]
            
            # close positions
            try:
                #close poisition for market one:
                print(">>> Closeing market 1 <<<")
                print(f"Closeing position for {get_contract_cn_name(position_market_m1)}")
                
                close_order_m1 = place_market_order(
                    market=position_market_m1,
                    side = side_m1,
                    size = position_size_m1,
                    price= accept_price_1,
                    reduce_only=True,
                )
                
                print(">>> Closeing <<<")
                
                
                #close poisition for market two:
                print(">>> Closeing market 2 <<<")
                print(f"Closeing position for {get_contract_cn_name(position_market_m2)}")
                
                close_order_m2 = place_market_order(
                    market=position_market_m2,
                    side = side_m2,
                    size = position_size_m2,
                    price= accept_price_2,
                    reduce_only=True,
                )
                print(">>> Closeing <<<")
            except Exception as e:
                print(f"Exit failed for {get_contract_cn_name(position_market_m1)} with {get_contract_cn_name(position_market_m2)}")
        # keep record if tems and save
        else:
            save_output.append(position)
    # save remaining items
    print(f"{len(save_output)} Items remaining. Saving file ...")
    with open("bot_agents.json","w",encoding='utf-8') as f:
        json.dump(save_output, f,ensure_ascii=False)
        
            