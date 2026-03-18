"""
Regression tests for grok-mcp (Grok API / xAI).

All tools require XAI_API_KEY — skipped automatically if not configured.
"""

import pytest
from conftest import has_xai_key


@pytest.mark.integration
@pytest.mark.requires_xai
def test_search_x_news(grok):
    if not has_xai_key():
        pytest.skip("XAI_API_KEY not configured")
    result = grok.search_x_news("NVDA", hours=24)
    assert isinstance(result, str)
    assert len(result) > 50  # should return substantive content
    assert "Error" not in result[:50]


@pytest.mark.integration
@pytest.mark.requires_xai
def test_get_ticker_sentiment_stock(grok):
    if not has_xai_key():
        pytest.skip("XAI_API_KEY not configured")
    result = grok.get_ticker_sentiment("TSLA", asset_type="stock")
    assert isinstance(result, str)
    assert len(result) > 50
    assert "Error" not in result[:50]


@pytest.mark.integration
@pytest.mark.requires_xai
def test_get_ticker_sentiment_crypto(grok):
    if not has_xai_key():
        pytest.skip("XAI_API_KEY not configured")
    result = grok.get_ticker_sentiment("BTC", asset_type="crypto")
    assert isinstance(result, str)
    assert len(result) > 50
    assert "Error" not in result[:50]


@pytest.mark.integration
@pytest.mark.requires_xai
def test_get_financial_news_web(grok):
    if not has_xai_key():
        pytest.skip("XAI_API_KEY not configured")
    result = grok.get_financial_news("美联储政策", source="web")
    assert isinstance(result, str)
    assert len(result) > 50
    assert "Error" not in result[:50]


@pytest.mark.integration
@pytest.mark.requires_xai
def test_get_financial_news_x_source(grok):
    if not has_xai_key():
        pytest.skip("XAI_API_KEY not configured")
    result = grok.get_financial_news("比特币", source="x")
    assert isinstance(result, str)
    assert len(result) > 50
    assert "Error" not in result[:50]


@pytest.mark.integration
@pytest.mark.requires_xai
def test_get_kol_mentions(grok):
    if not has_xai_key():
        pytest.skip("XAI_API_KEY not configured")
    result = grok.get_kol_mentions("Michael Saylor")
    assert isinstance(result, str)
    assert len(result) > 50
    assert "Error" not in result[:50]


def test_set_api_key_saves_config(grok, tmp_path, monkeypatch):
    """Verify set_api_key writes to the expected config path."""
    import json
    fake_config = tmp_path / "config.json"
    monkeypatch.setattr(grok, "CONFIG_FILE", fake_config)
    result = grok.set_api_key("test_key_12345")
    assert "saved" in result.lower() or "保存" in result
    assert fake_config.exists()
    saved = json.loads(fake_config.read_text())
    assert saved.get("api_key") == "test_key_12345"
