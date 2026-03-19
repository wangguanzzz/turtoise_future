"""Streamlit web app for visualizing cointegration analysis"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm

st.set_page_config(page_title="协整分析可视化", layout="wide")

# 合约代码到中文名称的映射 (全局定义，供所有页面使用)
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
    prefix = code[:2].lower()
    suffix = code[2:]
    cn_name = CONTRACT_NAMES.get(prefix, prefix.upper())
    return f"{cn_name}{suffix}"

# 添加页面导航
page = st.sidebar.radio("功能选择", ["协整分析", "回测", "配对概览"])

if page == "回测":
    st.title("📈 回测")
    st.markdown("对协整配对交易策略进行历史回测")

    # 加载回测模块
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from turtoise_future.strategies.pair_trading.backtest import run_backtest, load_backtest_data

    # 回测参数设置
    st.sidebar.header("回测参数")

    # 日期范围
    try:
        df_prices, df_pairs = load_backtest_data()
        min_date = pd.to_datetime(df_prices['datetime']).min().date()
        max_date = pd.to_datetime(df_prices['datetime']).max().date()
    except Exception as e:
        st.error(f"无法加载回测数据: {e}")
        st.stop()

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("开始日期", min_date, min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.date_input("结束日期", max_date, min_value=min_date, max_value=max_date)

    # 资金和参数
    initial_capital = st.sidebar.number_input("初始资金 (USD)", value=100000, step=10000, key="capital_bt")
    zscore_threshold = st.sidebar.slider("Z-Score 阈值", 0.5, 3.0, 1.5, 0.1, key="zscore_bt")
    half_life_threshold = st.sidebar.slider("半衰期阈值 (天)", 1, 20, 8, key="halflife_bt")
    window = st.sidebar.slider("Z-Score 窗口", 5, 60, 21, key="window_bt")
    usd_per_trade = st.sidebar.number_input("每笔交易金额 (USD)", value=50000, step=10000, key="usd_bt")
    commission_per_trade = st.sidebar.slider("手续费 (USD/笔)", 0.0, 500.0, 0.0, 10.0, key="commission_bt", help="每笔交易扣除的手续费（开仓+平仓各一次）")

    # 运行回测
    if st.button("🚀 运行回测", type="primary"):
        with st.spinner("回测运行中..."):
            try:
                result = run_backtest(
                    df_prices=df_prices,
                    df_pairs=df_pairs,
                    start_date=str(start_date),
                    end_date=str(end_date),
                    initial_capital=initial_capital,
                    zscore_threshold=zscore_threshold,
                    half_life_threshold=half_life_threshold,
                    window=window,
                    usd_per_trade=usd_per_trade,
                    commission_per_trade=commission_per_trade,
                )

                # 显示绩效指标
                st.subheader("📊 绩效指标")
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("初始资金", f"${result.initial_capital:,.0f}")
                m2.metric("最终资金", f"${result.final_capital:,.0f}")
                m3.metric("总收益率", f"{result.total_return*100:.2f}%")
                m4.metric("年化收益率", f"{result.annualized_return*100:.2f}%")
                m5.metric("夏普比率", f"{result.sharpe_ratio:.2f}")
                m6.metric("最大回撤", f"{result.max_drawdown*100:.2f}%")

                m7, m8, m9 = st.columns(3)
                m7.metric("胜率", f"{result.win_rate*100:.1f}%")
                m8.metric("盈亏比", f"{result.profit_loss_ratio:.2f}")
                m9.metric("交易次数", result.total_trades)

                # 权益曲线
                if result.equity_curve:
                    st.subheader("📈 权益曲线")
                    equity_df = pd.DataFrame(result.equity_curve)
                    fig_equity, ax = plt.subplots(figsize=(12, 5))
                    ax.plot(equity_df['capital'], linewidth=2, color='green')
                    ax.fill_between(range(len(equity_df)), equity_df['capital'], alpha=0.3, color='green')
                    ax.set_xlabel('时间')
                    ax.set_ylabel('资金 (USD)')
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig_equity)

                # 交易记录
                if result.trades:
                    st.subheader("📋 交易记录")
                    trades_df = pd.DataFrame(result.trades)

                    # 添加颜色标注
                    def color_pnl(val):
                        color = 'green' if val > 0 else 'red' if val < 0 else 'black'
                        return f'color: {color}'

                    # 显示表格
                    st.dataframe(
                        trades_df[['pair', 'entry_date', 'exit_date', 'direction', 'entry_zscore', 'exit_zscore', 'pnl']]
                        .style.format({'entry_zscore': '{:.2f}', 'exit_zscore': '{:.2f}', 'pnl': '${:.2f}'})
                        .applymap(lambda x: 'color: green' if isinstance(x, (int, float)) and x > 0 else ('color: red' if isinstance(x, (int, float)) and x < 0 else ''), subset=['pnl']),
                        use_container_width=True
                    )

                # 说明
                with st.expander("📖 回测参数说明"):
                    st.markdown(f"""
                    - **Z-Score 阈值**: 开仓信号触发阈值，当前为 {zscore_threshold}
                    - **半衰期阈值**: 只交易半衰期小于 {half_life_threshold} 天的配对
                    - **Z-Score 窗口**: 计算 Z-Score 使用的历史窗口天数，当前为 {window} 天
                    - **每笔交易金额**: 每边合约的交易金额，当前为 ${usd_per_trade:,}
                    - **手续费**: 每笔交易扣除的手续费，当前为 ${commission_per_trade:.0f}/笔（开仓+平仓共扣 {commission_per_trade*2:.0f} USD）
                    """)

            except Exception as e:
                st.error(f"回测失败: {e}")
                import traceback
                st.text(traceback.format_exc())

elif page == "配对概览":
    st.title("🔗 协整配对概览")
    st.markdown("展示所有发现的协整配对及其关系热力图")

    # 加载配对数据
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from turtoise_future.strategies.pair_trading.backtest import load_backtest_data

    try:
        df_pairs = load_backtest_data()[1]  # 只取 pairs DataFrame
    except Exception as e:
        st.error(f"无法加载配对数据: {e}")
        st.stop()

    # 统计概览
    st.subheader("📊 统计概览")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总配对数", len(df_pairs))

    # 获取所有合约
    all_contracts = set(df_pairs['base_market'].unique()) | set(df_pairs['quote_market'].unique())
    col2.metric("涉及合约数", len(all_contracts))

    col3.metric("平均半衰期", f"{df_pairs['half_life'].mean():.1f} 天")
    col4.metric("最短半衰期", f"{df_pairs['half_life'].min():.0f} 天")

    # 按品种统计配对数量
    st.subheader("📈 按品种统计配对数量")
    df_pairs['base_prefix'] = df_pairs['base_market'].str[:2]
    df_pairs['quote_prefix'] = df_pairs['quote_market'].str[:2]
    prefix_counts = pd.concat([
        df_pairs['base_prefix'].value_counts(),
        df_pairs['quote_prefix'].value_counts()
    ]).groupby(level=0).sum().sort_values(ascending=True)

    fig_prefix, ax_prefix = plt.subplots(figsize=(10, 6))
    prefix_counts.plot(kind='barh', ax=ax_prefix, color='steelblue')
    ax_prefix.set_xlabel('配对数量')
    ax_prefix.set_ylabel('品种')
    ax_prefix.grid(True, alpha=0.3)
    st.pyplot(fig_prefix)

    # 半衰期分布
    st.subheader("📉 半衰期分布")
    fig_hl, ax_hl = plt.subplots(figsize=(8, 4))
    df_pairs['half_life'].hist(bins=20, ax=ax_hl, color='steelblue', edgecolor='white')
    ax_hl.set_xlabel('半衰期 (天)')
    ax_hl.set_ylabel('配对数量')
    ax_hl.grid(True, alpha=0.3)
    st.pyplot(fig_hl)

    # 热力图 - 构建配对矩阵
    st.subheader("🗺️ 配对关系热力图")
    st.markdown("颜色表示回归速度（越深表示均值回归越快）")

    # 获取合约列表（按品种分组排序）
    all_contracts_sorted = sorted(all_contracts, key=lambda x: (x[:2], x[2:]))

    # 创建邻接矩阵
    n = len(all_contracts_sorted)
    contract_to_idx = {c: i for i, c in enumerate(all_contracts_sorted)}

    # 使用半衰期倒数作为值（越小越快回归，颜色越深）
    matrix = np.zeros((n, n))
    for _, row in df_pairs.iterrows():
        i = contract_to_idx.get(row['base_market'])
        j = contract_to_idx.get(row['quote_market'])
        if i is not None and j is not None:
            # 使用倒数，半衰期越小值越大（颜色越深）
            matrix[i, j] = 1.0 / row['half_life'] if row['half_life'] > 0 else 1
            matrix[j, i] = 1.0 / row['half_life'] if row['half_life'] > 0 else 1

    # 绘制热力图
    fig_heat, ax_heat = plt.subplots(figsize=(14, 12))
    im = ax_heat.imshow(matrix, cmap='YlOrRd', aspect='auto')

    # 设置标签
    ax_heat.set_xticks(range(n))
    ax_heat.set_yticks(range(n))
    ax_heat.set_xticklabels(all_contracts_sorted, rotation=90, fontsize=7)
    ax_heat.set_yticklabels(all_contracts_sorted, fontsize=7)

    ax_heat.set_xlabel('合约')
    ax_heat.set_ylabel('合约')

    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax_heat, shrink=0.8)
    cbar.set_label('回归速度 (1/半衰期)', rotation=270, labelpad=15)

    st.pyplot(fig_heat)

    # 配对列表
    st.subheader("📋 配对列表")
    display_df = df_pairs[['base_market', 'quote_market', 'hedge_ratio', 'half_life']].copy()
    display_df['base_name'] = display_df['base_market'].apply(get_cn_name)
    display_df['quote_name'] = display_df['quote_market'].apply(get_cn_name)
    display_df = display_df[['base_market', 'base_name', 'quote_market', 'quote_name', 'hedge_ratio', 'half_life']]
    display_df.columns = ['合约1', '名称', '合约2', '名称', '对冲比率', '半衰期']

    st.dataframe(
        display_df.style.format({
            '对冲比率': '{:.4f}',
            '半衰期': '{:.0f}'
        }),
        use_container_width=True
    )

else:
    # 原有协整分析页面
    st.title("📊 协整分析可视化工具")

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
window = st.sidebar.slider("Z-Score 窗口", 5, 60, 21, key="window_coint")
zscore_threshold = st.sidebar.slider("Z-Score 阈值", 0.5, 3.0, 1.5, 0.1, key="zscore_coint")

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
