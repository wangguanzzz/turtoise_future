//! Cointegration analysis module
//!
//! Implements the Engle-Granger two-step method for cointegration testing.

use crate::data::MarketPrices;
use crate::data::CointegratedPair;
use statrs::statistics::Statistics;

/// Calculate the half-life of mean reversion using Ornstein-Uhlenbeck formula
/// half_life = -log(2) / lambda where lambda is the decay parameter
pub fn calculate_half_life(spread: &[f64]) -> f64 {
    let n = spread.len();
    if n < 3 {
        return 0.0;
    }

    // Create lagged spread: spread_lag[i] = spread[i-1]
    let spread_lag: Vec<f64> = std::iter::once(&spread[1])
        .chain(spread.iter().take(n - 1))
        .copied()
        .collect();

    // Create spread return: spread_ret[i] = spread[i] - spread[i-1]
    let spread_ret: Vec<f64> = spread
        .iter()
        .zip(spread_lag.iter())
        .map(|(s, sl)| s - sl)
        .collect();

    // Add constant term for OLS: spread_ret = const + lambda * spread_lag + epsilon
    // We need to run OLS: y = X * beta
    // where y = spread_ret, X = [1, spread_lag]
    let n_obs = spread_ret.len();
    let mut X: Vec<Vec<f64>> = Vec::with_capacity(n_obs);
    let mut y: Vec<f64> = Vec::with_capacity(n_obs);

    for i in 0..n_obs {
        X.push(vec![1.0, spread_lag[i]]);
        y.push(spread_ret[i]);
    }

    // OLS: beta = (X'X)^(-1) X'y
    let beta = ols(&X, &y);

    // lambda = beta[1]
    let lambda = beta[1];

    if lambda >= 0.0 {
        return 0.0;
    }

    let half_life = -f64::ln(2.0) / lambda;
    half_life.round()
}

/// Simple OLS regression: y = X * beta
/// Returns beta coefficients
fn ols(X: &[Vec<f64>], y: &[f64]) -> Vec<f64> {
    let n = X.len();
    let k = X[0].len(); // number of parameters

    if n == 0 || k == 0 {
        return vec![0.0; k];
    }

    // X'X matrix
    let mut XtX: Vec<Vec<f64>> = vec![vec![0.0; k]; k];
    for i in 0..k {
        for j in 0..k {
            let mut sum = 0.0;
            for t in 0..n {
                sum += X[t][i] * X[t][j];
            }
            XtX[i][j] = sum;
        }
    }

    // X'y vector
    let mut Xty: Vec<f64> = vec![0.0; k];
    for i in 0..k {
        let mut sum = 0.0;
        for t in 0..n {
            sum += X[t][i] * y[t];
        }
        Xty[i] = sum;
    }

    // Solve X'X * beta = X'y using Gaussian elimination
    solve_linear_system(&XtX, &Xty)
}

/// Solve linear system Ax = b using Gaussian elimination with partial pivoting
fn solve_linear_system(A: &[Vec<f64>], b: &[f64]) -> Vec<f64> {
    let n = b.len();
    let mut aug: Vec<Vec<f64>> = A.iter()
        .zip(b.iter())
        .map(|(a_row, &b_val)| {
            let mut row = a_row.clone();
            row.push(b_val);
            row
        })
        .collect();

    // Forward elimination with partial pivoting
    for col in 0..n {
        // Find pivot
        let mut max_row = col;
        let mut max_val = aug[col][col].abs();
        for row in (col + 1)..n {
            if aug[row][col].abs() > max_val {
                max_val = aug[row][col].abs();
                max_row = row;
            }
        }

        // Swap rows
        aug.swap(col, max_row);

        // Eliminate
        for row in (col + 1)..n {
            if aug[col][col].abs() < 1e-12 {
                continue;
            }
            let factor = aug[row][col] / aug[col][col];
            for j in col..=n {
                aug[row][j] -= factor * aug[col][j];
            }
        }
    }

    // Back substitution
    let mut x = vec![0.0; n];
    for i in (0..n).rev() {
        if aug[i][i].abs() < 1e-12 {
            x[i] = 0.0;
            continue;
        }
        let mut sum = aug[i][n];
        for j in (i + 1)..n {
            sum -= aug[i][j] * x[j];
        }
        x[i] = sum / aug[i][i];
    }

    x
}

/// Calculate cointegration between two series using Engle-Granger method
///
/// Returns: (coint_flag, hedge_ratio, half_life)
/// coint_flag = 1 if p_value < 0.002 and t_stat < critical_value
pub fn calculate_cointegration(series_1: &[f64], series_2: &[f64]) -> (i32, f64, f64) {
    let n = series_1.len().min(series_2.len());
    if n < 10 {
        return (0, 0.0, 0.0);
    }

    let s1 = &series_1[..n];
    let s2 = &series_2[..n];

    // Step 1: OLS regression s1 = beta * s2 + epsilon
    // Solve s1 = X * beta where X = [s2]
    let X: Vec<Vec<f64>> = s2.iter().map(|&x| vec![x]).collect();
    let beta = ols(&X, s1);
    let hedge_ratio = beta[0];

    // Step 2: Calculate residuals (spread)
    let spread: Vec<f64> = s1.iter().zip(s2.iter()).map(|(a, b)| a - hedge_ratio * b).collect();

    // Step 3: ADF test on residuals
    let adf_result = adf_test(&spread);

    // Step 4: Calculate half-life
    let half_life = calculate_half_life(&spread);

    // Cointegration check: p_value < 0.002 and t_stat < critical_value (5%)
    let coint_flag = if adf_result.p_value < 0.002 && adf_result.t_stat < adf_result.critical_values.1 {
        1
    } else {
        0
    };

    (coint_flag, hedge_ratio, half_life)
}

/// ADF (Augmented Dickey-Fuller) test result
#[derive(Debug, Clone)]
pub struct AdfResult {
    pub t_stat: f64,
    pub p_value: f64,
    pub critical_values: (f64, f64, f64), // 1%, 5%, 10%
    pub used_lag: usize,
}

/// Augmented Dickey-Fuller test for stationarity
pub fn adf_test(series: &[f64]) -> AdfResult {
    let n = series.len();
    if n < 20 {
        return AdfResult {
            t_stat: 0.0,
            p_value: 1.0,
            critical_values: (-3.96, -3.41, -3.12),
            used_lag: 0,
        };
    }

    // Determine optimal lag using AIC
    let max_lag = ((n as f64).powf(0.25) as usize).min(12);
    let mut best_lag = 0;
    let mut best_aic = f64::INFINITY;

    // Use difference of series for ADF
    let diff: Vec<f64> = series.windows(2).map(|w| w[1] - w[0]).collect();

    for lag in 0..=max_lag {
        // Build design matrix for ADF regression:
        // Δy_t = alpha + lambda * y_{t-1} + sum(gamma_i * Δy_{t-i}) + epsilon_t
        let y_lag_idx: Vec<usize> = (lag + 1..series.len() - 1).collect();
        let n_reg = y_lag_idx.len();

        if n_reg < 10 {
            continue;
        }

        // Build X matrix: [1, y_{t-1}, Δy_t, Δy_{t-1}, ..., Δy_{t-lag}]
        let mut X: Vec<Vec<f64>> = Vec::with_capacity(n_reg);
        let mut y: Vec<f64> = Vec::with_capacity(n_reg);

        for &i in &y_lag_idx {
            let mut row = vec![1.0]; // constant
            row.push(series[i]); // y_{t-1}

            // Add lagged differences
            for j in 1..=lag {
                if i >= j {
                    row.push(diff[i - j]);
                }
            }
            X.push(row);
            y.push(diff[i]);
        }

        let beta = ols(&X, &y);
        let lambda = beta[1];

        // Calculate AIC
        let residuals: Vec<f64> = y.iter()
            .enumerate()
            .map(|(i, &yi)| {
                let mut pred = 0.0;
                for (j, &bj) in beta.iter().enumerate() {
                    pred += bj * X[i][j];
                }
                yi - pred
            })
            .collect();

        let ssr: f64 = residuals.iter().map(|&r| r * r).sum();
        let sigma2 = ssr / (n_reg as f64);
        let k = beta.len() as f64;
        let aic = n as f64 * f64::ln(sigma2) + 2.0 * k;

        if aic < best_aic {
            best_aic = aic;
            best_lag = lag;
        }
    }

    // Re-run ADF with best lag
    let lag = best_lag.min(12);
    let y_lag_idx: Vec<usize> = (lag + 1..series.len() - 1).collect();
    let n_reg = y_lag_idx.len();

    let mut X: Vec<Vec<f64>> = Vec::with_capacity(n_reg);
    let mut y: Vec<f64> = Vec::with_capacity(n_reg);

    for &i in &y_lag_idx {
        let mut row = vec![1.0];
        row.push(series[i]);
        for j in 1..=lag {
            if i >= j {
                row.push(diff[i - j]);
            }
        }
        X.push(row);
        y.push(diff[i]);
    }

    let beta = ols(&X, &y);
    let lambda = beta[1];

    // Calculate standard error of lambda
    let residuals: Vec<f64> = y.iter()
        .enumerate()
        .map(|(i, &yi)| {
            let mut pred = 0.0;
            for (j, &bj) in beta.iter().enumerate() {
                pred += bj * X[i][j];
            }
            yi - pred
        })
        .collect();

    let ssr: f64 = residuals.iter().map(|&r| r * r).sum();
    let n_params = X[0].len();
    let sigma = f64::sqrt(ssr / ((n_reg - n_params) as f64));

    // Standard error of lambda (from delta method approximation)
    // SE(lambda) = sigma / sqrt(sum((y_{t-1} - mean)^2))
    let y_lag: Vec<f64> = y_lag_idx.iter().map(|&i| series[i]).collect();
    let y_mean = y_lag.clone().mean();
    let var_y: f64 = y_lag.iter().map(|&y| (y - y_mean).powi(2)).sum();
    let se_lambda = if var_y > 0.0 { sigma / f64::sqrt(var_y) } else { 1.0 };

    let t_stat = if se_lambda > 1e-10 { lambda / se_lambda } else { 0.0 };

    // Approximate p-value using MacKinnon's method
    let p_value = approximate_p_value(t_stat, n_reg);

    // Critical values (MacKinnon approximate critical values)
    let critical_values = if n_reg > 100 {
        (-3.96, -3.41, -3.12)
    } else if n_reg > 50 {
        (-3.98, -3.43, -3.14)
    } else {
        (-4.04, -3.45, -3.15)
    };

    AdfResult {
        t_stat,
        p_value,
        critical_values,
        used_lag: lag,
    }
}

/// Approximate p-value for ADF t-statistic using MacKinnon's approximation
fn approximate_p_value(t_stat: f64, n: usize) -> f64 {
    // MacKinnon approximate p-value formula
    let t = t_stat;

    // Critical values at different significance levels
    let cv_1pct = -3.96;
    let cv_5pct = -3.41;
    let cv_10pct = -3.12;

    if t < cv_1pct {
        // Very significant
        let z = (cv_1pct - t).abs();
        if z > 3.0 {
            return 0.001
        }
        return 0.001 + 0.001 * z;
    } else if t < cv_5pct {
        let z = (cv_5pct - t).abs() / (cv_1pct - cv_5pct).abs();
        return 0.001 + 0.009 * (1.0 - z) + 0.01 * z;
    } else if t < cv_10pct {
        let z = (cv_10pct - t).abs() / (cv_5pct - cv_10pct).abs();
        return 0.01 + 0.04 * (1.0 - z) + 0.04 * z;
    } else {
        return 0.1 + 0.1 * ((t - cv_10pct).abs() / 0.5).min(1.0);
    }
}

/// Calculate rolling Z-score for the spread
pub fn calculate_zscore(spread: &[f64], window: usize) -> Vec<f64> {
    let n = spread.len();
    if n < window {
        return vec![f64::NAN; n];
    }

    let mut zscore = vec![f64::NAN; n];

    for i in (window - 1)..n {
        let window_data = &spread[(i + 1 - window)..=i];
        let mean = window_data.mean();
        let std = window_data.std_dev();

        if std > 1e-10 {
            // Current value (most recent)
            let x = spread[i];
            zscore[i] = (x - mean) / std;
        }
    }

    zscore
}

/// Find all cointegrated pairs in the market data
pub fn find_cointegrated_pairs(
    market_prices: &MarketPrices,
    max_half_life: usize,
) -> Vec<CointegratedPair> {
    let mut pairs = Vec::new();
    let contracts = &market_prices.contracts;

    for i in 0..contracts.len() {
        let base_market = &contracts[i];
        let series_1 = market_prices.get_series(base_market);

        if series_1.len() < 50 {
            continue;
        }

        for j in (i + 1)..contracts.len() {
            let quote_market = &contracts[j];
            let series_2 = market_prices.get_series(quote_market);

            if series_2.len() < 50 {
                continue;
            }

            let (coint_flag, hedge_ratio, half_life) = calculate_cointegration(&series_1, &series_2);

            if coint_flag == 1 && half_life > 0.0 && half_life <= max_half_life as f64 {
                pairs.push(CointegratedPair::new(
                    base_market,
                    quote_market,
                    hedge_ratio,
                    half_life,
                ));
            }
        }
    }

    pairs
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_half_life_calculation() {
        // Test with a mean-reverting series
        let spread = vec![1.0, 0.8, 0.64, 0.512, 0.41, 0.328, 0.262, 0.21];
        let hl = calculate_half_life(&spread);
        assert!(hl > 0.0);
    }

    #[test]
    fn test_zscore() {
        let spread = vec![1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0, 1.0, 2.0];
        let z = calculate_zscore(&spread, 5);
        assert!(!z.iter().all(|x| x.is_nan()));
    }
}
