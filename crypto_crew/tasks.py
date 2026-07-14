"""Task definitions — dynamically built based on user query."""

from crewai import Task

from crypto_crew.agents import (
    SUPERVISOR, MARKET_AGENT, NEWS_AGENT, TECHNICAL_AGENT,
    FUNDAMENTAL_AGENT, SENTIMENT_AGENT, PREDICTION_AGENT,
    BACKTEST_AGENT, RISK_AGENT, PAPER_AGENT,
)


def build_tasks(
    query: str,
    coin: str = "btc",
    days: int = 365,
    risk_profile: str = "conservative",
    include_backtest: bool = False,
    include_paper: bool = False,
) -> list[Task]:
    """Build the task list for this run.

    The task list is ordered: data gathering first, then analysis, then report.
    Supervisor compiles everything at the end.
    """
    tasks = []

    # ── Phase 1: Data gathering (parallel-ish via hierarchical delegation) ──
    tasks.append(Task(
        description=(
            f"Get current market data for {coin}: price, 24h change, volume, market cap. "
            f"Use the get_crypto_price tool with coin='{coin}'."
        ),
        agent=MARKET_AGENT,
        expected_output="JSON with current price and 24h stats.",
    ))

    tasks.append(Task(
        description=(
            f"Get the latest news for {coin}. Use get_news(coin='{coin}', limit=5). "
            "Summarize key headlines with impact ratings."
        ),
        agent=NEWS_AGENT,
        expected_output="List of news items with titles and impact ratings.",
    ))

    tasks.append(Task(
        description=(
            f"Get sentiment data for {coin}: Fear & Greed Index, social sentiment score. "
            f"Use get_sentiment(coin='{coin}')."
        ),
        agent=SENTIMENT_AGENT,
        expected_output="Sentiment snapshot with F&G index and social score.",
    ))

    tasks.append(Task(
        description=(
            f"First, get historical data for {coin} ({days} days) using get_historical_data. "
            "Then calculate RSI, MACD, Bollinger Bands, SMA 20/50/200, ATR using "
            "calculate_technical_indicators. Report trend direction and key S/R levels."
        ),
        agent=TECHNICAL_AGENT,
        expected_output="Technical indicators table with trend and support/resistance.",
    ))

    tasks.append(Task(
        description=(
            f"Get on-chain fundamentals for {coin}. "
            "If data is limited for this coin, note that and provide what's available."
        ),
        agent=FUNDAMENTAL_AGENT,
        expected_output="On-chain snapshot with TVL and health score if available.",
    ))

    # ── Phase 2: Prediction ─────────────────────────────────────────────
    tasks.append(Task(
        description=(
            f"Based on ALL previous data outputs, generate a prediction for {coin} "
            f"over ~{min(days, 7)} days. "
            "Include: short-term outlook, medium-term outlook, "
            "BOTH bullish and bearish cases, confidence score (1-10), key price levels. "
            "Cite specific data points that support each view."
        ),
        agent=PREDICTION_AGENT,
        expected_output="Structured prediction with dual-sided reasoning.",
    ))

    # ── Phase 3: Optional strategy modules ──────────────────────────────
    if include_backtest:
        tasks.append(Task(
            description=(
                f"Get historical data for {coin} then run a backtest. "
                "Try these strategies: RSI (oversold <30, overbought >70), "
                "MA crossover (20/50). Report which performed better. "
                "Include: total return, Sharpe ratio, max drawdown, win rate."
            ),
            agent=BACKTEST_AGENT,
            expected_output="Backtest report with performance metrics.",
        ))

    if include_paper:
        tasks.append(Task(
            description=(
                "Check current paper portfolio state with get_paper_portfolio. "
                "Based on the latest price and prediction, decide whether to buy, sell, or hold. "
                "If a trade is warranted, use execute_paper_trade. "
                "Report the updated portfolio."
            ),
            agent=PAPER_AGENT,
            expected_output="Paper portfolio state with any executed trades.",
        ))

    tasks.append(Task(
        description=(
            "Compute risk metrics for this coin/trade. "
            "Provide: volatility, ATR, suggested position size, stop-loss, take-profit. "
            "Use the risk profile: " + risk_profile
        ),
        agent=RISK_AGENT,
        expected_output="Risk metrics with position sizing advice.",
    ))

    # ── Phase 4: Supervisor compilation ─────────────────────────────────
    tasks.append(Task(
        description=(
            "Compile ALL previous task outputs into ONE comprehensive Markdown report. "
            "The report MUST have these sections in order:\n\n"
            "## 1. 📊 市場現價\n"
            "## 2. 📰 新聞摘要\n"
            "## 3. 🔬 技術分析\n"
            "## 4. ⛓️ 鏈上與基本面\n"
            "## 5. 💬 市場情緒\n"
            "## 6. 🔮 價格預測\n"
            "## 7. 📈 回測報告（如執行）\n"
            "## 8. ⚠️ 風險評估\n"
            "## 9. 💼 Paper Trading 狀態（如執行）\n\n"
            "For each section, cite the source and key numbers. "
            "The prediction MUST present both bullish and bearish views. "
            "At the VERY END, append the exact disclaimer text.\n\n"
            "IMPORTANT: All numbers MUST come from actual tool results — never invent data. "
            "Report in Chinese. Keep it scannable."
        ),
        agent=SUPERVISOR,
        expected_output="Complete Markdown report with all sections and disclaimer.",
        context_from_previous_tasks=True,
    ))

    return tasks
