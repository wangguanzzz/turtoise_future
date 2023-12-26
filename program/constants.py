from decouple import config
# select mode !!!
MODE = "DEVELOPMENT"

# close all open positions and orders
# ABORT_ALL_POSITIONS = False

# find cointegrated pairs
FIND_COINTEGRATED = True

# place trades
PLACE_TRADES = True

MANAGE_EXITS = True

# Resolution
RESOLUTION = "1DAY"

# Stats Window
WINDOW = 21

# Thresholds - Opening
MAX_HALF_LIFE = 24
ZSCORE_THRESH = 1.5
HALF_LIFE_THRESH = 8
USD_PER_TRADE = 50000
USD_MIN_COLLATERAL = 1880

# Threshold - Closing
CLOSE_AT_ZSCORE_CROSS = True

DICT ={
    'SHFE': '上海期货交易所',
    'CZCE': '郑州商品交易所',
    'DCE': '大连商品交易所'
}

COMMODITY_DICT = {
    'V0': 'PVC连续',
    'P0': '棕榈油连续',
    'B0': '豆二连续',
    'M0': '豆粕连续',
    'I0': '铁矿石连续',
    'JD0': '鸡蛋连续',
    'L0': '塑料连续',
    'PP0': '聚丙烯连续',
    'FB0': '纤维板连续',
    'Y0': '豆油连续',
    'C0': '玉米连续',
    'A0': '豆一连续',
    'J0': '焦炭连续',
    'JM0': '焦煤连续',
    'CS0': '淀粉连续',
    'EG0': '乙二醇连续',
    'EB0': '苯乙烯连续',
    'LH0': '生猪连续',
    'TA0': 'PTA连续',
    'OI0': '菜油连续',
    'RM0': '菜粕连续',
    'SR0': '白糖连续',
    'CF0': '棉花连续',
    'MA0': '甲醇连续',
    'FG0': '玻璃连续',
    'SF0': '硅铁连续',
    'SM0': '锰硅连续',
    'CY0': '棉纱连续',
    'AP0': '苹果连续',
    'CJ0': '红枣连续',
    'UR0': '尿素连续',
    'SA0': '纯碱连续',
    'PF0': '短纤连续',
    'PK0': '花生连续',
    'FU0': '燃料油连续',
    'AL0': '铝连续',
    'RU0': '天然橡胶连续',
    'ZN0': '沪锌连续',
    'CU0': '铜连续',
    'AU0': '黄金连续',
    'RB0': '螺纹钢连续',
    'PB0': '铅连续',
    'AG0': '白银连续',
    'BU0': '沥青连续',
    'HC0': '热轧卷板连续',
    'SN0': '锡连续',
    'NI0': '镍连续',
    'SP0': '纸浆连续',
    'NR0': '20号胶连续',
    'SS0': '不锈钢连续'
}
# supervised trading
PREPARE_DATA = False
GENERATE_MODEL = True