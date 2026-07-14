"""News tools — free sources.

Priority: onchainos social CLI (free tier) → CryptoCompare news endpoint → CoinGecko status updates.
"""

import logging
from typing import Optional

import requests

from crypto_crew.config import resolve_coin
from crypto_crew.integrations.cli_runner import run_cli_json, find_cli
from crypto_crew.models import NewsItem, NewsResult

logger = logging.getLogger(__name__)

CRYPTOCOMPARE_NEWS = "https://min-api.cryptocompare.com/data/v2/news/"


def _parse_impact(text: str) -> str:
    """Basic keyword-based impact rating."""
    text_lower = text.lower()
    high_words = ["hack", "sec", "ban", "crash", "exploit", "regulation", "lawsuit"]
    low_words = ["meme", "nft", "partnership", "integration", "update"]
    if any(w in text_lower for w in high_words):
        return "high"
    if any(w in text_lower for w in low_words):
        return "low"
    return "medium"


def _fetch_cryptocompare_news(query: str, limit: int = 10) -> list[NewsItem]:
    """Free tier: up to 200 calls/day, no API key needed for basic use."""
    try:
        resp = requests.get(
            CRYPTOCOMPARE_NEWS,
            params={"categories": query, "limit": min(limit, 50)},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        items = []
        for article in (data.get("Data") or [])[:limit]:
            items.append(NewsItem(
                title=article.get("title", ""),
                source=article.get("source", ""),
                url=article.get("url"),
                summary=article.get("body", "")[:300] if article.get("body") else None,
                impact=_parse_impact(article.get("title", "")),
                timestamp=str(article.get("published_on", "")),
            ))
        return items
    except requests.RequestException as e:
        logger.warning("CryptoCompare news failed: %s", e)
        return []


def _fetch_onchainos_news(symbol: str, limit: int = 10) -> list[NewsItem] | None:
    """Try onchainos social news-by-symbol CLI."""
    if not find_cli("onchainos"):
        return None
    data = run_cli_json(["onchainos", "social", "news-by-symbol",
                         "--token-symbols", symbol.upper(),
                         "--limit", str(limit)])
    if not data:
        return None
    # The CLI returns structured JSON; adapt to NewsItem
    items = []
    raw_list = data if isinstance(data, list) else (data.get("data") or data.get("items") or [])
    for article in raw_list[:limit]:
        items.append(NewsItem(
            title=article.get("title", ""),
            source=article.get("source", "") or article.get("sourceName", ""),
            url=article.get("sourceUrl"),
            summary=article.get("summary", "")[:300],
            impact=article.get("importance", "medium"),
            timestamp=str(article.get("timestamp", "")),
        ))
    return items


def get_news(coin: str = "btc", limit: int = 10) -> NewsResult:
    """Get latest news for *coin*.

    Priority: onchainos social CLI → CryptoCompare.
    """
    info = resolve_coin(coin)
    symbol = info.get("binance", "BTC").replace("USDT", "")

    # Try onchainos first
    items = _fetch_onchainos_news(symbol, limit)
    if items is not None:
        return NewsResult(items=items, source="onchainos")

    # Fallback: CryptoCompare
    items = _fetch_cryptocompare_news(info["name"], limit)
    source = "cryptocompare" if items else "none"
    return NewsResult(items=items, source=source)
