//! Commodity dictionary - mapping Chinese futures contract codes to names and sizes

use std::collections::HashMap;

pub struct CommodityInfo {
    pub name: String,
    pub contract_size: i32,
}

lazy_static::lazy_static! {
    pub static ref COMMODITY_DICT: HashMap<String, CommodityInfo> = {
        let mut m = HashMap::new();

        // DCE (大连商品交易所)
        m.insert("V0".to_string(), CommodityInfo { name: "PVC连续".to_string(), contract_size: 5 });
        m.insert("P0".to_string(), CommodityInfo { name: "棕榈油连续".to_string(), contract_size: 10 });
        m.insert("B0".to_string(), CommodityInfo { name: "豆二连续".to_string(), contract_size: 10 });
        m.insert("M0".to_string(), CommodityInfo { name: "豆粕连续".to_string(), contract_size: 10 });
        m.insert("I0".to_string(), CommodityInfo { name: "铁矿石连续".to_string(), contract_size: 100 });
        m.insert("JD0".to_string(), CommodityInfo { name: "鸡蛋连续".to_string(), contract_size: 10 });
        m.insert("L0".to_string(), CommodityInfo { name: "塑料连续".to_string(), contract_size: 5 });
        m.insert("PP0".to_string(), CommodityInfo { name: "聚丙烯连续".to_string(), contract_size: 5 });
        m.insert("FB0".to_string(), CommodityInfo { name: "纤维板连续".to_string(), contract_size: 10 });
        m.insert("Y0".to_string(), CommodityInfo { name: "豆油连续".to_string(), contract_size: 10 });
        m.insert("C0".to_string(), CommodityInfo { name: "玉米连续".to_string(), contract_size: 10 });
        m.insert("A0".to_string(), CommodityInfo { name: "豆一连续".to_string(), contract_size: 10 });
        m.insert("J0".to_string(), CommodityInfo { name: "焦炭连续".to_string(), contract_size: 100 });
        m.insert("JM0".to_string(), CommodityInfo { name: "焦煤连续".to_string(), contract_size: 60 });
        m.insert("CS0".to_string(), CommodityInfo { name: "淀粉连续".to_string(), contract_size: 10 });
        m.insert("EG0".to_string(), CommodityInfo { name: "乙二醇连续".to_string(), contract_size: 10 });
        m.insert("EB0".to_string(), CommodityInfo { name: "苯乙烯连续".to_string(), contract_size: 5 });
        m.insert("LH0".to_string(), CommodityInfo { name: "生猪连续".to_string(), contract_size: 16 });

        // CZCE (郑州商品交易所)
        m.insert("TA0".to_string(), CommodityInfo { name: "PTA连续".to_string(), contract_size: 5 });
        m.insert("OI0".to_string(), CommodityInfo { name: "菜油连续".to_string(), contract_size: 10 });
        m.insert("RM0".to_string(), CommodityInfo { name: "菜粕连续".to_string(), contract_size: 10 });
        m.insert("SR0".to_string(), CommodityInfo { name: "白糖连续".to_string(), contract_size: 10 });
        m.insert("CF0".to_string(), CommodityInfo { name: "棉花连续".to_string(), contract_size: 5 });
        m.insert("MA0".to_string(), CommodityInfo { name: "甲醇连续".to_string(), contract_size: 10 });
        m.insert("FG0".to_string(), CommodityInfo { name: "玻璃连续".to_string(), contract_size: 20 });
        m.insert("SF0".to_string(), CommodityInfo { name: "硅铁连续".to_string(), contract_size: 5 });
        m.insert("SM0".to_string(), CommodityInfo { name: "锰硅连续".to_string(), contract_size: 5 });
        m.insert("CY0".to_string(), CommodityInfo { name: "棉纱连续".to_string(), contract_size: 5 });
        m.insert("AP0".to_string(), CommodityInfo { name: "苹果连续".to_string(), contract_size: 10 });
        m.insert("CJ0".to_string(), CommodityInfo { name: "红枣连续".to_string(), contract_size: 5 });
        m.insert("UR0".to_string(), CommodityInfo { name: "尿素连续".to_string(), contract_size: 20 });
        m.insert("SA0".to_string(), CommodityInfo { name: "纯碱连续".to_string(), contract_size: 20 });
        m.insert("PK0".to_string(), CommodityInfo { name: "花生连续".to_string(), contract_size: 5 });

        // SHFE (上海期货交易所)
        m.insert("FU0".to_string(), CommodityInfo { name: "燃料油连续".to_string(), contract_size: 10 });
        m.insert("AL0".to_string(), CommodityInfo { name: "铝连续".to_string(), contract_size: 5 });
        m.insert("RU0".to_string(), CommodityInfo { name: "天然橡胶连续".to_string(), contract_size: 10 });
        m.insert("ZN0".to_string(), CommodityInfo { name: "沪锌连续".to_string(), contract_size: 5 });
        m.insert("CU0".to_string(), CommodityInfo { name: "铜连续".to_string(), contract_size: 5 });
        m.insert("RB0".to_string(), CommodityInfo { name: "螺纹钢连续".to_string(), contract_size: 10 });
        m.insert("PB0".to_string(), CommodityInfo { name: "铅连续".to_string(), contract_size: 5 });
        m.insert("BU0".to_string(), CommodityInfo { name: "沥青连续".to_string(), contract_size: 10 });
        m.insert("HC0".to_string(), CommodityInfo { name: "热轧卷板连续".to_string(), contract_size: 10 });
        m.insert("SN0".to_string(), CommodityInfo { name: "锡连续".to_string(), contract_size: 1 });
        m.insert("NI0".to_string(), CommodityInfo { name: "镍连续".to_string(), contract_size: 1 });
        m.insert("SP0".to_string(), CommodityInfo { name: "纸浆连续".to_string(), contract_size: 10 });
        m.insert("NR0".to_string(), CommodityInfo { name: "20号胶连续".to_string(), contract_size: 10 });
        m.insert("SS0".to_string(), CommodityInfo { name: "不锈钢连续".to_string(), contract_size: 5 });

        m
    };
}

pub fn get_contract_name(symbol: &str) -> Option<String> {
    COMMODITY_DICT.get(symbol).map(|info| info.name.clone())
}

pub fn get_contract_size(symbol: &str) -> i32 {
    COMMODITY_DICT.get(symbol).map(|info| info.contract_size).unwrap_or(1)
}

pub fn is_rare_contract(symbol: &str) -> bool {
    let rare_keywords = ["国际铜", "线材", "动力煤", "胶合板", "强麦", "普麦", "稻", "油菜籽"];
    if let Some(name) = get_contract_name(symbol) {
        for keyword in &rare_keywords {
            if name.contains(keyword) {
                return true;
            }
        }
    }
    false
}
