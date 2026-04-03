---
name: polymarket-mcp
description: >
  Polymarket prediction market data — market search, event discovery, odds/probabilities,
  trading volume, liquidity, and trending markets. All via public Gamma API, no API key required.
---

# Polymarket MCP

Read-only access to Polymarket prediction markets via the public Gamma API. No API key or wallet required.

## Setup

```json
{
  "mcpServers": {
    "polymarket-mcp": {
      "command": "uv",
      "args": ["run", "/path/to/crawl-x/polymarket-mcp/server.py"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `search_markets(query, category, limit, active_only)` | Search markets by keyword via full-text search (Gamma `/public-search`); `category` used as `events_tag` filter when query provided |
| `get_market(market_id)` | Full details for a single market — outcomes, odds, all volume periods, description, event info |
| `get_events(query, category, limit, active_only)` | Event list (each event groups multiple related markets); keyword search + category filter |
| `get_trending_markets(period, category, limit)` | Top markets ranked by volume; period: `24h` / `7d` / `30d` / `all` |

**Key Required**: No

## Parameters

- `query` — keyword matching against question, description, slug (e.g. `"Trump"`, `"Bitcoin"`, `"FIFA"`)
- `category` — tag slug for filtering (e.g. `"politics"`, `"sports"`, `"crypto"`)
- `limit` — number of results, default 10, max 100
- `active_only` — exclude closed/resolved markets (default `true`)
- `period` — volume window for trending: `"24h"` (default), `"7d"`, `"30d"`, `"all"`

## Usage Patterns

**Check odds on a political event:**
```
search_markets(query="tariff") → pick market_id → get_market(market_id)
```

**Discover what's most traded today:**
```
get_trending_markets(period="24h", limit=10)
```

**Browse all active prediction events in sports:**
```
get_events(category="sports", limit=10)
```

**Deep-dive into an event's sub-markets:**
```
get_events(query="World Cup") → note event, markets listed inline
```

**Research crypto sentiment:**
```
search_markets(query="Bitcoin", category="crypto")
get_trending_markets(period="7d", category="crypto")
```

## Output Fields

Each market displays:
- **Odds** — outcome probabilities (YES/NO % or multi-outcome)
- **Vol 24h / Total** — USD trading volume
- **Liquidity** — current liquidity pool
- **Status** — `active` / `closed` / `archived`
- **Ends** — resolution date
- **URL** — direct Polymarket link

`get_market` additionally shows: full description, all 4 volume periods (24h/7d/30d/all), spread, event name.

## Notes

- Gamma API is public, no authentication needed
- **Keyword search**: `search_markets(query=...)` and `get_events(query=...)` use the official `/public-search` endpoint — real full-text search across all markets (not just top 500 by volume)
- **Category filtering**: pass `category` alongside `query` to filter by tag slug (e.g. `"sports"`, `"politics"`, `"crypto"`). Without a query, category uses client-side filtering for `get_events` and has no effect for `search_markets`
- **Vol 24h / Liquidity** may show `—` for markets returned by keyword search (fields not available in `/public-search` response; use `get_market(id)` for full stats)
- Odds are displayed as probabilities (0–100%), derived from CLOB order book prices
- Multi-outcome markets (e.g. "Who wins the World Cup?") show all outcome probabilities
