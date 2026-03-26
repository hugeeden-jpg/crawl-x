# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
# ]
# ///

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from ssl_utils import apply_ssl_fix
    apply_ssl_fix()
except ImportError:
    pass

import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cmc-data")

CONFIG_FILE = Path.home() / ".config" / "cmc-mcp" / "config.json"
BASE = "https://pro-api.coinmarketcap.com/v1"
BASE_V2 = "https://pro-api.coinmarketcap.com/v2"

def load_config() -> dict:
    cfg = {"cmc_api_key": os.environ.get("CMC_API_KEY", "")}
    if CONFIG_FILE.exists():
        file_cfg = json.loads(CONFIG_FILE.read_text())
        if not cfg["cmc_api_key"]:
            cfg["cmc_api_key"] = file_cfg.get("cmc_api_key", "")
    return cfg

def cmc_get(path: str, params: dict = None, version: int = 1) -> dict:
    cfg = load_config()
    api_key = cfg.get("cmc_api_key", "")
    if not api_key:
        raise ValueError("CMC API key not set. Run configure() tool first.")
    base = BASE if version == 1 else BASE_V2
    r = requests.get(
        f"{base}{path}",
        headers={"X-CMC_PRO_API_KEY": api_key, "Accept": "application/json"},
        params=params,
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("status", {}).get("error_code", 0) != 0:
        raise ValueError(data["status"].get("error_message", "CMC API error"))
    return data


# ── Tools ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def configure(cmc_api_key: str) -> str:
    """Save CoinMarketCap API key. Get a free key at https://coinmarketcap.com/api/

    Args:
        cmc_api_key: Your CMC Pro API key (free tier is sufficient for most tools)
    """
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps({"cmc_api_key": cmc_api_key}, indent=2))
        return f"CMC API key saved to {CONFIG_FILE}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_listings(limit: int = 50, sort: str = "market_cap", sort_dir: str = "desc") -> str:
    """Get top cryptocurrencies by market cap, volume, or other metrics.

    Args:
        limit: Number of coins to return (max 5000 with paid plan, 200 free)
        sort: Sort field — 'market_cap', 'volume_24h', 'percent_change_24h',
              'percent_change_7d', 'market_cap_strict'
        sort_dir: 'asc' or 'desc'
    """
    try:
        data = cmc_get("/cryptocurrency/listings/latest", {
            "limit": limit, "sort": sort, "sort_dir": sort_dir,
            "convert": "USD",
        })
        coins = data["data"]
        lines = [f"CoinMarketCap Top {limit} — sorted by {sort}", "=" * 80,
                 f"{'#':<5} {'Symbol':<10} {'Name':<22} {'Price':>12} {'24h%':>8} {'7d%':>8} {'Mkt Cap':>14} {'Vol 24h':>14}"]
        for c in coins:
            rank   = c.get("cmc_rank", "")
            sym    = c.get("symbol", "")
            name   = c.get("name", "")[:20]
            q      = c.get("quote", {}).get("USD", {})
            price  = q.get("price", 0)
            chg24  = q.get("percent_change_24h", 0) or 0
            chg7   = q.get("percent_change_7d", 0) or 0
            mcap   = q.get("market_cap", 0) or 0
            vol    = q.get("volume_24h", 0) or 0
            price_fmt = f"${price:,.4f}" if price < 1 else f"${price:,.2f}"
            lines.append(
                f"{rank:<5} {sym:<10} {name:<22} {price_fmt:>12} {chg24:>+7.1f}% {chg7:>+7.1f}% "
                f"${mcap/1e9:>12,.1f}B ${vol/1e6:>12,.0f}M"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_quote(symbols: str) -> str:
    """Get latest price and market data for one or more cryptocurrencies.

    Args:
        symbols: Comma-separated ticker symbols, e.g. 'BTC,ETH,SOL,BNB'
    """
    try:
        data = cmc_get("/cryptocurrency/quotes/latest", {"symbol": symbols.upper(), "convert": "USD"})
        lines = [f"CMC Quotes — {symbols.upper()}", "=" * 70]
        for sym, coin_list in data["data"].items():
            if isinstance(coin_list, list):
                coin = coin_list[0]
            else:
                coin = coin_list
            q     = coin.get("quote", {}).get("USD", {})
            name  = coin.get("name", "")
            rank  = coin.get("cmc_rank", "")
            price = q.get("price", 0)
            chg1h  = q.get("percent_change_1h", 0) or 0
            chg24  = q.get("percent_change_24h", 0) or 0
            chg7d  = q.get("percent_change_7d", 0) or 0
            chg30d = q.get("percent_change_30d", 0) or 0
            mcap   = q.get("market_cap", 0) or 0
            vol    = q.get("volume_24h", 0) or 0
            dom    = q.get("market_cap_dominance", 0) or 0
            supply = coin.get("circulating_supply", 0) or 0
            max_supply = coin.get("max_supply")

            lines += [
                f"\n{sym} — {name} (Rank #{rank})",
                f"  {'Price:':<22} ${price:,.4f}" if price < 1 else f"  {'Price:':<22} ${price:,.2f}",
                f"  {'Change 1h/24h/7d/30d:':<22} {chg1h:+.1f}% / {chg24:+.1f}% / {chg7d:+.1f}% / {chg30d:+.1f}%",
                f"  {'Market Cap:':<22} ${mcap/1e9:.2f}B",
                f"  {'Volume 24h:':<22} ${vol/1e6:.1f}M",
                f"  {'Dominance:':<22} {dom:.2f}%",
                f"  {'Circulating Supply:':<22} {supply:,.0f} {sym}",
                f"  {'Max Supply:':<22} {f'{max_supply:,.0f}' if max_supply else 'Unlimited'}",
            ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_global_metrics() -> str:
    """Get global cryptocurrency market metrics: total market cap, BTC dominance, DeFi, stablecoins, etc."""
    try:
        data = cmc_get("/global-metrics/quotes/latest", {"convert": "USD"})
        d = data["data"]
        q = d.get("quote", {}).get("USD", {})

        total_mcap  = q.get("total_market_cap", 0)
        total_vol   = q.get("total_volume_24h", 0)
        btc_dom     = d.get("btc_dominance", 0)
        eth_dom     = d.get("eth_dominance", 0)
        defi_mcap   = q.get("defi_market_cap", 0)
        defi_vol    = q.get("defi_volume_24h", 0)
        defi_dom    = q.get("defi_24h_percentage_change", 0)
        stbl_mcap   = q.get("stablecoin_market_cap", 0)
        stbl_vol    = q.get("stablecoin_volume_24h", 0)
        derivatives_vol = q.get("derivatives_volume_24h", 0)
        active_coins = d.get("active_cryptocurrencies", 0)
        active_pairs = d.get("active_market_pairs", 0)

        lines = [
            "Global Crypto Market Metrics",
            "=" * 45,
            f"{'Total Market Cap:':<28} ${total_mcap/1e12:.3f}T",
            f"{'Total Volume 24h:':<28} ${total_vol/1e9:.1f}B",
            f"{'BTC Dominance:':<28} {btc_dom:.2f}%",
            f"{'ETH Dominance:':<28} {eth_dom:.2f}%",
            f"{'DeFi Market Cap:':<28} ${defi_mcap/1e9:.1f}B",
            f"{'DeFi Volume 24h:':<28} ${defi_vol/1e9:.1f}B",
            f"{'Stablecoin Market Cap:':<28} ${stbl_mcap/1e9:.1f}B",
            f"{'Stablecoin Volume 24h:':<28} ${stbl_vol/1e9:.1f}B",
            f"{'Derivatives Volume 24h:':<28} ${derivatives_vol/1e9:.1f}B",
            f"{'Active Cryptocurrencies:':<28} {active_coins:,}",
            f"{'Active Trading Pairs:':<28} {active_pairs:,}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_category_list() -> str:
    """List all available cryptocurrency categories (sectors) on CoinMarketCap: DeFi, Layer-1, Meme, etc."""
    try:
        data = cmc_get("/cryptocurrency/categories")
        cats = data.get("data", [])
        lines = [f"CMC Categories ({len(cats)} total)", "=" * 65,
                 f"{'ID':<10} {'Name':<35} {'#Coins':>8} {'Avg Chg 24h':>12} {'Mkt Cap':>14}"]
        for c in cats:
            cid    = c.get("id", "")
            name   = c.get("name", "")[:33]
            coins  = c.get("num_tokens", 0)
            chg    = c.get("avg_price_change", 0) or 0
            mcap   = c.get("market_cap", 0) or 0
            lines.append(f"{cid:<10} {name:<35} {coins:>8,} {chg:>+11.1f}% ${mcap/1e9:>12,.1f}B")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_category(category_id: str) -> str:
    """Get all coins and their performance within a specific CMC category.

    Args:
        category_id: Category ID from get_category_list(), e.g. '605e2ce9d41eae1066535f7c' for DeFi
    """
    try:
        data = cmc_get("/cryptocurrency/category", {"id": category_id, "convert": "USD"})
        cat = data.get("data", {})
        name     = cat.get("name", "")
        desc     = cat.get("description", "")
        coins    = cat.get("coins", [])
        avg_chg  = cat.get("avg_price_change", 0) or 0
        mcap     = cat.get("market_cap", 0) or 0
        vol      = cat.get("volume", 0) or 0

        lines = [
            f"CMC Category: {name}",
            f"{desc[:120] + '...' if len(desc) > 120 else desc}",
            "=" * 70,
            f"{'Avg 24h Change:':<22} {avg_chg:+.2f}%",
            f"{'Market Cap:':<22} ${mcap/1e9:.2f}B",
            f"{'Volume 24h:':<22} ${vol/1e6:.0f}M",
            "",
            f"{'#':<5} {'Symbol':<10} {'Name':<22} {'Price':>12} {'24h%':>8} {'7d%':>8} {'Mkt Cap':>14}",
            "-" * 80,
        ]
        for i, c in enumerate(coins[:50], 1):
            q = c.get("quote", {}).get("USD", {})
            price  = q.get("price", 0) or 0
            chg24  = q.get("percent_change_24h", 0) or 0
            chg7   = q.get("percent_change_7d", 0) or 0
            mcap_c = q.get("market_cap", 0) or 0
            price_fmt = f"${price:,.4f}" if price < 1 else f"${price:,.2f}"
            lines.append(
                f"{i:<5} {c.get('symbol',''):<10} {c.get('name','')[:20]:<22} "
                f"{price_fmt:>12} {chg24:>+7.1f}% {chg7:>+7.1f}% ${mcap_c/1e9:>12,.2f}B"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_trending(limit: int = 20) -> str:
    """Get currently trending cryptocurrencies on CoinMarketCap.

    Args:
        limit: Number of trending coins to return
    """
    try:
        data = cmc_get("/cryptocurrency/trending/latest", {"limit": limit, "convert": "USD"})
        coins = data.get("data", [])
        lines = [f"CMC Trending Cryptocurrencies (Top {limit})", "=" * 70,
                 f"{'#':<5} {'Symbol':<10} {'Name':<22} {'Price':>12} {'24h%':>8} {'7d%':>8} {'Mkt Cap':>14}"]
        for i, c in enumerate(coins, 1):
            q      = c.get("quote", {}).get("USD", {})
            price  = q.get("price", 0) or 0
            chg24  = q.get("percent_change_24h", 0) or 0
            chg7   = q.get("percent_change_7d", 0) or 0
            mcap   = q.get("market_cap", 0) or 0
            price_fmt = f"${price:,.4f}" if price < 1 else f"${price:,.2f}"
            lines.append(
                f"{i:<5} {c.get('symbol',''):<10} {c.get('name','')[:20]:<22} "
                f"{price_fmt:>12} {chg24:>+7.1f}% {chg7:>+7.1f}% ${mcap/1e9:>12,.2f}B"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_fear_greed() -> str:
    """Get the CoinMarketCap Fear & Greed Index (current and recent history)."""
    try:
        data = cmc_get("/fear-and-greed/historical", {"limit": 7})
        entries = data.get("data", [])

        lines = ["CMC Fear & Greed Index", "=" * 40]
        for e in entries:
            value     = e.get("value", 0)
            category  = e.get("value_classification", "")
            timestamp = e.get("timestamp", "")[:10]
            bar = "█" * (value // 5) + "░" * (20 - value // 5)
            lines.append(f"{timestamp}  [{bar}] {value:>3}/100  {category}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
