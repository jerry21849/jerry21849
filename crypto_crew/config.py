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
PORTFOLIO_COINS: list[str] = ["btc", "eth", "sol"]
GRADIO_PORT = int(os.getenv("GRADIO_PORT", "7860"))

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

_PLACEHOLDER_KEYS = {
    "",
    "sk-your-key-here",
    "your-api-key",
    "changeme",
}


def validate_api_key() -> None:
    """Raise ValueError if OPENAI_API_KEY is missing or a placeholder."""
    # Re-read env each call so CLI overrides / late dotenv loads are honored.
    key = (os.getenv("OPENAI_API_KEY") or LLM_API_KEY or "").strip()
    if not key or key.lower() in _PLACEHOLDER_KEYS or key.startswith("sk-your-"):
        raise ValueError(
            "OPENAI_API_KEY 未設定或仍為占位符。"
            "請在 .env 中填入有效的 API Key（參考 .env.example）。"
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
