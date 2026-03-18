"""Commodity dictionary mapping contract codes to Chinese names and contract sizes"""

# Exchange names
EXCHANGE_DICT = {
    "SHFE": "上海期货交易所",
    "CZCE": "郑州商品交易所",
    "DCE": "大连商品交易所",
}

# Commodity dictionary: symbol -> (name, contract_size)
COMMODITY_DICT = {
    # DCE (大连商品交易所)
    "V0": ("PVC连续", 5),
    "P0": ("棕榈油连续", 10),
    "B0": ("豆二连续", 10),
    "M0": ("豆粕连续", 10),
    "I0": ("铁矿石连续", 100),
    "JD0": ("鸡蛋连续", 10),
    "L0": ("塑料连续", 5),
    "PP0": ("聚丙烯连续", 5),
    "FB0": ("纤维板连续", 10),
    "Y0": ("豆油连续", 10),
    "C0": ("玉米连续", 10),
    "A0": ("豆一连续", 10),
    "J0": ("焦炭连续", 100),
    "JM0": ("焦煤连续", 60),
    "CS0": ("淀粉连续", 10),
    "EG0": ("乙二醇连续", 10),
    "EB0": ("苯乙烯连续", 5),
    "LH0": ("生猪连续", 16),

    # CZCE (郑州商品交易所)
    "TA0": ("PTA连续", 5),
    "OI0": ("菜油连续", 10),
    "RM0": ("菜粕连续", 10),
    "SR0": ("白糖连续", 10),
    "CF0": ("棉花连续", 5),
    "MA0": ("甲醇连续", 10),
    "FG0": ("玻璃连续", 20),
    "SF0": ("硅铁连续", 5),
    "SM0": ("锰硅连续", 5),
    "CY0": ("棉纱连续", 5),
    "AP0": ("苹果连续", 10),
    "CJ0": ("红枣连续", 5),
    "UR0": ("尿素连续", 20),
    "SA0": ("纯碱连续", 20),
    "PK0": ("花生连续", 5),

    # SHFE (上海期货交易所)
    "FU0": ("燃料油连续", 10),
    "AL0": ("铝连续", 5),
    "RU0": ("天然橡胶连续", 10),
    "ZN0": ("沪锌连续", 5),
    "CU0": ("铜连续", 5),
    "RB0": ("螺纹钢连续", 10),
    "PB0": ("铅连续", 5),
    "BU0": ("沥青连续", 10),
    "HC0": ("热轧卷板连续", 10),
    "SN0": ("锡连续", 1),
    "NI0": ("镍连续", 1),
    "SP0": ("纸浆连续", 10),
    "NR0": ("20号胶连续", 10),
    "SS0": ("不锈钢连续", 5),
}


def get_contract_name(symbol: str) -> str:
    """Get Chinese name for a contract symbol"""
    return COMMODITY_DICT.get(symbol, (None, None))[0]


def get_contract_size(symbol: str) -> int:
    """Get contract size for a symbol"""
    return COMMODITY_DICT.get(symbol, (None, 1))[1]
