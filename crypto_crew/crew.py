"""Crew orchestration — build and run the multi-agent crew."""

import logging
import re
from typing import Optional

from crewai import Crew, Process

from crypto_crew.agents import SUPERVISOR, MARKET_AGENT, NEWS_AGENT, TECHNICAL_AGENT, FUNDAMENTAL_AGENT, SENTIMENT_AGENT, PREDICTION_AGENT, BACKTEST_AGENT, RISK_AGENT, PAPER_AGENT
from crypto_crew.tasks import build_tasks
from crypto_crew.config import LLM_API_KEY, LLM_MODEL, DEFAULT_COIN, resolve_coin
from crypto_crew.integrations.cli_runner import find_cli

logger = logging.getLogger(__name__)


def _detect_intent(query: str) -> dict:
    """Parse user query for flags: coin, backtest, paper, days, risk."""
    result = {
        "coin": DEFAULT_COIN,
        "days": 7,
        "backtest": False,
        "paper": False,
        "risk_profile": "conservative",
    }

    q = query.lower()

    # Detect coin
    known_coins = {
        "btc": "btc", "bitcoin": "btc",
        "eth": "eth", "ethereum": "eth",
        "sol": "sol", "solana": "sol",
        "xrp": "xrp", "ripple": "xrp",
        "bnb": "bnb", "binance coin": "bnb",
        "doge": "doge", "dogecoin": "doge",
        "ada": "ada", "cardano": "ada",
        "dot": "dot", "polkadot": "dot",
    }
    for keyword, coin in known_coins.items():
        if keyword in q:
            result["coin"] = coin
            break

    # Intent detection
    if any(w in q for w in ("回测", "backtest", "策略", "交易策略", "rsi", "ma cross", "bollinger")):
        result["backtest"] = True
    if any(w in q for w in ("paper trading", "模拟交易", "虚拟交易", "持仓", "仓位", "portfolio", "交易员")):
        result["paper"] = True
    if any(w in q for w in ("激进", "aggressive", "高风险")):
        result["risk_profile"] = "aggressive"
    if any(w in q for w in ("保守", "conservative", "低风险")):
        result["risk_profile"] = "conservative"

    # Days
    day_match = re.search(r"(\d+)\s*(天|日|d)", q)
    if day_match:
        result["days"] = min(int(day_match.group(1)), 365)

    return result


def build_crew(query: str, **overrides) -> Crew:
    """Build a CrewAI crew for *query*."""
    intent = _detect_intent(query)
    intent.update(overrides)

    coin = intent["coin"]
    info = resolve_coin(coin)

    # Log available CLI tools
    for cli in ("onchainos", "twitter"):
        if find_cli(cli):
            logger.info("Found CLI: %s", cli)
        else:
            logger.info("CLI not found: %s", cli)

    tasks = build_tasks(
        query=query,
        coin=info["coingecko"],
        days=intent["days"],
        risk_profile=intent["risk_profile"],
        include_backtest=intent["backtest"],
        include_paper=intent["paper"],
    )

    all_agents = [
        SUPERVISOR, MARKET_AGENT, NEWS_AGENT, TECHNICAL_AGENT,
        FUNDAMENTAL_AGENT, SENTIMENT_AGENT, PREDICTION_AGENT,
        BACKTEST_AGENT, RISK_AGENT, PAPER_AGENT,
    ]

    crew = Crew(
        agents=all_agents,
        tasks=tasks,
        process=Process.hierarchical,
        manager_agent=SUPERVISOR,
        verbose=True,
    )

    return crew


def run_analysis(query: str, **overrides) -> str:
    """Run the full multi-agent analysis and return the final report."""
    crew = build_crew(query, **overrides)
    result = crew.kickoff()
    return str(result)
