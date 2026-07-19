"""Task definitions — dynamically built based on user query."""

from crewai import Task

from crypto_crew.agents import (
    get_supervisor,
    get_market_agent,
    get_news_agent,
    get_technical_agent,
    get_fundamental_agent,
    get_sentiment_agent,
    get_prediction_agent,
    get_backtest_agent,
    get_risk_agent,
    get_paper_agent,
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

    Tasks use explicit ``context`` lists so later agents receive prior outputs
    (CrewAI 1.x API — replaces deprecated context_from_previous_tasks).
    """
    market_task = Task(
        description=(
            f"Get current market data for {coin}: price, 24h change, volume, market cap. "
            f"Use the get_crypto_price tool with coin='{coin}'."
        ),
        agent=get_market_agent(),
        expected_output="JSON with current price and 24h stats.",
    )

    news_task = Task(
        description=(
            f"Get the latest news for {coin}. Use get_news(coin='{coin}', limit=5). "
            "Summarize key headlines with impact ratings."
        ),
        agent=get_news_agent(),
        expected_output="List of news items with titles and impact ratings.",
    )

    sentiment_task = Task(
        description=(
            f"Get sentiment data for {coin}: Fear & Greed Index, social sentiment score. "
            f"Use get_sentiment(coin='{coin}')."
        ),
        agent=get_sentiment_agent(),
        expected_output="Sentiment snapshot with F&G index and social score.",
    )

    technical_task = Task(
        description=(
            f"First, get historical data for {coin} ({days} days) using get_historical_data. "
            "Then calculate RSI, MACD, Bollinger Bands, SMA 20/50/200, ATR using "
            "calculate_technical_indicators. Report trend direction and key S/R levels."
        ),
        agent=get_technical_agent(),
        expected_output="Technical indicators table with trend and support/resistance.",
    )

    fundamental_task = Task(
        description=(
            f"Get on-chain fundamentals for {coin}. "
            "If data is limited for this coin, note that and provide what's available."
        ),
        agent=get_fundamental_agent(),
        expected_output="On-chain snapshot with TVL and health score if available.",
    )

    data_tasks = [market_task, news_task, sentiment_task, technical_task, fundamental_task]

    prediction_task = Task(
        description=(
            f"Based on ALL previous data outputs, generate a prediction for {coin} "
            f"over ~{min(days, 7)} days. "
            "Include: short-term outlook, medium-term outlook, "
            "BOTH bullish and bearish cases, confidence score (1-10), key price levels. "
            "Cite specific data points that support each view."
        ),
        agent=get_prediction_agent(),
        expected_output="Structured prediction with dual-sided reasoning.",
        context=list(data_tasks),
    )

    tasks: list[Task] = list(data_tasks) + [prediction_task]
    optional_after: list[Task] = []

    if include_backtest:
        backtest_task = Task(
            description=(
                f"Get historical data for {coin} then run backtests. "
                "Try strategies: RSI (oversold <30, overbought >70), "
                "MA crossover (20/50), and optionally mean_reversion or macd_histogram. "
                "Report which performed better. "
                "Include: total return, Sharpe ratio, max drawdown, win rate."
            ),
            agent=get_backtest_agent(),
            expected_output="Backtest report with performance metrics.",
            context=[market_task, technical_task],
        )
        tasks.append(backtest_task)
        optional_after.append(backtest_task)

    if include_paper:
        paper_task = Task(
            description=(
                "Check current paper portfolio state with get_paper_portfolio. "
                "Based on the latest price and prediction, decide whether to buy, sell, or hold. "
                "If a trade is warranted, use execute_paper_trade with strategy_tag='default'. "
                "Report the updated portfolio."
            ),
            agent=get_paper_agent(),
            expected_output="Paper portfolio state with any executed trades.",
            context=[market_task, prediction_task],
        )
        tasks.append(paper_task)
        optional_after.append(paper_task)

    risk_task = Task(
        description=(
            "Compute risk metrics for this coin/trade. "
            "Provide: volatility, ATR, suggested position size, stop-loss, take-profit. "
            f"Use the risk profile: {risk_profile}"
        ),
        agent=get_risk_agent(),
        expected_output="Risk metrics with position sizing advice.",
        context=[market_task, technical_task],
    )
    tasks.append(risk_task)

    report_context = list(data_tasks) + [prediction_task, risk_task] + optional_after
    supervisor_task = Task(
        description=(
            f"User query: {query}\n\n"
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
        agent=get_supervisor(),
        expected_output="Complete Markdown report with all sections and disclaimer.",
        context=report_context,
        output_file="reports/latest_report.md",
        create_directory=True,
        markdown=True,
    )
    tasks.append(supervisor_task)

    return tasks
