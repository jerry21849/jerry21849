"""Tests for market data tools — mock external APIs."""

import json
import requests
import pytest
from unittest.mock import patch, MagicMock
from crypto_crew.tools.market import get_crypto_price, get_historical_data
from crypto_crew.models import MarketSnapshot


class TestGetCryptoPrice:
    @patch("crypto_crew.tools.market.requests.get")
    def test_coingecko_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "bitcoin": {
                "usd": 42345.67,
                "usd_24h_vol": 28000000000,
                "usd_24h_change": 2.34,
                "usd_market_cap": 820000000000,
            }
        }
        result = get_crypto_price("btc")
        assert isinstance(result, MarketSnapshot)
        assert result.price_usd == 42345.67
        assert result.change_24h_pct == 2.34
        assert result.volume_24h_usd == 28000000000
        assert result.market_cap_usd == 820000000000
        assert result.source == "coingecko"
        assert result.error is None

    @patch("crypto_crew.tools.market.requests.get")
    def test_coingecko_429_then_success(self, mock_get):
        """Test rate-limit retry logic."""
        mock_get.side_effect = [
            MagicMock(status_code=429),
            MagicMock(status_code=200, json=lambda: {
                "bitcoin": {"usd": 43000.0, "usd_24h_vol": 1, "usd_24h_change": 1, "usd_market_cap": 1}
            }),
        ]
        result = get_crypto_price("btc")
        assert result.price_usd == 43000.0
        assert mock_get.call_count == 2

    @patch("crypto_crew.tools.market.requests.get")
    def test_all_apis_fail(self, mock_get):
        """Both CoinGecko and Binance fail."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        result = get_crypto_price("btc")
        assert result.error is not None
        assert "unavailable" in result.error.lower()


class TestGetHistoricalData:
    @patch("crypto_crew.tools.market.requests.get")
    def test_coingecko_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "prices": [[1700000000000, 42000], [1700086400000, 42500]],
            "total_volumes": [[1700000000000, 28000000000], [1700086400000, 29000000000]],
        }
        result = get_historical_data("btc", days=2)
        assert result is not None
        assert len(result) == 2
        assert result[0]["timestamp"] == 1700000000000
        assert result[0]["close"] == 42000

    @patch("crypto_crew.tools.market.requests.get")
    def test_no_data(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}
        result = get_historical_data("btc")
        # Falls through to Binance, which also fails
        assert result is None or len(result) == 0
