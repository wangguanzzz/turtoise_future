
from constants import  FIND_COINTEGRATED,PLACE_TRADES,MANAGE_EXITS
from func_messaging import send_message
from func_public import construct_market_prices
from func_cointegration import store_cointegration_results
from func_entry_pairs import open_positions
from func_exit_pairs import manage_trade_exits
import traceback

if __name__ == "__main__":
    print('hello bot')
    try:
        print('connecting to client...')
        #client = connect_dydx()
    except Exception as e:
        print("error connecting to client",e)
        exit(1)
    
    # abort all open positions
    # if ABORT_ALL_POSITIONS:
    #     try:
    #         print("closing all positions ...")
    #         #abort_all_positions(client)
    #     except Exception as e:
    #         print("error closing all positions",e)
    #         exit(1)
    
    # find cointegrated pairs
    if FIND_COINTEGRATED:
        # construct market prices
        try:
            print("fetching market prices, please allow 3 mintues ...")
            df_market_prices = construct_market_prices()
        except Exception as e:
            print("error constructing market prices",e)
            exit(1)
        # store cointegrated pairs    
        try:
            print("storing cointegrated pairs")
            stores_result = store_cointegration_results(df_market_prices)
            if stores_result != "saved":
                print("Error saving cointegrated pairs")
                exit(1)
        except Exception as e:
            print("Error saving cointegrated pairs",e)
            exit(1)     
    
    if PLACE_TRADES:        
        # store cointegrated pairs    
        try:
            print("Find trading oppotunities")
            open_positions()
        except Exception as e:
            print("Error trading pairs: ",e)
            traceback.print_exc()
            exit(1)    
             
    if MANAGE_EXITS:        
        # store cointegrated pairs    
        try:
            print("Managing exits ...")
            manage_trade_exits()
        except Exception as e:
            print("Error manage extis: ",e)
            traceback.print_exc()
            exit(1)    