---
name: market-data-mcp
description: >
  Access real-time and historical stock market data. Use for stock quotes,
  price history, company financials, analyst recommendations, earnings calendars,
  and news sentiment. Powered by yfinance (free, 15-min delayed) and Finnhub.
---

# Market Data MCP

Provides stock market data via yfinance (no key) and Finnhub (key required for news/sentiment).

## Setup

Dependencies are declared inline (PEP 723) — `uv run` installs them automatically on first use.

Claude Desktop config:
```json
{
  "market-data": {
    "command": "uv",
    "args": ["run", "/Users/eden/crawl-x/market-data-mcp/server.py"],
    "env": {"FINNHUB_API_KEY": "your_key_here"}
  }
}
```

## Tools

| Tool | Key Required | Description |
|------|-------------|-------------|
| `configure(finnhub_api_key)` | — | Save Finnhub API key |
| `get_quote(ticker)` | No | Current price, change%, volume, market cap |
| `get_stock_info(ticker)` | No | Company profile, PE, EPS, beta |
| `get_stock_history(ticker, period, interval)` | No | OHLCV history table |
| `get_financials(ticker, statement)` | No | Income/balance/cashflow statements |
| `get_analyst_recommendations(ticker)` | No | Buy/hold/sell counts + changes |
| `get_market_news(category)` | Yes | Latest market news (general/forex/crypto/merger) |
| `get_company_news(ticker, days)` | Yes | Company-specific news |
| `get_earnings_calendar(days_ahead)` | Yes | Upcoming earnings with estimates |
| `get_news_sentiment(ticker)` | Yes | Buzz score + bullish/bearish % |

## Usage Patterns

**Quick stock check (no API key):**
```
get_quote("NVDA") → get_stock_info("NVDA")
```

**Earnings research:**
```
get_earnings_calendar(14) → get_analyst_recommendations("AAPL") → get_news_sentiment("AAPL")
```

**Historical analysis:**
```
get_stock_history("SPY", period="1y", interval="1wk")
```

## Notes
- yfinance data is 15-min delayed for US markets
- Finnhub free tier: 60 calls/minute
- `statement` values: `income`, `balance`, `cashflow`
- `period` values: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`
- `interval` values: `1m`, `5m`, `15m`, `1h`, `1d`, `1wk`, `1mo`
