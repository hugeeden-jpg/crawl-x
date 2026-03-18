"""
Regression tests for sentiment-mcp (Fear&Greed + Quiver).

Free API (no key):               get_fear_greed_index
Requires QUIVER_API_KEY:         get_congressional_trades, get_wsb_mentions,
                                  get_insider_sentiment
"""

import pytest
from conftest import has_quiver_key


# ── Fear & Greed Index (free, no key) ─────────────────────────────────────────

@pytest.mark.integration
def test_get_fear_greed_index_single_day(sentiment):
    result = sentiment.get_fear_greed_index(days=1)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Fear & Greed" in result
    assert "Score" in result or any(c.isdigit() for c in result)


@pytest.mark.integration
def test_get_fear_greed_index_week(sentiment):
    result = sentiment.get_fear_greed_index(days=7)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Fear & Greed" in result
    # Should have 7 rows of data
    data_lines = [l for l in result.splitlines() if l.strip() and "-" in l[:15] and any(c.isdigit() for c in l)]
    assert len(data_lines) >= 5


@pytest.mark.integration
def test_get_fear_greed_index_format(sentiment):
    """Validate classification labels."""
    result = sentiment.get_fear_greed_index(days=1)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    # Classification should be one of the known labels
    known = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
    assert any(label in result for label in known)


# ── Quiver tools (key required) ───────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.requires_quiver
def test_get_congressional_trades_all(sentiment):
    if not has_quiver_key():
        pytest.skip("QUIVER_API_KEY not configured")
    result = sentiment.get_congressional_trades(days=30)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Congressional Trades" in result


@pytest.mark.integration
@pytest.mark.requires_quiver
def test_get_congressional_trades_by_ticker(sentiment):
    if not has_quiver_key():
        pytest.skip("QUIVER_API_KEY not configured")
    result = sentiment.get_congressional_trades(ticker="NVDA", days=90)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "NVDA" in result


@pytest.mark.integration
@pytest.mark.requires_quiver
def test_get_wsb_mentions(sentiment):
    if not has_quiver_key():
        pytest.skip("QUIVER_API_KEY not configured")
    result = sentiment.get_wsb_mentions("GME")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "WSB Mentions" in result
    assert "GME" in result


@pytest.mark.integration
@pytest.mark.requires_quiver
def test_get_insider_sentiment(sentiment):
    if not has_quiver_key():
        pytest.skip("QUIVER_API_KEY not configured")
    result = sentiment.get_insider_sentiment("AAPL")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Insider Trading" in result
    assert "AAPL" in result
