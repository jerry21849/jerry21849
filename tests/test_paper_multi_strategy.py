"""Tests for multi-strategy paper trading isolation + legacy migration."""

import json
from pathlib import Path

from crypto_crew.tools import paper_trade as pt


class TestMultiStrategy:
    def setup_method(self):
        pt._save_portfolio(pt._default_portfolio())

    def test_isolated_cash(self):
        pt.execute_paper_trade("buy", "BTC", 1000, 50000.0, strategy_tag="rsi")
        default_p = pt.get_paper_portfolio("default")
        rsi_p = pt.get_paper_portfolio("rsi")
        assert default_p.cash == default_p.initial_cash
        assert rsi_p.cash < rsi_p.initial_cash
        assert "BTC" in rsi_p.positions
        assert "BTC" not in default_p.positions

    def test_legacy_migration(self):
        legacy = {
            "initial_cash": 10000.0,
            "cash": 9000.0,
            "positions": {"ETH": {"quantity": 1.0, "entry_price": 1000.0}},
            "trade_history": [{"action": "buy", "symbol": "ETH"}],
            "total_trades": 1,
        }
        pt._save_portfolio(legacy)
        # load triggers migrate
        data = pt._load_portfolio()
        assert "strategies" in data
        assert "default" in data["strategies"]
        port = pt.get_paper_portfolio("default")
        assert port.cash == 9000.0
        assert "ETH" in port.positions
