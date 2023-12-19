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

