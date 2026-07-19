"""Integration tests for crew orchestration — no live LLM calls."""

import pytest
from unittest.mock import patch, MagicMock

from crypto_crew.crew import _detect_intent, build_crew, run_analysis
from crypto_crew.config import validate_api_key


class TestDetectIntent:
    def test_btc_default(self):
        r = _detect_intent("給我市場概況")
        assert r["coin"] == "btc"

    def test_eth_detection(self):
        r = _detect_intent("分析 ETH 走勢")
        assert r["coin"] == "eth"

    def test_backtest_flag(self):
        r = _detect_intent("分析 BTC，回測 RSI 策略")
        assert r["backtest"] is True

    def test_paper_flag(self):
        r = _detect_intent("開始 Paper Trading")
        assert r["paper"] is True

    def test_aggressive_risk(self):
        r = _detect_intent("分析 SOL 激進")
        assert r["risk_profile"] == "aggressive"
        assert r["coin"] == "sol"

    def test_days_parse(self):
        r = _detect_intent("分析 BTC 未來 14 天")
        assert r["days"] == 14


class TestValidateApiKey:
    def test_missing_raises(self, monkeypatch):
        monkeypatch.setattr("crypto_crew.config.LLM_API_KEY", "")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            validate_api_key()

    def test_placeholder_raises(self, monkeypatch):
        monkeypatch.setattr("crypto_crew.config.LLM_API_KEY", "sk-your-key-here")
        with pytest.raises(ValueError):
            validate_api_key()

    def test_valid_passes(self, monkeypatch):
        monkeypatch.setattr("crypto_crew.config.LLM_API_KEY", "sk-real-test-key-abc")
        validate_api_key()  # no raise


class TestBuildCrew:
    def test_build_crew_constructs(self, monkeypatch):
        # CrewAI Agent init requires some credential present
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy-key-for-agent-init")
        crew = build_crew("分析 BTC，回測 RSI")
        assert crew is not None
        assert len(crew.tasks) >= 7  # data + prediction + risk + supervisor + backtest
        assert len(crew.agents) == 10


class TestRunAnalysis:
    def test_missing_key(self, monkeypatch):
        monkeypatch.setattr("crypto_crew.config.LLM_API_KEY", "")
        monkeypatch.setattr("crypto_crew.crew.validate_api_key", validate_api_key)
        monkeypatch.setattr("crypto_crew.config.LLM_API_KEY", "")
        # Patch the import used inside run_analysis
        with patch("crypto_crew.crew.validate_api_key", side_effect=ValueError("OPENAI_API_KEY 未設定")):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                run_analysis("分析 BTC")

    def test_fallback_on_kickoff_failure(self, monkeypatch):
        monkeypatch.setattr("crypto_crew.crew.validate_api_key", lambda: None)

        mock_crew = MagicMock()
        mock_crew.kickoff.side_effect = RuntimeError("LLM down")

        with patch("crypto_crew.crew.build_crew", return_value=mock_crew):
            with patch("crypto_crew.crew._fallback_tool_pipeline", return_value="## fallback report") as fb:
                out = run_analysis("分析 BTC")
                assert "fallback" in out
                fb.assert_called_once()
