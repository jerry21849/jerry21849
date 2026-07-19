"""CLI entry point — parse args, run the crew, print report."""

import argparse
import sys
import logging

from rich.console import Console
from rich.markdown import Markdown

from crypto_crew.config import GRADIO_PORT, PORTFOLIO_COINS

console = Console()
logger = logging.getLogger(__name__)


def _run_analyze(args: argparse.Namespace) -> int:
    from crypto_crew.crew import run_analysis
    from crypto_crew.report import render_report

    query = " ".join(args.query) if args.query else ""
    if not query:
        try:
            query = console.input("[bold cyan]🔍 請輸入分析查詢: [/]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n⚠️  已取消")
            return 1

    if not query.strip():
        console.print("[red]❌ 查詢不能為空[/]")
        return 1

    overrides = {}
    if args.coin:
        overrides["coin"] = args.coin
    if args.days and args.days > 0:
        overrides["days"] = args.days
    if args.risk:
        overrides["risk_profile"] = args.risk
    if args.cash and args.cash > 0:
        overrides["initial_cash"] = args.cash
    if getattr(args, "backtest", False):
        overrides["backtest"] = True
    if getattr(args, "paper", False):
        overrides["paper"] = True

    console.print(f"\n[bold green]🚀 啟動多代理分析:[/] {query}\n")

    try:
        result = run_analysis(query, **overrides)
        report = render_report(result)

        if args.json:
            import json

            console.print_json(json.dumps({"query": query, "report": report}))
        else:
            console.print(Markdown(report))

        console.print("\n[dim]💡 提示: 重新執行 `python -m crypto_crew` 繼續分析[/]")
        return 0
    except ValueError as e:
        console.print(f"[red]❌ {e}[/]")
        return 1
    except Exception as e:
        console.print(f"[red]❌ 分析失敗: {e}[/]")
        logger.exception("Analysis failed")
        return 1


def _run_portfolio(args: argparse.Namespace) -> int:
    from crypto_crew.crew import run_portfolio_analysis

    coins = [c.strip() for c in (args.coins or "").split(",") if c.strip()]
    if not coins:
        coins = list(PORTFOLIO_COINS)

    risk = args.risk or "conservative"
    console.print(f"\n[bold green]📦 組合分析:[/] {', '.join(coins)}（{risk}）\n")
    try:
        report = run_portfolio_analysis(coins=coins, risk_profile=risk)
        if args.json:
            import json

            console.print_json(json.dumps({"coins": coins, "report": report}))
        else:
            console.print(Markdown(report))
        return 0
    except Exception as e:
        console.print(f"[red]❌ 組合分析失敗: {e}[/]")
        logger.exception("Portfolio analysis failed")
        return 1


def _run_web(args: argparse.Namespace) -> int:
    from crypto_crew.web import launch

    port = args.port or GRADIO_PORT
    console.print(f"[bold green]🌐 啟動 Web UI[/] http://127.0.0.1:{port}")
    try:
        launch(port=port, share=bool(args.share))
        return 0
    except Exception as e:
        console.print(f"[red]❌ Web UI 啟動失敗: {e}[/]")
        logger.exception("Web launch failed")
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="加密貨幣多代理智能助手 — 研究+預測+回測+Paper Trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "範例:\n"
            "  python -m crypto_crew \"分析 BTC\"\n"
            "  python -m crypto_crew \"分析 ETH，給我未來 7 天預測，回測 RSI 策略\"\n"
            "  python -m crypto_crew portfolio --coins btc,eth,sol\n"
            "  python -m crypto_crew web --port 7860\n"
        ),
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細日誌")

    sub = parser.add_subparsers(dest="command")

    # Default / analyze: also accept bare query args without subcommand
    analyze_p = sub.add_parser("analyze", help="單幣多代理分析")
    analyze_p.add_argument("query", nargs="*", help="分析查詢")
    analyze_p.add_argument("--coin", "-c", default="", help="指定幣種")
    analyze_p.add_argument("--days", "-d", type=int, default=0, help="歷史數據天數")
    analyze_p.add_argument(
        "--risk",
        choices=["conservative", "aggressive"],
        default="",
        help="風險偏好",
    )
    analyze_p.add_argument("--cash", type=float, default=0, help="Paper Trading 初始資金")
    analyze_p.add_argument("--backtest", action="store_true", help="強制執行回測")
    analyze_p.add_argument("--paper", action="store_true", help="強制 Paper Trading")
    analyze_p.add_argument("--json", action="store_true", help="輸出原始 JSON")
    analyze_p.set_defaults(func=_run_analyze)

    port_p = sub.add_parser("portfolio", help="多幣種組合分析")
    port_p.add_argument(
        "--coins",
        default=",".join(PORTFOLIO_COINS),
        help="逗號分隔幣種，如 btc,eth,sol",
    )
    port_p.add_argument(
        "--risk",
        choices=["conservative", "aggressive"],
        default="conservative",
        help="風險偏好",
    )
    port_p.add_argument("--json", action="store_true", help="輸出 JSON")
    port_p.set_defaults(func=_run_portfolio)

    web_p = sub.add_parser("web", help="啟動 Gradio Web UI")
    web_p.add_argument("--port", type=int, default=GRADIO_PORT, help="埠號")
    web_p.add_argument("--share", action="store_true", help="建立公網分享連結")
    web_p.set_defaults(func=_run_web)

    # Pre-parse to support legacy: python -m crypto_crew "分析 BTC"
    raw = list(argv) if argv is not None else sys.argv[1:]
    known_cmds = {"analyze", "portfolio", "web", "-h", "--help"}
    if raw and raw[0] not in known_cmds and not raw[0].startswith("-"):
        # Treat as analyze query
        raw = ["analyze", *raw]
    elif not raw:
        raw = ["analyze"]
    elif raw[0] in ("-v", "--verbose") and (
        len(raw) == 1 or raw[1] not in ("analyze", "portfolio", "web")
    ):
        # verbose + optional query
        rest = raw[1:]
        raw = ["analyze", *rest]
        # re-inject verbose via namespace later
        if "-v" not in rest and "--verbose" not in rest:
            pass

    # Handle global verbose before subcommand
    verbose = False
    if "-v" in raw:
        verbose = True
        raw = [x for x in raw if x != "-v"]
    if "--verbose" in raw:
        verbose = True
        raw = [x for x in raw if x != "--verbose"]

    if verbose:
        logging.basicConfig(level=logging.INFO)

    if not raw:
        raw = ["analyze"]

    # If still looks like flags-only analyze
    if raw[0].startswith("-") and raw[0] not in known_cmds:
        raw = ["analyze", *raw]

    args = parser.parse_args(raw)
    if not hasattr(args, "func"):
        # Fallback: analyze with remaining
        return _run_analyze(
            argparse.Namespace(
                query=getattr(args, "query", []) or [],
                coin=getattr(args, "coin", ""),
                days=getattr(args, "days", 0),
                risk=getattr(args, "risk", ""),
                cash=getattr(args, "cash", 0),
                backtest=False,
                paper=False,
                json=False,
            )
        )
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
