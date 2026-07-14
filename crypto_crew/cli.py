"""CLI entry point — parse args, run the crew, print report."""

import argparse
import sys
import logging

from rich.console import Console
from rich.markdown import Markdown

from crypto_crew.crew import run_analysis
from crypto_crew.report import render_report

console = Console()
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="加密貨幣多代理智能助手 — 研究+預測+回測+Paper Trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "範例:\n"
            "  python -m crypto_crew \"分析 BTC\"\n"
            "  python -m crypto_crew \"分析 ETH，給我未來 7 天預測，回測 RSI 策略\"\n"
            "  python -m crypto_crew \"分析 SOL，開始 Paper Trading\" --cash 5000\n"
        ),
    )
    parser.add_argument("query", nargs="*", help="分析查詢（如 '分析 BTC，給我預測'）")
    parser.add_argument("--coin", "-c", default="", help="指定幣種（覆蓋查詢自動檢測）")
    parser.add_argument("--days", "-d", type=int, default=0, help="歷史數據天數")
    parser.add_argument("--risk", choices=["conservative", "aggressive"], default="",
                        help="風險偏好")
    parser.add_argument("--cash", type=float, default=0, help="Paper Trading 初始資金")
    parser.add_argument("--json", action="store_true", help="輸出原始 JSON（除錯用）")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細日誌")

    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    # Build query string
    query = " ".join(args.query) if args.query else ""
    if not query:
        # Interactive prompt
        try:
            query = console.input("[bold cyan]🔍 請輸入分析查詢: [/]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n⚠️  已取消")
            return 1

    if not query.strip():
        console.print("[red]❌ 查詢不能為空[/]")
        return 1

    # Build overrides
    overrides = {}
    if args.coin:
        overrides["coin"] = args.coin
    if args.days > 0:
        overrides["days"] = args.days
    if args.risk:
        overrides["risk_profile"] = args.risk
    if args.cash > 0:
        overrides["initial_cash"] = args.cash

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

    except Exception as e:
        console.print(f"[red]❌ 分析失敗: {e}[/]")
        logger.exception("Analysis failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
