"""Feature engineering for supervised learning"""

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ...config.commodities import COMMODITY_DICT
from ...data.fetcher import FuturesFetcher
import time


def prepare_data():
    """Prepare feature data for all commodities"""
    for symbol in COMMODITY_DICT.keys():
        time.sleep(1)
        print(f"Preparing data for {symbol}")

        fetcher = FuturesFetcher()
        df = fetcher.get_historical_prices(symbol)
        df.rename(
            columns={
                "date": "Date",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            },
            inplace=True,
        )
        df.set_index("Date", inplace=True)

        # Calculate basic features
        df["Returns"] = df["Close"].pct_change()
        df["Range"] = df["High"] / df["Low"] - 1

        # Add RSI
        rsi = RSIIndicator(close=df["Close"], window=14).rsi()
        df["RSI"] = rsi
        df["RSI_Ret"] = df["RSI"] / df["RSI"].shift(1)

        # Add Moving Average
        df["MA_12"] = df["Close"].rolling(window=12).mean()
        df["MA_21"] = df["Close"].rolling(window=21).mean()

        # Rolling Cumulative Returns
        df["Roll_Rets"] = df["Returns"].rolling(window=30).sum()

        # Rolling Cumulative Range
        df["Avg_Range"] = df["Range"].rolling(window=30).mean()

        # Add Time Intervals
        t_steps = [1, 2]
        t_features = ["Returns", "Range", "RSI_Ret"]
        for ts in t_steps:
            for tf in t_features:
                df[f"{tf}_T{ts}"] = df[tf].shift(ts)

        # Correct for Stationarity
        df_fs = df.copy()
        df_fs[["Open", "High", "Low", "Volume"]] = df_fs[
            ["Open", "High", "Low", "Volume"]
        ].pct_change()

        # Keep last N entries if length > threshold
        from ...config.settings import settings

        if len(df_fs) > settings.train_threshold:
            df_fs = df_fs.tail(settings.train_threshold)

        df_fs.dropna(inplace=True)
        df_fs.replace([np.inf, -np.inf], np.nan, inplace=True)
        df_fs.fillna(0, inplace=True)

        # Save DataFrame
        from pathlib import Path
        data_dir = Path(__file__).parent.parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        df_fs.to_csv(data_dir / f"{symbol}.csv")
