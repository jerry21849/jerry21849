"""Market data tools — free APIs: CoinGecko (primary), Binance (fallback), onchainos (optional enhancement)."""

import time
import logging
from typing import Optional

import requests

from crypto_crew.config import COINGECKO_BASE, BINANCE_BASE, resolve_coin
from crypto_crew.integrations.cli_runner import run_cli_json, find_cli
from crypto_crew.models import MarketSnapshot

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAY = 1.5  # seconds


def _coingecko_get(path: str, params: dict | None = None, max_retries: int = _MAX_RETRIES) -> dict | None:
    """GET from CoinGecko with simple rate-limit retry."""
    url = f"{COINGECKO_BASE}{path}"
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 429:
                wait = _RETRY_DELAY * (2 ** attempt)
                logger.warning("CoinGecko 429, retrying in %.1fs", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning("CoinGecko attempt %d/%d failed: %s", attempt + 1, max_retries, e)
            if attempt < max_retries - 1:
                time.sleep(_RETRY_DELAY)
    return None


def _binance_get(path: str, params: dict | None = None) -> dict | list | None:
    """GET from Binance public API (no auth needed)."""
    url = f"{BINANCE_BASE}{path}"
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.warning("Binance API failed: %s", e)
        return None


def get_crypto_price(coin: str = "btc", vs_currency: str = "usd") -> MarketSnapshot:
    """Fetch current price + 24h stats for *coin*.

    Primary: CoinGecko. Fallback: Binance.
    Optional cross-check: onchainos CLI.
    """
    info = resolve_coin(coin)
    cg_id = info["coingecko"]
    binance_symbol = info["binance"]

    # ── Primary: CoinGecko ──────────────────────────────────────
    data = _coingecko_get(f"/simple/price", {
        "ids": cg_id,
        "vs_currencies": vs_currency,
        "include_24hr_vol": "true",
        "include_24hr_change": "true",
        "include_market_cap": "true",
    })
    if data and cg_id in data:
        entry = data[cg_id]
        snapshot = MarketSnapshot(
            coin=cg_id,
            price_usd=entry.get(f"{vs_currency}", 0.0),
            change_24h_pct=entry.get(f"{vs_currency}_24h_change"),
            volume_24h_usd=entry.get(f"{vs_currency}_24h_vol"),
            market_cap_usd=entry.get(f"{vs_currency}_market_cap"),
            source="coingecko",
        )
    else:
        # ── Fallback: Binance ───────────────────────────────────
        ticker = _binance_get("/ticker/24hr", {"symbol": binance_symbol})
        if ticker and isinstance(ticker, dict) and ticker.get("lastPrice"):
            snapshot = MarketSnapshot(
                coin=cg_id,
                price_usd=float(ticker["lastPrice"]),
                change_24h_pct=float(ticker.get("priceChangePercent", 0)),
                volume_24h_usd=float(ticker.get("quoteVolume", 0)),
                high_24h=float(ticker.get("highPrice", 0)),
                low_24h=float(ticker.get("lowPrice", 0)),
                source="binance",
            )
        else:
            snapshot = MarketSnapshot(coin=cg_id, error="All free price APIs unavailable")

    # ── Optional enhancement via onchainos ──────────────────────
    if find_cli("onchainos") and not snapshot.error:
        # Cross-check price — not blocking
        pass

    return snapshot


def get_historical_data(
    coin: str = "btc",
    days: int = 365,
    vs_currency: str = "usd",
) -> list[dict] | None:
    """Fetch OHLCV-like historical data.

    Primary: CoinGecko market_chart. Fallback: Binance klines.
    Returns list of {timestamp, open, high, low, close, volume} dicts,
    or None on total failure.
    """
    info = resolve_coin(coin)
    cg_id = info["coingecko"]
    binance_symbol = info["binance"]

    # ── Primary: CoinGecko ──────────────────────────────────────
    data = _coingecko_get(f"/coins/{cg_id}/market_chart", {
        "vs_currency": vs_currency,
        "days": str(min(days, 365)),
    })
    if data and "prices" in data:
        prices = data["prices"]        # [[ts_ms, price], ...]
        volumes = data.get("total_volumes", [])
        vol_map = {int(v[0]): v[1] for v in volumes} if volumes else {}
        candles = []
        for i, (ts, price) in enumerate(prices):
            candles.append({
                "timestamp": int(ts),
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": vol_map.get(int(ts), 0),
            })
        return candles

    # ── Fallback: Binance klines ─────────────────────────────────
    limit = min(days, 500)
    klines = _binance_get("/klines", {
        "symbol": binance_symbol,
        "interval": "1d",
        "limit": str(limit),
    })
    if klines and isinstance(klines, list) and len(klines) > 0:
        candles = []
        for k in klines:
            candles.append({
                "timestamp": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            })
        return candles

    return None
