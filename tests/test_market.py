"""
Regression tests for market-data-mcp.
Earnings calendar requires Finnhub key. SimFin tests require SimFin key.
"""

import pytest
from conftest import has_finnhub_key, has_simfin_key, skip_if_rate_limited

pytestmark = pytest.mark.integration

requires_finnhub = pytest.mark.skipif(
    not has_finnhub_key(), reason="FINNHUB_API_KEY not configured"
)
requires_simfin = pytest.mark.skipif(
    not has_simfin_key(), reason="SIMFIN_API_KEY not configured"
)


@requires_finnhub
def test_get_earnings_calendar_default(market_data):
    result = market_data.get_earnings_calendar()
    skip_if_rate_limited(result)
    assert "Earnings Calendar" in result
    assert "Ticker" in result or "Symbol" in result or "Date" in result


@requires_finnhub
def test_get_earnings_calendar_extended(market_data):
    result = market_data.get_earnings_calendar(days_ahead=14)
    skip_if_rate_limited(result)
    assert "Earnings Calendar" in result
    assert not result.startswith("Error:")


@requires_simfin
def test_get_simfin_financials_income(market_data):
    result = market_data.get_simfin_financials("AAPL", statement="income", period="ttm")
    skip_if_rate_limited(result)
    assert "AAPL" in result
    assert not result.startswith("Error:")
    # Should contain financial data
    assert any(kw in result for kw in ["Revenue", "Income", "Statement", "SimFin"])


@requires_simfin
def test_get_simfin_financials_balance(market_data):
    result = market_data.get_simfin_financials("MSFT", statement="balance", period="ttm")
    skip_if_rate_limited(result)
    assert "MSFT" in result
    assert not result.startswith("Error:")


def test_get_simfin_financials_no_key_returns_helpful_message(market_data):
    """When no SimFin key is configured, should return a helpful message, not crash."""
    if has_simfin_key():
        pytest.skip("SimFin key is configured — skipping no-key test")
    result = market_data.get_simfin_financials("AAPL")
    assert "simfin.com" in result.lower() or "simfin" in result.lower() or "Error" in result
