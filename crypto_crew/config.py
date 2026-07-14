"""Configuration — env vars, symbol mapping, free API endpoints, disclaimer."""

import os
from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
PAPER_INITIAL_CASH = float(os.getenv("PAPER_INITIAL_CASH", "10000"))

# ── Symbol resolution ──────────────────────────────────────────────
# Maps user-friendly coin names → CoinGecko id / Binance symbol / general alias
SYMBOL_MAP: dict[str, dict[str, str]] = {
    "btc": {"coingecko": "bitcoin", "binance": "BTCUSDT", "name": "Bitcoin"},
    "eth": {"coingecko": "ethereum", "binance": "ETHUSDT", "name": "Ethereum"},
    "sol": {"coingecko": "solana", "binance": "SOLUSDT", "name": "Solana"},
    "xrp": {"coingecko": "ripple", "binance": "XRPUSDT", "name": "XRP"},
    "bnb": {"coingecko": "binancecoin", "binance": "BNBUSDT", "name": "BNB"},
    "doge": {"coingecko": "dogecoin", "binance": "DOGEUSDT", "name": "Dogecoin"},
    "ada": {"coingecko": "cardano", "binance": "ADAUSDT", "name": "Cardano"},
    "dot": {"coingecko": "polkadot", "binance": "DOTUSDT", "name": "Polkadot"},
    "matic": {"coingecko": "matic-network", "binance": "MATICUSDT", "name": "Polygon"},
    "link": {"coingecko": "chainlink", "binance": "LINKUSDT", "name": "Chainlink"},
}

DEFAULT_COIN = "btc"

# ── Free API endpoints ─────────────────────────────────────────────
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
BINANCE_BASE = "https://api.binance.com/api/v3"
ALTERNATIVE_ME = "https://api.alternative.me/fng/"
DEFILLAMA_BASE = "https://api.llama.fi"

# ── CLI tool paths (auto-detected) ─────────────────────────────────
ONCHAINOS_CMD = "onchainos"
TWITTER_CLI = os.getenv("TWITTER_CLI") or "twitter"

# ── Paper Trading defaults ─────────────────────────────────────────
PAPER_TAKER_FEE = 0.001   # 0.1%
PAPER_SLIPPAGE = 0.0005   # 0.05%

# ── Disclaimer ─────────────────────────────────────────────────────
DISCLAIMER = (
    "\n\n---\n"
    "⚠️ **免責聲明**：本分析僅供參考，不是財務建議。"
    "加密貨幣波動極大，投資有虧損風險，請自行研究（DYOR）。"
    "預測準確率無法保證。"
)


def resolve_coin(coin: str) -> dict[str, str]:
    """Resolve a coin alias to its canonical IDs. Falls back to BTC."""
    key = coin.strip().lower()
    if key in SYMBOL_MAP:
        return SYMBOL_MAP[key]
    # Try partial match
    for sym, info in SYMBOL_MAP.items():
        if key in sym or key in info["coingecko"] or key in info["name"].lower():
            return info
    return SYMBOL_MAP[DEFAULT_COIN]
