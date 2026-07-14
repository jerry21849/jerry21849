"""Sentiment tools — free sources.

Fear & Greed Index (alternative.me) + onchainos social sentiment (CLI) +
agent-reach/Twitter search as fallback for X sentiment.
"""

import logging
import re
from typing import Optional

import requests

from crypto_crew.config import ALTERNATIVE_ME, resolve_coin
from crypto_crew.integrations.cli_runner import run_cli, run_cli_json, find_cli
from crypto_crew.models import SentimentSnapshot

logger = logging.getLogger(__name__)


def get_fear_greed() -> tuple[Optional[int], str, str]:
    """Fetch Fear & Greed Index from alternative.me (free, no key)."""
    try:
        resp = requests.get(ALTERNATIVE_ME, params={"limit": "1"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        entry = data["data"][0]
        value = int(entry["value"])
        classification = entry.get("value_classification", "Neutral")
        return value, classification, "alternative.me"
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        logger.warning("Fear & Greed fetch failed: %s", e)
        return None, "Unknown", "alternative.me"


def _llm_sentiment_score(texts: list[str]) -> float:
    """Simple keyword-based sentiment scorer when LLM is not available inline.

    Returns a float in [-1, 1]. Positive = bullish, negative = bearish.
    Handles both English words and Chinese characters.
    """
    if not texts:
        return 0.0
    # English keywords
    bull_en = {"bullish", "buy", "moon", "pump", "long", "uptrend", " breakout"}
    bear_en = {"bearish", "sell", "crash", "dump", "short", "downtrend"}
    # Chinese keywords (checked via substring match because re.split on CJK is unreliable)
    bull_cn = ["突破", "买入", "买", "看涨", "看多", "利好", "做多", "做多", "反弹", "拉盘"]
    bear_cn = ["跌破", "卖出", "卖", "看跌", "看空", "利空", "做空", "恐慌", "崩盘", "砸盘"]

    score = 0.0
    count = 0
    for text in texts:
        lower = text.lower()
        bulls = 0
        bears = 0
        # English token matching
        tokens = re.findall(r"[a-zA-Z]+", lower)
        token_set = set(tokens)
        bulls += len(token_set & bull_en)
        bears += len(token_set & bear_en)
        # Chinese substring matching
        for kw in bull_cn:
            if kw in lower:
                bulls += 1
        for kw in bear_cn:
            if kw in lower:
                bears += 1
        total = bulls + bears
        if total > 0:
            score += (bulls - bears) / total
            count += 1
    return round(score / count, 4) if count > 0 else 0.0


def _fetch_onchainos_sentiment(symbol: str) -> Optional[float]:
    """Try onchainos social sentiment-symbol CLI."""
    if not find_cli("onchainos"):
        return None
    data = run_cli_json([
        "onchainos", "social", "sentiment-symbol",
        "--token-symbols", symbol.upper(),
    ])
    if not data:
        return None
    # Extract overall sentiment from response
    items = data if isinstance(data, list) else (data.get("data") or [data])
    if not items:
        return None
    # Try a few common field names
    for item in items if isinstance(items, list) else [items]:
        for key in ("sentimentScore", "score", "bullishRatio", "sentiment"):
            val = item.get(key)
            if val is not None:
                try:
                    return float(val) * 2 - 1 if key in ("bullishRatio",) else float(val)
                except (ValueError, TypeError):
                    continue
    return None


def _fetch_twitter_sentiment(symbol: str, max_tweets: int = 20) -> Optional[float]:
    """Fallback: use agent-reach / twitter CLI to search and score."""
    if not find_cli("twitter"):
        return None
    stdout, stderr, rc = run_cli([
        "twitter", "search", f"{symbol} crypto", "-n", str(max_tweets),
    ])
    if rc != 0 or not stdout:
        return None
    # Extract tweet texts from output (simple line-based extraction)
    texts = []
    for line in stdout.splitlines():
        line = line.strip()
        if line and len(line) > 20 and not line.startswith("["):
            texts.append(line)
    return _llm_sentiment_score(texts[:max_tweets])


def get_sentiment(coin: str = "btc") -> SentimentSnapshot:
    """Get multi-source sentiment snapshot.

    Combines: Fear & Greed + onchainos social sentiment + Twitter fallback.
    """
    info = resolve_coin(coin)
    symbol = info.get("binance", "BTC").replace("USDT", "")

    fng_value, fng_label, fng_source = get_fear_greed()

    # Try onchainos sentiment CLI
    social_score = _fetch_onchainos_sentiment(symbol)

    # Fallback: Twitter keyword scoring
    if social_score is None:
        social_score = _fetch_twitter_sentiment(symbol)

    # Try Reddit pulse via agent-reach (if available)
    reddit_pulse = None
    if find_cli("opencli") or find_cli("rdt"):
        # Non-blocking attempt
        try:
            r_stdout, r_stderr, r_rc = run_cli(
                ["opencli", "reddit", "search", f"{symbol} crypto", "-f", "yaml"],
                timeout=15,
            ) if find_cli("opencli") else (None, None, -1)
            if r_rc == 0 and r_stdout:
                reddit_pulse = "Reddit discussion detected" if len(r_stdout) > 50 else "Low Reddit activity"
        except Exception:
            reddit_pulse = None

    return SentimentSnapshot(
        fear_greed_index=fng_value,
        fear_greed_label=fng_label,
        social_score=social_score,
        reddit_pulse=reddit_pulse,
        source=fng_source,
    )
