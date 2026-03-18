"""
Regression tests for crypto-mcp (CoinGecko + DeFi Llama + Glassnode).

Free API (no key):               get_global_market, get_trending_coins,
                                  get_crypto_price, get_crypto_market_data,
                                  get_defi_tvl_overview, get_protocol_tvl,
                                  get_chain_tvl
Requires GLASSNODE_API_KEY:      get_onchain_metric, get_exchange_flows
"""

import pytest
from conftest import has_glassnode_key, skip_if_rate_limited


# ── CoinGecko tools (free, no key) ────────────────────────────────────────────

@pytest.mark.integration
def test_get_global_market(crypto):
    result = crypto.get_global_market()
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "Global Crypto Market" in result
    assert "BTC Dominance" in result
    assert "Total Market Cap" in result


@pytest.mark.integration
def test_get_trending_coins(crypto):
    result = crypto.get_trending_coins()
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "Trending Coins" in result
    assert "Market Cap Rank" in result


@pytest.mark.integration
def test_get_crypto_price_bitcoin(crypto):
    result = crypto.get_crypto_price("bitcoin")
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "Bitcoin" in result or "BTC" in result
    assert "Price:" in result
    assert "24h Change:" in result


@pytest.mark.integration
def test_get_crypto_price_ethereum(crypto):
    result = crypto.get_crypto_price("ethereum")
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "Ethereum" in result or "ETH" in result


@pytest.mark.integration
def test_get_crypto_price_invalid_coin(crypto):
    """Invalid coin ID must return an error string, not raise."""
    result = crypto.get_crypto_price("this-coin-does-not-exist-xyz999")
    assert isinstance(result, str)
    # CoinGecko will return a 404; the tool should catch it


@pytest.mark.integration
def test_get_crypto_market_data(crypto):
    result = crypto.get_crypto_market_data("bitcoin")
    assert isinstance(result, str)
    skip_if_rate_limited(result)
    assert not result.startswith("Error:")
    assert "Market Data" in result
    assert "ATH" in result
    assert "Market Cap" in result


# ── DeFi Llama tools (free, no key) ──────────────────────────────────────────

@pytest.mark.integration
def test_get_defi_tvl_overview(crypto):
    result = crypto.get_defi_tvl_overview(limit=10)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "DeFi TVL Overview" in result
    assert "TVL" in result
    # Should have at least a few protocols
    lines = [l for l in result.splitlines() if l.strip() and not l.startswith("=") and not l.startswith("-")]
    assert len(lines) >= 5


@pytest.mark.integration
def test_get_protocol_tvl_aave(crypto):
    result = crypto.get_protocol_tvl("aave")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "TVL" in result
    assert "aave" in result.lower() or "Aave" in result


@pytest.mark.integration
def test_get_chain_tvl_ethereum(crypto):
    result = crypto.get_chain_tvl("ethereum")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Ethereum" in result
    assert "TVL" in result
    assert "Date" in result


@pytest.mark.integration
def test_get_chain_tvl_solana(crypto):
    result = crypto.get_chain_tvl("solana")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "TVL" in result


# ── Glassnode tools (key required) ───────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.requires_glassnode
def test_get_onchain_metric_active_addresses(crypto):
    if not has_glassnode_key():
        pytest.skip("GLASSNODE_API_KEY not configured")
    result = crypto.get_onchain_metric("addresses/active_count", asset="BTC")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "BTC" in result
    assert "Date" in result


@pytest.mark.integration
@pytest.mark.requires_glassnode
def test_get_exchange_flows_btc(crypto):
    if not has_glassnode_key():
        pytest.skip("GLASSNODE_API_KEY not configured")
    result = crypto.get_exchange_flows("BTC")
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Exchange Flows" in result
    assert "Inflow" in result
    assert "Outflow" in result
