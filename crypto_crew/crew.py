"""Crew orchestration — build and run the multi-agent crew."""

import logging
import re
import time
from typing import Any

from crewai import Crew, Process

from crypto_crew.agents import all_agents, get_supervisor
from crypto_crew.tasks import build_tasks
from crypto_crew.config import (
    DEFAULT_COIN,
    PORTFOLIO_COINS,
    resolve_coin,
    validate_api_key,
    DISCLAIMER,
)
from crypto_crew.integrations.cli_runner import find_cli
from crypto_crew.tools import market, news, sentiment, technical, onchain
from crypto_crew.tools import backtest as bt, paper_trade, risk as risk_tools
from crypto_crew.report import render_report, render_portfolio_report

logger = logging.getLogger(__name__)


def _detect_intent(query: str) -> dict[str, Any]:
    """Parse user query for flags: coin, backtest, paper, days, risk."""
    result: dict[str, Any] = {
        "coin": DEFAULT_COIN,
        "days": 7,
        "backtest": False,
        "paper": False,
        "risk_profile": "conservative",
    }

    q = query.lower()

    known_coins = {
        "btc": "btc",
        "bitcoin": "btc",
        "eth": "eth",
        "ethereum": "eth",
        "sol": "sol",
        "solana": "sol",
        "xrp": "xrp",
        "ripple": "xrp",
        "bnb": "bnb",
        "binance coin": "bnb",
        "doge": "doge",
        "dogecoin": "doge",
        "ada": "ada",
        "cardano": "ada",
        "dot": "dot",
        "polkadot": "dot",
    }
    for keyword, coin in known_coins.items():
        if keyword in q:
            result["coin"] = coin
            break

    if any(w in q for w in ("回测", "回測", "backtest", "策略", "交易策略", "rsi", "ma cross", "bollinger")):
        result["backtest"] = True
    if any(w in q for w in ("paper trading", "模拟交易", "模擬交易", "虚拟交易", "虛擬交易", "持仓", "持倉", "仓位", "倉位", "portfolio", "交易员", "交易員")):
        result["paper"] = True
    if any(w in q for w in ("激进", "激進", "aggressive", "高风险", "高風險")):
        result["risk_profile"] = "aggressive"
    if any(w in q for w in ("保守", "conservative", "低风险", "低風險")):
        result["risk_profile"] = "conservative"

    day_match = re.search(r"(\d+)\s*(天|日|d)", q)
    if day_match:
        result["days"] = min(int(day_match.group(1)), 365)

    return result


def build_crew(query: str, **overrides) -> Crew:
    """Build a CrewAI crew for *query*."""
    intent = _detect_intent(query)
    intent.update({k: v for k, v in overrides.items() if v is not None and v != ""})

    coin = intent["coin"]
    info = resolve_coin(coin)

    for cli in ("onchainos", "twitter"):
        if find_cli(cli):
            logger.info("Found CLI: %s", cli)
        else:
            logger.info("CLI not found: %s", cli)

    tasks = build_tasks(
        query=query,
        coin=info["coingecko"],
        days=intent.get("days", 7),
        risk_profile=intent.get("risk_profile", "conservative"),
        include_backtest=bool(intent.get("backtest")),
        include_paper=bool(intent.get("paper")),
    )

    agents = all_agents()
    supervisor = get_supervisor()

    try:
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.hierarchical,
            manager_agent=supervisor,
            verbose=True,
        )
    except Exception as e:
        logger.warning("Hierarchical crew failed (%s); falling back to sequential", e)
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    return crew


def _fallback_tool_pipeline(
    coin: str,
    days: int = 90,
    risk_profile: str = "conservative",
    include_backtest: bool = False,
    include_paper: bool = False,
) -> str:
    """Deterministic tool-only pipeline when CrewAI / LLM is unavailable."""
    sections: list[str] = []
    alias = coin if len(coin) <= 5 else DEFAULT_COIN
    # resolve_coin accepts aliases; coingecko ids also often work via partial match
    snap = market.get_crypto_price(alias if alias in ("btc", "eth", "sol") else coin)
    if snap.error and coin not in ("btc", "eth"):
        # try alias from coingecko id reverse
        from crypto_crew.config import SYMBOL_MAP
        for k, v in SYMBOL_MAP.items():
            if v["coingecko"] == coin:
                alias = k
                snap = market.get_crypto_price(k)
                break

    sections.append("## 1. 📊 市場現價\n")
    if snap.error:
        sections.append(f"數據不可用：{snap.error}\n")
    else:
        chg = f"{snap.change_24h_pct:.2f}%" if snap.change_24h_pct is not None else "N/A"
        vol = f"${snap.volume_24h_usd:,.0f}" if snap.volume_24h_usd is not None else "N/A"
        mcap = f"${snap.market_cap_usd:,.0f}" if snap.market_cap_usd is not None else "N/A"
        sections.append(
            f"- **幣種**: {snap.coin}\n"
            f"- **現價**: ${snap.price_usd:,.2f}\n"
            f"- **24h 變化**: {chg}\n"
            f"- **24h 成交量**: {vol}\n"
            f"- **市值**: {mcap}\n"
            f"- **來源**: {snap.source}\n"
        )

    news_res = news.get_news(alias, limit=5)
    sections.append("\n## 2. 📰 新聞摘要\n")
    if not news_res.items:
        sections.append(f"暫無新聞（source={news_res.source}）。\n")
    else:
        for item in news_res.items[:5]:
            sections.append(f"- [{item.impact}] **{item.title}**（{item.source}）\n")

    hist_days = max(days, 90)
    candles = market.get_historical_data(alias, days=hist_days)
    tech = technical.calculate_technical_indicators(candles or [])
    sections.append("\n## 3. 🔬 技術分析\n")
    if tech.error:
        sections.append(f"{tech.error}\n")
    else:
        sections.append(f"- **趨勢**: {tech.trend}\n")
        if tech.support is not None:
            sections.append(f"- **支撐**: ${tech.support:,.2f}\n")
        if tech.resistance is not None:
            sections.append(f"- **阻力**: ${tech.resistance:,.2f}\n")
        for row in tech.indicators[:8]:
            sig = f" — {row.signal}" if row.signal else ""
            sections.append(f"- {row.name}: {row.value}{sig}\n")

    onchain_snap = onchain.get_onchain_snapshot(alias)
    sections.append("\n## 4. ⛓️ 鏈上與基本面\n")
    sections.append(f"- **健康度評分**: {onchain_snap.score}/10\n")
    if onchain_snap.tvl_usd is not None:
        sections.append(f"- **TVL**: ${onchain_snap.tvl_usd:,.0f}\n")
    if onchain_snap.notes:
        sections.append(f"- {onchain_snap.notes}\n")

    sent = sentiment.get_sentiment(alias)
    sections.append("\n## 5. 💬 市場情緒\n")
    sections.append(
        f"- **Fear & Greed**: {sent.fear_greed_index}（{sent.fear_greed_label}）\n"
        f"- **社群分數**: {sent.social_score}\n"
        f"- **來源**: {sent.source}\n"
    )

    sections.append("\n## 6. 🔮 價格預測\n")
    sections.append(
        "_LLM 不可用，以下為基於工具數據的規則摘要：_\n\n"
        f"- 技術趨勢為 **{tech.trend if not tech.error else '未知'}**；"
        f"情緒標籤為 **{sent.fear_greed_label}**。\n"
        "- **多頭觀點**: 若趨勢偏多且情緒未極端貪婪，短線可觀察阻力位突破。\n"
        "- **空頭觀點**: 若波動升高或情緒過熱，注意支撐失守風險。\n"
        "- **信心分數**: 4/10（無 LLM 綜合推理）。\n"
    )

    if include_backtest and candles:
        sections.append("\n## 7. 📈 回測報告\n")
        for strat in ("rsi", "ma_cross", "bollinger"):
            report = bt.run_backtest(strat, candles)
            if report.error:
                sections.append(f"- **{strat}**: {report.error}\n")
            else:
                sections.append(
                    f"- **{strat}**: 報酬 {report.total_return_pct}% | "
                    f"Sharpe {report.sharpe_ratio} | MaxDD {report.max_drawdown_pct}% | "
                    f"勝率 {report.win_rate_pct}% | 交易數 {report.total_trades}\n"
                )
    else:
        sections.append("\n## 7. 📈 回測報告\n\n_未執行_\n")

    sections.append("\n## 8. ⚠️ 風險評估\n")
    risk_adv = risk_tools.compute_risk_metrics(
        candles or [],
        current_price=snap.price_usd if not snap.error else None,
        risk_profile=risk_profile,
    )
    if risk_adv.error:
        sections.append(f"{risk_adv.error}\n")
    else:
        sections.append(
            f"- **年化波動**: {risk_adv.volatility_pct}%\n"
            f"- **ATR**: {risk_adv.atr}\n"
            f"- **建議倉位**: {risk_adv.suggested_position_size_pct}%\n"
            f"- **止損**: {risk_adv.stop_loss_pct}% | **止盈**: {risk_adv.take_profit_pct}%\n"
            f"- **VaR 95%**: {risk_adv.var_95_pct}%\n"
            f"- {risk_adv.notes}\n"
        )

    sections.append("\n## 9. 💼 Paper Trading 狀態\n")
    if include_paper:
        port = paper_trade.get_paper_portfolio()
        sections.append(
            f"- **現金**: ${port.cash:,.2f}\n"
            f"- **初始資金**: ${port.initial_cash:,.2f}\n"
            f"- **持倉數**: {len(port.positions)}\n"
            f"- **總交易**: {port.total_trades}\n"
        )
        for sym, pos in port.positions.items():
            sections.append(
                f"  - {sym}: qty={pos.quantity:.6f} @ ${pos.entry_price:,.2f}\n"
            )
    else:
        sections.append("_未執行_\n")

    sections.append(DISCLAIMER)
    return "".join(sections)


def run_analysis(query: str, **overrides) -> str:
    """Run the full multi-agent analysis and return the final report."""
    validate_api_key()
    intent = _detect_intent(query)
    intent.update({k: v for k, v in overrides.items() if v is not None and v != ""})

    try:
        crew = build_crew(query, **overrides)
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        logger.exception("CrewAI kickoff failed; using tool fallback: %s", e)
        info = resolve_coin(intent["coin"])
        # Prefer short alias for tools
        coin_key = intent["coin"]
        return _fallback_tool_pipeline(
            coin=coin_key,
            days=int(intent.get("days", 90)),
            risk_profile=str(intent.get("risk_profile", "conservative")),
            include_backtest=bool(intent.get("backtest")),
            include_paper=bool(intent.get("paper")),
        )


def run_portfolio_analysis(
    coins: list[str] | None = None,
    risk_profile: str = "conservative",
    delay_sec: float = 2.0,
) -> str:
    """Analyze multiple coins with tool pipeline and synthesize allocation notes."""
    coin_list = coins or list(PORTFOLIO_COINS)
    coin_list = [c.strip().lower() for c in coin_list if c and c.strip()]
    if not coin_list:
        coin_list = list(PORTFOLIO_COINS)

    per_coin: dict[str, dict[str, Any]] = {}
    for i, coin in enumerate(coin_list):
        if i > 0 and delay_sec > 0:
            time.sleep(delay_sec)
        info = resolve_coin(coin)
        snap = market.get_crypto_price(coin)
        candles = market.get_historical_data(coin, days=90)
        tech = technical.calculate_technical_indicators(candles or [])
        sent = sentiment.get_sentiment(coin)
        risk_adv = risk_tools.compute_risk_metrics(
            candles or [],
            current_price=snap.price_usd if not snap.error else None,
            risk_profile=risk_profile,
        )
        per_coin[coin] = {
            "name": info["name"],
            "market": snap,
            "technical": tech,
            "sentiment": sent,
            "risk": risk_adv,
        }

    # Simple allocation: inverse volatility weighting with caps
    weights: dict[str, float] = {}
    inv_vols: dict[str, float] = {}
    for coin, data in per_coin.items():
        vol = data["risk"].volatility_pct or 50.0
        if data["risk"].error:
            vol = 50.0
        inv_vols[coin] = 1.0 / max(float(vol), 1.0)
    total_inv = sum(inv_vols.values()) or 1.0
    for coin, inv in inv_vols.items():
        weights[coin] = round(100.0 * inv / total_inv, 1)

    # Normalize rounding drift
    drift = round(100.0 - sum(weights.values()), 1)
    if weights and abs(drift) >= 0.1:
        first = next(iter(weights))
        weights[first] = round(weights[first] + drift, 1)

    return render_portfolio_report(per_coin, weights, risk_profile=risk_profile)
