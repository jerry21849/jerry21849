"""Pydantic models for structured data exchange between agents."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class MarketSnapshot(BaseModel):
    coin: str = "bitcoin"
    price_usd: float = 0.0
    change_24h_pct: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    market_cap_usd: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    source: str = "coingecko"
    error: Optional[str] = None


class NewsItem(BaseModel):
    title: str
    source: str
    url: Optional[str] = None
    summary: Optional[str] = None
    impact: str = "medium"  # high / medium / low
    timestamp: Optional[str] = None


class NewsResult(BaseModel):
    items: list[NewsItem] = []
    source: str = "onchainos"
    error: Optional[str] = None


class TechIndicatorRow(BaseModel):
    name: str
    value: str
    signal: Optional[str] = None  # buy / sell / neutral


class TechSummary(BaseModel):
    indicators: list[TechIndicatorRow] = []
    trend: str = "neutral"      # bullish / bearish / neutral
    support: Optional[float] = None
    resistance: Optional[float] = None
    error: Optional[str] = None


class OnChainSnapshot(BaseModel):
    tvl_usd: Optional[float] = None
    tvl_change_24h: Optional[float] = None
    fee_revenue: Optional[float] = None
    score: Optional[int] = None      # 1-10 project health score (LLM-informed)
    notes: str = ""
    error: Optional[str] = None


class SentimentSnapshot(BaseModel):
    fear_greed_index: Optional[int] = None
    fear_greed_label: str = "Neutral"
    social_score: Optional[float] = None   # -1 to 1
    reddit_pulse: Optional[str] = None
    source: str = "alternative.me"
    error: Optional[str] = None


class PredictionResult(BaseModel):
    coin: str = "bitcoin"
    prediction_days: int = 7
    short_term_outlook: str = ""
    medium_term_outlook: str = ""
    bullish_case: str = ""
    bearish_case: str = ""
    confidence_score: int = 5  # 1-10
    key_levels: str = ""
    error: Optional[str] = None


class BacktestReport(BaseModel):
    strategy: str = ""
    total_return_pct: float = 0.0
    annualized_return_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown_pct: float = 0.0
    win_rate_pct: Optional[float] = None
    total_trades: int = 0
    equity_curve_description: str = ""
    error: Optional[str] = None


class RiskAdvice(BaseModel):
    volatility_pct: Optional[float] = None
    atr: Optional[float] = None
    suggested_position_size_pct: float = 5.0
    stop_loss_pct: float = 5.0
    take_profit_pct: float = 10.0
    var_95_pct: Optional[float] = None
    notes: str = ""
    error: Optional[str] = None


class PaperPosition(BaseModel):
    symbol: str
    quantity: float
    entry_price: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None


class PaperPortfolio(BaseModel):
    initial_cash: float = 10000.0
    cash: float = 10000.0
    positions: dict[str, PaperPosition] = {}
    trade_history: list[dict] = []
    total_trades: int = 0
    error: Optional[str] = None


class FinalReport(BaseModel):
    market: Optional[MarketSnapshot] = None
    news: Optional[NewsResult] = None
    technical: Optional[TechSummary] = None
    onchain: Optional[OnChainSnapshot] = None
    sentiment: Optional[SentimentSnapshot] = None
    prediction: Optional[PredictionResult] = None
    backtest: Optional[BacktestReport] = None
    risk: Optional[RiskAdvice] = None
    paper: Optional[PaperPortfolio] = None
