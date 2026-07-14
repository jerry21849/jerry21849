"""Paper Trading tools — simulated trading with persistence.

Maintains portfolio state in state/paper_portfolio.json.
Supports multi-strategy simulation, 0.1% taker fee, configurable slippage.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from crypto_crew.config import PAPER_INITIAL_CASH, PAPER_TAKER_FEE, PAPER_SLIPPAGE
from crypto_crew.models import PaperPortfolio, PaperPosition

logger = logging.getLogger(__name__)

_STATE_DIR = Path(__file__).resolve().parent.parent / "state"
_PORTFOLIO_FILE = _STATE_DIR / "paper_portfolio.json"


def _load_portfolio() -> dict:
    """Load portfolio from JSON, creating default if missing/corrupt."""
    if not _PORTFOLIO_FILE.exists():
        return _default_portfolio()
    try:
        with open(_PORTFOLIO_FILE) as f:
            data = json.load(f)
        # Basic integrity check
        if "cash" not in data:
            raise ValueError("Missing 'cash' field")
        return data
    except (json.JSONDecodeError, ValueError, OSError) as e:
        logger.warning("Portfolio file corrupt, resetting: %s", e)
        return _default_portfolio()


def _default_portfolio() -> dict:
    return {
        "initial_cash": PAPER_INITIAL_CASH,
        "cash": PAPER_INITIAL_CASH,
        "positions": {},
        "trade_history": [],
        "total_trades": 0,
    }


def _save_portfolio(data: dict) -> None:
    """Persist portfolio state."""
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(_PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_paper_portfolio() -> PaperPortfolio:
    """Get current paper portfolio state."""
    data = _load_portfolio()
    positions = {}
    for sym, pos in data.get("positions", {}).items():
        positions[sym] = PaperPosition(
            symbol=sym,
            quantity=pos.get("quantity", 0),
            entry_price=pos.get("entry_price", 0),
        )
    return PaperPortfolio(
        initial_cash=data.get("initial_cash", PAPER_INITIAL_CASH),
        cash=data.get("cash", PAPER_INITIAL_CASH),
        positions=positions,
        trade_history=data.get("trade_history", [])[-20:],  # last 20 trades
        total_trades=data.get("total_trades", 0),
    )


def execute_paper_trade(
    action: str,
    symbol: str,
    amount_usd: float,
    current_price: float,
) -> PaperPortfolio:
    """Execute a simulated trade.

    Args:
        action: "buy" or "sell".
        symbol: Trading pair / coin symbol (e.g. "BTC").
        amount_usd: Dollar amount to trade.
        current_price: Execution price (before slippage).

    Returns:
        Updated PaperPortfolio.
    """
    data = _load_portfolio()
    cash = data["cash"]
    positions: dict = data["positions"]
    fee = PAPER_TAKER_FEE
    slippage = PAPER_SLIPPAGE
    action = action.lower()

    if action == "buy":
        # Apply slippage (buy at slightly higher price)
        exec_price = current_price * (1 + slippage)
        cost = amount_usd
        total_cost = cost * (1 + fee)

        if total_cost > cash:
            # Adjust to available cash
            total_cost = cash
            cost = cash / (1 + fee)

        qty = cost / exec_price
        cash -= total_cost

        # Update position
        sym = symbol.upper()
        if sym in positions:
            old = positions[sym]
            avg_price = ((old["quantity"] * old["entry_price"]) + (qty * exec_price)) / (old["quantity"] + qty)
            old["quantity"] += qty
            old["entry_price"] = avg_price
        else:
            positions[sym] = {"quantity": qty, "entry_price": exec_price}

        data["trade_history"].append({
            "action": "buy",
            "symbol": sym,
            "quantity": round(qty, 8),
            "price": round(exec_price, 2),
            "fee": round(cost * fee, 2),
        })

    elif action == "sell":
        sym = symbol.upper()
        if sym not in positions or positions[sym]["quantity"] <= 0:
            logger.warning("No %s position to sell", sym)
            return _portfolio_to_model(data)

        pos = positions[sym]
        exec_price = current_price * (1 - slippage)
        sell_qty = pos["quantity"]
        proceeds = sell_qty * exec_price * (1 - fee)
        cash += proceeds

        data["trade_history"].append({
            "action": "sell",
            "symbol": sym,
            "quantity": round(sell_qty, 8),
            "price": round(exec_price, 2),
            "fee": round(sell_qty * exec_price * fee, 2),
        })

        del positions[sym]

    else:
        logger.warning("Unknown action: %s (use 'buy' or 'sell')", action)

    data["cash"] = cash
    data["total_trades"] = len(data["trade_history"])
    _save_portfolio(data)
    return _portfolio_to_model(data)


def _portfolio_to_model(data: dict) -> PaperPortfolio:
    positions = {}
    for sym, pos in data.get("positions", {}).items():
        positions[sym] = PaperPosition(
            symbol=sym,
            quantity=pos.get("quantity", 0),
            entry_price=pos.get("entry_price", 0),
        )
    return PaperPortfolio(
        initial_cash=data.get("initial_cash", PAPER_INITIAL_CASH),
        cash=data.get("cash", PAPER_INITIAL_CASH),
        positions=positions,
        trade_history=data.get("trade_history", [])[-20:],
        total_trades=data.get("total_trades", 0),
    )
