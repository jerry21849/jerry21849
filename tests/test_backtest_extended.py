"""Tests for extended backtest strategies."""

import json
from pathlib import Path

from crypto_crew.tools.backtest import run_backtest
from crypto_crew.models import BacktestReport

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_candles() -> list[dict]:
    with open(FIXTURE_DIR / "btc_ohlcv_sample.json") as f:
        return json.load(f)


class TestExtendedStrategies:
    def test_mean_reversion(self):
        candles = _load_candles()
        result = run_backtest("mean_reversion", candles)
        assert isinstance(result, BacktestReport)
        assert result.error is None
        assert result.total_return_pct is not None
        assert result.sharpe_ratio is not None
        assert result.max_drawdown_pct <= 0

    def test_macd_histogram(self):
        candles = _load_candles()
        result = run_backtest("macd_histogram", candles)
        assert result.error is None
        assert result.total_trades >= 0
        assert result.equity_curve_description

    def test_mean_reversion_custom_params(self):
        candles = _load_candles()
        result = run_backtest(
            "mean_reversion",
            candles,
            params={"period": 15, "entry_z": 1.2, "exit_z": 0.3},
        )
        assert result.error is None
