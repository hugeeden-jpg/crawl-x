#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
# ]
# ///
"""
Crypto MCP Server - CoinGecko + DeFi Llama + Glassnode
Crypto prices, market data, DeFi TVL, on-chain metrics
"""

import os
import json
from pathlib import Path

# requests uses certifi by default; on macOS + Homebrew openssl the chain may not verify.
_brew_ca = Path("/opt/homebrew/etc/openssl@3/cert.pem")
if _brew_ca.exists():
    os.environ.setdefault("REQUESTS_CA_BUNDLE", str(_brew_ca))

import requests
from datetime import datetime

from mcp.server.fastmcp import FastMCP

CONFIG_FILE = Path.home() / ".config" / "crypto-mcp" / "config.json"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
DEFILLAMA_BASE = "https://api.llama.fi"
GLASSNODE_BASE = "https://api.glassnode.com/v1/metrics"

mcp = FastMCP("crypto-data")


def load_config() -> dict:
    cfg = {
        "coingecko_api_key": os.environ.get("COINGECKO_API_KEY", ""),
        "glassnode_api_key": os.environ.get("GLASSNODE_API_KEY", ""),
    }
    if CONFIG_FILE.exists():
        file_cfg = json.loads(CONFIG_FILE.read_text())
        for k in ("coingecko_api_key", "glassnode_api_key"):
            if not cfg[k]:
                cfg[k] = file_cfg.get(k, "")
    return cfg


def coingecko_get(endpoint: str, params: dict = None) -> dict | list:
    cfg = load_config()
    headers = {}
    if cfg["coingecko_api_key"]:
        headers["x-cg-demo-api-key"] = cfg["coingecko_api_key"]
    r = requests.get(f"{COINGECKO_BASE}{endpoint}", params=params or {}, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def glassnode_get(endpoint: str, params: dict) -> list:
    cfg = load_config()
    if not cfg["glassnode_api_key"]:
        raise ValueError("Glassnode API key not configured. Use configure() tool.")
    params["api_key"] = cfg["glassnode_api_key"]
    r = requests.get(f"{GLASSNODE_BASE}{endpoint}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def iso_to_ts(date_str: str) -> int:
    return int(datetime.fromisoformat(date_str).timestamp())


@mcp.tool()
def configure(coingecko_api_key: str = "", glassnode_api_key: str = "") -> str:
    """Save CoinGecko and Glassnode API keys to config file"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({
        "coingecko_api_key": coingecko_api_key,
        "glassnode_api_key": glassnode_api_key,
    }, indent=2))
    return f"Config saved to {CONFIG_FILE}"


@mcp.tool()
def get_crypto_price(coin_id: str) -> str:
    """
    Get current price, 24h change%, market cap, and volume for a cryptocurrency

    Args:
        coin_id: CoinGecko coin ID (e.g. bitcoin, ethereum, solana, binancecoin)
    """
    try:
        data = coingecko_get(
            f"/coins/{coin_id}",
            {"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"},
        )
        mkt = data.get("market_data", {})
        price = mkt.get("current_price", {}).get("usd")
        change_24h = mkt.get("price_change_percentage_24h")
        market_cap = mkt.get("market_cap", {}).get("usd")
        volume = mkt.get("total_volume", {}).get("usd")
        name = data.get("name", coin_id)
        symbol = data.get("symbol", "").upper()

        lines = [f"=== {name} ({symbol}) ==="]
        lines.append(f"Price:      ${price:,.4f}" if price else "Price: N/A")
        lines.append(f"24h Change: {change_24h:+.2f}%" if change_24h is not None else "24h Change: N/A")
        lines.append(f"Market Cap: ${market_cap:,.0f}" if market_cap else "Market Cap: N/A")
        lines.append(f"Volume 24h: ${volume:,.0f}" if volume else "Volume 24h: N/A")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_crypto_market_data(coin_id: str) -> str:
    """
    Get comprehensive market data: ATH, circulating supply, dominance, price changes

    Args:
        coin_id: CoinGecko coin ID (e.g. bitcoin, ethereum)
    """
    try:
        data = coingecko_get(
            f"/coins/{coin_id}",
            {"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"},
        )
        mkt = data.get("market_data", {})
        name = data.get("name", coin_id)
        symbol = data.get("symbol", "").upper()

        lines = [f"=== {name} ({symbol}) Market Data ===\n"]
        price = mkt.get("current_price", {}).get("usd")
        lines.append(f"Price (USD):          ${price:,.4f}" if price else "Price: N/A")

        for period in ["1h", "24h", "7d", "30d", "1y"]:
            key = f"price_change_percentage_{period}"
            val = mkt.get(key)
            if val is not None:
                lines.append(f"Change {period:>4}:           {val:+.2f}%")

        ath = mkt.get("ath", {}).get("usd")
        ath_date = mkt.get("ath_date", {}).get("usd", "")[:10]
        ath_pct = mkt.get("ath_change_percentage", {}).get("usd")
        if ath:
            lines.append(f"\nATH:                  ${ath:,.4f} ({ath_date})")
            lines.append(f"From ATH:             {ath_pct:+.1f}%" if ath_pct is not None else "")

        cap = mkt.get("market_cap", {}).get("usd")
        rank = data.get("market_cap_rank")
        circ = mkt.get("circulating_supply")
        total = mkt.get("total_supply")
        lines.append(f"\nMarket Cap:           ${cap:,.0f}" if cap else "")
        lines.append(f"Market Cap Rank:      #{rank}" if rank else "")
        lines.append(f"Circulating Supply:   {circ:,.0f} {symbol}" if circ else "")
        lines.append(f"Total Supply:         {total:,.0f} {symbol}" if total else "")

        return "\n".join(l for l in lines if l)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_global_market() -> str:
    """
    Get global crypto market overview: total market cap, BTC dominance, top movers
    """
    try:
        data = coingecko_get("/global")
        d = data.get("data", {})

        total_mcap = d.get("total_market_cap", {}).get("usd", 0)
        total_vol = d.get("total_volume", {}).get("usd", 0)
        btc_dom = d.get("market_cap_percentage", {}).get("btc", 0)
        eth_dom = d.get("market_cap_percentage", {}).get("eth", 0)
        change_24h = d.get("market_cap_change_percentage_24h_usd", 0)
        active_coins = d.get("active_cryptocurrencies", 0)
        markets = d.get("markets", 0)

        lines = ["=== Global Crypto Market ===\n"]
        lines.append(f"Total Market Cap:     ${total_mcap/1e12:.3f}T" if total_mcap > 1e12 else f"Total Market Cap:     ${total_mcap/1e9:.1f}B")
        lines.append(f"24h Change:           {change_24h:+.2f}%")
        lines.append(f"Total Volume 24h:     ${total_vol/1e9:.1f}B")
        lines.append(f"BTC Dominance:        {btc_dom:.1f}%")
        lines.append(f"ETH Dominance:        {eth_dom:.1f}%")
        lines.append(f"Active Cryptocurrencies: {active_coins:,}")
        lines.append(f"Active Exchanges:     {markets:,}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_trending_coins() -> str:
    """
    Get top 7 trending coins on CoinGecko (most searched in last 24h)
    """
    try:
        data = coingecko_get("/search/trending")
        coins = data.get("coins", [])

        lines = ["=== Trending Coins (CoinGecko) ===\n"]
        lines.append(f"{'#':<3} {'Name':<20} {'Symbol':<8} {'Market Cap Rank':<18} {'Price Change 24h'}")
        lines.append("-" * 65)
        for i, coin_wrap in enumerate(coins[:7], 1):
            c = coin_wrap.get("item", {})
            name = c.get("name", "")[:19]
            symbol = c.get("symbol", "")[:7]
            rank = c.get("market_cap_rank", "N/A")
            data_fields = c.get("data", {})
            pct = data_fields.get("price_change_percentage_24h", {}).get("usd", "N/A")
            pct_str = f"{pct:+.2f}%" if isinstance(pct, (int, float)) else "N/A"
            lines.append(f"{i:<3} {name:<20} {symbol:<8} {str(rank):<18} {pct_str}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_defi_tvl_overview(limit: int = 20) -> str:
    """
    Get top DeFi protocols by Total Value Locked (TVL) from DeFi Llama

    Args:
        limit: Number of protocols to show (default: 20)
    """
    try:
        r = requests.get(f"{DEFILLAMA_BASE}/protocols", timeout=15)
        r.raise_for_status()
        protocols = r.json()
        sorted_protos = sorted(protocols, key=lambda x: x.get("tvl") or 0, reverse=True)

        lines = ["=== DeFi TVL Overview (DeFi Llama) ===\n"]
        lines.append(f"{'#':<4} {'Protocol':<25} {'TVL':>14} {'Change 1d':>11} {'Change 7d':>11} {'Chain'}")
        lines.append("-" * 80)
        for i, p in enumerate(sorted_protos[:limit], 1):
            name = p.get("name", "")[:24]
            tvl = p.get("tvl", 0)
            ch1d = p.get("change_1d")
            ch7d = p.get("change_7d")
            chain = p.get("chain", p.get("chains", [""])[0] if p.get("chains") else "")[:10]
            tvl_str = f"${tvl/1e9:.3f}B" if tvl >= 1e9 else f"${tvl/1e6:.1f}M"
            ch1d_str = f"{ch1d:+.1f}%" if ch1d is not None else "N/A"
            ch7d_str = f"{ch7d:+.1f}%" if ch7d is not None else "N/A"
            lines.append(f"{i:<4} {name:<25} {tvl_str:>14} {ch1d_str:>11} {ch7d_str:>11} {chain}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_protocol_tvl(protocol: str) -> str:
    """
    Get TVL history and chain breakdown for a specific DeFi protocol

    Args:
        protocol: Protocol slug (e.g. aave, uniswap, lido, compound, makerdao)
    """
    try:
        r = requests.get(f"{DEFILLAMA_BASE}/protocol/{protocol}", timeout=15)
        r.raise_for_status()
        data = r.json()

        name = data.get("name", protocol)
        description = data.get("description", "")[:200]
        category = data.get("category", "")
        chains = data.get("chains", [])
        current_tvl = data.get("tvl", [{}])[-1].get("totalLiquidityUSD", 0) if data.get("tvl") else 0

        lines = [f"=== {name} TVL Analysis ==="]
        lines.append(f"Category: {category}")
        lines.append(f"Chains:   {', '.join(chains[:10])}")
        lines.append(f"Current TVL: ${current_tvl/1e9:.3f}B" if current_tvl >= 1e9 else f"Current TVL: ${current_tvl/1e6:.1f}M")
        if description:
            lines.append(f"\n{description}")

        # TVL trend (last 30 days)
        tvl_history = data.get("tvl", [])
        if tvl_history:
            lines.append(f"\n--- TVL Trend (last 30 days) ---")
            lines.append(f"{'Date':<14} {'TVL':>14}")
            lines.append("-" * 30)
            for entry in tvl_history[-30:]:
                ts = entry.get("date", 0)
                tvl = entry.get("totalLiquidityUSD", 0)
                date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                tvl_str = f"${tvl/1e9:.3f}B" if tvl >= 1e9 else f"${tvl/1e6:.1f}M"
                lines.append(f"{date:<14} {tvl_str:>14}")

        # Chain breakdown
        chain_tvls = data.get("chainTvls", {})
        if chain_tvls:
            lines.append(f"\n--- Chain Breakdown ---")
            for chain, chain_data in list(chain_tvls.items())[:10]:
                if isinstance(chain_data, dict):
                    tvl_list = chain_data.get("tvl", [])
                    latest = tvl_list[-1].get("totalLiquidityUSD", 0) if tvl_list else 0
                elif isinstance(chain_data, list):
                    latest = chain_data[-1].get("totalLiquidityUSD", 0) if chain_data else 0
                else:
                    continue
                tvl_str = f"${latest/1e9:.3f}B" if latest >= 1e9 else f"${latest/1e6:.1f}M"
                lines.append(f"  {chain:<20} {tvl_str:>14}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_chain_tvl(chain: str) -> str:
    """
    Get TVL trend for a specific blockchain

    Args:
        chain: Chain name (e.g. ethereum, solana, bsc, avalanche, polygon, arbitrum)
    """
    try:
        r = requests.get(f"{DEFILLAMA_BASE}/v2/historicalChainTvl/{chain}", timeout=15)
        r.raise_for_status()
        data = r.json()

        lines = [f"=== {chain.capitalize()} Chain TVL (last 30 days) ===\n"]
        lines.append(f"{'Date':<14} {'TVL':>14}")
        lines.append("-" * 30)
        for entry in data[-30:]:
            ts = entry.get("date", 0)
            tvl = entry.get("tvl", 0)
            date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            tvl_str = f"${tvl/1e9:.3f}B" if tvl >= 1e9 else f"${tvl/1e6:.1f}M"
            lines.append(f"{date:<14} {tvl_str:>14}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_onchain_metric(metric: str, asset: str = "BTC", since: str = None, until: str = None) -> str:
    """
    Get on-chain metrics from Glassnode (requires API key)

    Args:
        metric: Metric path e.g. "market/price_usd_close", "addresses/active_count",
                "transactions/count", "supply/current", "indicators/sopr"
        asset: Asset symbol (default: BTC; also ETH, LTC, etc.)
        since: Start date ISO format e.g. "2024-01-01" (optional)
        until: End date ISO format e.g. "2024-12-31" (optional)
    """
    try:
        params = {"a": asset.upper(), "i": "24h"}
        if since:
            params["s"] = iso_to_ts(since)
        if until:
            params["u"] = iso_to_ts(until)

        data = glassnode_get(f"/{metric}", params)

        lines = [f"=== Glassnode: {asset.upper()} — {metric} ===\n"]
        lines.append(f"{'Date':<14} {'Value':>18}")
        lines.append("-" * 35)
        for entry in data[-40:]:
            ts = entry.get("t", 0)
            val = entry.get("v")
            date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            if val is None:
                val_str = "N/A"
            elif abs(val) >= 1e9:
                val_str = f"${val/1e9:.4f}B"
            elif abs(val) >= 1e6:
                val_str = f"${val/1e6:.4f}M"
            elif abs(val) >= 1000:
                val_str = f"{val:,.2f}"
            else:
                val_str = f"{val:.6f}"
            lines.append(f"{date:<14} {val_str:>18}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_exchange_flows(asset: str = "BTC") -> str:
    """
    Get exchange inflow, outflow, and netflow from Glassnode

    Args:
        asset: Asset symbol (default: BTC)
    """
    try:
        results = {}
        for flow_type, endpoint in [
            ("inflow", "transactions/transfers_volume_to_exchanges_sum"),
            ("outflow", "transactions/transfers_volume_from_exchanges_sum"),
            ("netflow", "transactions/transfers_volume_exchanges_net"),
        ]:
            try:
                data = glassnode_get(f"/{endpoint}", {"a": asset.upper(), "i": "24h"})
                results[flow_type] = data[-14:] if data else []
            except Exception:
                results[flow_type] = []

        lines = [f"=== {asset.upper()} Exchange Flows (Glassnode, last 14 days) ===\n"]
        lines.append(f"{'Date':<14} {'Inflow':>14} {'Outflow':>14} {'Netflow':>14}")
        lines.append("-" * 60)

        def fmt(v):
            return "N/A" if v is None else f"{v:,.2f}"

        dates = set()
        for flow_type in results:
            for entry in results[flow_type]:
                dates.add(entry.get("t", 0))

        for ts in sorted(dates):
            date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            in_val = next((e["v"] for e in results["inflow"] if e.get("t") == ts), None)
            out_val = next((e["v"] for e in results["outflow"] if e.get("t") == ts), None)
            net_val = next((e["v"] for e in results["netflow"] if e.get("t") == ts), None)
            lines.append(f"{date:<14} {fmt(in_val):>14} {fmt(out_val):>14} {fmt(net_val):>14}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
