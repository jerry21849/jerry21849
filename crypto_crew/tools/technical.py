"""Technical analysis tools — all local computation using the `ta` library.

Replaces any paid TA API (altFINS, etc.) entirely.
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np
import ta

from crypto_crew.models import TechSummary, TechIndicatorRow

logger = logging.getLogger(__name__)

_INDICATOR_MAP = {
    "RSI": {"name": "RSI (14)", "fn": lambda df: ta.momentum.RSIIndicator(df["close"], window=14).rsi()},
    "MACD": {"name": "MACD", "fn": lambda df: ta.trend.MACD(df["close"]).macd()},
    "MACD_signal": {"name": "MACD Signal", "fn": lambda df: ta.trend.MACD(df["close"]).macd_signal()},
    "BB_high": {"name": "Bollinger High", "fn": lambda df: ta.volatility.BollingerBands(df["close"]).bollinger_hband()},
    "BB_mid": {"name": "Bollinger Mid", "fn": lambda df: ta.volatility.BollingerBands(df["close"]).bollinger_mavg()},
    "BB_low": {"name": "Bollinger Low", "fn": lambda df: ta.volatility.BollingerBands(df["close"]).bollinger_lband()},
    "SMA_20": {"name": "SMA (20)", "fn": lambda df: ta.trend.SMAIndicator(df["close"], window=20).sma_indicator()},
    "SMA_50": {"name": "SMA (50)", "fn": lambda df: ta.trend.SMAIndicator(df["close"], window=50).sma_indicator()},
    "SMA_200": {"name": "SMA (200)", "fn": lambda df: ta.trend.SMAIndicator(df["close"], window=200).sma_indicator()},
    "EMA_12": {"name": "EMA (12)", "fn": lambda df: ta.trend.EMAIndicator(df["close"], window=12).ema_indicator()},
    "EMA_26": {"name": "EMA (26)", "fn": lambda df: ta.trend.EMAIndicator(df["close"], window=26).ema_indicator()},
    "ATR": {"name": "ATR (14)", "fn": lambda df: ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"]).average_true_range()},
    "Stoch": {"name": "Stoch %K", "fn": lambda df: ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"]).stoch()},
}


def _candles_to_df(candles: list[dict]) -> pd.DataFrame:
    """Convert list of candle dicts to a pandas DataFrame."""
    df = pd.DataFrame(candles)
    # Ensure numeric columns
    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def _detect_trend(df: pd.DataFrame, latest: dict[str, float]) -> str:
    """Heuristic trend detection from recent indicator values."""
    try:
        sma20 = latest.get("SMA_20")
        sma50 = latest.get("SMA_50")
        sma200 = latest.get("SMA_200")
        close = latest.get("close", df["close"].iloc[-1] if len(df) else 0)
        rsi = latest.get("RSI")

        bullish_count = 0
        bearish_count = 0

        if sma20 and sma50 and sma20 > sma50:
            bullish_count += 1
        elif sma20 and sma50:
            bearish_count += 1

        if sma50 and sma200 and sma50 > sma200:
            bullish_count += 1
        elif sma50 and sma200:
            bearish_count += 1

        if close > (sma20 or close):
            bullish_count += 1
        elif close < (sma20 or close):
            bearish_count += 1

        if rsi is not None:
            if rsi > 60:
                bullish_count += 1
            elif rsi < 40:
                bearish_count += 1

        if bullish_count > bearish_count:
            return "bullish"
        if bearish_count > bullish_count:
            return "bearish"
        return "neutral"
    except Exception:
        return "neutral"


def calculate_technical_indicators(
    candles: list[dict],
    indicators: list[str] | None = None,
) -> TechSummary:
    """Compute technical indicators from candle data using the local `ta` library.

    Args:
        candles: List of {timestamp, open, high, low, close, volume} dicts.
        indicators: Subset of keys from _INDICATOR_MAP; defaults to all.

    Returns:
        TechSummary with computed indicator rows + trend + S/R levels.
    """
    if not candles or len(candles) < 30:
        return TechSummary(error=f"Insufficient data: need ≥30 candles, got {len(candles or [])}")

    df = _candles_to_df(candles)
    if len(df) < 30:
        return TechSummary(error=f"Insufficient data after parsing: {len(df)} rows")

    selected = indicators or list(_INDICATOR_MAP.keys())
    latest_values: dict[str, float] = {"close": float(df["close"].iloc[-1])}
    rows = []

    for key in selected:
        spec = _INDICATOR_MAP.get(key)
        if not spec:
            continue
        try:
            series = spec["fn"](df)
            val = series.iloc[-1]
            if pd.isna(val):
                continue
            latest_values[key] = float(val)
            # Generate signal
            signal = _signal_for_indicator(key, float(val), df)
            rows.append(TechIndicatorRow(
                name=spec["name"],
                value=f"{val:.2f}",
                signal=signal,
            ))
        except Exception as e:
            logger.warning("Indicator %s failed: %s", key, e)

    trend = _detect_trend(df, latest_values)

    # Support / Resistance from recent price action
    recent = df.tail(20)
    support = float(recent["low"].min()) if len(recent) else None
    resistance = float(recent["high"].max()) if len(recent) else None

    return TechSummary(
        indicators=rows,
        trend=trend,
        support=support,
        resistance=resistance,
    )


def _signal_for_indicator(key: str, value: float, df: pd.DataFrame) -> str | None:
    """Simple heuristic signal per indicator."""
    if key == "RSI":
        if value > 70:
            return "sell (overbought)"
        if value < 30:
            return "buy (oversold)"
        return "neutral"
    if key == "Stoch":
        if value > 80:
            return "sell (overbought)"
        if value < 20:
            return "buy (oversold)"
        return "neutral"
    if "MACD" in key:
        return None  # Signal from MACD line vs signal line
    return None
