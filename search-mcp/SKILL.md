---
name: search-data
description: >
  Search Google to find real URLs when you don't know a website's address.
  Use this before guessing URLs or fetching unknown pages — search first, then fetch.
---

# search-data MCP — Google Search

## When to Use

Use the `search` tool whenever you need to find a URL you don't know, verify that a website exists, or discover relevant sources on a topic. **Always search first, then fetch** — never guess a URL.

Examples:
- "Find the official documentation for library X" → `search("library X official docs")`
- "What is the CoinGlass API endpoint?" → `search("CoinGlass API documentation")`
- "Latest news about topic Y" → `search("topic Y news 2025")`

## Tool

### `search`

Search Google and return ranked results with title, URL, and snippet.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | required | Search keywords |
| `num_results` | int | 10 | Number of results (max 50) |
| `language` | str | `"en"` | Result language, e.g. `"zh-CN"` |

**Returns:** Formatted string listing results, each with title, URL, and snippet.

**Example output:**
```
Search results for "scrapling python" (5 results):

1. scrapling · PyPI
   URL: https://pypi.org/project/scrapling/
   Snippet: Scrapling is a powerful, flexible, and high-performance...

2. D4Vinci/Scrapling: Undetectable Web Scraping Library
   URL: https://github.com/D4Vinci/Scrapling
   Snippet: A Python library that makes web scraping fast, reliable...
```

## Notes

- Powered by Scrapling `StealthyFetcher` — handles Google's anti-bot detection
- No API key required
- If Google returns a CAPTCHA page, the tool returns an error; retry after a short pause
