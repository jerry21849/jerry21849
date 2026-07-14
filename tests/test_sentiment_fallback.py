"""Tests for sentiment tools — mock external APIs, test fallback paths."""

import pytest
from unittest.mock import patch, MagicMock
from crypto_crew.tools.sentiment import get_fear_greed, get_sentiment, _llm_sentiment_score


class TestFearGreed:
    @patch("crypto_crew.tools.sentiment.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "data": [{"value": "45", "value_classification": "Fear"}]
        }
        value, label, source = get_fear_greed()
        assert value == 45
        assert label == "Fear"
        assert source == "alternative.me"

    @patch("crypto_crew.tools.sentiment.requests.get")
    def test_api_failure(self, mock_get):
        import requests; mock_get.side_effect = requests.ConnectionError("Timeout")
        value, label, source = get_fear_greed()
        assert value is None
        assert label == "Unknown"


class TestLLMSentiment:
    def test_bullish_keywords(self):
        texts = ["BTC to the moon! Bullish!", "Buy the dip, mega pump incoming"]
        score = _llm_sentiment_score(texts)
        assert score > 0

    def test_bearish_keywords(self):
        texts = ["Market crash, sell everything", "Bearish trend, short now"]
        score = _llm_sentiment_score(texts)
        assert score < 0

    def test_mixed_sentiment(self):
        texts = ["Bullish on BTC, bearish on ETH"]
        score = _llm_sentiment_score(texts)
        # Should be near-neutral
        assert -0.5 < score < 0.5

    def test_chinese_bullish(self):
        texts = ["比特币突破新高，看涨买入！利好不断"]
        score = _llm_sentiment_score(texts)
        assert score > 0

    def test_chinese_bearish(self):
        texts = ["利空出尽？市场看跌，做空信号"]
        score = _llm_sentiment_score(texts)
        assert score < 0

    def test_empty_texts(self):
        assert _llm_sentiment_score([]) == 0.0

    def test_no_keywords(self):
        assert _llm_sentiment_score(["The weather is nice today"]) == 0.0


class TestGetSentiment:
    @patch("crypto_crew.tools.sentiment.get_fear_greed")
    def test_basic_snapshot(self, mock_fng):
        mock_fng.return_value = (50, "Neutral", "alternative.me")
        result = get_sentiment("btc")
        assert result.fear_greed_index == 50
        assert result.fear_greed_label == "Neutral"
