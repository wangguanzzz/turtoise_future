# import akshare as ak
import pandas as pd
# df = ak.futures_zh_daily_sina(symbol="V0")
# print(df)

from func_hmm import add_hmm_feature

df = pd.read_csv('data/A0.csv')
res = add_hmm_feature(df)
print(res)