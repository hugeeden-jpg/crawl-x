---
name: cmc-mcp
description: >
  CoinMarketCap crypto data — market cap rankings, real-time quotes, global metrics,
  category/sector analysis, trending coins, and CMC Fear & Greed Index.
  Requires a free CMC API key.
---

# CoinMarketCap MCP

CoinMarketCap data: rankings, quotes, categories, trending, Fear & Greed. Different source from crypto-mcp (CoinGecko).

## Setup

Dependencies are declared inline (PEP 723) — `uv run` installs them automatically on first use.

Get a free API key at: https://coinmarketcap.com/api/ (Basic plan, no credit card)

Configure after install:
```
mcp__cmc-data__configure(cmc_api_key="your-key-here")
```

Claude Desktop config:
```json
{
  "cmc-data": {
    "command": "uv",
    "args": ["run", "/Users/eden/crawl-x/cmc-mcp/server.py"]
  }
}
```

## Tools

| Tool | Key Required | Description |
|------|-------------|-------------|
| `configure(cmc_api_key)` | — | Save CMC API key to `~/.config/cmc-mcp/config.json` |
| `get_listings(limit, sort, sort_dir)` | Yes | Top coins by market cap, volume, or 24h change |
| `get_quote(symbols)` | Yes | Real-time quotes for one or more coins (e.g. `"BTC,ETH,SOL"`) |
| `get_global_metrics()` | Yes | Total market cap, BTC/ETH dominance, DeFi, stablecoins, derivatives |
| `get_category_list()` | Yes | All CMC categories (DeFi, Layer-1, Meme, AI, etc.) with stats |
| `get_category(category_id)` | Yes | All coins in a category with performance data |
| `get_trending(limit)` | Yes | Currently trending coins on CMC |
| `get_fear_greed()` | Yes | CMC Fear & Greed Index — last 7 days |

## Usage Patterns

**Market overview:**
```
get_global_metrics() → get_listings(limit=20) → get_fear_greed()
```

**Sector rotation analysis:**
```
get_category_list() → get_category("605e2ce9d41eae1066535f7c")  # DeFi
```

**Multi-coin comparison:**
```
get_quote("BTC,ETH,SOL,BNB,XRP")
```

**Trend discovery:**
```
get_trending(20) → get_quote("PEPE,WIF,BONK")
```

## Notes
- vs `crypto-mcp` (CoinGecko): CMC has more complete category data and a native Fear & Greed index
- `get_fear_greed()` is CMC's own index; Alternative.me's index is in `sentiment-mcp`
- Free Basic plan: 10,000 credits/month (~300 req/day)
- `get_category_list()` returns category IDs needed for `get_category()`
