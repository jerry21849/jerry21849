"""Risk management tools — local computation of ATR, VaR, volatility, position sizing."""

import logging
from typing import Optional

import pandas as pd
import numpy as np

from crypto_crew.models import RiskAdvice

logger = logging.getLogger(__name__)


def _candles_to_df(candles: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(candles)
    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_values("timestamp", inplace=True)
    df["return"] = df["close"].pct_change()
    return df


def compute_risk_metrics(
    candles: list[dict],
    current_price: Optional[float] = None,
    portfolio_value: float = 10000.0,
    risk_profile: str = "conservative",
) -> RiskAdvice:
    """Compute risk metrics from OHLCV data.

    Args:
        candles: List of OHLCV dicts.
        current_price: Current market price (latest close if None).
        portfolio_value: Total portfolio value for position sizing.
        risk_profile: "conservative" | "aggressive".

    Returns:
        RiskAdvice with VaR, ATR, suggested sizing.
    """
    if not candles or len(candles) < 20:
        return RiskAdvice(error=f"Insufficient data: need ≥20 candles, got {len(candles or [])}")

    df = _candles_to_df(candles)
    price = current_price or float(df["close"].iloc[-1])

    # Volatility (daily return std, annualized)
    daily_returns = df["return"].dropna()
    daily_vol = float(daily_returns.std())
    annualized_vol = daily_vol * np.sqrt(365) * 100  # as %
    daily_vol_pct = daily_vol * 100

    # ATR (14-period)
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = float(tr.tail(14).mean())

    # VaR 95% (historical)
    var_95 = float(np.percentile(daily_returns, 5)) * 100  # as %

    # Position sizing based on risk profile
    risk_per_trade = 0.02 if risk_profile == "aggressive" else 0.01  # 1-2% per trade
    suggested_position = risk_per_trade / max(daily_vol_pct / 100, 0.001)
    suggested_position_pct = min(max(suggested_position * 100, 1.0), 30.0)

    # Stop loss based on ATR
    atr_pct = (atr / price) * 100 if price > 0 else 5.0
    stop_loss = atr_pct * (2 if risk_profile == "conservative" else 1.5)
    take_profit = stop_loss * (2.5 if risk_profile == "conservative" else 2.0)

    # Notes
    notes_parts = [
        f"Daily volatility: {daily_vol_pct:.2f}%",
        f"Annualized volatility: {annualized_vol:.1f}%",
        f"ATR: ${atr:.2f} ({atr_pct:.2f}%)",
        f"VaR (95%): {var_95:.2f}% daily",
        f"Risk profile: {risk_profile}",
    ]

    if atr_pct > 5:
        notes_parts.append("⚠️ High volatility — consider reducing position size")
    elif atr_pct < 1.5:
        notes_parts.append("✅ Low volatility environment")

    return RiskAdvice(
        volatility_pct=round(annualized_vol, 2),
        atr=round(atr, 2),
        suggested_position_size_pct=round(suggested_position_pct, 1),
        stop_loss_pct=round(stop_loss, 1),
        take_profit_pct=round(take_profit, 1),
        var_95_pct=round(var_95, 2),
        notes=" | ".join(notes_parts),
    )
