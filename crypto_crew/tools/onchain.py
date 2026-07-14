"""On-chain & fundamental data tools — free sources.

DefiLlama (TVL, fees) + Jina Reader for whitepaper/web summaries.
"""

import logging
from typing import Optional

import requests

from crypto_crew.config import DEFILLAMA_BASE
from crypto_crew.models import OnChainSnapshot

logger = logging.getLogger(__name__)

JINA_READER = "https://r.jina.ai/http://"


def get_defi_tvl(protocol: str = "bitcoin") -> Optional[dict]:
    """Fetch TVL data from DefiLlama (free, no key).

    For individual chains, uses /v2/chains. For protocols, uses /protocol/{slug}.
    """
    try:
        # Try as a chain first
        resp = requests.get(f"{DEFILLAMA_BASE}/v2/chains", timeout=15)
        resp.raise_for_status()
        chains = resp.json()
        for chain in (chains if isinstance(chains, list) else []):
            if protocol.lower() in chain.get("name", "").lower():
                return {
                    "tvl": chain.get("tvl"),
                    "change_24h": chain.get("change_1d"),
                }
    except requests.RequestException as e:
        logger.warning("DefiLlama chain TVL failed: %s", e)
    return None


def _fetch_web_summary(url: str) -> Optional[str]:
    """Use Jina Reader to get a short summary from a URL."""
    try:
        reader_url = f"{JINA_READER}{url}"
        resp = requests.get(reader_url, timeout=20,
                            headers={"X-Return-Format": "text"})
        if resp.status_code == 200:
            text = resp.text.strip()
            return text[:800] if text else None
    except requests.RequestException as e:
        logger.warning("Jina Reader failed for %s: %s", url, e)
    return None


def get_onchain_snapshot(coin: str = "btc") -> OnChainSnapshot:
    """Get on-chain / fundamental snapshot for *coin*.

    Combines DefiLlama TVL + optional web summary.
    """
    info = {"bitcoin": "bitcoin", "ethereum": "ethereum"}.get(coin, coin)
    tvl_data = get_defi_tvl(info)
    notes = ""

    if tvl_data:
        notes += f"TVL on-chain: ${tvl_data.get('tvl', 'N/A'):,.0f}" if tvl_data.get('tvl') else "TVL data unavailable"
        if tvl_data.get("change_24h"):
            notes += f" | 24h change: {tvl_data['change_24h']:+.2f}%"

    # For major coins, fetch a brief project summary via Jina
    if coin in ("btc", "bitcoin"):
        web = _fetch_web_summary("bitcoin.org/bitcoin.pdf")
        if web:
            notes += f"\nProject summary: {web[:200]}..."
    elif coin in ("eth", "ethereum"):
        web = _fetch_web_summary("ethereum.org/en/whitepaper/")
        if web:
            notes += f"\nProject summary: {web[:200]}..."

    score = 7 if "bitcoin" in coin or "ethereum" in coin else 5

    return OnChainSnapshot(
        tvl_usd=tvl_data.get("tvl") if tvl_data else None,
        tvl_change_24h=tvl_data.get("change_24h") if tvl_data else None,
        score=score,
        notes=notes[:500] if notes else "On-chain data limited for this asset.",
    )
