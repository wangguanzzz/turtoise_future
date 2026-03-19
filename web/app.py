"""Streamlit web app for visualizing cointegration analysis"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm

st.set_page_config(page_title="协整分析可视化", layout="wide")

st.title("📊 协整分析可视化工具")

# 合约代码到中文名称的映射
CONTRACT_NAMES = {
    # 贵金属
    "ag": "白银", "au": "黄金",
    # 基本金属
    "cu": "铜", "al": "铝", "zn": "锌", "pb": "铅", "ni": "镍", "sn": "锡",
    # 黑色系
    "rb": "螺纹钢", "hc": "热卷", "i": "铁矿石", "j": "焦炭", "jm": "焦煤",
    "ru": "橡胶", "fu": "燃料油", "bu": "沥青", "sp": "纸浆",
    # 化工
    "v": "PVC", "l": "塑料", "pp": "聚丙烯", "eg": "乙二醇", "eb": "苯乙烯",
    "ma": "甲醇", "ta": "PTA", "ur": "尿素", "sa": "纯碱",
    # 农产品
    "a": "豆一", "b": "豆二", "m": "豆粕", "y": "豆油", "p": "棕榈油",
    "c": "玉米", "cs": "淀粉", "jd": "鸡蛋", "lh": "生猪", "fb": "纤维板",
    "sr": "白糖", "cf": "棉花", "oi": "菜油", "rm": "菜粕", "sf": "硅铁",
    "sm": "锰硅", "cy": "棉纱", "ap": "苹果", "cj": "红枣", "pk": "花生",
    # 有色
    "nr": "20号胶", "ss": "不锈钢",
}

def get_cn_name(code: str) -> str:
    """从合约代码提取中文名称"""
    # 例如: cu2604 -> 铜2604
    prefix = code[:2].lower()
    suffix = code[2:]
    cn_name = CONTRACT_NAMES.get(prefix, prefix.upper())
    return f"{cn_name}{suffix}"

# Load data
@st.cache_data
def load_data():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df = pd.read_csv(os.path.join(base_dir, 'program/market_price.csv'), parse_dates=['datetime'])
    return df

try:
    df = load_data()
    contracts = [c for c in df.columns if c != 'datetime']
    # 创建合约选项列表（显示中文）
    contract_options = [f"{get_cn_name(c)} ({c})" for c in contracts]
    # 映射
    contract_map = {f"{get_cn_name(c)} ({c})": c for c in contracts}
except Exception as e:
    st.error(f"无法加载数据: {e}")
    st.stop()

# Sidebar - Contract selection
st.sidebar.header("选择合约")

# 默认选择铜
default_idx1 = next((i for i, c in enumerate(contracts) if c == 'cu2604'), 0)
default_idx2 = next((i for i, c in enumerate(contracts) if c == 'cu2605'), 1)

option_1 = st.sidebar.selectbox("合约1", contract_options, index=default_idx1)
option_2 = st.sidebar.selectbox("合约2", contract_options, index=default_idx2)

# 获取实际合约代码
asset_1 = contract_map[option_1]
asset_2 = contract_map[option_2]

# Settings
st.sidebar.header("参数设置")
window = st.sidebar.slider("Z-Score 窗口", 5, 60, 21)
zscore_threshold = st.sidebar.slider("Z-Score 阈值", 0.5, 3.0, 1.5, 0.1)

# Calculate functions
def calculate_cointegration(series_1, series_2):
    coint_res = coint(series_1, series_2)
    coint_t = coint_res[0]
    p_value = coint_res[1]
    critical_value = coint_res[2][1]
    model = sm.OLS(series_1, series_2).fit()
    hedge_ratio = model.params[0]
    coint_flag = 1 if p_value < 0.05 and coint_t < critical_value else 0
    return coint_flag, hedge_ratio, p_value, coint_t, critical_value

def calculate_zscore(spread, window):
    spread_series = pd.Series(spread)
    mean = spread_series.rolling(center=False, window=window).mean()
    std = spread_series.rolling(center=False, window=window).std()
    x = spread_series.rolling(center=False, window=1).mean()
    zscore = (x - mean) / std
    return zscore

def calculate_half_life(spread):
    df_spread = pd.DataFrame(spread, columns=['spread'])
    spread_lag = df_spread.spread.shift(1)
    spread_lag.iloc[0] = spread_lag.iloc[1]
    spread_ret = df_spread.spread - spread_lag
    spread_ret.iloc[0] = spread_ret.iloc[1]
    spread_lag2 = sm.add_constant(spread_lag)
    model = sm.OLS(spread_ret, spread_lag2)
    res = model.fit()
    halflife = round(-np.log(2) / res.params.iloc[1], 0)
    return halflife

# Main analysis
if asset_1 and asset_2:
    # Calculate
    series_1 = df[asset_1].values.astype(float)
    series_2 = df[asset_2].values.astype(float)

    coint_flag, hedge_ratio, p_value, coint_t, critical_value = calculate_cointegration(series_1, series_2)
    spread = series_1 - (hedge_ratio * series_2)
    half_life = calculate_half_life(spread)
    zscore = calculate_zscore(spread, window)

    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Hedge Ratio", f"{hedge_ratio:.4f}")
    col2.metric("Half Life", f"{half_life:.0f} 天")
    col3.metric("P-Value", f"{p_value:.4f}")
    col4.metric("T-Stat", f"{coint_t:.4f}")
    col5.metric("协整", "✅ 是" if coint_flag else "❌ 否", delta_color="normal")

    # 中文名称
    cn_name_1 = get_cn_name(asset_1)
    cn_name_2 = get_cn_name(asset_2)

    # Price comparison chart
    st.subheader(f"📈 {cn_name_1} vs {cn_name_2} 价格对比")
    asset_1_norm = series_1 / series_1[0] * 100
    asset_2_norm = series_2 / series_2[0] * 100

    fig1, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(asset_1_norm, label=cn_name_1, linewidth=1.5)
    ax1.plot(asset_2_norm, label=cn_name_2, linewidth=1.5)
    ax1.set_xlabel('时间')
    ax1.set_ylabel('归一化价格 (起点=100)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig1)

    # Spread and Z-Score chart
    st.subheader("📉 Spread 和 Z-Score 分析")

    fig2, ax2 = plt.subplots(figsize=(12, 5))
    ax2.plot(spread, color='blue', label='Spread', linewidth=1.5)
    ax2.set_ylabel('Spread', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    ax2.legend(loc='upper left')

    ax3 = ax2.twinx()
    ax3.plot(zscore, color='green', label='Z-Score', linewidth=1.5, alpha=0.7)
    ax3.axhline(y=0, color='r', linestyle='--', linewidth=1)
    ax3.axhline(y=zscore_threshold, color='orange', linestyle='--', linewidth=1, label=f'+{zscore_threshold} STD')
    ax3.axhline(y=-zscore_threshold, color='orange', linestyle='--', linewidth=1, label=f'-{zscore_threshold} STD')
    ax3.set_ylabel('Z-Score', color='green')
    ax3.tick_params(axis='y', labelcolor='green')
    ax3.legend(loc='upper right')

    st.pyplot(fig2)

    # 交易信号
    latest_zscore = zscore.iloc[-1] if not zscore.empty else 0
    st.subheader("🚨 交易信号")

    signal_col1, signal_col2, signal_col3 = st.columns(3)
    with signal_col1:
        st.info(f"最新 Z-Score: **{latest_zscore:.2f}**")
    with signal_col2:
        if latest_zscore > zscore_threshold:
            st.warning("📉 **做空信号**: Z-Score 超过 +1.5")
        elif latest_zscore < -zscore_threshold:
            st.warning("📈 **做多信号**: Z-Score 低于 -1.5")
        else:
            st.success("⏳ **无信号**: 等待机会")
    with signal_col3:
        half_life_info = f"预计 {half_life:.0f} 天后回归均值" if half_life > 0 else "无法计算"
        st.text(half_life_info)

    # Explanation
    with st.expander("📖 指标说明"):
        st.markdown("""
        - **Hedge Ratio**: 对冲比率，用于计算Spread
        - **Half Life**: 均值回归半周期，表示价差回归均值所需的预期时间
        - **P-Value**: 协整检验的p值，<0.05表示显著协整
        - **T-Stat**: 协整检验的t统计量
        - **Z-Score**: 标准化价差，超过设定阈值表示可能存在交易机会
        - **交易信号**:
          - Z-Score > +1.5: 价差偏高，做空价差
          - Z-Score < -1.5: 价差偏低，做多价差
        """)
