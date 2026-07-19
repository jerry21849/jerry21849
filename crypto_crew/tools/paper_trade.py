"""Paper Trading tools — simulated trading with persistence.

Maintains portfolio state in state/paper_portfolio.json.
Supports multi-strategy isolation via strategy_tag, 0.1% taker fee, configurable slippage.
"""

import json
import logging
from pathlib import Path

from crypto_crew.config import PAPER_INITIAL_CASH, PAPER_TAKER_FEE, PAPER_SLIPPAGE
from crypto_crew.models import PaperPortfolio, PaperPosition

logger = logging.getLogger(__name__)

_STATE_DIR = Path(__file__).resolve().parent.parent / "state"
_PORTFOLIO_FILE = _STATE_DIR / "paper_portfolio.json"
_DEFAULT_TAG = "default"


def _default_portfolio() -> dict:
    return {
        "version": 2,
        "initial_cash": PAPER_INITIAL_CASH,
        "strategies": {
            _DEFAULT_TAG: {
                "cash": PAPER_INITIAL_CASH,
                "positions": {},
                "trade_history": [],
                "total_trades": 0,
            }
        },
    }


def _is_legacy(data: dict) -> bool:
    """Detect pre-multi-strategy portfolio format."""
    return "strategies" not in data and "cash" in data


def _migrate_legacy(data: dict) -> dict:
    """Convert flat portfolio to strategy-tagged structure."""
    return {
        "version": 2,
        "initial_cash": data.get("initial_cash", PAPER_INITIAL_CASH),
        "strategies": {
            _DEFAULT_TAG: {
                "cash": data.get("cash", PAPER_INITIAL_CASH),
                "positions": data.get("positions", {}),
                "trade_history": data.get("trade_history", []),
                "total_trades": data.get("total_trades", 0),
            }
        },
    }


def _load_portfolio() -> dict:
    """Load portfolio from JSON, creating default if missing/corrupt; migrate legacy."""
    if not _PORTFOLIO_FILE.exists():
        return _default_portfolio()
    try:
        with open(_PORTFOLIO_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if _is_legacy(data):
            logger.info("Migrating legacy paper portfolio to multi-strategy format")
            data = _migrate_legacy(data)
            _save_portfolio(data)
        if "strategies" not in data:
            raise ValueError("Missing 'strategies' field")
        return data
    except (json.JSONDecodeError, ValueError, OSError) as e:
        logger.warning("Portfolio file corrupt, resetting: %s", e)
        return _default_portfolio()


def _save_portfolio(data: dict) -> None:
    """Persist portfolio state."""
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(_PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _ensure_strategy(data: dict, strategy_tag: str) -> dict:
    """Return mutable strategy bucket, creating it if needed."""
    tag = strategy_tag or _DEFAULT_TAG
    strategies = data.setdefault("strategies", {})
    if tag not in strategies:
        strategies[tag] = {
            "cash": data.get("initial_cash", PAPER_INITIAL_CASH),
            "positions": {},
            "trade_history": [],
            "total_trades": 0,
        }
    return strategies[tag]


def _bucket_to_model(data: dict, bucket: dict) -> PaperPortfolio:
    positions = {}
    for sym, pos in bucket.get("positions", {}).items():
        positions[sym] = PaperPosition(
            symbol=sym,
            quantity=pos.get("quantity", 0),
            entry_price=pos.get("entry_price", 0),
        )
    return PaperPortfolio(
        initial_cash=data.get("initial_cash", PAPER_INITIAL_CASH),
        cash=bucket.get("cash", PAPER_INITIAL_CASH),
        positions=positions,
        trade_history=bucket.get("trade_history", [])[-20:],
        total_trades=bucket.get("total_trades", 0),
    )


def get_paper_portfolio(strategy_tag: str = _DEFAULT_TAG) -> PaperPortfolio:
    """Get current paper portfolio state for *strategy_tag*."""
    data = _load_portfolio()
    bucket = _ensure_strategy(data, strategy_tag)
    return _bucket_to_model(data, bucket)


def execute_paper_trade(
    action: str,
    symbol: str,
    amount_usd: float,
    current_price: float,
    strategy_tag: str = _DEFAULT_TAG,
) -> PaperPortfolio:
    """Execute a simulated trade under *strategy_tag*.

    Args:
        action: "buy" or "sell".
        symbol: Trading pair / coin symbol (e.g. "BTC").
        amount_usd: Dollar amount to trade.
        current_price: Execution price (before slippage).
        strategy_tag: Isolates cash/positions per strategy (default: "default").

    Returns:
        Updated PaperPortfolio for that strategy.
    """
    data = _load_portfolio()
    bucket = _ensure_strategy(data, strategy_tag)
    cash = bucket["cash"]
    positions: dict = bucket["positions"]
    fee = PAPER_TAKER_FEE
    slippage = PAPER_SLIPPAGE
    action = action.lower()

    if action == "buy":
        exec_price = current_price * (1 + slippage)
        cost = amount_usd
        total_cost = cost * (1 + fee)

        if total_cost > cash:
            total_cost = cash
            cost = cash / (1 + fee)

        qty = cost / exec_price if exec_price > 0 else 0.0
        cash -= total_cost

        sym = symbol.upper()
        if sym in positions:
            old = positions[sym]
            avg_price = (
                (old["quantity"] * old["entry_price"]) + (qty * exec_price)
            ) / (old["quantity"] + qty)
            old["quantity"] += qty
            old["entry_price"] = avg_price
        else:
            positions[sym] = {"quantity": qty, "entry_price": exec_price}

        bucket["trade_history"].append({
            "action": "buy",
            "symbol": sym,
            "quantity": round(qty, 8),
            "price": round(exec_price, 2),
            "fee": round(cost * fee, 2),
            "strategy_tag": strategy_tag or _DEFAULT_TAG,
        })

    elif action == "sell":
        sym = symbol.upper()
        if sym not in positions or positions[sym]["quantity"] <= 0:
            logger.warning("No %s position to sell (strategy=%s)", sym, strategy_tag)
            return _bucket_to_model(data, bucket)

        pos = positions[sym]
        exec_price = current_price * (1 - slippage)
        sell_qty = pos["quantity"]
        proceeds = sell_qty * exec_price * (1 - fee)
        cash += proceeds

        bucket["trade_history"].append({
            "action": "sell",
            "symbol": sym,
            "quantity": round(sell_qty, 8),
            "price": round(exec_price, 2),
            "fee": round(sell_qty * exec_price * fee, 2),
            "strategy_tag": strategy_tag or _DEFAULT_TAG,
        })

        del positions[sym]

    else:
        logger.warning("Unknown action: %s (use 'buy' or 'sell')", action)

    bucket["cash"] = cash
    bucket["total_trades"] = len(bucket["trade_history"])
    _save_portfolio(data)
    return _bucket_to_model(data, bucket)
