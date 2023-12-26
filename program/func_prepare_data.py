import numpy as np
import pandas as pd
from stratmanager import StrategyManager
import sklearn.mixture as mix
from ta.momentum import RSIIndicator
from constants import COMMODITY_DICT
from func_hmm import add_hmm_feature
import time
def prepare_data():
    for symbol in COMMODITY_DICT.keys():
        # protect API
        time.sleep(1)
        print(f"prepare data for {symbol}")
        strat_mgr = StrategyManager(symbol=symbol)
        df_fe = strat_mgr.df.copy()
        # Add RSI
        rsi = RSIIndicator(close=df_fe["Close"], window=14).rsi()
        df_fe["RSI"] = rsi
        df_fe["RSI_Ret"] = df_fe["RSI"] / df_fe["RSI"].shift(1)
        # Add Moving Average
        df_fe["MA_12"] = df_fe["Close"].rolling(window=12).mean()
        df_fe["MA_21"] = df_fe["Close"].rolling(window=21).mean()
        # Rolling Cumulative Returns
        df_fe["Roll_Rets"] = df_fe["Returns"].rolling(window=30).sum()
        # Rolling Cumulative Range
        df_fe["Avg_Range"] = df_fe["Range"].rolling(window=30).mean()
        # Add Time Intervals
        t_steps = [1, 2]
        t_features = ["Returns", "Range", "RSI_Ret"]
        for ts in t_steps:
            for tf in t_features:
                df_fe[f"{tf}_T{ts}"] = df_fe[tf].shift(ts)
        
        
        # Correct for Stationarity
        df_fs = df_fe.copy()
        df_fs[["Open", "High", "Low", "Volume","Hold"]] = df_fs[["Open", "High", "Low", "Volume","Hold"]].pct_change()
        df_fs = add_hmm_feature(df_fs)
        
        # Check for NaN
        df_fs.dropna(inplace=True)
        
        df_fs.replace([np.inf, -np.inf], np.nan, inplace=True)
        df_fs.fillna(0, inplace=True)
        # Save DataFrame
        df_fs.to_csv(f"data/{symbol}.csv")