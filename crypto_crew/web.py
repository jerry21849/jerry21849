"""Gradio Web UI for crypto-crew."""

from __future__ import annotations

import logging
import os

from crypto_crew.config import GRADIO_PORT, PORTFOLIO_COINS, SYMBOL_MAP, validate_api_key
from crypto_crew.crew import run_analysis, run_portfolio_analysis
from crypto_crew.report import render_report

logger = logging.getLogger(__name__)


def _build_query(
    query: str,
    coin: str,
    do_backtest: bool,
    do_paper: bool,
    risk: str,
) -> str:
    parts = [query.strip()] if query and query.strip() else []
    if coin:
        parts.append(f"分析 {coin.upper()}")
    if do_backtest:
        parts.append("回測 RSI 策略")
    if do_paper:
        parts.append("開始 Paper Trading")
    if risk == "aggressive":
        parts.append("激進風險")
    elif risk == "conservative":
        parts.append("保守風險")
    return "，".join(parts) if parts else f"分析 {coin or 'BTC'}"


def analyze_ui(
    query: str,
    coin: str,
    do_backtest: bool,
    do_paper: bool,
    risk: str,
) -> str:
    """Gradio callback: run single-coin analysis."""
    try:
        validate_api_key()
    except ValueError as e:
        return f"❌ {e}"

    full_query = _build_query(query, coin, do_backtest, do_paper, risk)
    overrides = {
        "coin": (coin or "btc").lower(),
        "backtest": bool(do_backtest),
        "paper": bool(do_paper),
        "risk_profile": risk or "conservative",
    }
    try:
        raw = run_analysis(full_query, **overrides)
        return render_report(raw)
    except Exception as e:
        logger.exception("Web analysis failed")
        return f"❌ 分析失敗: {e}"


def portfolio_ui(coins_csv: str, risk: str) -> str:
    """Gradio callback: multi-coin portfolio analysis."""
    coins = [c.strip().lower() for c in (coins_csv or "").split(",") if c.strip()]
    if not coins:
        coins = list(PORTFOLIO_COINS)
    try:
        return run_portfolio_analysis(coins=coins, risk_profile=risk or "conservative")
    except Exception as e:
        logger.exception("Portfolio web analysis failed")
        return f"❌ 組合分析失敗: {e}"


def build_app():
    """Construct the Gradio Blocks app."""
    import gradio as gr

    coin_choices = sorted(SYMBOL_MAP.keys())

    with gr.Blocks(title="加密貨幣多代理智能助手") as app:
        gr.Markdown(
            "# 🚀 加密貨幣多代理智能助手\n"
            "研究 + 預測 + 回測 + Paper Trading（僅供參考，非財務建議）"
        )
        with gr.Tab("單幣分析"):
            query = gr.Textbox(
                label="查詢",
                placeholder="例如：分析 BTC，給我未來 7 天預測",
                lines=2,
            )
            with gr.Row():
                coin = gr.Dropdown(choices=coin_choices, value="btc", label="幣種")
                risk = gr.Radio(
                    choices=["conservative", "aggressive"],
                    value="conservative",
                    label="風險偏好",
                )
            with gr.Row():
                do_backtest = gr.Checkbox(label="回測", value=False)
                do_paper = gr.Checkbox(label="Paper Trading", value=False)
            btn = gr.Button("開始分析", variant="primary")
            out = gr.Markdown(label="報告")
            btn.click(
                analyze_ui,
                inputs=[query, coin, do_backtest, do_paper, risk],
                outputs=out,
            )

        with gr.Tab("組合分析"):
            coins_in = gr.Textbox(
                label="幣種列表（逗號分隔）",
                value=",".join(PORTFOLIO_COINS),
            )
            risk2 = gr.Radio(
                choices=["conservative", "aggressive"],
                value="conservative",
                label="風險偏好",
            )
            btn2 = gr.Button("組合分析", variant="primary")
            out2 = gr.Markdown(label="組合報告")
            btn2.click(portfolio_ui, inputs=[coins_in, risk2], outputs=out2)

        gr.Markdown(
            "> ⚠️ 本分析僅供參考，不是財務建議。加密貨幣波動極大，請自行研究（DYOR）。"
        )

    return app


def launch(port: int | None = None, share: bool = False) -> None:
    """Launch Gradio server."""
    port = port or GRADIO_PORT
    # Headless / CI: do not force browser open
    inbrowser = os.environ.get("DISPLAY") is not None or os.name == "nt"
    if os.environ.get("CRYPTO_CREW_HEADLESS", "").lower() in ("1", "true", "yes"):
        inbrowser = False

    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=port, share=share, inbrowser=inbrowser)
