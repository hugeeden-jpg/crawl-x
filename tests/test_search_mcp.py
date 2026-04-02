"""
Regression tests for search-mcp (Google search via Scrapling).
No API key required. All tests marked slow — not run by default to avoid
triggering Google anti-bot detection in CI. Run manually:
  cd tests && uv run pytest test_search_mcp.py -v
"""

import pytest
from conftest import skip_if_rate_limited

pytestmark = [pytest.mark.integration, pytest.mark.slow]


def test_search_basic(search):
    result = search.search("python web scraping")
    skip_if_rate_limited(result)
    assert "URL: https://" in result
    assert not result.startswith("Error:")
    assert "Search results" in result


def test_search_returns_multiple_results(search):
    result = search.search("openai gpt api", num_results=5)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "3." in result


def test_search_language_param(search):
    result = search.search("人工智能 新闻", language="zh-CN", num_results=5)
    skip_if_rate_limited(result)
    assert "URL: https://" in result
    assert not result.startswith("Error:")


def test_search_no_ad_urls(search):
    result = search.search("buy laptop online", num_results=10)
    skip_if_rate_limited(result)
    assert "googleadservices.com" not in result
    assert "google.com/aclk" not in result


def test_search_no_results_query(search):
    result = search.search("xkqzwqp93847zjzmzqp", num_results=5)
    skip_if_rate_limited(result)
    assert isinstance(result, str)
    assert len(result) > 0
