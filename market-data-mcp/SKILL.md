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
| `configure(finnhub_api_key, simfin_api_key)` | — | Save API keys |
| `get_quote(ticker)` | No | Current price, change%, volume, market cap |
| `get_stock_info(ticker)` | No | Company profile, PE, EPS, beta |
| `get_stock_history(ticker, period, interval)` | No | OHLCV history table |
| `get_financials(ticker, statement)` | No | Income/balance/cashflow statements |
| `get_analyst_recommendations(ticker)` | No | Buy/hold/sell counts + changes |
| `get_market_news(category)` | Yes | Latest market news (general/forex/crypto/merger) |
| `get_company_news(ticker, days)` | Yes | Company-specific news |
| `get_earnings_calendar(days_ahead)` | Yes | Upcoming earnings with estimates |
| `get_economic_calendar(days_ahead, country)` | Yes (premium) | Upcoming macro events: CPI, NFP, GDP, FOMC, PMI |
| `get_ipo_calendar(days_ahead)` | Yes | Upcoming IPO listings with price range and exchange |
| `get_dividend_calendar(ticker)` | No | Ex-dividend date, payment date, yield estimate |
| `get_options_expiry(ticker)` | No | Options expiration dates with call/put OI and P/C ratio |
| `get_news_sentiment(ticker)` | Yes | Buzz score + bullish/bearish % |
| `get_simfin_financials(ticker, statement, period)` | SimFin | Standardized cross-company financials |

## Usage Patterns

**Quick stock check (no API key):**
```
get_quote("NVDA") → get_stock_info("NVDA")
```

**Earnings research:**
```
get_earnings_calendar(14) → get_analyst_recommendations("AAPL") → get_news_sentiment("AAPL")
```

**Calendar suite:**
```
get_economic_calendar(7, "US") → get_ipo_calendar(30) → get_dividend_calendar("AAPL") → get_options_expiry("SPY")
```

**Historical analysis:**
```
get_stock_history("SPY", period="1y", interval="1wk")
```

## Notes
- yfinance data is 15-min delayed for US markets
- Finnhub free tier: 60 calls/minute
- SimFin free tier: 2000 req/day — register at https://simfin.com, then `configure(simfin_api_key=...)`
- `statement` values: `income`, `balance`, `cashflow`
- `period` values (history): `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`
- `period` values (SimFin): `ttm`, `q1`, `q2`, `q3`, `q4`, `fy`
- `interval` values: `1m`, `5m`, `15m`, `1h`, `1d`, `1wk`, `1mo`
