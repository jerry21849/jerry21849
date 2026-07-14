"""Backtesting tools — local computation with pandas.

Built-in strategies: RSI, MA Crossover, Bollinger Bands.
Outputs performance metrics + equity curve description.
"""

import logging
from typing import Optional, Literal

import pandas as pd
import numpy as np

from crypto_crew.models import BacktestReport

logger = logging.getLogger(__name__)

StrategyName = Literal["rsi", "ma_cross", "bollinger"]


def _candles_to_df(candles: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(candles)
    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def _rsi_strategy(df: pd.DataFrame, rsi_period: int = 14, oversold: float = 30,
                  overbought: float = 70) -> pd.DataFrame:
    """Generate signals: 1 = buy, -1 = sell, 0 = hold."""
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(rsi_period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    df["rsi"] = rsi
    df["signal"] = 0
    df.loc[df["rsi"] < oversold, "signal"] = 1
    df.loc[df["rsi"] > overbought, "signal"] = -1
    # Only take first signal after each change
    df["position"] = df["signal"].diff().fillna(0).abs().clip(0, 1) * df["signal"]
    # Forward fill: once positioned, stay
    df["position"] = df["position"].replace(0, np.nan).ffill().fillna(0)
    return df


def _ma_cross_strategy(df: pd.DataFrame, fast: int = 20, slow: int = 50) -> pd.DataFrame:
    df["sma_fast"] = df["close"].rolling(fast).mean()
    df["sma_slow"] = df["close"].rolling(slow).mean()
    df["signal"] = 0
    df.loc[df["sma_fast"] > df["sma_slow"], "signal"] = 1
    df.loc[df["sma_fast"] <= df["sma_slow"], "signal"] = -1
    df["position"] = df["signal"].diff().fillna(0)
    # Only trade on cross
    df["position"] = df["position"].abs().clip(0, 1) * df["signal"]
    df["position"] = df["position"].replace(0, np.nan).ffill().fillna(0)
    return df


def _bollinger_strategy(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    from ta.volatility import BollingerBands
    bb = BollingerBands(df["close"], window=period, window_dev=std_dev)
    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()
    df["bb_mid"] = bb.bollinger_mavg()
    df["signal"] = 0
    df.loc[df["close"] < df["bb_low"], "signal"] = 1    # buy near lower
    df.loc[df["close"] > df["bb_high"], "signal"] = -1  # sell near upper
    df["position"] = df["signal"].diff().fillna(0).abs().clip(0, 1) * df["signal"]
    df["position"] = df["position"].replace(0, np.nan).ffill().fillna(0)
    return df


def run_backtest(
    strategy: StrategyName = "rsi",
    candles: list[dict] | None = None,
    params: dict | None = None,
    initial_capital: float = 10000.0,
    fee_pct: float = 0.001,
) -> BacktestReport:
    """Run a backtest for *strategy* on *candles*.

    Args:
        strategy: one of "rsi", "ma_cross", "bollinger".
        candles: list of OHLCV dicts.
        params: strategy-specific overrides (e.g. {"oversold": 25}).
        initial_capital: starting cash.
        fee_pct: taker fee per trade.

    Returns:
        BacktestReport with performance metrics.
    """
    if not candles or len(candles) < 50:
        n = len(candles) if candles else 0
        return BacktestReport(strategy=strategy, error=f"Insufficient data: need ≥50 candles, got {n}")

    df = _candles_to_df(candles)
    if len(df) < 50:
        return BacktestReport(strategy=strategy, error=f"Insufficient data: {len(df)} rows")

    params = params or {}

    # Generate signals
    if strategy == "rsi":
        df = _rsi_strategy(df, **params)
    elif strategy == "ma_cross":
        df = _ma_cross_strategy(df, **params)
    elif strategy == "bollinger":
        df = _bollinger_strategy(df, **params)
    else:
        return BacktestReport(strategy=strategy, error=f"Unknown strategy: {strategy}")

    # Simulate trading
    cash = initial_capital
    position = 0.0
    trades = 0
    wins = 0
    equity_curve = [initial_capital]

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i - 1]
        price = float(row["close"])
        sig = row.get("position", 0)

        # Check position change
        if sig != 0 and prev_row.get("position", 0) == 0 and sig == 1:
            # Buy
            position = (cash * (1 - fee_pct)) / price
            cash = 0.0
            trades += 1
        elif sig != 0 and prev_row.get("position", 0) != 0 and sig == -1 and position > 0:
            # Sell
            cash = position * price * (1 - fee_pct)
            position = 0.0
            trades += 1
            if cash > initial_capital:
                wins += 1

        portfolio_value = cash + position * price
        equity_curve.append(portfolio_value)

    # Close any remaining position at last price
    final_price = float(df["close"].iloc[-1])
    if position > 0:
        cash = position * final_price * (1 - fee_pct)
        position = 0.0
        if cash > initial_capital:
            wins += 1
        trades += 1

    final_value = cash + position * final_price
    total_return = ((final_value - initial_capital) / initial_capital) * 100

    # Metrics
    n_days = len(df)
    annualized = ((1 + total_return / 100) ** (365 / max(n_days, 1)) - 1) * 100 if n_days > 0 else 0.0

    equity_arr = np.array(equity_curve)
    peak = np.maximum.accumulate(equity_arr)
    drawdown = (equity_arr - peak) / peak
    max_dd = float(np.min(drawdown)) * 100

    # Sharpe (assuming 0% risk-free for simplicity)
    returns = np.diff(equity_arr) / equity_arr[:-1]
    sharpe = float(np.mean(returns) / max(np.std(returns), 1e-8) * np.sqrt(365)) if len(returns) > 1 else 0.0

    win_rate = (wins / max(trades, 1)) * 100

    # Equity curve description
    peak_val = max(equity_curve)
    trough_val = min(equity_curve)
    description = (
        f"Initial: ${initial_capital:,.0f} → Final: ${final_value:,.0f} "
        f"(Peak: ${peak_val:,.0f}, Trough: ${trough_val:,.0f}). "
        f"{'Steady growth' if total_return > 0 else 'Declining trend'} over {n_days} periods."
    )

    return BacktestReport(
        strategy=strategy,
        total_return_pct=round(total_return, 2),
        annualized_return_pct=round(annualized, 2),
        sharpe_ratio=round(sharpe, 3),
        max_drawdown_pct=round(max_dd, 2),
        win_rate_pct=round(win_rate, 1),
        total_trades=trades,
        equity_curve_description=description,
    )
