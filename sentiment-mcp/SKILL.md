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

**Reddit:** Create a "script" app at https://www.reddit.com/prefs/apps (no username needed)
**Quiver:** Free tier at https://www.quiverquant.com/

Claude Desktop config:
```json
{
  "sentiment-data": {
    "command": "uv",
    "args": ["run", "/Users/eden/crawl-x/sentiment-mcp/server.py"],
    "env": {
      "REDDIT_CLIENT_ID": "...",
      "REDDIT_CLIENT_SECRET": "...",
      "QUIVER_API_KEY": "..."
    }
  }
}
```

## Tools

| Tool | Key Required | Description |
|------|-------------|-------------|
| `configure(reddit_client_id, reddit_client_secret, quiver_api_key)` | — | Save credentials |
| `get_reddit_posts(subreddit, query, limit, sort)` | Reddit | Browse/search subreddit |
| `get_reddit_ticker_mentions(ticker, subreddits, hours)` | Reddit | Cross-subreddit ticker search |
| `get_fear_greed_index(days)` | No | Crypto Fear & Greed (1-30 days) |
| `get_congressional_trades(ticker, days)` | Quiver | Congressional stock trades |
| `get_wsb_mentions(ticker)` | Quiver | WSB mention count + rank |
| `get_insider_sentiment(ticker)` | Quiver | Insider buy/sell activity |

## Usage Patterns

**Retail sentiment check:**
```
get_reddit_ticker_mentions("TSLA", hours=48) → get_fear_greed_index(7)
```

**Crypto mood:**
```
get_fear_greed_index(7) → get_reddit_ticker_mentions("BTC", hours=24)
```

**Smart money tracking:**
```
get_congressional_trades(days=30) → get_insider_sentiment("NVDA")
```

## Notes
- Reddit: read-only script app, no user login needed
- Quiver free tier: limited calls/day
- Fear & Greed: Alternative.me, updates daily
