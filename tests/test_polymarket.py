"""
Regression tests for polymarket-mcp (Polymarket Gamma API).
No API key required. All tests run by default.
"""

import pytest
from conftest import skip_if_rate_limited

pytestmark = pytest.mark.integration


def test_search_markets_with_query(polymarket):
    result = polymarket.search_markets(query="Trump", limit=5)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "Polymarket Markets" in result


def test_search_markets_no_query(polymarket):
    result = polymarket.search_markets(limit=5)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "Odds:" in result


def test_search_markets_category_filter(polymarket):
    result = polymarket.search_markets(category="sports", limit=5)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")


def test_get_market(polymarket):
    # First grab an active market ID via search
    search_result = polymarket.search_markets(limit=1)
    skip_if_rate_limited(search_result)
    assert not search_result.startswith("Error:")

    # Extract market ID from URL slug, then call get_market with a known-good ID
    # Use a stable market approach: search trending and grab first ID via raw API
    import requests
    resp = requests.get(
        "https://gamma-api.polymarket.com/markets",
        params={"limit": 1, "order": "volume24hr", "ascending": "false", "active": "true", "closed": "false"},
        timeout=15,
    )
    market_id = resp.json()[0]["id"]

    result = polymarket.get_market(market_id)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "Volume 24h:" in result
    assert "Status:" in result


def test_get_market_invalid_id(polymarket):
    result = polymarket.get_market("000000000")
    assert isinstance(result, str)
    # Should return an error, not raise an exception


def test_get_events_with_query(polymarket):
    result = polymarket.get_events(query="election", limit=3)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "Polymarket Events" in result


def test_get_events_no_query(polymarket):
    result = polymarket.get_events(limit=5)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "Markets:" in result


def test_get_trending_markets_24h(polymarket):
    result = polymarket.get_trending_markets(period="24h", limit=5)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "24 hours" in result
    assert "#1" in result


def test_get_trending_markets_7d(polymarket):
    result = polymarket.get_trending_markets(period="7d", limit=3)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "7 days" in result


def test_get_trending_markets_30d(polymarket):
    result = polymarket.get_trending_markets(period="30d", limit=3)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "30 days" in result


def test_get_trending_markets_all(polymarket):
    result = polymarket.get_trending_markets(period="all", limit=3)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "all time" in result


def test_get_trending_markets_category(polymarket):
    result = polymarket.get_trending_markets(period="24h", category="sports", limit=5)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
