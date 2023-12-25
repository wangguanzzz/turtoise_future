# import akshare as ak

# df = ak.futures_zh_daily_sina(symbol="V0")
# print(df)

import csv

# 你的元组列表
tuples = [('a', 1), ('b', 2), ('c', 0)]

# 指定 CSV 文件的名称
filename = "output.csv"

# 打开文件，准备写入
with open(filename, 'w', newline='') as file:
    writer = csv.writer(file)

    # 写入所有的元组
    for tup in tuples:
        writer.writerow(tup)

print(f"文件 '{filename}' 已经被成功创建。")