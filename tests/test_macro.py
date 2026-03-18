"""
Regression tests for macro-mcp (FRED + SEC EDGAR).

Free API (SEC EDGAR, no key):    search_edgar_company, get_recent_filings, get_13f_holdings
Requires FRED_API_KEY:           get_key_indicators, get_fred_data, search_fred_series
"""

import pytest
from conftest import has_fred_key, skip_if_rate_limited


# ── SEC EDGAR tools (no key required) ────────────────────────────────────────

@pytest.mark.integration
def test_search_edgar_company(macro):
    result = macro.search_edgar_company("Apple")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "EDGAR Company Search" in result
    assert "AAPL" in result or "Apple" in result


@pytest.mark.integration
def test_get_recent_filings_10k(macro):
    result = macro.get_recent_filings("AAPL", form_type="10-K", limit=3)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "10-K" in result
    # Accession numbers follow the pattern XXXXXXXXXX-YY-ZZZZZZ
    assert "-" in result


@pytest.mark.integration
def test_get_recent_filings_10q(macro):
    result = macro.get_recent_filings("MSFT", form_type="10-Q", limit=3)
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "10-Q" in result


@pytest.mark.integration
def test_get_13f_holdings_berkshire(macro):
    # Berkshire CIK: 1067983
    result = macro.get_13f_holdings("1067983")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    # Should mention 13F or return a "not found" message — either is valid
    assert "13F" in result or "Berkshire" in result


# ── FRED tools (key required) ─────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.requires_fred
def test_get_key_indicators(macro):
    if not has_fred_key():
        pytest.skip("FRED_API_KEY not configured")
    result = macro.get_key_indicators()
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Key Macro Indicators" in result
    assert "DFF" in result      # Fed Funds Rate
    assert "UNRATE" in result   # Unemployment
    assert "DGS10" in result    # 10Y Treasury


@pytest.mark.integration
@pytest.mark.requires_fred
def test_get_fred_data_fed_funds_rate(macro):
    if not has_fred_key():
        pytest.skip("FRED_API_KEY not configured")
    result = macro.get_fred_data("DFF")
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "DFF" in result
    assert "Date" in result


@pytest.mark.integration
@pytest.mark.requires_fred
def test_get_fred_data_with_date_range(macro):
    if not has_fred_key():
        pytest.skip("FRED_API_KEY not configured")
    result = macro.get_fred_data("CPIAUCSL", start_date="2024-01-01", end_date="2024-12-31")
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "CPIAUCSL" in result
    assert "2024" in result


@pytest.mark.integration
@pytest.mark.requires_fred
def test_search_fred_series(macro):
    if not has_fred_key():
        pytest.skip("FRED_API_KEY not configured")
    result = macro.search_fred_series("inflation", limit=5)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "FRED Series Search" in result
    assert "inflation" in result.lower()
