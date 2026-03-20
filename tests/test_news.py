"""
Regression tests for news-mcp (GDELT).
No API key required. All tests run by default; rate-limit errors are skipped.
"""

import pytest
from conftest import skip_if_rate_limited

pytestmark = pytest.mark.integration


def test_search_news_basic(news):
    result = news.search_news("Federal Reserve")
    skip_if_rate_limited(result)
    assert "GDELT" in result
    assert not result.startswith("Error:")


def test_search_news_short_timespan(news):
    result = news.search_news("Apple Inc", timespan="1d", max_records=5)
    skip_if_rate_limited(result)
    # Either articles or "No articles found" — both are valid
    assert "GDELT" in result or "No articles found" in result
    assert not result.startswith("Error:")


def test_search_news_max_records_clamped(news):
    """max_records > 250 should be clamped to 250, not error."""
    result = news.search_news("Tesla", timespan="7d", max_records=9999)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")


def test_get_news_sentiment_basic(news):
    result = news.get_news_sentiment("Federal Reserve")
    skip_if_rate_limited(result)
    assert "Sentiment" in result
    assert "Tone" in result or "tone" in result
    assert not result.startswith("Error:")


def test_get_news_sentiment_short_timespan(news):
    result = news.get_news_sentiment("Bitcoin", timespan="3d")
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "Sentiment" in result or "No sentiment data" in result
