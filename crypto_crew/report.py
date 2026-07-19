"""Report rendering — structured Markdown output with disclaimer."""

import re
from typing import Any

from crypto_crew.config import DISCLAIMER
from crypto_crew.models import MarketSnapshot, TechSummary, SentimentSnapshot, RiskAdvice

_SECTION_HEADERS = [
    ("1", "市場現價", "📊"),
    ("2", "新聞摘要", "📰"),
    ("3", "技術分析", "🔬"),
    ("4", "鏈上與基本面", "⛓️"),
    ("5", "市場情緒", "💬"),
    ("6", "價格預測", "🔮"),
    ("7", "回測報告", "📈"),
    ("8", "風險評估", "⚠️"),
    ("9", "Paper Trading", "💼"),
]

_DISCLAIMER_BLOCK = (
    "\n\n---\n\n"
    "> ⚠️ **免責聲明**：本分析僅供參考，不是財務建議。"
    "加密貨幣波動極大，投資有虧損風險，請自行研究（DYOR）。"
    "預測準確率無法保證。\n"
)


def _fmt_num(value: float | int | None, decimals: int = 2, prefix: str = "") -> str:
    if value is None:
        return "N/A"
    try:
        if decimals == 0:
            return f"{prefix}{float(value):,.0f}"
        return f"{prefix}{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def _ensure_sections(text: str) -> str:
    """Ensure standard section headers exist; append missing ones as skipped."""
    missing = []
    for num, title, emoji in _SECTION_HEADERS:
        # Match either Chinese title fragment or section number heading
        pattern = rf"##\s*{num}\.|{re.escape(title)}|Paper Trading"
        if title == "Paper Trading":
            if not re.search(r"Paper Trading|模擬交易|虚拟交易", text, re.I):
                missing.append(f"## {num}. {emoji} {title}\n\n_（本節未產出）_\n")
        elif not re.search(pattern, text):
            missing.append(f"## {num}. {emoji} {title}\n\n_（本節未產出）_\n")
    if missing:
        text = text.rstrip() + "\n\n" + "\n".join(missing)
    return text


def _strip_old_disclaimer(text: str) -> str:
    """Remove prior disclaimer variants so we append a clean block once."""
    patterns = [
        r"\n---\n+>? ?⚠️?\s*\*?\*?免責聲明\*?\*?.*",
        r"\n+本分析僅供參考.*",
    ]
    cleaned = text
    for pat in patterns:
        cleaned = re.sub(pat, "", cleaned, flags=re.S)
    return cleaned.rstrip()


def render_report(report_text: str) -> str:
    """Post-process the raw crew output into final report.

    Ensures:
    1. Core sections are present (or marked as skipped).
    2. Disclaimer is at the very end as a blockquote.
    3. Empty input yields a minimal failure message.
    """
    if not report_text or not str(report_text).strip():
        return "無法生成報告。" + _DISCLAIMER_BLOCK

    text = str(report_text).strip()
    text = _strip_old_disclaimer(text)
    text = _ensure_sections(text)
    text = text.rstrip() + _DISCLAIMER_BLOCK
    return text


def render_portfolio_report(
    per_coin: dict[str, dict[str, Any]],
    weights: dict[str, float],
    risk_profile: str = "conservative",
) -> str:
    """Build a multi-coin portfolio Markdown report."""
    lines: list[str] = [
        "# 📦 多幣種組合分析\n",
        f"**風險偏好**: {risk_profile}\n",
        "\n## 配置建議（波動率反向加權）\n\n",
        "| 幣種 | 建議權重 | 現價 | 24h% | 趨勢 | F&G | 建議倉位% |\n",
        "|------|----------|------|------|------|-----|----------|\n",
    ]

    for coin, data in per_coin.items():
        market: MarketSnapshot = data["market"]
        tech: TechSummary = data["technical"]
        sent: SentimentSnapshot = data["sentiment"]
        risk: RiskAdvice = data["risk"]
        name = data.get("name", coin.upper())
        w = weights.get(coin, 0.0)
        price = _fmt_num(market.price_usd, 2, "$") if not market.error else "N/A"
        chg = (
            f"{market.change_24h_pct:+.2f}%"
            if market.change_24h_pct is not None and not market.error
            else "N/A"
        )
        trend = tech.trend if not tech.error else "N/A"
        fng = (
            f"{sent.fear_greed_index}"
            if sent.fear_greed_index is not None
            else "N/A"
        )
        pos = (
            f"{risk.suggested_position_size_pct}"
            if not risk.error
            else "N/A"
        )
        lines.append(
            f"| {name} ({coin.upper()}) | {w}% | {price} | {chg} | {trend} | {fng} | {pos} |\n"
        )

    lines.append("\n## 分幣種摘要\n")
    for coin, data in per_coin.items():
        market = data["market"]
        tech = data["technical"]
        risk = data["risk"]
        name = data.get("name", coin.upper())
        lines.append(f"\n### {name}\n")
        if market.error:
            lines.append(f"- 市場數據: {market.error}\n")
        else:
            lines.append(
                f"- 現價 {_fmt_num(market.price_usd, 2, '$')}，"
                f"來源 {market.source}\n"
            )
        if tech.error:
            lines.append(f"- 技術: {tech.error}\n")
        else:
            lines.append(
                f"- 趨勢 **{tech.trend}**；"
                f"支撐 {_fmt_num(tech.support, 2, '$')} / "
                f"阻力 {_fmt_num(tech.resistance, 2, '$')}\n"
            )
        if risk.error:
            lines.append(f"- 風險: {risk.error}\n")
        else:
            lines.append(
                f"- 年化波動 {_fmt_num(risk.volatility_pct, 1)}%，"
                f"止損 {risk.stop_loss_pct}% / 止盈 {risk.take_profit_pct}%\n"
            )

    lines.append(
        "\n## 配置說明\n\n"
        "權重按各幣年化波動率的倒數比例分配，波動越高權重越低；"
        "此為研究用示意，非投資建議。\n"
    )
    lines.append(_DISCLAIMER_BLOCK)
    return "".join(lines)
