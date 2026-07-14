"""Tests for backtesting tools — all local, uses sample OHLCV fixture."""

import json
import pytest
from pathlib import Path

from crypto_crew.tools.backtest import run_backtest
from crypto_crew.models import BacktestReport

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_candles() -> list[dict]:
    with open(FIXTURE_DIR / "btc_ohlcv_sample.json") as f:
        return json.load(f)


class TestBacktest:
    def test_rsi_strategy(self):
        candles = _load_candles()
        result = run_backtest("rsi", candles)
        assert isinstance(result, BacktestReport)
        assert result.error is None
        assert result.total_trades >= 0
        assert result.sharpe_ratio is not None or result.error
        assert result.max_drawdown_pct <= 0  # MaxDD is negative or zero

    def test_ma_cross_strategy(self):
        candles = _load_candles()
        result = run_backtest("ma_cross", candles)
        assert result.error is None
        assert result.total_trades >= 0

    def test_bollinger_strategy(self):
        candles = _load_candles()
        result = run_backtest("bollinger", candles)
        assert result.error is None
        assert result.total_trades >= 0

    def test_insufficient_data(self):
        result = run_backtest("rsi", [])
        assert result.error is not None
        assert "insufficient" in result.error.lower()

    def test_unknown_strategy(self):
        candles = _load_candles()
        result = run_backtest("unknown_strategy", candles)
        assert result.error is not None

    def test_custom_params(self):
        candles = _load_candles()
        result = run_backtest("rsi", candles, params={"oversold": 25, "overbought": 75})
        assert result.error is None
        assert result.total_return_pct is not None
