"""Tests for technical analysis tools — all local, no external calls."""

import json
import pytest
from pathlib import Path

from crypto_crew.tools.technical import calculate_technical_indicators

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_candles(name: str = "btc_ohlcv_sample.json") -> list[dict]:
    with open(FIXTURE_DIR / name) as f:
        return json.load(f)


class TestTechnicalIndicators:
    def test_rsi_computed(self):
        candles = _load_candles()
        result = calculate_technical_indicators(candles, indicators=["RSI"])
        assert result.error is None
        assert len(result.indicators) >= 1
        rsi_row = [r for r in result.indicators if "RSI" in r.name]
        assert len(rsi_row) == 1
        rsi_val = float(rsi_row[0].value)
        assert 0 <= rsi_val <= 100

    def test_macd_computed(self):
        candles = _load_candles()
        result = calculate_technical_indicators(candles, indicators=["MACD"])
        assert result.error is None
        assert any("MACD" in r.name for r in result.indicators)

    def test_all_indicators(self):
        candles = _load_candles()
        result = calculate_technical_indicators(candles)
        assert result.error is None
        assert len(result.indicators) >= 5

    def test_trend_detected(self):
        candles = _load_candles()
        result = calculate_technical_indicators(candles)
        assert result.trend in ("bullish", "bearish", "neutral")

    def test_support_resistance(self):
        candles = _load_candles()
        result = calculate_technical_indicators(candles)
        assert result.support is not None
        assert result.resistance is not None
        assert result.support < result.resistance

    def test_insufficient_data(self):
        result = calculate_technical_indicators([])
        assert result.error is not None

    def test_few_candles(self):
        result = calculate_technical_indicators(
            [{"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000}]
            * 10
        )
        assert result.error is not None
