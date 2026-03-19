---
name: sentiment-mcp
description: >
  Social media sentiment and alternative data for financial markets. Use for
  Reddit discussions (WSB, r/stocks), Crypto Fear & Greed Index,
  congressional stock trades, and WSB mention tracking.
---

# Sentiment Data MCP

Social + alternative data: Reddit, Fear/Greed Index, Quiver Quantitative.

## Setup

Dependencies are declared inline (PEP 723) — `uv run` installs them automatically on first use.

**Quiver:** Free tier at https://www.quiverquant.com/quiverapi/

Claude Desktop config:
```json
{
  "sentiment-data": {
    "command": "uv",
    "args": ["run", "/Users/eden/crawl-x/sentiment-mcp/server.py"],
    "env": {
      "QUIVER_API_KEY": "..."
    }
  }
}
```

Or use the configure tool:
```
configure(quiver_api_key="...")
```

## Tools

| Tool | Key Required | Description |
|------|-------------|-------------|
| `configure(quiver_api_key)` | — | Save Quiver API key |
| `get_fear_greed_index(days)` | No | Crypto Fear & Greed (1-30 days) |
| `get_congressional_trades(ticker, days)` | Quiver | Congressional stock trades |
| `get_wsb_mentions(ticker)` | Quiver | WSB mention count + rank |
| `get_insider_sentiment(ticker)` | Quiver | Insider buy/sell activity |

## Usage Patterns

**Crypto mood:**
```
get_fear_greed_index(7)
```

**Smart money tracking:**
```
get_congressional_trades(days=30) → get_insider_sentiment("NVDA")
```

## Notes
- Quiver free tier: limited calls/day
- Fear & Greed: Alternative.me, updates daily
- Reddit data: use `social-data` MCP (public JSON API, no key needed)
