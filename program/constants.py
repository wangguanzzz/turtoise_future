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

CONTINUE_CONTRACTS = ['V0', 'P0', 'B0', 'M0', 'I0', 'JD0', 'L0', 'PP0', 'FB0', 'BB0', 'Y0', 'C0', 'A0', 'J0', 'JM0', 'CS0', 'EG0', 'RR0', 'EB0', 'LH0', 'TA0', 'OI0', 'RS0', 'RM0', 'ZC0',  'SR0', 'CF0',  'MA0', 'FG0',  'SF0', 'SM0', 'CY0', 'AP0', 'CJ0', 'UR0', 'SA0', 'PF0', 'PK0', 'FU0', 'SC0', 'AL0', 'RU0', 'ZN0', 'CU0', 'AU0', 'RB0', 'PB0', 'AG0', 'BU0', 'HC0', 'SN0', 'NI0', 'SP0', 'NR0', 'SS0']

# supervised trading
PREPARE_DATA = False
GENERATE_MODEL = True