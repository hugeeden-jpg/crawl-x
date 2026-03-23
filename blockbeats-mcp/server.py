#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
# ]
# ///
"""
BlockBeats MCP Server — BlockBeats Pro API
Crypto news, on-chain data, market sentiment, derivatives
"""

import json
import os
from pathlib import Path

import requests
from mcp.server.fastmcp import FastMCP

CONFIG_FILE = Path.home() / ".config" / "blockbeats-mcp" / "config.json"
BASE_URL = "http://api-pro.theblockbeats.info"
DAILY_TX_FILE = Path("/tmp/blockbeats_daily_tx.json")

mcp = FastMCP("blockbeats")


def load_api_key() -> str:
    key = os.environ.get("BLOCKBEATS_API_KEY", "")
    if key:
        return key
    if CONFIG_FILE.exists():
        cfg = json.loads(CONFIG_FILE.read_text())
        return cfg.get("api_key", "")
    return ""


def api_get(path: str, params: dict = None) -> object:
    key = load_api_key()
    if not key:
        raise ValueError(
            "BlockBeats API key not configured. "
            "Use configure(api_key='your_key'), or apply at https://www.theblockbeats.info/"
        )
    r = requests.get(
        f"{BASE_URL}{path}",
        params={k: v for k, v in (params or {}).items() if v is not None},
        headers={"api-key": key},
        timeout=15,
    )
    r.raise_for_status()
    body = r.json()
    if body.get("status") != 0:
        raise ValueError(f"API error {body.get('status')}: {body.get('message', '')}")
    return body.get("data", body)


def trim(data, limit: int):
    """Trim a list to the last `limit` items. No-op if data is not a list."""
    if isinstance(data, list) and limit and limit > 0:
        return data[-limit:]
    return data


# ── Configuration ─────────────────────────────────────────────────────────────

@mcp.tool()
def configure(api_key: str) -> str:
    """Save BlockBeats Pro API key to ~/.config/blockbeats-mcp/config.json

    Args:
        api_key: BlockBeats Pro API key (apply at https://www.theblockbeats.info/)
    """
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    cfg["api_key"] = api_key
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    return f"API key saved to {CONFIG_FILE}"


# ── News & Search ──────────────────────────────────────────────────────────────

@mcp.tool()
def get_newsflash(
    category: str = "",
    page: int = 1,
    size: int = 10,
    lang: str = "en",
) -> str:
    """Get paginated newsflash list by category.

    Args:
        category: newsflash category — one of: "" (all), important, original,
                  first, onchain, financing, prediction, ai (default: "" = all)
        page: page number (default: 1)
        size: items per page, max 100 (default: 10)
        lang: language — en or cn (default: en)
    """
    path = f"/v1/newsflash/{category}" if category else "/v1/newsflash"
    data = api_get(path, {"page": page, "size": size, "lang": lang})
    items = data.get("data", data) if isinstance(data, dict) else data
    label = category.capitalize() if category else "All"
    lines = [f"=== BlockBeats Newsflash [{label}] — page {page} ===\n"]
    for item in (items if isinstance(items, list) else []):
        lines.append(f"[{item.get('create_time', '')}] {item.get('title', '')}")
        abstract = item.get("abstract", "")
        if abstract:
            lines.append(f"  {abstract[:200]}")
        link = item.get("link") or item.get("url", "")
        if link:
            lines.append(f"  {link}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def get_newsflash_24h(lang: str = "en") -> str:
    """Get all newsflashes from the last 24 hours (no pagination).

    Args:
        lang: language — en or cn (default: en)
    """
    data = api_get("/v1/newsflash/24h", {"lang": lang})
    items = data if isinstance(data, list) else data.get("data", [])
    lines = [f"=== BlockBeats Newsflash [Last 24h] — {len(items)} items ===\n"]
    for item in items:
        lines.append(f"[{item.get('create_time', '')}] {item.get('title', '')}")
        abstract = item.get("abstract", "")
        if abstract:
            lines.append(f"  {abstract[:200]}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def get_articles(
    category: str = "",
    page: int = 1,
    size: int = 10,
    lang: str = "en",
) -> str:
    """Get paginated article list by category.

    Args:
        category: article category — one of: "" (all), important, original (default: "" = all)
        page: page number (default: 1)
        size: items per page (default: 10)
        lang: language — en or cn (default: en)
    """
    path = f"/v1/article/{category}" if category else "/v1/article"
    data = api_get(path, {"page": page, "size": size, "lang": lang})
    items = data.get("data", data) if isinstance(data, dict) else data
    label = category.capitalize() if category else "All"
    lines = [f"=== BlockBeats Articles [{label}] — page {page} ===\n"]
    for item in (items if isinstance(items, list) else []):
        lines.append(f"[{item.get('create_time', '')}] {item.get('title', '')}")
        abstract = item.get("abstract", "")
        if abstract:
            lines.append(f"  {abstract[:200]}")
        link = item.get("link") or item.get("url", "")
        if link:
            lines.append(f"  {link}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def get_articles_24h(lang: str = "en") -> str:
    """Get all articles from the last 24 hours (no pagination, up to 50).

    Args:
        lang: language — en or cn (default: en)
    """
    data = api_get("/v1/article/24h", {"lang": lang})
    items = data if isinstance(data, list) else data.get("data", [])
    lines = [f"=== BlockBeats Articles [Last 24h] — {len(items)} items ===\n"]
    for item in items:
        lines.append(f"[{item.get('create_time', '')}] {item.get('title', '')}")
        abstract = item.get("abstract", "")
        if abstract:
            lines.append(f"  {abstract[:200]}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def search_news(
    keyword: str,
    page: int = 1,
    size: int = 10,
    lang: str = "en",
) -> str:
    """Search news and articles by keyword.

    Args:
        keyword: search keyword
        page: page number (default: 1)
        size: items per page, max 100 (default: 10)
        lang: language — en or cn (default: en)
    """
    data = api_get("/v1/search", {"name": keyword, "page": page, "size": size, "lang": lang})
    items = data.get("data", data) if isinstance(data, dict) else data
    total = data.get("total", "?") if isinstance(data, dict) else "?"
    lines = [f"=== Search: \"{keyword}\" — {total} results (page {page}) ===\n"]
    for item in (items if isinstance(items, list) else []):
        kind = "Article" if item.get("type") == 0 else "Newsflash"
        lines.append(f"[{kind}] [{item.get('time_cn', '')}] {item.get('title', '')}")
        abstract = item.get("abstract", "")
        if abstract:
            lines.append(f"  {abstract[:200]}")
        url = item.get("url", "")
        if url:
            lines.append(f"  {url}")
        lines.append("")
    return "\n".join(lines)


# ── Market Data ────────────────────────────────────────────────────────────────

@mcp.tool()
def get_btc_etf_flow(limit: int = 30) -> str:
    """Get BTC spot ETF daily net inflow / cumulative net inflow.

    Args:
        limit: number of most recent days to return (default: 30, 0 = all)
    """
    data = api_get("/v1/data/btc_etf")
    data = trim(data, limit)
    lines = ["=== BTC Spot ETF Net Inflow ===\n"]
    lines.append(f"{'Date':<12} {'Daily (M USD)':>14} {'Cumulative (M USD)':>20}")
    lines.append("-" * 50)
    for row in (data if isinstance(data, list) else []):
        day = float(row.get("day_net_inflow_million", 0))
        total = float(row.get("total_net_inflow_million", 0))
        sign = "+" if day >= 0 else ""
        lines.append(f"{row.get('date', ''):<12} {sign}{day:>13,.2f} {total:>19,.2f}")
    return "\n".join(lines)


@mcp.tool()
def get_daily_onchain_tx() -> str:
    """Get daily on-chain transaction volume for all chains.

    IMPORTANT: This endpoint returns ~500KB of multi-chain historical data.
    To avoid flooding the context window, the full response is written to
    /tmp/blockbeats_daily_tx.json and only a compact summary is returned.

    To query a specific chain's history, use Bash:
      jq '.[] | select(.name=="solana") | .data[-7:]' /tmp/blockbeats_daily_tx.json
    """
    data = api_get("/v1/data/daily_tx")
    DAILY_TX_FILE.write_text(json.dumps(data, ensure_ascii=False))

    lines = [f"=== Daily On-chain Transactions (full data → {DAILY_TX_FILE}) ===\n"]
    lines.append(f"{'Chain':<15} {'Latest Date':<12} {'Tx Count':>15} {'vs Prev':>10}")
    lines.append("-" * 56)
    for chain in (data if isinstance(data, list) else []):
        series = chain.get("data", [])
        if not series:
            continue
        name = chain.get("name_capitalized", chain.get("name", ""))[:14]
        latest = series[-1]
        date = latest.get("date", "")[:10]
        tx_now = int(latest.get("daily_transactions", 0))
        if len(series) >= 2:
            tx_prev = int(series[-2].get("daily_transactions", 1))
            pct = (tx_now - tx_prev) / tx_prev * 100
            trend = f"{'+' if pct >= 0 else ''}{pct:.1f}%"
        else:
            trend = "N/A"
        lines.append(f"{name:<15} {date:<12} {tx_now:>15,} {trend:>10}")

    lines.append(f"\nFull data: jq '.[] | select(.name==\"<chain>\") | .data[-7:]' {DAILY_TX_FILE}")
    return "\n".join(lines)


@mcp.tool()
def get_ibit_fbtc_flow(limit: int = 30) -> str:
    """Get IBIT and FBTC ETF net inflow data.

    Args:
        limit: number of most recent days to return (default: 30, 0 = all)
    """
    data = api_get("/v1/data/ibit_fbtc")
    # data is {"ibit": [{date, day_net_inflow}, ...], "fbtc": [...]}
    ibit = trim(data.get("ibit", []) if isinstance(data, dict) else [], limit)
    fbtc = trim(data.get("fbtc", []) if isinstance(data, dict) else [], limit)
    lines = ["=== IBIT / FBTC ETF Net Inflow ===\n"]
    # Merge by date
    ibit_map = {r["date"]: r.get("day_net_inflow", "") for r in ibit}
    fbtc_map = {r["date"]: r.get("day_net_inflow", "") for r in fbtc}
    dates = sorted(set(list(ibit_map.keys()) + list(fbtc_map.keys())))
    if dates:
        lines.append(f"{'Date':<12} {'IBIT':>14} {'FBTC':>14}")
        lines.append("-" * 42)
        for d in dates:
            iv = ibit_map.get(d, "")
            fv = fbtc_map.get(d, "")
            try:
                iv_s = f"{float(iv):>14,.2f}"
            except (ValueError, TypeError):
                iv_s = f"{str(iv):>14}"
            try:
                fv_s = f"{float(fv):>14,.2f}"
            except (ValueError, TypeError):
                fv_s = f"{str(fv):>14}"
            lines.append(f"{d:<12} {iv_s} {fv_s}")
    return "\n".join(lines)


@mcp.tool()
def get_stablecoin_marketcap(limit: int = 30) -> str:
    """Get stablecoin (USDT, USDC, etc.) market cap history.

    Args:
        limit: number of most recent entries to return (default: 30, 0 = all)
    """
    data = api_get("/v1/data/stablecoin_marketcap")
    # data is {"usdt": [{date, market_cap}, ...], "usdc": [...], ...}
    coins = list(data.keys()) if isinstance(data, dict) else []
    lines = ["=== Stablecoin Market Cap (billions USD) ===\n"]
    if not coins:
        return "\n".join(lines)
    # Merge all coins by date, show up to 5 coins
    show_coins = coins[:5]
    coin_maps = {c: {r["date"]: r.get("market_cap", "") for r in trim(data[c], limit)} for c in show_coins}
    dates = sorted(set(d for m in coin_maps.values() for d in m))
    header = f"{'Date':<12}" + "".join(f"{c.upper():>16}" for c in show_coins)
    lines.append(header)
    lines.append("-" * (12 + 16 * len(show_coins)))
    for d in dates:
        line = f"{d:<12}"
        for c in show_coins:
            v = coin_maps[c].get(d, "")
            try:
                line += f"{float(v)/1e9:>16,.2f}"
            except (ValueError, TypeError):
                line += f"{str(v):>16}"
        lines.append(line)
    return "\n".join(lines)


@mcp.tool()
def get_compliant_exchange_total(limit: int = 30) -> str:
    """Get total assets held by compliant (regulated) exchanges.

    Args:
        limit: number of most recent entries to return (default: 30, 0 = all)
    """
    data = api_get("/v1/data/compliant_total")
    data = trim(data, limit)
    lines = ["=== Compliant Exchange Total Assets ===\n"]
    if isinstance(data, list) and data:
        keys = [k for k in data[0].keys() if k != "date"]
        header = f"{'Date':<12}" + "".join(f"{k:>18}" for k in keys[:4])
        lines.append(header)
        lines.append("-" * (12 + 18 * min(len(keys), 4)))
        for row in data:
            line = f"{row.get('date', ''):<12}"
            for k in keys[:4]:
                v = row.get(k, "")
                try:
                    line += f"{float(v):>18,.2f}"
                except (ValueError, TypeError):
                    line += f"{str(v):>18}"
            lines.append(line)
    return "\n".join(lines)


@mcp.tool()
def get_us_treasury_yield(type: str = "1M", limit: int = 30) -> str:
    """Get US 10-year Treasury yield time series.

    Args:
        type: time range — 1D, 1W, 1M (default: 1M)
        limit: number of most recent data points (default: 30, 0 = all)
    """
    data = api_get("/v1/data/us10y", {"type": type})
    data = trim(data, limit)
    lines = [f"=== US 10Y Treasury Yield [{type}] ===\n"]
    lines.append(f"{'Date':<20} {'Yield (%)':>10}")
    lines.append("-" * 32)
    for row in (data if isinstance(data, list) else []):
        date = row.get("create_time") or row.get("date") or row.get("time", "")
        val = row.get("close") or row.get("value") or row.get("v", "")
        try:
            lines.append(f"{str(date):<20} {float(val):>10.4f}")
        except (ValueError, TypeError):
            lines.append(f"{str(date):<20} {str(val):>10}")
    return "\n".join(lines)


@mcp.tool()
def get_dxy_index(type: str = "1M", limit: int = 30) -> str:
    """Get US Dollar Index (DXY) time series.

    Args:
        type: time range — 1D, 1W, 1M (default: 1M)
        limit: number of most recent data points (default: 30, 0 = all)
    """
    data = api_get("/v1/data/dxy", {"type": type})
    data = trim(data, limit)
    lines = [f"=== DXY Dollar Index [{type}] ===\n"]
    lines.append(f"{'Date':<20} {'DXY':>10}")
    lines.append("-" * 32)
    for row in (data if isinstance(data, list) else []):
        date = row.get("create_time") or row.get("date") or row.get("time", "")
        val = row.get("close") or row.get("value") or row.get("v", "")
        try:
            lines.append(f"{str(date):<20} {float(val):>10.4f}")
        except (ValueError, TypeError):
            lines.append(f"{str(date):<20} {str(val):>10}")
    return "\n".join(lines)


@mcp.tool()
def get_m2_supply(type: str = "1Y", limit: int = 24) -> str:
    """Get global M2 money supply time series.

    Args:
        type: time range — 3M, 6M, 1Y, 3Y (default: 1Y)
        limit: number of most recent data points (default: 24, 0 = all)
    """
    data = api_get("/v1/data/m2_supply", {"type": type})
    data = trim(data, limit)
    lines = [f"=== Global M2 Money Supply [{type}] ===\n"]
    lines.append(f"{'Date':<20} {'M2 (T USD)':>12}  {'YoY'}")
    lines.append("-" * 42)
    for row in (data if isinstance(data, list) else []):
        date = row.get("date") or row.get("time", "")
        supply = row.get("supply") or row.get("close") or row.get("value") or row.get("v", "")
        yoy = row.get("yoy_growth", "")
        try:
            supply_t = float(supply) / 1e12
            yoy_s = f"{float(yoy):+.2f}%" if yoy else ""
            lines.append(f"{str(date):<20} {supply_t:>12.2f}  {yoy_s}")
        except (ValueError, TypeError):
            lines.append(f"{str(date):<20} {str(supply):>12}")
    return "\n".join(lines)


@mcp.tool()
def get_bitfinex_long_positions(
    symbol: str = "btc",
    type: str = "1D",
    limit: int = 30,
) -> str:
    """Get Bitfinex long position size for BTC or ETH (proxy for large-player sentiment).

    Args:
        symbol: btc or eth (default: btc)
        type: 1D, 1W, 1M, h24 (default: 1D; h24 is near real-time)
        limit: number of most recent data points (default: 30, 0 = all)
    """
    data = api_get("/v1/data/bitfinex_long", {"symbol": symbol, "type": type})
    data = trim(data, limit)
    lines = [f"=== Bitfinex {symbol.upper()} Long Positions [{type}] ===\n"]
    lines.append(f"{'Date':<24} {'Long Positions':>16} {'Price (USD)':>14}")
    lines.append("-" * 56)
    for row in (data if isinstance(data, list) else []):
        date = row.get("create_time") or row.get("date") or row.get("time", "")
        val = row.get("long") or row.get("close") or row.get("value") or row.get("v", "")
        price = row.get("price", "")
        try:
            price_str = f"{float(price):>14,.2f}"
        except (ValueError, TypeError):
            price_str = f"{str(price):>14}"
        try:
            lines.append(f"{str(date):<24} {float(val):>16,.0f} {price_str}")
        except (ValueError, TypeError):
            lines.append(f"{str(date):<24} {str(val):>16}")
    return "\n".join(lines)


@mcp.tool()
def get_contract_oi_data(dataType: str = "1D", limit: int = 30) -> str:
    """Get derivatives platform open interest data (Binance, Bybit, Hyperliquid).

    Args:
        dataType: time range — 1D, 1W, 1M, 3M, 6M, 12M (default: 1D)
        limit: number of most recent data points (default: 30, 0 = all)
    """
    data = api_get("/v1/data/contract", {"dataType": dataType})
    data = trim(data, limit)
    lines = [f"=== Derivatives Platform OI [{dataType}] ===\n"]
    if not isinstance(data, list) or not data:
        return "\n".join(lines)
    # Flat format: [{date, binance_open_interest, bybit_open_interest, hyperliquid_open_interest, ...}]
    PLATFORMS = [
        ("Binance",     "binance_open_interest",     "binance_volume"),
        ("Bybit",       "bybit_open_interest",        "bybit_volume"),
        ("Hyperliquid", "hyperliquid_open_interest",  "hyperliquid_volume"),
    ]
    lines.append(f"{'Date':<12} {'Platform':<14} {'OI (USD)':>18} {'Volume (USD)':>18}")
    lines.append("-" * 64)
    for row in data:
        date = row.get("date", "")
        for name, oi_key, vol_key in PLATFORMS:
            oi = row.get(oi_key, "")
            vol = row.get(vol_key, "")
            try:
                oi_s = f"{float(oi):>18,.0f}"
            except (ValueError, TypeError):
                oi_s = f"{str(oi):>18}"
            try:
                vol_s = f"{float(vol):>18,.0f}"
            except (ValueError, TypeError):
                vol_s = f"{str(vol):>18}"
            lines.append(f"{date:<12} {name:<14} {oi_s} {vol_s}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def get_sentiment_indicator() -> str:
    """Get market buy/sell sentiment indicator (composite of 11 sub-indicators).

    Interpretation:
    - Overall score < 20 → potential buy zone
    - Overall score > 80 → potential sell zone
    - Individual status: Buy / Hold / Sell
    """
    data = api_get("/v1/data/bottom_top_indicator")
    items = data if isinstance(data, list) else []
    lines = ["=== Market Sentiment Indicator ===\n"]
    buy_count = sum(1 for i in items if i.get("status") == "Buy")
    hold_count = sum(1 for i in items if i.get("status") == "Hold")
    sell_count = sum(1 for i in items if i.get("status") == "Sell")
    lines.append(f"Signal summary: {buy_count} Buy  /  {hold_count} Hold  /  {sell_count} Sell")
    if items:
        lines.append(f"Updated: {items[0].get('create_time', '')}")
    lines.append("")
    lines.append(f"{'Indicator':<45} {'Status'}")
    lines.append("-" * 55)
    for item in items:
        name = item.get("name", "")[:44]
        status = item.get("status", "")
        lines.append(f"{name:<45} {status}")
    return "\n".join(lines)


@mcp.tool()
def get_top10_netflow(network: str = "solana") -> str:
    """Get top 10 tokens by on-chain net inflow for a given network.

    Args:
        network: solana, base, or ethereum (default: solana)
    """
    data = api_get("/v1/data/top10_netflow", {"network": network})
    items = data if isinstance(data, list) else data.get("data", [])
    lines = [f"=== Top 10 On-chain Net Inflow [{network.capitalize()}] ===\n"]
    lines.append(f"{'#':<3} {'Token':<12} {'Net Inflow (USD)':>18} {'Market Cap':>16}")
    lines.append("-" * 52)
    for i, item in enumerate(items[:10], 1):
        symbol = item.get("tokenSymbol") or item.get("symbol") or item.get("name", "")
        inflow = item.get("netflow") or item.get("net_inflow") or item.get("inflow", "")
        mcap = item.get("marketCap") or item.get("market_cap") or item.get("marketcap", "")
        try:
            inflow_str = f"${float(inflow):>16,.0f}"
        except (ValueError, TypeError):
            inflow_str = f"{str(inflow):>18}"
        try:
            mcap_str = f"${float(mcap):>14,.0f}"
        except (ValueError, TypeError):
            mcap_str = f"{str(mcap):>16}"
        lines.append(f"{i:<3} {str(symbol):<12} {inflow_str} {mcap_str}")
    return "\n".join(lines)



if __name__ == "__main__":
    mcp.run()
