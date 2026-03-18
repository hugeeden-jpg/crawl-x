"""
Regression tests for market-data-mcp (yfinance + Finnhub).

Free API (yfinance, no key):     get_quote, get_stock_info, get_stock_history,
                                  get_financials, get_analyst_recommendations
Requires FINNHUB_API_KEY:        get_market_news, get_company_news,
                                  get_earnings_calendar, get_news_sentiment
"""

import pytest
from conftest import has_finnhub_key


# ── yfinance tools (no key required) ─────────────────────────────────────────

@pytest.mark.integration
def test_get_quote_returns_price(market_data):
    result = market_data.get_quote("AAPL")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "=== AAPL Quote ===" in result
    assert "Price:" in result
    assert "Change:" in result


@pytest.mark.integration
def test_get_quote_invalid_ticker_no_exception(market_data):
    """Tool must return a string (possibly error), never raise."""
    result = market_data.get_quote("XXXXINVALID99999")
    assert isinstance(result, str)


@pytest.mark.integration
def test_get_stock_info_fields(market_data):
    result = market_data.get_stock_info("MSFT")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "=== MSFT Company Info ===" in result
    assert "Sector" in result
    assert "PE Ratio" in result


@pytest.mark.integration
def test_get_stock_history_columns(market_data):
    result = market_data.get_stock_history("NVDA", period="5d", interval="1d")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "NVDA Price History" in result
    assert "Open" in result
    assert "Close" in result
    assert "Volume" in result


@pytest.mark.integration
def test_get_financials_income(market_data):
    result = market_data.get_financials("AAPL", "income")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Income Statement" in result


@pytest.mark.integration
def test_get_financials_balance(market_data):
    result = market_data.get_financials("AAPL", "balance")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Balance Sheet" in result


@pytest.mark.integration
def test_get_financials_cashflow(market_data):
    result = market_data.get_financials("AAPL", "cashflow")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Cash Flow" in result


@pytest.mark.integration
def test_get_financials_invalid_type(market_data):
    result = market_data.get_financials("AAPL", "invalid_type")
    assert "Invalid statement type" in result


@pytest.mark.integration
def test_get_analyst_recommendations(market_data):
    result = market_data.get_analyst_recommendations("AAPL")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Analyst Recommendations" in result


# ── Finnhub tools (key required) ──────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.requires_finnhub
def test_get_market_news(market_data):
    if not has_finnhub_key():
        pytest.skip("FINNHUB_API_KEY not configured")
    result = market_data.get_market_news("general")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Market News" in result


@pytest.mark.integration
@pytest.mark.requires_finnhub
def test_get_company_news(market_data):
    if not has_finnhub_key():
        pytest.skip("FINNHUB_API_KEY not configured")
    result = market_data.get_company_news("TSLA", days=7)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "TSLA News" in result


@pytest.mark.integration
@pytest.mark.requires_finnhub
def test_get_earnings_calendar(market_data):
    if not has_finnhub_key():
        pytest.skip("FINNHUB_API_KEY not configured")
    result = market_data.get_earnings_calendar(days_ahead=14)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Earnings Calendar" in result


@pytest.mark.integration
@pytest.mark.requires_finnhub
def test_get_news_sentiment(market_data):
    if not has_finnhub_key():
        pytest.skip("FINNHUB_API_KEY not configured")
    result = market_data.get_news_sentiment("AAPL")
    assert isinstance(result, str)
    # /news-sentiment is a Finnhub Premium endpoint; free keys get 403
    if "403" in result:
        pytest.skip("get_news_sentiment requires Finnhub Premium (403 Forbidden)")
    assert not result.startswith("Error:")
    assert "News Sentiment" in result
    assert "Buzz" in result
