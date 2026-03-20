---
name: news-mcp
description: >
  Search real-time global news and track sentiment timelines via GDELT.
  Use for monitoring news coverage of stocks, companies, people, events, or countries.
  Free, no API key required. Covers 100+ languages and 65+ countries.
---

# News MCP (GDELT)

Provides global news search and sentiment analysis via the GDELT DOC API v2.
No API key required — free, but **rate limited: 1 request per 5 seconds per IP** (applies even when using MCP tools).

## Setup

Dependencies are declared inline (PEP 723) — `uv run` installs them automatically on first use.

Claude Desktop config:
```json
{
  "news-data": {
    "command": "uv",
    "args": ["run", "/Users/eden/crawl-x/news-mcp/server.py"]
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `search_news(query, timespan, max_records)` | Search news articles with title, source, URL |
| `get_news_sentiment(query, timespan)` | Daily sentiment timeline (tone score) |
| `batch_news(requests_json)` | Batch fetch multiple queries; auto rate-limits 5s between each request |

## Usage Patterns

**Track stock news coverage:**
```
search_news("Apple Inc", timespan="7d", max_records=20)
```

**Monitor sentiment around an event:**
```
get_news_sentiment("Federal Reserve interest rate", timespan="14d")
```

**Company earnings news:**
```
search_news("NVIDIA earnings", timespan="3d")
```

**Geopolitical events:**
```
get_news_sentiment("China trade war", timespan="30d")
```

**Batch fetch (multiple queries, auto rate-limited):**
```
batch_news('[
  {"api": "search_news", "query": "Apple Inc", "timespan": "3d", "max_records": 10},
  {"api": "get_news_sentiment", "query": "Federal Reserve", "timespan": "7d"},
  {"api": "search_news", "query": "NVIDIA earnings", "timespan": "1d"}
]')
```

## Notes
- `timespan` values: `1d`, `3d`, `7d`, `14d`, `30d`
- Tone scale: positive = optimistic/bullish coverage, negative = critical/bearish
- Typical tone range for financial news: −5 to +2
- GDELT updates every 15 minutes
- **Rate limit: 1 request per 5 seconds (IP-based)** — applies to all calls including MCP tool calls; avoid rapid sequential calls to prevent 429 errors
