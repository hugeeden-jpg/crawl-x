---
name: news-mcp
description: >
  Search real-time global news and track sentiment timelines via GDELT and NewsAPI.org.
  Use for monitoring news coverage of stocks, companies, people, events, or countries.
  GDELT is free with no key required. NewsAPI requires a free key (100 req/day, no per-request limit).
---

# News MCP (GDELT + NewsAPI.org)

Provides global news search, top headlines, and sentiment analysis via two backends:
- **GDELT**: no API key, 100+ languages, 65+ countries — but **1 req/5s IP rate limit**
- **NewsAPI.org**: free key (newsapi.org/register), English-focused, 100 req/day, no per-request limit

## Setup

Dependencies are declared inline (PEP 723) — `uv run` installs them automatically on first use.

NewsAPI key configuration:
```
configure(newsapi_key="your_key_here")
# stored at ~/.config/news-mcp/config.json
```

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
| `configure(newsapi_key)` | Save NewsAPI.org key to local config |
| `search_newsapi(query, days, language, max_records, sort_by)` | Search articles via NewsAPI — no per-request rate limit |
| `get_top_headlines(category, country, query, max_records, sources)` | Top headlines by category/country or specific sources |
| `search_news(query, timespan, max_records)` | GDELT global news search (100+ languages) — 1 req/5s limit |
| `get_news_sentiment(query, timespan)` | GDELT daily sentiment timeline (tone score) — 1 req/5s limit |
| `batch_news(requests_json)` | Batch any mix of above; auto sleeps 5s around GDELT calls only |

## Usage Patterns

**Search recent news (NewsAPI, no rate limit):**
```
search_newsapi("NVIDIA earnings", days=3, max_records=20)
search_newsapi("Federal Reserve", days=7, sort_by="relevancy")
```

**Top US business headlines:**
```
get_top_headlines(category="business", country="us")
```

**Top headlines from specific sources:**
```
get_top_headlines(sources="bloomberg,reuters,the-wall-street-journal", query="Fed rate")
```

**Global news coverage (GDELT, multilingual):**
```
search_news("Apple Inc", timespan="7d", max_records=20)
```

**Sentiment timeline (GDELT):**
```
get_news_sentiment("Federal Reserve interest rate", timespan="14d")
get_news_sentiment("China trade war", timespan="30d")
```

**Batch fetch — mix sources freely:**
```
batch_news('[
  {"api": "get_top_headlines", "sources": "bloomberg,reuters", "query": "earnings"},
  {"api": "search_newsapi", "query": "NVIDIA", "days": 3},
  {"api": "search_news", "query": "Apple Inc", "timespan": "3d"},
  {"api": "get_news_sentiment", "query": "Federal Reserve", "timespan": "7d"}
]')
```

## Notes

**NewsAPI:**
- Free tier: 100 req/day (resets midnight UTC), no per-request rate limit
- `days` max = 30 (free tier history limit)
- `sort_by`: `publishedAt` (default), `relevancy`, `popularity`
- `get_top_headlines` `country` only supports `us`
- `sources` cannot be combined with `country` or `category`
- Common source IDs: `bloomberg`, `reuters`, `the-wall-street-journal`, `financial-times`, `cnbc`, `business-insider`, `fortune`, `financial-post`

**GDELT:**
- `timespan` values: `1d`, `3d`, `7d`, `14d`, `30d`
- Tone scale: positive = optimistic/bullish, negative = critical/bearish; typical financial range −5 to +2
- Updates every 15 minutes
- **Rate limit: 1 req/5s IP-based** — `batch_news` handles this automatically
