//! Backtest engine for pair trading

use crate::data::{load_cointegrated_pairs, load_market_prices, MarketPrices, CointegratedPair};
use crate::strategies::cointegration::calculate_zscore;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Trade direction
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum TradeDirection {
    LongSpread,  // Buy base, sell quote
    ShortSpread, // Sell base, buy quote
}

/// Represents a single trade
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trade {
    pub pair: String,
    pub base_market: String,
    pub quote_market: String,
    pub direction: String, // "long_spread" or "short_spread"
    pub entry_date: String,
    pub entry_price_base: f64,
    pub entry_price_quote: f64,
    pub base_size: i32,
    pub quote_size: i32,
    pub entry_zscore: f64,
    pub hedge_ratio: f64,
    pub commission: f64,

    pub exit_date: Option<String>,
    pub exit_price_base: Option<f64>,
    pub exit_price_quote: Option<f64>,
    pub exit_zscore: Option<f64>,
    pub pnl: Option<f64>,
}

impl Trade {
    pub fn new(
        pair: &str,
        base_market: &str,
        quote_market: &str,
        direction: TradeDirection,
        entry_date: &str,
        entry_price_base: f64,
        entry_price_quote: f64,
        base_size: i32,
        quote_size: i32,
        entry_zscore: f64,
        hedge_ratio: f64,
        commission: f64,
    ) -> Self {
        Self {
            pair: pair.to_string(),
            base_market: base_market.to_string(),
            quote_market: quote_market.to_string(),
            direction: if direction == TradeDirection::LongSpread {
                "long_spread".to_string()
            } else {
                "short_spread".to_string()
            },
            entry_date: entry_date.to_string(),
            entry_price_base,
            entry_price_quote,
            base_size,
            quote_size,
            entry_zscore,
            hedge_ratio,
            commission,
            exit_date: None,
            exit_price_base: None,
            exit_price_quote: None,
            exit_zscore: None,
            pnl: None,
        }
    }

    pub fn close(&mut self, exit_date: &str, exit_price_base: f64, exit_price_quote: f64, exit_zscore: f64) {
        self.exit_date = Some(exit_date.to_string());
        self.exit_price_base = Some(exit_price_base);
        self.exit_price_quote = Some(exit_price_quote);
        self.exit_zscore = Some(exit_zscore);

        // Calculate PnL
        // Long spread: Buy base, sell quote -> base profit - quote loss
        // Short spread: Sell base, buy quote -> base loss - quote profit
        let (base_pnl, quote_pnl) = if self.direction == "long_spread" {
            (
                (exit_price_base - self.entry_price_base) * self.base_size as f64,
                (self.entry_price_quote - exit_price_quote) * self.quote_size as f64,
            )
        } else {
            (
                (self.entry_price_base - exit_price_base) * self.base_size as f64,
                (exit_price_quote - self.entry_price_quote) * self.quote_size as f64,
            )
        };

        let gross_pnl = base_pnl + quote_pnl;
        self.pnl = Some(gross_pnl - self.commission);
    }

    pub fn to_dict(&self) -> HashMap<String, serde_json::Value> {
        let mut map = HashMap::new();
        map.insert("pair".to_string(), serde_json::json!(self.pair));
        map.insert("base_market".to_string(), serde_json::json!(self.base_market));
        map.insert("quote_market".to_string(), serde_json::json!(self.quote_market));
        map.insert("direction".to_string(), serde_json::json!(self.direction));
        map.insert("entry_date".to_string(), serde_json::json!(self.entry_date));
        map.insert("entry_price_base".to_string(), serde_json::json!(self.entry_price_base));
        map.insert("entry_price_quote".to_string(), serde_json::json!(self.entry_price_quote));
        map.insert("base_size".to_string(), serde_json::json!(self.base_size));
        map.insert("quote_size".to_string(), serde_json::json!(self.quote_size));
        map.insert("entry_zscore".to_string(), serde_json::json!(self.entry_zscore));
        map.insert("hedge_ratio".to_string(), serde_json::json!(self.hedge_ratio));
        map.insert("exit_date".to_string(), serde_json::json!(self.exit_date));
        map.insert("exit_price_base".to_string(), serde_json::json!(self.exit_price_base));
        map.insert("exit_price_quote".to_string(), serde_json::json!(self.exit_price_quote));
        map.insert("exit_zscore".to_string(), serde_json::json!(self.exit_zscore));
        map.insert("pnl".to_string(), serde_json::json!(self.pnl));
        map
    }
}

/// Backtest result container
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestResult {
    pub initial_capital: f64,
    pub final_capital: f64,
    pub total_return: f64,
    pub annualized_return: f64,
    pub sharpe_ratio: f64,
    pub max_drawdown: f64,
    pub win_rate: f64,
    pub profit_loss_ratio: f64,
    pub total_trades: usize,
    pub trades: Vec<Trade>,
    pub equity_curve: Vec<EquityPoint>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EquityPoint {
    pub date: String,
    pub capital: f64,
    pub open_positions: usize,
}

/// Run backtest for pair trading strategy
pub fn run_backtest(
    prices: &MarketPrices,
    pairs: &[CointegratedPair],
    start_date: &str,
    end_date: &str,
    initial_capital: f64,
    zscore_threshold: f64,
    half_life_threshold: usize,
    window: usize,
    usd_per_trade: f64,
    commission_per_trade: f64,
    close_at_zscore_cross: bool,
) -> BacktestResult {
    // Filter data by date range
    let start_idx = prices.datetimes.iter().position(|d| d.as_str() >= start_date);
    let end_idx = prices.datetimes.iter().rposition(|d| d.as_str() <= end_date);

    let (start_idx, end_idx) = match (start_idx, end_idx) {
        (Some(s), Some(e)) if s < e => (s, e),
        _ => return BacktestResult::default(),
    };

    if end_idx - start_idx < window + 1 {
        return BacktestResult::default();
    }

    // Build filtered price series
    let filtered_dates: Vec<String> = prices.datetimes[start_idx..=end_idx].to_vec();
    let mut filtered_prices: HashMap<String, Vec<f64>> = HashMap::new();

    for contract in &prices.contracts {
        let full_series = prices.get_series(contract);
        if full_series.len() > end_idx {
            filtered_prices.insert(
                contract.clone(),
                full_series[start_idx..=end_idx].to_vec(),
            );
        }
    }

    // Initialize result
    let mut result = BacktestResult::default();
    result.initial_capital = initial_capital;
    let mut capital = initial_capital;

    // Track positions
    let mut open_trades: Vec<Trade> = Vec::new();
    let mut all_trades: Vec<Trade> = Vec::new();

    // Pre-calculate spreads and z-scores for all pairs
    let mut pair_data: HashMap<String, (Vec<f64>, Vec<f64>)> = HashMap::new();

    for pair in pairs {
        if pair.half_life > half_life_threshold as f64 {
            continue;
        }

        let Some(series_1) = filtered_prices.get(&pair.base_market) else {
            continue;
        };
        let Some(series_2) = filtered_prices.get(&pair.quote_market) else {
            continue;
        };

        if series_1.len() != series_2.len() {
            continue;
        }

        let spread: Vec<f64> = series_1
            .iter()
            .zip(series_2.iter())
            .map(|(s1, s2)| s1 - pair.hedge_ratio * s2)
            .collect();

        let zscore = calculate_zscore(&spread, window);

        let pair_key = format!("{}/{}", pair.base_market, pair.quote_market);
        pair_data.insert(pair_key, (spread, zscore));
    }

    // Track equity curve
    let mut equity_curve = Vec::new();

    // Iterate through each day
    for i in 0..filtered_dates.len() {
        let current_date = filtered_dates[i].as_str();

        // Skip first 'window' days (not enough data for z-score)
        if i < window {
            continue;
        }

        // Check open positions for exit
        let mut trades_to_close = Vec::new();

        for trade in &mut open_trades {
            let pair_key = format!("{}/{}", trade.base_market, trade.quote_market);

            let Some((_, zscore_series)) = pair_data.get(&pair_key) else {
                continue;
            };

            let zscore_current = zscore_series.get(i).copied().unwrap_or(f64::NAN);

            if zscore_current.is_nan() {
                continue;
            }

            let z_score_traded = trade.entry_zscore;
            let z_score_level_check = zscore_current.abs() > zscore_threshold;

            let z_score_cross_check = if close_at_zscore_cross {
                (zscore_current < 0.0 && z_score_traded > 0.0)
                    || (zscore_current > 0.0 && z_score_traded < 0.0)
            } else {
                zscore_current.abs() < 0.2
            };

            if z_score_level_check && z_score_cross_check {
                // Close position
                let base_price = filtered_prices
                    .get(&trade.base_market)
                    .and_then(|s| s.get(i))
                    .copied()
                    .unwrap_or(0.0);
                let quote_price = filtered_prices
                    .get(&trade.quote_market)
                    .and_then(|s| s.get(i))
                    .copied()
                    .unwrap_or(0.0);

                trade.close(current_date, base_price, quote_price, zscore_current);
                capital += trade.pnl.unwrap_or(0.0);
                trades_to_close.push(trade.clone());
            }
        }

        // Remove closed trades
        for trade in &trades_to_close {
            open_trades.retain(|t| t.pair != trade.pair);
            all_trades.push(trade.clone());
        }

        // Check for new entries
        for pair in pairs {
            if pair.half_life > half_life_threshold as f64 {
                continue;
            }

            let Some(series_1) = filtered_prices.get(&pair.base_market) else {
                continue;
            };
            let Some(series_2) = filtered_prices.get(&pair.quote_market) else {
                continue;
            };

            // Check if already have position on this pair
            let has_position = open_trades.iter().any(|t| {
                t.base_market == pair.base_market && t.quote_market == pair.quote_market
            });
            if has_position {
                continue;
            }

            let pair_key = format!("{}/{}", pair.base_market, pair.quote_market);
            let Some((_, zscore_series)) = pair_data.get(&pair_key) else {
                continue;
            };

            let zscore_current = zscore_series.get(i).copied().unwrap_or(f64::NAN);

            if zscore_current.is_nan() {
                continue;
            }

            // Check entry conditions
            if zscore_current.abs() >= zscore_threshold {
                let base_price = series_1[i];
                let quote_price = series_2[i];

                // Calculate position size
                let base_quantity = usd_per_trade / base_price;
                let quote_quantity = usd_per_trade / quote_price;
                let base_size = base_quantity as i32;
                let quote_size = quote_quantity as i32;

                if base_size < 1 || quote_size < 1 {
                    continue;
                }

                // Determine direction
                let direction = if zscore_current < 0.0 {
                    TradeDirection::LongSpread
                } else {
                    TradeDirection::ShortSpread
                };

                // Calculate commission (entry + exit)
                let total_commission = 2.0 * commission_per_trade;

                let trade = Trade::new(
                    &pair_key,
                    &pair.base_market,
                    &pair.quote_market,
                    direction,
                    current_date,
                    base_price,
                    quote_price,
                    base_size,
                    quote_size,
                    zscore_current,
                    pair.hedge_ratio,
                    total_commission,
                );

                open_trades.push(trade);
            }
        }

        // Record equity
        equity_curve.push(EquityPoint {
            date: current_date.to_string(),
            capital,
            open_positions: open_trades.len(),
        });
    }

    // Close any remaining positions at the end
    let last_idx = filtered_dates.len() - 1;
    for mut trade in open_trades {
        let base_price = filtered_prices
            .get(&trade.base_market)
            .and_then(|s| s.get(last_idx))
            .copied()
            .unwrap_or(0.0);
        let quote_price = filtered_prices
            .get(&trade.quote_market)
            .and_then(|s| s.get(last_idx))
            .copied()
            .unwrap_or(0.0);

        trade.close(filtered_dates[last_idx].as_str(), base_price, quote_price, 0.0);
        capital += trade.pnl.unwrap_or(0.0);
        all_trades.push(trade);
    }

    // Calculate final metrics
    result.final_capital = capital;
    result.total_trades = all_trades.len();
    result.trades = all_trades;
    result.equity_curve = equity_curve;

    // Calculate performance metrics
    if initial_capital > 0.0 {
        result.total_return = (capital - initial_capital) / initial_capital;

        // Calculate days in backtest (simple Y-M-D parsing)
        let parse_date = |s: &str| -> Option<(i32, u32, u32)> {
            let parts: Vec<&str> = s.split('-').collect();
            if parts.len() == 3 {
                let year: i32 = parts[0].parse().ok()?;
                let month: u32 = parts[1].parse().ok()?;
                let day: u32 = parts[2].parse().ok()?;
                Some((year, month, day))
            } else {
                None
            }
        };

        if let (Some((start_y, start_m, start_d)), Some((end_y, end_m, end_d))) =
            (parse_date(start_date), parse_date(end_date))
        {
            // Simple day count (approximation)
            let start_days = start_y as i64 * 365 + start_m as i64 * 30 + start_d as i64;
            let end_days = end_y as i64 * 365 + end_m as i64 * 30 + end_d as i64;
            let days = (end_days - start_days) as f64;
            let years = days / 365.0;

            if years > 0.0 {
                result.annualized_return = f64::powf(1.0 + result.total_return, 1.0 / years) - 1.0;
            }
        }
    }

    // Calculate Sharpe ratio
    if result.equity_curve.len() > 1 {
        let mut returns = Vec::new();
        for i in 1..result.equity_curve.len() {
            let prev_capital = result.equity_curve[i - 1].capital;
            let curr_capital = result.equity_curve[i].capital;
            if prev_capital > 0.0 {
                let ret = (curr_capital - prev_capital) / prev_capital;
                returns.push(ret);
            }
        }

        if !returns.is_empty() {
            let mean_ret = returns.iter().sum::<f64>() / returns.len() as f64;
            let std_ret = {
                let var = returns.iter().map(|r| (r - mean_ret).powi(2)).sum::<f64>() / returns.len() as f64;
                var.sqrt()
            };

            if std_ret > 0.0 {
                result.sharpe_ratio = mean_ret / std_ret * f64::sqrt(252.0);
            }
        }
    }

    // Calculate max drawdown
    if !result.equity_curve.is_empty() {
        let mut peak = result.equity_curve[0].capital;
        let mut max_dd = 0.0f64;

        for point in &result.equity_curve {
            if point.capital > peak {
                peak = point.capital;
            }
            let dd = if peak > 0.0 { (peak - point.capital) / peak } else { 0.0 };
            if dd > max_dd {
                max_dd = dd;
            }
        }

        result.max_drawdown = max_dd;
    }

    // Calculate win rate and profit/loss ratio
    if !result.trades.is_empty() {
        let winning_trades: Vec<_> = result.trades.iter().filter(|t| t.pnl.unwrap_or(0.0) > 0.0).collect();
        let losing_trades: Vec<_> = result.trades.iter().filter(|t| t.pnl.unwrap_or(0.0) <= 0.0).collect();

        result.win_rate = winning_trades.len() as f64 / result.trades.len() as f64;

        if !winning_trades.is_empty() && !losing_trades.is_empty() {
            let avg_win = winning_trades.iter().map(|t| t.pnl.unwrap_or(0.0)).sum::<f64>() / winning_trades.len() as f64;
            let avg_loss = losing_trades.iter().map(|t| t.pnl.unwrap_or(0.0).abs()).sum::<f64>() / losing_trades.len() as f64;

            if avg_loss > 0.0 {
                result.profit_loss_ratio = avg_win / avg_loss;
            }
        }
    }

    result
}

impl Default for BacktestResult {
    fn default() -> Self {
        Self {
            initial_capital: 0.0,
            final_capital: 0.0,
            total_return: 0.0,
            annualized_return: 0.0,
            sharpe_ratio: 0.0,
            max_drawdown: 0.0,
            win_rate: 0.0,
            profit_loss_ratio: 0.0,
            total_trades: 0,
            trades: Vec::new(),
            equity_curve: Vec::new(),
        }
    }
}

/// Load data for backtesting
pub fn load_backtest_data(
    prices_path: &std::path::Path,
    pairs_path: &std::path::Path,
) -> Result<(MarketPrices, Vec<CointegratedPair>), String> {
    let prices = load_market_prices(prices_path)?;
    let pairs = load_cointegrated_pairs(pairs_path)?;
    Ok((prices, pairs))
}

impl BacktestResult {
    pub fn to_dict(&self) -> HashMap<String, serde_json::Value> {
        let mut map = HashMap::new();
        map.insert("initial_capital".to_string(), serde_json::json!(self.initial_capital));
        map.insert("final_capital".to_string(), serde_json::json!(self.final_capital));
        map.insert("total_return".to_string(), serde_json::json!(self.total_return));
        map.insert("annualized_return".to_string(), serde_json::json!(self.annualized_return));
        map.insert("sharpe_ratio".to_string(), serde_json::json!(self.sharpe_ratio));
        map.insert("max_drawdown".to_string(), serde_json::json!(self.max_drawdown));
        map.insert("win_rate".to_string(), serde_json::json!(self.win_rate));
        map.insert("profit_loss_ratio".to_string(), serde_json::json!(self.profit_loss_ratio));
        map.insert("total_trades".to_string(), serde_json::json!(self.total_trades));
        map.insert("trades".to_string(), serde_json::json!(self.trades.iter().map(|t| t.to_dict()).collect::<Vec<_>>()));
        map.insert("equity_curve".to_string(), serde_json::json!(self.equity_curve));
        map
    }

    pub fn save(&self, path: &std::path::Path) -> Result<(), String> {
        let content = serde_json::to_string_pretty(&self.to_dict())
            .map_err(|e| format!("Failed to serialize: {}", e))?;
        std::fs::write(path, content).map_err(|e| format!("Failed to write file: {}", e))?;
        Ok(())
    }
}
