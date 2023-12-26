from func_prepare_data import prepare_data
from func_select_feature import select_feature
from func_binary_classification import binary_classification
from constants import PREPARE_DATA,GENERATE_MODEL,COMMODITY_DICT
from func_public import get_contract_cn_name
from pprint import pprint
import csv
import traceback



if __name__ == "__main__":
    if PREPARE_DATA:
        print('start preparing data ......') 
        prepare_data()
    if GENERATE_MODEL:
        print('start train model ......')
        directions = ['long','short']
        for direction in directions:
            
            output = []
            for contract in COMMODITY_DICT.keys():
                print(f"market: {contract}, direction: {direction}")
                try:
                    params, features = select_feature(contract,direction)
                    result = binary_classification(contract,direction,params,features)
                    output.append(result)
                except Exception as e:
                    print(f"ERROR for {contract} {direction}")
                    traceback.print_exc()
                    continue
            # 指定 CSV 文件的名称
            filename = f"result/{direction}_result.csv"
            #打开文件，准备写入
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                # 写入所有的元组
                for tup in output:
                    writer.writerow(tup)
        

        
        
    
            
            