---
name: scrape-mcp
description: >
  Scrape financial data that has no public API: insider stock purchases/sales from
  OpenInsider, congressional stock trades from Capitol Trades, CME FedWatch
  Fed rate probability distributions, Circle USDC/EURC reserve transparency data,
  and The Block crypto news search. Uses Scrapling with stealth browser support.
---

# Financial Scraper MCP

Scrapling-based scrapers for data without public APIs.

## Setup

Scrapling is installed globally via uv (already done):
```bash
uv tool install "scrapling[all]>=0.4.2"
scrapling install  # installs Playwright browsers
```

`mcp[cli]` is declared inline (PEP 723) and resolved by Scrapling's own Python env.

**IMPORTANT:** Must use Scrapling's uv-managed Python (has all [all] extras + curl_cffi):
```json
{
  "financial-scraper": {
    "command": "/Users/eden/.local/share/uv/tools/scrapling/bin/python",
    "args": ["/Users/eden/crawl-x/scrape-mcp/server.py"]
  }
}
```

No environment variables required.

## Tools

| Tool | Scraping Method | Description |
|------|----------------|-------------|
| `get_insider_trades(ticker, trade_type, days)` | `Fetcher` (plain HTML) | OpenInsider: insider buy/sell activity |
| `get_congressional_trades(ticker, politician, days)` | `StealthyFetcher` + XHR | Capitol Trades: politician stock trades |
| `get_fed_rate_probabilities()` | `StealthyFetcher` + network interception | CME FedWatch: FOMC rate probabilities |
| `get_circle_reserves()` | `StealthyFetcher` | Circle: USDC/EURC circulation, reserves, mint/burn flows (7d/30d/365d) |
| `search_theblock(query, size, fetch_body)` | `requests` (plain JSON API) | The Block: search crypto news articles; optionally fetch full body of first result |

## Usage Patterns

**Insider activity research:**
```
get_insider_trades("NVDA", trade_type="P", days=30)
get_insider_trades("NVDA", trade_type="S", days=30)
```

**Political trading signals:**
```
get_congressional_trades(days=14)
get_congressional_trades(ticker="MSFT")
```

**Macro rate outlook:**
```
get_fed_rate_probabilities()
```

**Stablecoin reserve transparency:**
```
get_circle_reserves()
```

**Crypto news search:**
```
search_theblock("USDC stablecoin")
search_theblock("Bitcoin ETF", fetch_body=True)
```

## Notes
- OpenInsider: plain HTML, fast (~2s); Fetcher (no JS needed)
- Capitol Trades: React SPA, requires StealthyFetcher (~10-15s)
- CME FedWatch: Dynamic chart data via XHR; uses network interception pattern from fetch_utxo.py (~15-30s)
- Circle Transparency: StealthyFetcher + regex parsing; data as of last weekly update (~10s)
- The Block: plain JSON API (`requests`), fast (~1-2s); `fetch_body=True` adds a second request for full article text
- Browser launches on each call — expect 5-30s response times
- Targets may change their HTML structure; if parsing fails, raw text fallback is returned
