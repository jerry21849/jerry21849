"""Tests for report rendering."""

from crypto_crew.report import render_report, render_portfolio_report
from crypto_crew.models import (
    MarketSnapshot,
    TechSummary,
    SentimentSnapshot,
    RiskAdvice,
)


class TestRenderReport:
    def test_empty(self):
        out = render_report("")
        assert "無法生成報告" in out
        assert "免責聲明" in out

    def test_appends_disclaimer(self):
        out = render_report("## 1. 市場現價\n價格 100")
        assert "免責聲明" in out
        assert out.count("免責聲明") == 1

    def test_dedupes_existing_disclaimer(self):
        text = "## 1. 市場現價\n\n---\n⚠️ **免責聲明**：舊的"
        out = render_report(text)
        assert "免責聲明" in out
        # Should not keep the stripped old fragment as separate plus new infinitely
        assert out.strip().endswith("預測準確率無法保證。") or "DYOR" in out

    def test_fills_missing_sections(self):
        out = render_report("只有一段前言")
        assert "市場現價" in out or "未產出" in out


class TestRenderPortfolioReport:
    def test_basic_table(self):
        per_coin = {
            "btc": {
                "name": "Bitcoin",
                "market": MarketSnapshot(coin="bitcoin", price_usd=50000, change_24h_pct=1.2),
                "technical": TechSummary(trend="bullish", support=48000, resistance=52000),
                "sentiment": SentimentSnapshot(fear_greed_index=55, fear_greed_label="Neutral"),
                "risk": RiskAdvice(
                    volatility_pct=40.0,
                    suggested_position_size_pct=5.0,
                    stop_loss_pct=4.0,
                    take_profit_pct=10.0,
                ),
            }
        }
        out = render_portfolio_report(per_coin, {"btc": 100.0})
        assert "Bitcoin" in out
        assert "100" in out and "%" in out
        assert "免責聲明" in out
