"""Agent definitions — 10 CrewAI agents with role-specific tools (lazy init)."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from crewai.tools import tool

from crypto_crew.tools import market, news, sentiment, technical, onchain
from crypto_crew.tools import backtest as bt, paper_trade, risk

if TYPE_CHECKING:
    from crewai import Agent

# ── Tool wrappers (CrewAI @tool decorator) ────────────────────────

@tool("get_crypto_price")
def tool_get_crypto_price(coin: str = "btc") -> str:
    """Fetch current price and 24h stats for a cryptocurrency (e.g. 'btc', 'eth')."""
    return market.get_crypto_price(coin).model_dump_json()


@tool("get_historical_data")
def tool_get_historical_data(coin: str = "btc", days: int = 365) -> str:
    """Fetch historical OHLCV candlestick data. Returns JSON list."""
    import json
    data = market.get_historical_data(coin, days)
    return json.dumps(data or [])


@tool("get_news")
def tool_get_news(coin: str = "btc", limit: int = 10) -> str:
    """Fetch latest news headlines for a cryptocurrency."""
    return news.get_news(coin, limit).model_dump_json()


@tool("get_sentiment")
def tool_get_sentiment(coin: str = "btc") -> str:
    """Get Fear & Greed Index + social sentiment for a coin."""
    return sentiment.get_sentiment(coin).model_dump_json()


@tool("calculate_technical_indicators")
def tool_calc_technical(candles_json: str, indicators: str = "") -> str:
    """Calculate RSI, MACD, Bollinger Bands, SMA, EMA, ATR, Stoch from candle JSON. indicators is comma-separated or empty for all."""
    import json
    candles = json.loads(candles_json)
    ind_list = [s.strip() for s in indicators.split(",") if s.strip()] if indicators else None
    return technical.calculate_technical_indicators(candles, ind_list).model_dump_json()


@tool("get_onchain_data")
def tool_get_onchain(coin: str = "btc") -> str:
    """Fetch on-chain fundamentals: TVL, development activity, project health."""
    return onchain.get_onchain_snapshot(coin).model_dump_json()


@tool("run_backtest")
def tool_run_backtest(strategy: str = "rsi", candles_json: str = "", params_json: str = "{}") -> str:
    """Run a backtest. strategy: 'rsi', 'ma_cross', 'bollinger', 'mean_reversion', 'macd_histogram'. candles_json from get_historical_data."""
    import json
    candles = json.loads(candles_json) if candles_json else None
    params = json.loads(params_json) if params_json else {}
    return bt.run_backtest(strategy, candles, params).model_dump_json()


@tool("get_paper_portfolio")
def tool_get_portfolio(strategy_tag: str = "default") -> str:
    """Get current paper trading portfolio state (cash, positions, history). Optional strategy_tag isolates strategies."""
    return paper_trade.get_paper_portfolio(strategy_tag=strategy_tag).model_dump_json()


@tool("execute_paper_trade")
def tool_execute_trade(
    action: str,
    symbol: str,
    amount_usd: float,
    price: float,
    strategy_tag: str = "default",
) -> str:
    """Execute a paper trade. action: 'buy' or 'sell'. Updates portfolio state. strategy_tag isolates strategies."""
    return paper_trade.execute_paper_trade(
        action, symbol, amount_usd, price, strategy_tag=strategy_tag
    ).model_dump_json()


@tool("compute_risk_metrics")
def tool_compute_risk(
    candles_json: str,
    portfolio_value: float = 10000.0,
    risk_profile: str = "conservative",
) -> str:
    """Compute VaR, ATR, volatility, position sizing from candle data."""
    import json
    candles = json.loads(candles_json) if candles_json else []
    return risk.compute_risk_metrics(
        candles, portfolio_value=portfolio_value, risk_profile=risk_profile
    ).model_dump_json()


# ── Lazy agent factories (avoid LLM credential check at import time) ──

@lru_cache(maxsize=1)
def get_supervisor() -> Agent:
    from crewai import Agent

    return Agent(
        role="Supervisor — 總指揮",
        goal=(
            "解析用戶查詢，決定啟動哪些子代理、設定優先順序。"
            "彙整所有子代理的分析結果為一份完整的 Markdown 報告。"
            "確保報告包含免責聲明。所有數字必須來自工具調用，禁止虛構。"
            "在彙整時保留並引用前序任務輸出中的關鍵數據點，作為上下文記憶。"
        ),
        backstory=(
            "你是加密貨幣研究團隊的總指揮，擅長將複雜問題分解為可並行處理的子任務。"
            "你的中文報告清晰易懂，總是標註數據來源並附加風險提示。"
            "彙整報告時你會明確引用各子代理已產出的數字與結論，不重新臆造數據。"
            "若前序分析存在矛盾，你會並列呈現並標註不確定性。"
        ),
        verbose=True,
        allow_delegation=True,
    )


@lru_cache(maxsize=1)
def get_market_agent() -> Agent:
    from crewai import Agent

    return Agent(
        role="Market Data Agent — 市場數據工程師",
        goal="提供準確的現價、24h變化、成交量、市值、歷史OHLCV數據。支援多幣種。",
        backstory="你擅長從 CoinGecko 和 Binance 等地提取市場數據。",
        tools=[tool_get_crypto_price, tool_get_historical_data],
        verbose=True,
    )


@lru_cache(maxsize=1)
def get_news_agent() -> Agent:
    from crewai import Agent

    return Agent(
        role="News & Event Agent — 加密新聞記者",
        goal="抓取最新加密貨幣新聞，給出影響評級（高/中/低）。",
        backstory="你即時監控 CoinDesk、Cointelegraph 等來源的新聞流。",
        tools=[tool_get_news],
        verbose=True,
    )


@lru_cache(maxsize=1)
def get_technical_agent() -> Agent:
    from crewai import Agent

    return Agent(
        role="Technical Analysis Agent — 圖表分析師",
        goal="計算 RSI、MACD、布林帶、SMA/EMA、ATR、Stoch 等技術指標，判斷趨勢和支撐阻力位。",
        backstory="你是資深技術分析師，所有指標都用本地 python 精確計算，不使用付費 API。",
        tools=[tool_calc_technical, tool_get_historical_data],
        verbose=True,
    )


@lru_cache(maxsize=1)
def get_fundamental_agent() -> Agent:
    from crewai import Agent

    return Agent(
        role="Fundamental & On-Chain Agent — 基本面分析師",
        goal="評估項目健康度，涵蓋 TVL、開發活動、鏈上數據。使用免費 API。",
        backstory="你透過 DefiLlama 等免費來源獲取鏈上基本面。",
        tools=[tool_get_onchain],
        verbose=True,
    )


@lru_cache(maxsize=1)
def get_sentiment_agent() -> Agent:
    from crewai import Agent

    return Agent(
        role="Sentiment Agent — 市場情緒分析師",
        goal="提供情緒分數（-1~1）、Fear & Greed 指數、社群熱度（X/Reddit）。",
        backstory="你綜合 alternative.me 指標和社群討論來量化市場情緒。",
        tools=[tool_get_sentiment],
        verbose=True,
    )


@lru_cache(maxsize=1)
def get_prediction_agent() -> Agent:
    from crewai import Agent

    return Agent(
        role="Prediction Agent — 預測專家",
        goal=(
            "綜合市場、新聞、技術、基本面、情緒數據，給出短期和中期預測。"
            "必須同時給出 bullish 和 bearish 兩面觀點及信心分數。"
        ),
        backstory="你擅長在多維度數據中發現模式，但始終保持客觀，提供多空雙向視角。",
        tools=[
            tool_get_crypto_price,
            tool_get_historical_data,
            tool_get_news,
            tool_calc_technical,
            tool_get_onchain,
            tool_get_sentiment,
        ],
        verbose=True,
    )


@lru_cache(maxsize=1)
def get_backtest_agent() -> Agent:
    from crewai import Agent

    return Agent(
        role="Backtesting Agent — 量化回測工程師",
        goal=(
            "使用 RSI、MA 交叉、布林帶、均值回歸、MACD 柱狀圖策略執行回測，"
            "輸出總報酬、Sharpe、Max Drawdown、勝率、權益曲線。"
        ),
        backstory="你專注於用本地 pandas 代碼回測交易策略，結果精確可複現。",
        tools=[tool_run_backtest, tool_get_historical_data],
        verbose=True,
    )


@lru_cache(maxsize=1)
def get_risk_agent() -> Agent:
    from crewai import Agent

    return Agent(
        role="Risk Management Agent — 風險控制官",
        goal="計算波動率、ATR、VaR，給出建議倉位大小、止損止盈、最大風險暴露。",
        backstory="你負責計算 VaR、ATR 等風險指標，確保交易風險可控。",
        tools=[tool_compute_risk, tool_get_historical_data],
        verbose=True,
    )


@lru_cache(maxsize=1)
def get_paper_agent() -> Agent:
    from crewai import Agent

    return Agent(
        role="Paper Trading Agent — 模擬交易員",
        goal="維護虛擬倉位，記錄交易日誌，給出買賣建議。0.1% 手續費，支援滑點模擬與多策略隔離。",
        backstory="你管理模擬交易帳戶，狀態持久化到本地，支援多策略同時模擬。",
        tools=[tool_get_portfolio, tool_execute_trade, tool_get_crypto_price],
        verbose=True,
    )


def all_agents() -> list:
    """Return all 10 agents (constructed lazily)."""
    return [
        get_supervisor(),
        get_market_agent(),
        get_news_agent(),
        get_technical_agent(),
        get_fundamental_agent(),
        get_sentiment_agent(),
        get_prediction_agent(),
        get_backtest_agent(),
        get_risk_agent(),
        get_paper_agent(),
    ]


# Backwards-compatible module-level names via __getattr__
_AGENT_GETTERS = {
    "SUPERVISOR": get_supervisor,
    "MARKET_AGENT": get_market_agent,
    "NEWS_AGENT": get_news_agent,
    "TECHNICAL_AGENT": get_technical_agent,
    "FUNDAMENTAL_AGENT": get_fundamental_agent,
    "SENTIMENT_AGENT": get_sentiment_agent,
    "PREDICTION_AGENT": get_prediction_agent,
    "BACKTEST_AGENT": get_backtest_agent,
    "RISK_AGENT": get_risk_agent,
    "PAPER_AGENT": get_paper_agent,
}


def __getattr__(name: str):
    if name in _AGENT_GETTERS:
        return _AGENT_GETTERS[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
