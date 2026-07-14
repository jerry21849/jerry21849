"""Tests for paper trading tools — portfolio persistence and trade execution."""

import json
import pytest
from pathlib import Path
from crypto_crew.tools.paper_trade import (
    execute_paper_trade,
    get_paper_portfolio,
    _load_portfolio,
    _save_portfolio,
    _default_portfolio,
)
from crypto_crew.models import PaperPortfolio, PaperPosition


class TestPaperTrade:
    def setup_method(self):
        """Reset portfolio to defaults before each test."""
        _save_portfolio(_default_portfolio())

    def test_initial_portfolio(self):
        portfolio = get_paper_portfolio()
        assert portfolio.cash == 10000.0
        assert portfolio.positions == {}
        assert portfolio.total_trades == 0

    def test_buy_then_sell(self):
        # Buy
        execute_paper_trade("buy", "BTC", 1000, 50000.0)
        portfolio = get_paper_portfolio()
        assert "BTC" in portfolio.positions
        assert portfolio.cash < 10000.0  # Cash decreased
        assert portfolio.total_trades >= 1

        # Sell
        execute_paper_trade("sell", "BTC", 0, 51000.0)
        portfolio = get_paper_portfolio()
        assert "BTC" not in portfolio.positions  # Position closed
        assert portfolio.total_trades >= 2

    def test_buy_insufficient_cash_adjusts(self):
        """Buying more than available cash should use all cash."""
        portfolio = get_paper_portfolio()
        execute_paper_trade("buy", "BTC", 999999, 50000.0)
        portfolio = get_paper_portfolio()
        # Should have bought with most of available cash
        assert portfolio.cash < 100  # Very little cash left
        assert "BTC" in portfolio.positions

    def test_sell_no_position(self):
        """Selling without holding should be a no-op."""
        portfolio_before = get_paper_portfolio()
        execute_paper_trade("sell", "ETH", 0, 3000.0)
        portfolio_after = get_paper_portfolio()
        assert portfolio_after.cash == portfolio_before.cash

    def test_trade_fee_applied(self):
        """0.1% taker fee should be reflected."""
        execute_paper_trade("buy", "BTC", 1000, 50000.0)
        portfolio = get_paper_portfolio()
        # 1000 * 0.001 = $1 fee
        expected_cash = 10000 - 1000 - 1  # approx
        assert abs(portfolio.cash - expected_cash) < 0.1

    def test_average_entry_price(self):
        """Buying same coin twice should average entry price."""
        execute_paper_trade("buy", "BTC", 1000, 40000.0)
        execute_paper_trade("buy", "BTC", 1000, 50000.0)
        portfolio = get_paper_portfolio()
        pos = portfolio.positions["BTC"]
        # Average: (1000*40000 + 1000*50000) / (qty from both buys)
        # But fees reduce the quantity a bit
        assert pos.entry_price > 40000
        assert pos.entry_price < 50000

    def test_trade_history_limit(self):
        """Trade history should keep last 20 trades."""
        for i in range(25):
            execute_paper_trade("buy", "BTC", 100, 50000.0)
            execute_paper_trade("sell", "BTC", 0, 51000.0)
        portfolio = get_paper_portfolio()
        assert len(portfolio.trade_history) <= 20
