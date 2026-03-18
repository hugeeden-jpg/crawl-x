---
name: crypto-mcp
description: >
  Cryptocurrency market data, DeFi analytics, and on-chain metrics.
  Use for crypto prices, global market overview, trending coins, DeFi protocol TVL,
  chain-level TVL, Glassnode on-chain metrics (active addresses, SOPR, exchange flows).
---

# Crypto Data MCP

Crypto market + DeFi + on-chain: CoinGecko, DeFi Llama, Glassnode.

## Setup

Dependencies are declared inline (PEP 723) — `uv run` installs them automatically on first use.

**CoinGecko:** Free Demo API key at https://www.coingecko.com/en/api (optional, removes rate limit)
**Glassnode:** API key at https://glassnode.com (free tier = limited metrics)

Claude Desktop config:
```json
{
  "crypto-data": {
    "command": "uv",
    "args": ["run", "/Users/eden/crawl-x/crypto-mcp/server.py"],
    "env": {
      "GLASSNODE_API_KEY": "...",
      "COINGECKO_API_KEY": ""
    }
  }
}
```

## Tools

| Tool | Key Required | Description |
|------|-------------|-------------|
| `configure(coingecko_api_key, glassnode_api_key)` | — | Save API keys |
| `get_crypto_price(coin_id)` | No | Price, 24h change%, market cap, volume |
| `get_crypto_market_data(coin_id)` | No | ATH, supply, multi-period returns |
| `get_global_market()` | No | Total market cap, BTC/ETH dominance |
| `get_trending_coins()` | No | Top 7 trending (most searched) |
| `get_defi_tvl_overview(limit)` | No | Top DeFi protocols by TVL |
| `get_protocol_tvl(protocol)` | No | Protocol TVL history + chain breakdown |
| `get_chain_tvl(chain)` | No | Blockchain TVL trend |
| `get_onchain_metric(metric, asset, since, until)` | Glassnode | Any Glassnode metric as time series |
| `get_exchange_flows(asset)` | Glassnode | Exchange inflow/outflow/netflow |

## Common coin_id values

| Name | coin_id |
|------|---------|
| Bitcoin | bitcoin |
| Ethereum | ethereum |
| Solana | solana |
| BNB | binancecoin |
| XRP | ripple |
| USDC | usd-coin |
| Cardano | cardano |

## Common Glassnode metrics

| Metric path | Description |
|-------------|-------------|
| `market/price_usd_close` | Daily close price |
| `addresses/active_count` | Active addresses |
| `transactions/count` | Transaction count |
| `indicators/sopr` | Spent Output Profit Ratio |
| `indicators/nupl` | Net Unrealized Profit/Loss |
| `supply/current` | Current circulating supply |
| `mining/hash_rate_mean` | Hash rate |

## Notes
- CoinGecko free tier: 30 calls/min (key adds to 500/min)
- DeFi Llama: free, no key, generous limits
- Glassnode free tier: daily resolution, limited metrics; advanced requires paid plan
- `since`/`until` accept ISO date strings: `"2024-01-01"`
