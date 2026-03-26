---
name: binance-mcp
description: >
  Binance futures market data — funding rates, open interest, long/short ratios,
  liquidations, basis spread, top movers, and OHLCV klines. All via public Binance
  FAPI endpoints, no API key required.
---

# Binance Futures MCP

Real-time and historical Binance USD-M futures data. No API key required.

## Setup

Dependencies are declared inline (PEP 723) — `uv run` installs them automatically on first use.

Claude Desktop config:
```json
{
  "binance-mcp": {
    "command": "uv",
    "args": ["run", "/Users/eden/crawl-x/binance-mcp/server.py"]
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `get_funding_rate(symbol, limit)` | Current and historical funding rates (8h periods) |
| `get_open_interest(symbol, period, limit)` | Open interest history — contracts + USD value |
| `get_long_short_ratio(symbol, period, limit)` | Top trader long/short position ratio |
| `get_liquidations_summary(symbol)` | Recent forced liquidations — long/short totals |
| `get_market_stats(symbol)` | 24h price stats: price, change, high, low, volume |
| `get_top_movers(limit)` | Top gainers and losers across all USDT-M futures |
| `get_futures_kline(symbol, interval, limit)` | OHLCV candlestick data |
| `get_basis(symbol, period, limit)` | Futures basis vs spot index (premium/discount %) |

All tools: Key Required = **No**

## Symbol Format

- Input: `BTCUSDT`, `BTC`, `btc` — all accepted
- USDT appended automatically if no quote currency specified
- Examples: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `BNBUSDT`, `XRPUSDT`

## Usage Patterns

**Market structure overview:**
```
get_funding_rate("BTCUSDT") → get_open_interest("BTCUSDT") → get_long_short_ratio("BTCUSDT")
```

**Squeeze risk check:**
```
get_liquidations_summary("BTCUSDT") → get_funding_rate("BTCUSDT", limit=30)
```

**Basis / carry trade:**
```
get_basis("BTCUSDT", period="1d", limit=30)
```

**Daily briefing:**
```
get_top_movers(20) → get_market_stats("BTCUSDT")
```

## Notes
- Data source: Binance FAPI v1/v2 (USD-M perpetuals)
- `get_long_short_ratio` shows *top trader* account positions, not all traders
- Funding rate > 0 = longs pay shorts (bullish sentiment); < 0 = shorts pay longs
- Basis > 0 = futures premium (contango); < 0 = backwardation
