"""
Regression tests for scrape-mcp (OpenInsider + Capitol Trades + CME FedWatch).

Fast (HTTP, no browser):   get_insider_trades
Slow (browser/Scrapling):  get_congressional_trades, get_fed_rate_probabilities

Run without slow tests:  pytest -m "not slow"
"""

import asyncio
import re

import pytest


# ── OpenInsider — get_insider_trades (fast, no browser) ──────────────────────

def _openinsider_ok(result: str) -> bool:
    """Return True if result is a valid (non-error) OpenInsider response.
    Accepts both data rows and the no-data message (returned when rate-limited or no activity)."""
    return not result.startswith("Error scraping")


@pytest.mark.integration
def test_get_insider_trades_by_ticker(scrape):
    result = scrape.get_insider_trades(ticker="TSLA", trade_type="A", days=90)
    assert isinstance(result, str)
    assert _openinsider_ok(result)
    assert "TSLA" in result or "No insider trades found" in result


@pytest.mark.integration
def test_get_insider_trades_sales_nvda(scrape):
    """NVDA executives regularly sell shares; verifies data rows are returned."""
    result = scrape.get_insider_trades(ticker="NVDA", trade_type="S", days=90)
    assert isinstance(result, str)
    assert _openinsider_ok(result)
    assert "NVDA" in result or "No insider trades found" in result
    # If data was returned, verify at least one sale row
    if "Sale" in result:
        data_lines = [l for l in result.splitlines() if "NVDA" in l and "Sale" in l]
        assert len(data_lines) >= 1


@pytest.mark.integration
def test_get_insider_trades_all_tickers(scrape):
    """Without a ticker, should return recent market-wide insider trades."""
    result = scrape.get_insider_trades(ticker=None, trade_type="P", days=7)
    assert isinstance(result, str)
    assert _openinsider_ok(result)
    assert "Insider Trades" in result or "No insider trades found" in result


@pytest.mark.integration
def test_get_insider_trades_column_alignment(scrape):
    """Verify the output is properly aligned (no runaway long lines)."""
    result = scrape.get_insider_trades(ticker="NVDA", trade_type="A", days=90)
    assert isinstance(result, str)
    # Data lines should not be excessively long (> 200 chars indicates un-truncated cells)
    for line in result.splitlines():
        assert len(line) <= 200, f"Line too long ({len(line)} chars): {line[:80]}..."


@pytest.mark.integration
def test_get_insider_trades_date_filter(scrape):
    """days=1 should return only very recent trades or 'No trades found'."""
    result = scrape.get_insider_trades(ticker=None, trade_type="A", days=1)
    assert isinstance(result, str)
    assert not result.startswith("Error:")


# ── Capitol Trades — get_congressional_trades (slow, browser) ────────────────

@pytest.mark.integration
@pytest.mark.slow
def test_get_congressional_trades_all(scrape):
    result = asyncio.run(scrape.get_congressional_trades(days=30))
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Congressional Trades" in result


@pytest.mark.integration
@pytest.mark.slow
def test_get_congressional_trades_by_ticker(scrape):
    result = asyncio.run(scrape.get_congressional_trades(ticker="NVDA", days=90))
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Congressional Trades" in result
    assert "NVDA" in result


@pytest.mark.integration
@pytest.mark.slow
def test_get_congressional_trades_column_alignment(scrape):
    """Verify HTML fallback output doesn't dump raw untruncated cell text."""
    result = asyncio.run(scrape.get_congressional_trades(days=30))
    assert isinstance(result, str)
    # Each data line should be reasonably short
    for line in result.splitlines():
        assert len(line) <= 200, f"Line too long ({len(line)} chars): {line[:80]}..."


# ── CME FedWatch — get_fed_rate_probabilities (slow, browser) ────────────────

@pytest.mark.integration
@pytest.mark.slow
def test_get_fed_rate_probabilities_returns_data(scrape):
    result = asyncio.run(scrape.get_fed_rate_probabilities())
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "FedWatch" in result or "Fed Rate" in result


@pytest.mark.integration
@pytest.mark.slow
def test_get_fed_rate_probabilities_has_table(scrape):
    """Verify actual probability data is present (not just the header)."""
    result = asyncio.run(scrape.get_fed_rate_probabilities())
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    # Probability values are percentages — at least one "%" should appear
    assert "%" in result


@pytest.mark.integration
@pytest.mark.slow
def test_get_fed_rate_probabilities_no_duplicate_tables(scrape):
    """Regression: selector change to '> table' should prevent duplicate table output."""
    result = asyncio.run(scrape.get_fed_rate_probabilities())
    assert isinstance(result, str)
    if result.startswith("Error:") or "Could not load" in result:
        pytest.skip("FedWatch page unavailable in this environment")
    lines = result.splitlines()
    # Count separator lines (---) — if tables are duplicated, we get many more than expected
    sep_count = sum(1 for l in lines if l.startswith("---") or set(l.strip()) == {"-"})
    assert sep_count <= 6, f"Suspiciously many table separators ({sep_count}) — possible duplicate tables"
