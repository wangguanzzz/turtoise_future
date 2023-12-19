
import pandas as pd
import numpy as np
from constants import RESOLUTION
import time
from pprint import pprint
import akshare as ak
from datetime import datetime

MARKET_REFERENCE = 'market_reference.csv'

def is_rare_contract(market):
    for rare_contract in ('国际铜', '线材', '动力煤', '胶合板', '强麦', '普麦', '稻', '油菜籽'):
        if rare_contract in get_contract_cn_name(market):
            print(f"market {get_contract_cn_name(market)} is low volume")
            return True
    return False

def get_contract_cn_name(market):
    df = pd.read_csv(MARKET_REFERENCE)
    matching_row = df[df['合约代码'] == market]
    return matching_row.iloc[0]['合约名称']
    
def get_all_main_contracts():
    df = ak.futures_comm_info(symbol="所有")
    df = df[df['交易所名称'].isin(['上海期货交易所', '大连商品交易所', '郑州商品交易所'])]
    df = df[df['备注']=='主力合约']
    df.to_csv(MARKET_REFERENCE)
    return df
    

def construct_market_prices():
    # assign varialbes
    tradeable_markets = get_all_main_contracts()['合约代码'].tolist()
    
    # set initial dataframe
    close_prices = get_candels_historical(tradeable_markets[0])
    df = pd.DataFrame(close_prices)
    df.set_index("datetime", inplace=True)
    
    
    # append other prices to dataframe
    # you can limit the amount to loop through here to save time in development
    for market in tradeable_markets[1:]:
        
        try:
            close_prices_add = get_candels_historical(market)
            df_add = pd.DataFrame(close_prices_add)
            print(market, len(df_add))
            # skip if the history candle is less than 100 days
            if len(df_add) < 100:
                continue
            df_add.set_index("datetime", inplace=True)
            df = pd.merge(df,df_add, how="inner", on="datetime",copy=False )
            del df_add
        except:
            continue
    # check any columns with NaNs
    nans = df.columns[df.isna().any()].tolist()
    if len(nans)> 0:
        print("Droping columns:")
        print(nans)
        df.drop(columns=nans, inplace=True)
    
    # return results
    df.to_csv('market_price.csv')
    return df
def get_candels_historical(market):
    # define output
    close_prices = []
    df = ak.futures_zh_daily_sina(symbol=market)
   
    for index,row in  df.iterrows():
        close_prices.append({"datetime": row["date"], market: row["close"]})
    return close_prices

# get candles recent
def get_candles_recent(market):
    df = pd.read_csv('market_price.csv')

    if market in df.columns:
        close_prices = df[market].tolist()
        return np.array(close_prices).astype(np.float)
    else:
        res = ak.futures_zh_daily_sina(symbol=market)
        close_prices  = res['close'].tolist()
        return np.array(close_prices).astype(np.float)[-len(df):]
    

    