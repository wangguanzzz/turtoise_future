//! Web UI module for Turtoise Future
//!
//! Provides HTTP server with HTML pages for cointegration analysis, backtesting, and pairs overview.

use axum::{
    extract::{Form, Query, State},
    response::{Html, IntoResponse, Redirect},
    routing::{get, post},
    Router,
};
use serde::Deserialize;
use std::collections::{HashMap, HashSet};
use tower_http::cors::{Any, CorsLayer};

use crate::commodity::get_contract_name;
use crate::data::{load_cointegrated_pairs, load_market_prices, MarketPrices};
use crate::strategies::cointegration::calculate_zscore;

/// Application state shared across handlers
#[derive(Clone)]
pub struct AppState {
    pub data_dir: String,
}

impl AppState {
    pub fn new(data_dir: String) -> Self {
        Self { data_dir }
    }
}

// =============================================================================
// Handlers
// =============================================================================

/// Home page - redirect to analysis
pub async fn home() -> impl IntoResponse {
    Redirect::to("/analysis")
}

/// Cointegration analysis page
pub async fn analysis_page(
    State(state): State<AppState>,
    Query(params): Query<AnalysisQuery>,
) -> impl IntoResponse {
    let prices_path = std::path::Path::new(&state.data_dir).join("market_price.csv");

    let prices = match load_market_prices(&prices_path) {
        Ok(p) => p,
        Err(e) => {
            return Html(render_error_page("无法加载数据", &e.to_string()));
        }
    };

    let contracts: Vec<(String, String)> = prices
        .contracts
        .iter()
        .map(|c| {
            let cn_name = get_contract_name(c).unwrap_or_else(|| c.clone());
            (c.clone(), cn_name)
        })
        .collect();

    let selected1 = params.contract1.clone().unwrap_or_else(|| {
        contracts.iter().find(|c| c.0.starts_with("cu")).map(|c| c.0.clone())
            .unwrap_or_else(|| contracts.first().map(|c| c.0.clone()).unwrap_or_default())
    });
    let selected2 = params.contract2.clone().unwrap_or_else(|| {
        contracts.iter().skip(1).find(|c| c.0.starts_with("cu")).map(|c| c.0.clone())
            .unwrap_or_else(|| contracts.get(1).map(|c| c.0.clone()).unwrap_or_default())
    });
    let window = params.window.unwrap_or(21);
    let zscore_threshold = params.zscore_threshold.unwrap_or(1.5);

    // Generate contract options HTML
    let contract_options: String = contracts.iter()
        .map(|(code, cn_name)| {
            let sel1 = if code == &selected1 { "selected" } else { "" };
            let sel2 = if code == &selected2 { "selected" } else { "" };
            format!(r#"<option value="{}" {}>{}{}</option>"#, code, sel1, cn_name, code)
        })
        .collect();

    // If we have selected contracts, calculate analysis
    if !selected1.is_empty() && !selected2.is_empty() {
        if let Some(result_html) = calculate_analysis(&prices, &selected1, &selected2, window, zscore_threshold) {
            let content = format!(r#"
<div class="row">
    <div class="sidebar">
        <h3>参数设置</h3>
        <form id="analysisForm">
            <div class="form-group">
                <label for="contract1">合约1</label>
                <select id="contract1" name="contract1">{}</select>
            </div>
            <div class="form-group">
                <label for="contract2">合约2</label>
                <select id="contract2" name="contract2">{}</select>
            </div>
            <div class="form-group">
                <label for="window">Z-Score 窗口 (天)</label>
                <input type="number" id="window" name="window" value="{}" min="5" max="60">
            </div>
            <div class="form-group">
                <label for="zscore_threshold">Z-Score 阈值</label>
                <input type="number" id="zscore_threshold" name="zscore_threshold" value="{}" min="0.5" max="3.0" step="0.1">
            </div>
            <button type="submit" class="btn-secondary">分析</button>
        </form>
    </div>
    <div style="flex: 1;">
        {}
    </div>
</div>
<script>
document.getElementById('analysisForm').onsubmit = function(e) {{
    e.preventDefault();
    var c1 = document.getElementById('contract1').value;
    var c2 = document.getElementById('contract2').value;
    var w = document.getElementById('window').value;
    var z = document.getElementById('zscore_threshold').value;
    window.location.href = '/analysis?contract1=' + c1 + '&contract2=' + c2 + '&window=' + w + '&zscore_threshold=' + z;
}};
</script>
"#, contract_options, contract_options, window, zscore_threshold, result_html);

            return Html(render_page("协整分析 - Turtoise Future", "analysis", &content));
        }
    }

    // Default page without results
    let content = format!(r#"
<div class="row">
    <div class="sidebar">
        <h3>参数设置</h3>
        <form id="analysisForm">
            <div class="form-group">
                <label for="contract1">合约1</label>
                <select id="contract1" name="contract1">{}</select>
            </div>
            <div class="form-group">
                <label for="contract2">合约2</label>
                <select id="contract2" name="contract2">{}</select>
            </div>
            <div class="form-group">
                <label for="window">Z-Score 窗口 (天)</label>
                <input type="number" id="window" name="window" value="{}" min="5" max="60">
            </div>
            <div class="form-group">
                <label for="zscore_threshold">Z-Score 阈值</label>
                <input type="number" id="zscore_threshold" name="zscore_threshold" value="{}" min="0.5" max="3.0" step="0.1">
            </div>
            <button type="submit" class="btn-secondary">分析</button>
        </form>
    </div>
    <div style="flex: 1;">
        <div class="card"><p>请选择两个合约然后点击"分析"按钮</p></div>
    </div>
</div>
<script>
document.getElementById('analysisForm').onsubmit = function(e) {{
    e.preventDefault();
    var c1 = document.getElementById('contract1').value;
    var c2 = document.getElementById('contract2').value;
    var w = document.getElementById('window').value;
    var z = document.getElementById('zscore_threshold').value;
    window.location.href = '/analysis?contract1=' + c1 + '&contract2=' + c2 + '&window=' + w + '&zscore_threshold=' + z;
}};
</script>
"#, contract_options, contract_options, window, zscore_threshold);

    Html(render_page("协整分析 - Turtoise Future", "analysis", &content))
}

fn calculate_analysis(prices: &MarketPrices, contract1: &str, contract2: &str, window: usize, zscore_threshold: f64) -> Option<String> {
    let series1 = prices.get_series(contract1);
    let series2 = prices.get_series(contract2);

    if series1.len() < 20 || series1.len() != series2.len() {
        return None;
    }

    // Calculate hedge ratio using OLS
    let hedge_ratio = calculate_hedge_ratio(&series1, &series2);

    // Calculate spread
    let spread: Vec<f64> = series1.iter().zip(series2.iter())
        .map(|(s1, s2)| s1 - hedge_ratio * s2)
        .collect();

    // Calculate z-score
    let zscores = calculate_zscore(&spread, window);
    let latest_zscore = zscores.last().copied().unwrap_or(0.0);

    // Calculate half-life (simplified)
    let half_life = calculate_half_life_simple(&spread);

    // Determine signal
    let (signal, signal_class) = if latest_zscore > zscore_threshold {
        ("做空", "negative")
    } else if latest_zscore < -zscore_threshold {
        ("做多", "positive")
    } else {
        ("等待", "")
    };

    // Normalize prices
    let norm1: Vec<f64> = if series1[0] != 0.0 {
        series1.iter().map(|p| p / series1[0] * 100.0).collect()
    } else {
        vec![]
    };
    let norm2: Vec<f64> = if series2[0] != 0.0 {
        series2.iter().map(|p| p / series2[0] * 100.0).collect()
    } else {
        vec![]
    };

    // Serialize data for JavaScript
    let dates_json = serde_json::to_string(&prices.datetimes).unwrap_or_else(|_| "[]".to_string());
    let norm1_json = serde_json::to_string(&norm1).unwrap_or_else(|_| "[]".to_string());
    let norm2_json = serde_json::to_string(&norm2).unwrap_or_else(|_| "[]".to_string());
    let spread_json = serde_json::to_string(&spread).unwrap_or_else(|_| "[]".to_string());
    let zscore_json = serde_json::to_string(&zscores).unwrap_or_else(|_| "[]".to_string());

    let half_life_str = format!("{:.0}", half_life);
    let half_life_forecast = if half_life > 0.0 {
        format!("{:.0} 天后回归", half_life)
    } else {
        "无均值回归".to_string()
    };

    let cn_name1 = get_contract_name(contract1).unwrap_or_else(|| contract1.to_string());
    let cn_name2 = get_contract_name(contract2).unwrap_or_else(|| contract2.to_string());

    Some(format!(r#"
        <div class="card">
            <h2>协整指标</h2>
            <div class="metrics">
                <div class="metric"><div class="metric-value">{:.4}</div><div class="metric-label">Hedge Ratio</div></div>
                <div class="metric"><div class="metric-value">{}</div><div class="metric-label">Half Life (天)</div></div>
                <div class="metric"><div class="metric-value">{:.2}</div><div class="metric-label">最新 Z-Score</div></div>
                <div class="metric"><div class="metric-value {}">{}</div><div class="metric-label">信号</div></div>
                <div class="metric"><div class="metric-value">{}</div><div class="metric-label">预计回归</div></div>
            </div>
        </div>
        <div class="card">
            <h2>{} vs {} 价格对比 (归一化)</h2>
            <div id="priceChart" class="chart-container"></div>
        </div>
        <div class="card">
            <h2>Spread 和 Z-Score 分析</h2>
            <div id="spreadChart" class="chart-container"></div>
        </div>
        <script>
        var dates = {};
        var norm1 = {};
        var norm2 = {};
        var spread = {};
        var zscore = {};
        var priceChart = echarts.init(document.getElementById('priceChart'));
        priceChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            legend: {{ data: ['{}', '{}'] }},
            xAxis: {{ type: 'category', data: dates, axisLabel: {{ rotate: 45 }} }},
            yAxis: {{ type: 'value', name: '归一化价格' }},
            series: [
                {{ name: '{}', type: 'line', data: norm1, smooth: true }},
                {{ name: '{}', type: 'line', data: norm2, smooth: true }}
            ],
            grid: {{ bottom: 80 }}
        }});
        var spreadChart = echarts.init(document.getElementById('spreadChart'));
        spreadChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            legend: {{ data: ['Spread', 'Z-Score'] }},
            xAxis: {{ type: 'category', data: dates, axisLabel: {{ rotate: 45 }} }},
            yAxis: [
                {{ type: 'value', name: 'Spread', position: 'left' }},
                {{ type: 'value', name: 'Z-Score', position: 'right' }}
            ],
            series: [
                {{ name: 'Spread', type: 'line', data: spread, smooth: true, yAxisIndex: 0 }},
                {{ name: 'Z-Score', type: 'line', data: zscore, smooth: true, yAxisIndex: 1 }}
            ],
            grid: {{ bottom: 80 }}
        }});
        </script>
    "#,
        hedge_ratio, half_life_str, latest_zscore, signal_class, signal, half_life_forecast,
        cn_name1, cn_name2,
        dates_json, norm1_json, norm2_json, spread_json, zscore_json,
        contract1, contract2, contract1, contract2
    ))
}

fn calculate_hedge_ratio(series1: &[f64], series2: &[f64]) -> f64 {
    let n = series1.len().min(series2.len());
    if n == 0 { return 1.0; }
    let s1 = &series1[..n];
    let s2 = &series2[..n];
    let mean1 = s1.iter().sum::<f64>() / n as f64;
    let mean2 = s2.iter().sum::<f64>() / n as f64;
    let mut cov = 0.0;
    let mut var2 = 0.0;
    for i in 0..n {
        let d1 = s1[i] - mean1;
        let d2 = s2[i] - mean2;
        cov += d1 * d2;
        var2 += d2 * d2;
    }
    if var2 != 0.0 { cov / var2 } else { 1.0 }
}

fn calculate_half_life_simple(spread: &[f64]) -> f64 {
    let n = spread.len();
    if n < 3 { return 0.0; }
    let diff: Vec<f64> = spread.windows(2).map(|w| w[1] - w[0]).collect();
    let n_diff = diff.len();
    if n_diff < 3 { return 10.0; }
    let mean_diff = diff.iter().sum::<f64>() / n_diff as f64;
    let mut autocorr = 0.0;
    for i in 1..n_diff {
        let lag = diff[i - 1] - mean_diff;
        let cur = diff[i] - mean_diff;
        autocorr += lag * cur;
    }
    let var = diff.iter().map(|d| (d - mean_diff).powi(2)).sum::<f64>() / n_diff as f64;
    if var > 0.0 { autocorr /= var * (n_diff - 1) as f64; }
    if autocorr > 0.0 && autocorr < 1.0 {
        (-f64::ln(1.0 - autocorr)).abs()
    } else {
        10.0
    }
}

#[derive(Debug, Deserialize)]
pub struct AnalysisQuery {
    pub contract1: Option<String>,
    pub contract2: Option<String>,
    pub window: Option<usize>,
    pub zscore_threshold: Option<f64>,
}

/// Backtest page
pub async fn backtest_page(State(state): State<AppState>) -> impl IntoResponse {
    let prices_path = std::path::Path::new(&state.data_dir).join("market_price.csv");

    let prices = match load_market_prices(&prices_path) {
        Ok(p) => p,
        Err(e) => {
            return Html(render_error_page("无法加载数据", &e.to_string()));
        }
    };

    let min_date = prices.datetimes.first().cloned().unwrap_or_default();
    let max_date = prices.datetimes.last().cloned().unwrap_or_default();

    let content = format!(r#"
<form action="/backtest/run" method="post" class="row">
    <div class="sidebar">
        <h3>回测参数</h3>
        <div class="form-group">
            <label for="start_date">开始日期</label>
            <input type="date" id="start_date" name="start_date" value="{}">
        </div>
        <div class="form-group">
            <label for="end_date">结束日期</label>
            <input type="date" id="end_date" name="end_date" value="{}">
        </div>
        <div class="form-group">
            <label for="initial_capital">初始资金 (USD)</label>
            <input type="number" id="initial_capital" name="initial_capital" value="100000" step="10000">
        </div>
        <div class="form-group">
            <label for="zscore_threshold">Z-Score 阈值</label>
            <input type="number" id="zscore_threshold" name="zscore_threshold" value="1.5" min="0.5" max="3.0" step="0.1">
        </div>
        <div class="form-group">
            <label for="half_life_threshold">半衰期阈值 (天)</label>
            <input type="number" id="half_life_threshold" name="half_life_threshold" value="8" min="1" max="20">
        </div>
        <div class="form-group">
            <label for="window">Z-Score 窗口</label>
            <input type="number" id="window" name="window" value="21" min="5" max="60">
        </div>
        <div class="form-group">
            <label for="usd_per_trade">每笔交易金额 (USD)</label>
            <input type="number" id="usd_per_trade" name="usd_per_trade" value="50000" step="10000">
        </div>
        <div class="form-group">
            <label for="commission">手续费 (USD/笔)</label>
            <input type="number" id="commission" name="commission" value="0" step="10">
        </div>
        <button type="submit">运行回测</button>
    </div>
    <div style="flex: 1;">
        <div class="card"><p>点击"运行回测"按钮开始回测分析</p></div>
    </div>
</form>
"#, min_date, max_date);

    Html(render_page("回测 - Turtoise Future", "backtest", &content))
}

#[derive(Debug, Deserialize)]
pub struct BacktestForm {
    pub start_date: String,
    pub end_date: String,
    pub initial_capital: f64,
    pub zscore_threshold: f64,
    pub half_life_threshold: usize,
    pub window: usize,
    pub usd_per_trade: f64,
    pub commission: f64,
}

/// Run backtest
pub async fn run_backtest(
    State(state): State<AppState>,
    Form(form): Form<BacktestForm>,
) -> impl IntoResponse {
    let prices_path = std::path::Path::new(&state.data_dir).join("market_price.csv");
    let pairs_path = std::path::Path::new(&state.data_dir).join("cointegrated_pairs.csv");

    let prices = match load_market_prices(&prices_path) {
        Ok(p) => p,
        Err(e) => {
            return Html(render_error_page("无法加载价格数据", &e.to_string()));
        }
    };

    let pairs = match load_cointegrated_pairs(&pairs_path) {
        Ok(p) => p,
        Err(e) => {
            return Html(render_error_page("无法加载配对数据", &e.to_string()));
        }
    };

    let result = crate::backtest::run_backtest(
        &prices,
        &pairs,
        &form.start_date,
        &form.end_date,
        form.initial_capital,
        form.zscore_threshold,
        form.half_life_threshold,
        form.window,
        form.usd_per_trade,
        form.commission,
        true,
    );

    let equity_dates: Vec<String> = result.equity_curve.iter().map(|e| e.date.clone()).collect();
    let equity_capitals: Vec<f64> = result.equity_curve.iter().map(|e| e.capital).collect();

    let total_return_pct = result.total_return * 100.0;
    let annualized_return_pct = result.annualized_return * 100.0;
    let max_drawdown_pct = result.max_drawdown * 100.0;
    let win_rate_pct = result.win_rate * 100.0;

    let return_class = if result.total_return >= 0.0 { "pnl-positive" } else { "pnl-negative" };
    let ann_return_class = if result.annualized_return >= 0.0 { "pnl-positive" } else { "pnl-negative" };
    let dd_class = if result.max_drawdown > 0.0 { "pnl-negative" } else { "" };

    // Build trades table
    let trades_rows: String = result.trades.iter().map(|t| {
        let pnl_class = if t.pnl.unwrap_or(0.0) >= 0.0 { "pnl-positive" } else { "pnl-negative" };
        format!(r#"<tr>
            <td>{}</td><td>{}</td><td>{}</td><td>{}</td>
            <td>{:.2}</td><td>{:.2}</td>
            <td class="{}">${:.2}</td>
        </tr>"#,
            t.pair, t.direction, t.entry_date,
            t.exit_date.clone().unwrap_or_default(),
            t.entry_zscore, t.exit_zscore.unwrap_or(0.0),
            pnl_class, t.pnl.unwrap_or(0.0)
        )
    }).collect();

    let equity_dates_json = serde_json::to_string(&equity_dates).unwrap_or_else(|_| "[]".to_string());
    let equity_capitals_json = serde_json::to_string(&equity_capitals).unwrap_or_else(|_| "[]".to_string());

    let content = format!(r#"
<form action="/backtest/run" method="post" class="row">
    <div class="sidebar">
        <h3>回测参数</h3>
        <div class="form-group">
            <label for="start_date">开始日期</label>
            <input type="date" id="start_date" name="start_date" value="{}">
        </div>
        <div class="form-group">
            <label for="end_date">结束日期</label>
            <input type="date" id="end_date" name="end_date" value="{}">
        </div>
        <div class="form-group">
            <label for="initial_capital">初始资金 (USD)</label>
            <input type="number" id="initial_capital" name="initial_capital" value="100000" step="10000">
        </div>
        <div class="form-group">
            <label for="zscore_threshold">Z-Score 阈值</label>
            <input type="number" id="zscore_threshold" name="zscore_threshold" value="1.5" min="0.5" max="3.0" step="0.1">
        </div>
        <div class="form-group">
            <label for="half_life_threshold">半衰期阈值 (天)</label>
            <input type="number" id="half_life_threshold" name="half_life_threshold" value="8" min="1" max="20">
        </div>
        <div class="form-group">
            <label for="window">Z-Score 窗口</label>
            <input type="number" id="window" name="window" value="21" min="5" max="60">
        </div>
        <div class="form-group">
            <label for="usd_per_trade">每笔交易金额 (USD)</label>
            <input type="number" id="usd_per_trade" name="usd_per_trade" value="50000" step="10000">
        </div>
        <div class="form-group">
            <label for="commission">手续费 (USD/笔)</label>
            <input type="number" id="commission" name="commission" value="0" step="10">
        </div>
        <button type="submit">运行回测</button>
    </div>
    <div style="flex: 1;">
        <div class="card">
            <h2>绩效指标</h2>
            <div class="metrics">
                <div class="metric"><div class="metric-value">${:.0}</div><div class="metric-label">初始资金</div></div>
                <div class="metric"><div class="metric-value">${:.0}</div><div class="metric-label">最终资金</div></div>
                <div class="metric"><div class="metric-value {}">{:.2}%</div><div class="metric-label">总收益率</div></div>
                <div class="metric"><div class="metric-value {}">{:.2}%</div><div class="metric-label">年化收益率</div></div>
                <div class="metric"><div class="metric-value">{:.2}</div><div class="metric-label">夏普比率</div></div>
                <div class="metric"><div class="metric-value {}">{:.2}%</div><div class="metric-label">最大回撤</div></div>
                <div class="metric"><div class="metric-value">{:.1}%</div><div class="metric-label">胜率</div></div>
                <div class="metric"><div class="metric-value">{:.2}</div><div class="metric-label">盈亏比</div></div>
                <div class="metric"><div class="metric-value">{}</div><div class="metric-label">交易次数</div></div>
            </div>
        </div>
        <div class="card">
            <h2>权益曲线</h2>
            <div id="equityChart" class="chart-container"></div>
        </div>
        <div class="card">
            <h2>交易记录</h2>
            <table>
                <thead><tr><th>配对</th><th>方向</th><th>入场日期</th><th>出场日期</th><th>入场Z</th><th>出场Z</th><th>盈亏</th></tr></thead>
                <tbody>{}</tbody>
            </table>
        </div>
    </div>
</form>
<script>
var dates = {};
var capitals = {};
var equityChart = echarts.init(document.getElementById('equityChart'));
equityChart.setOption({{
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: dates, axisLabel: {{ rotate: 45 }} }},
    yAxis: {{ type: 'value', name: '资金 (USD)' }},
    series: [{{
        name: '资金',
        type: 'line',
        data: capitals,
        smooth: true,
        areaStyle: {{ opacity: 0.3 }},
        lineStyle: {{ color: '#4CAF50', width: 2 }},
        itemStyle: {{ color: '#4CAF50' }}
    }}],
    grid: {{ bottom: 80 }}
}});
</script>
"#,
        form.start_date, form.end_date,
        result.initial_capital, result.final_capital,
        return_class, total_return_pct,
        ann_return_class, annualized_return_pct,
        result.sharpe_ratio,
        dd_class, max_drawdown_pct,
        win_rate_pct, result.profit_loss_ratio, result.total_trades,
        trades_rows,
        equity_dates_json, equity_capitals_json
    );

    Html(render_page("回测结果 - Turtoise Future", "backtest", &content))
}

/// Pairs overview page
pub async fn pairs_page(State(state): State<AppState>) -> impl IntoResponse {
    let pairs_path = std::path::Path::new(&state.data_dir).join("cointegrated_pairs.csv");

    let pairs = match load_cointegrated_pairs(&pairs_path) {
        Ok(p) => p,
        Err(e) => {
            return Html(render_error_page("无法加载配对数据", &e.to_string()));
        }
    };

    let total_pairs = pairs.len();

    let mut contracts: HashSet<String> = HashSet::new();
    for pair in &pairs {
        contracts.insert(pair.base_market.clone());
        contracts.insert(pair.quote_market.clone());
    }
    let total_contracts = contracts.len();

    let half_lives: Vec<f64> = pairs.iter().map(|p| p.half_life).filter(|h| *h > 0.0).collect();
    let avg_half_life = if half_lives.is_empty() { 0.0 } else { half_lives.iter().sum::<f64>() / half_lives.len() as f64 };
    let min_half_life = half_lives.iter().copied().fold(0.0, f64::min);

    // Build pairs table
    let pairs_rows: String = pairs.iter().map(|p| {
        let base_name = get_contract_name(&p.base_market).unwrap_or_else(|| p.base_market.clone());
        let quote_name = get_contract_name(&p.quote_market).unwrap_or_else(|| p.quote_market.clone());
        format!(r#"<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{:.4}</td><td>{:.0} 天</td></tr>"#,
            p.base_market, base_name, p.quote_market, quote_name, p.hedge_ratio, p.half_life)
    }).collect();

    let content = format!(r#"
<div class="card">
    <h2>统计概览</h2>
    <div class="metrics">
        <div class="metric"><div class="metric-value">{}</div><div class="metric-label">总配对数</div></div>
        <div class="metric"><div class="metric-value">{}</div><div class="metric-label">涉及合约数</div></div>
        <div class="metric"><div class="metric-value">{:.1} 天</div><div class="metric-label">平均半衰期</div></div>
        <div class="metric"><div class="metric-value">{:.0} 天</div><div class="metric-label">最短半衰期</div></div>
    </div>
</div>
<div class="card">
    <h2>配对列表</h2>
    <table>
        <thead><tr><th>合约1</th><th>名称</th><th>合约2</th><th>名称</th><th>对冲比率</th><th>半衰期</th></tr></thead>
        <tbody>{}</tbody>
    </table>
</div>
"#, total_pairs, total_contracts, avg_half_life, min_half_life, pairs_rows);

    Html(render_page("配对概览 - Turtoise Future", "pairs", &content))
}

/// Render a complete page
fn render_page(title: &str, page: &str, content: &str) -> String {
    format!(r#"<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #333; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 20px 0; margin-bottom: 30px; text-align: center; }}
        header h1 {{ font-size: 2rem; }}
        nav {{ background: white; padding: 15px 0; margin-bottom: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        nav ul {{ display: flex; justify-content: center; list-style: none; gap: 30px; }}
        nav a {{ text-decoration: none; color: #333; font-weight: 500; padding: 8px 16px; border-radius: 4px; transition: all 0.2s; }}
        nav a:hover, nav a.active {{ background: #4CAF50; color: white; }}
        .card {{ background: white; border-radius: 8px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .card h2 {{ color: #1a1a2e; margin-bottom: 20px; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .metric {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2rem; font-weight: bold; color: #4CAF50; }}
        .metric-label {{ color: #666; font-size: 0.9rem; margin-top: 5px; }}
        .pnl-positive {{ color: #4CAF50; }}
        .pnl-negative {{ color: #e53935; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .chart-container {{ width: 100%; height: 400px; margin: 20px 0; }}
        .form-group {{ margin-bottom: 15px; }}
        label {{ display: block; margin-bottom: 5px; font-weight: 500; }}
        input, select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; }}
        button {{ background: #4CAF50; color: white; border: none; padding: 12px 24px; border-radius: 4px; cursor: pointer; font-size: 1rem; }}
        button:hover {{ background: #45a049; }}
        .row {{ display: grid; grid-template-columns: 300px 1fr; gap: 20px; }}
        .sidebar {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); height: fit-content; }}
        footer {{ text-align: center; padding: 20px; color: #666; margin-top: 40px; }}
    </style>
</head>
<body>
    <header><h1>Turtoise Future - 期货量化交易系统</h1></header>
    <div class="container">
        <nav>
            <ul>
                <li><a href="/analysis" {}>协整分析</a></li>
                <li><a href="/backtest" {}>回测</a></li>
                <li><a href="/pairs" {}>配对概览</a></li>
            </ul>
        </nav>
        {}
    </div>
    <footer><p>Turtoise Future - Rust Implementation</p></footer>
</body>
</html>"#,
        title,
        if page == "analysis" { "class=\"active\"" } else { "" },
        if page == "backtest" { "class=\"active\"" } else { "" },
        if page == "pairs" { "class=\"active\"" } else { "" },
        content
    )
}

/// Render an error page
fn render_error_page(title: &str, message: &str) -> String {
    format!(r#"<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>错误 - Turtoise Future</title>
    <style>
        body {{ font-family: sans-serif; padding: 40px; background: #f5f7fa; }}
        .error {{ background: white; padding: 40px; border-radius: 8px; max-width: 600px; margin: 100px auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #e53935; }}
        p {{ color: #666; margin: 20px 0; }}
        a {{ color: #4CAF50; }}
    </style>
</head>
<body>
    <div class="error">
        <h1>{}</h1>
        <p>{}</p>
        <p><a href="/">返回首页</a></p>
    </div>
</body>
</html>"#, title, message)
}

/// Create the web router
pub fn create_router(data_dir: String) -> Router {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        .route("/", get(home))
        .route("/analysis", get(analysis_page))
        .route("/backtest", get(backtest_page))
        .route("/backtest/run", post(run_backtest))
        .route("/pairs", get(pairs_page))
        .layer(cors)
        .with_state(AppState::new(data_dir))
}

/// Start the web server
pub async fn start_server(data_dir: String, port: u16) {
    let addr = format!("0.0.0.0:{}", port);
    let router = create_router(data_dir);

    println!("Web UI: http://localhost:{}", port);
    println!("  - 协整分析: http://localhost:{}/analysis", port);
    println!("  - 回测: http://localhost:{}/backtest", port);
    println!("  - 配对概览: http://localhost:{}/pairs", port);

    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    axum::serve(listener, router).await.unwrap();
}
