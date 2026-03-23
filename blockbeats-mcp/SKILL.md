---
name: blockbeats-skill
description: BlockBeats Skill covers over 1,500 information sources, including AI-driven insights, Hyperliquid on-chain data, and Polymarket market analytics. It also features robust keyword-based search functionality. Requires the blockbeats-mcp MCP server to be registered.
metadata:
  openclaw:
    emoji: "📰"
    requires:
      mcp:
        - blockbeats-mcp
    os:
      - darwin
      - linux
      - win32
    tags:
      - crypto
      - news
      - market-data
      - on-chain
      - defi
  version: 2.0.0
---

# BlockBeats API Skill

Query crypto newsflashes, articles, search results, and on-chain market data via the BlockBeats MCP server.

All tools are accessed through the `blockbeats-mcp` MCP server (prefix: `mcp__blockbeats-mcp__`). No direct HTTP calls or API keys are needed in tool calls — the MCP server handles authentication.

---

## Scenario 1: Market Overview

**Triggers**: How's the market today, market overview, daily summary, market conditions

Call the following four tools in parallel:

```
mcp__blockbeats-mcp__get_sentiment_indicator()
mcp__blockbeats-mcp__get_newsflash(category="important", size=5, lang="en")
mcp__blockbeats-mcp__get_btc_etf_flow()
mcp__blockbeats-mcp__get_daily_onchain_tx()
```

> **⚠ `get_daily_onchain_tx` returns a large payload** (multi-chain historical series, ~500KB+).
> For the Market Overview, **only read the last 2 entries** from each chain's `data` array to compute today's volume and day-over-day change. Do NOT attempt to display or summarize the full history.
>
> If the user asks for a deeper analysis or wants to inspect a specific chain's full trend, use the **write-to-file strategy** described in the Data Size Management section below.

**Output format**:
```
📊 Market Overview · [Today's date]

Sentiment Index: [value] → [<20 potential buy zone / 20-80 neutral / >80 potential sell zone]
BTC ETF: Today net inflow [value] million USD, cumulative [value] million
On-chain Volume: Today [value] (vs yesterday [↑/↓][change%])
Key News:
  · [Title 1] [time]
  · [Title 2] [time]
  · [Title 3] [time]
```

**Interpretation rules**:
- Sentiment < 20 → Alert user to potential opportunities
- Sentiment > 80 → Warn about sell-off risk
- ETF positive inflow 3 days in a row → Institutional accumulation signal
- ETF net inflow > 500M/day → Strong buy signal
- Rising on-chain volume → Increasing on-chain activity and market heat

---

## Scenario 2: Capital Flow Analysis

**Triggers**: Where is capital flowing, on-chain trends, which tokens are being bought, stablecoins, smart money

Call in parallel (select `network` based on user intent: `solana` / `base` / `ethereum`):

```
mcp__blockbeats-mcp__get_top10_netflow(network="solana")
mcp__blockbeats-mcp__get_stablecoin_marketcap()
mcp__blockbeats-mcp__get_btc_etf_flow()
```

**Output format**:
```
💰 Capital Flow Analysis

On-chain Trending ([chain]):
  1. [token] Net inflow $[value]  Market cap $[value]
  2. ...

Stablecoins: USDT [↑/↓] USDC [↑/↓] (expansion/contraction signal)
Institutional: ETF today [inflow/outflow] [value] million USD
```

**Interpretation rules**:
- Stablecoin market cap expanding → More capital in market, stronger buy potential
- Stablecoin market cap shrinking → Capital exiting, caution advised

---

## Scenario 3: Macro Environment Assessment

**Triggers**: Macro environment, is it a good time to enter, liquidity, US Treasuries, dollar, M2, big picture

Call in parallel:

```
mcp__blockbeats-mcp__get_m2_supply(type="1Y")
mcp__blockbeats-mcp__get_us_treasury_yield(type="1M")
mcp__blockbeats-mcp__get_dxy_index(type="1M")
mcp__blockbeats-mcp__get_compliant_exchange_total()
```

**Output format**:
```
🌐 Macro Environment Assessment

Global M2: [latest value] YoY [↑/↓][change%] → [expansionary/contractionary]
US Treasury Yield (10Y): [latest value]% → [rising/falling trend]
Dollar Index (DXY): [latest value] → [strong/weak]
Compliant Exchange Assets: $[value] → [inflow/outflow trend]

Overall: [bullish/neutral/bearish] for crypto market
```

**Interpretation rules**:
- M2 YoY > 5% → Loose liquidity, favorable for risk assets
- M2 YoY < 0% → Liquidity tightening, caution
- DXY rising → Strong dollar, crypto under pressure
- DXY falling → Weak dollar, crypto benefits
- Rising Treasury yield → Higher risk-free rate, capital returning to bonds
- Rising compliant exchange assets → Growing institutional allocation appetite

---

## Scenario 4: Derivatives Market Analysis

**Triggers**: Futures market, long/short positioning, open interest, Binance Bybit OI, leverage risk

Call in parallel:

```
mcp__blockbeats-mcp__get_contract_oi_data(dataType="1D")
mcp__blockbeats-mcp__get_bitfinex_long_positions(symbol="btc", type="1W", limit=3)
```

**Output format**:
```
⚡ Derivatives Market Analysis

Platform OI (latest):
  Binance OI $[value]  Vol $[value]
  Bybit   OI $[value]  Vol $[value]
  Hyperliquid OI $[value]  Vol $[value]

Bitfinex BTC Longs: [value] @ $[price] → [increasing/decreasing] (leveraged long sentiment [strong/weak])
```

> `get_contract_oi_data` returns rows: `Date | Platform | OI (USD) | Volume (USD)`. Read the most recent date's 3 rows for the snapshot above.

**Interpretation rules**:
- Bitfinex longs persistently increasing → Large players bullish, market confidence growing
- Bitfinex longs dropping sharply → Watch for long liquidation cascade

---

## Scenario 5: Keyword Search

**Triggers**: search [keyword], find [keyword], [keyword] news, what's happening with [keyword]

```
mcp__blockbeats-mcp__search_news(keyword="[keyword]", size=10, lang="en")
```

Response fields: `title`, `abstract`, `content` (plain text after HTML stripping), `type` (0=article, 1=newsflash), `time_cn` (relative time), `url`; pagination: `total`, `page`, `size`, `total_pages`; `size` max 100

---

## Scenario 6: Newsflash & Article Lists

Select the appropriate tool and `category` parameter based on user intent. Default `size=10`.

**Newsflash category mapping**:

| User says | Tool call |
|-----------|-----------|
| latest news / newsflash list / what's new | `mcp__blockbeats-mcp__get_newsflash(category="", size=10)` |
| last 24 hours / past 24h / today's all news | `mcp__blockbeats-mcp__get_newsflash_24h()` |
| important news / major events / key headlines | `mcp__blockbeats-mcp__get_newsflash(category="important")` |
| original newsflash / original coverage | `mcp__blockbeats-mcp__get_newsflash(category="original")` |
| first-report / exclusive / scoop | `mcp__blockbeats-mcp__get_newsflash(category="first")` |
| on-chain news / on-chain data updates | `mcp__blockbeats-mcp__get_newsflash(category="onchain")` |
| financing news / fundraising / VC deals | `mcp__blockbeats-mcp__get_newsflash(category="financing")` |
| prediction market / Polymarket / forecast | `mcp__blockbeats-mcp__get_newsflash(category="prediction")` |
| AI news / AI updates / AI projects | `mcp__blockbeats-mcp__get_newsflash(category="ai")` |

**Article category mapping**:

| User says | Tool call |
|-----------|-----------|
| article list / in-depth articles / latest articles | `mcp__blockbeats-mcp__get_articles(category="")` |
| last 24 hours articles / today's articles | `mcp__blockbeats-mcp__get_articles_24h()` |
| important articles / key reports | `mcp__blockbeats-mcp__get_articles(category="important")` |
| original articles / original analysis | `mcp__blockbeats-mcp__get_articles(category="original")` |

**Example call** (AI newsflash, latest 10 in English):

```
mcp__blockbeats-mcp__get_newsflash(category="ai", page=1, size=10, lang="en")
```

**Output format**:

```
📰 [Category Name] · Latest [N] items

1. [Title] [time_cn]
   [abstract, if available]

2. [Title] [time_cn]
   [abstract, if available]
...
```

**Notes**:
- `content` field is HTML; strip tags and display plain text only
- Article results use `link` for URL (not `url`)

---

## Tool Reference

### News & Search Tools

| Tool | Key Parameters | Description |
|------|---------------|-------------|
| `mcp__blockbeats-mcp__get_newsflash` | `category`, `page`, `size`, `lang` | Paginated newsflash list by category |
| `mcp__blockbeats-mcp__get_newsflash_24h` | `lang` | All newsflashes from last 24h (no pagination) |
| `mcp__blockbeats-mcp__get_articles` | `category`, `page`, `size`, `lang` | Paginated article list by category |
| `mcp__blockbeats-mcp__get_articles_24h` | `lang` | All articles from last 24h (no pagination, up to 50) |
| `mcp__blockbeats-mcp__search_news` | `keyword`, `page`, `size`, `lang` | Keyword search across all content |

### Market Data Tools

| Tool | Key Parameters | Description |
|------|---------------|-------------|
| `mcp__blockbeats-mcp__get_btc_etf_flow` | `limit` (default 30) | BTC ETF daily/cumulative net inflow |
| `mcp__blockbeats-mcp__get_daily_onchain_tx` | — | Daily on-chain tx volume. **⚠ Server writes full data to `/tmp/blockbeats_daily_tx.json`; returns compact summary only.** |
| `mcp__blockbeats-mcp__get_ibit_fbtc_flow` | `limit` (default 30) | IBIT and FBTC ETF net inflow (side-by-side) |
| `mcp__blockbeats-mcp__get_stablecoin_marketcap` | `limit` (default 30) | Stablecoin market cap history in **billions USD** (USDT, USDC, etc.) |
| `mcp__blockbeats-mcp__get_compliant_exchange_total` | `limit` (default 30) | Compliant exchange total asset holdings |
| `mcp__blockbeats-mcp__get_us_treasury_yield` | `type` (1W/1M), `limit` | US 10Y Treasury yield. Note: `1D` may return 500 if today's data is not yet available |
| `mcp__blockbeats-mcp__get_dxy_index` | `type` (1W/1M), `limit` | Dollar Index (DXY). Note: `1D` may return 500 if today's data is not yet available |
| `mcp__blockbeats-mcp__get_m2_supply` | `type` (3M/6M/1Y/3Y), `limit` | Global M2 money supply with YoY growth column |
| `mcp__blockbeats-mcp__get_bitfinex_long_positions` | `symbol` (btc/eth), `type` (1D/1W/1M/h24), `limit` | Bitfinex long positions with BTC price |
| `mcp__blockbeats-mcp__get_contract_oi_data` | `dataType` (1D/1W/1M/3M/6M/12M), `limit` | Derivatives OI by date: Binance / Bybit / Hyperliquid |
| `mcp__blockbeats-mcp__get_sentiment_indicator` | — | Market buy/sell sentiment indicator |
| `mcp__blockbeats-mcp__get_top10_netflow` | `network` (solana/base/ethereum) | Top 10 tokens by on-chain net inflow (tokenSymbol + marketCap) |

---

## Time Dimension Mapping

| User says | Parameter |
|-----------|-----------|
| today / latest / real-time | `type="1D"` or `size=5` |
| this week / recent | `type="1W"` |
| this month / last 30 days | `type="1M"` |
| this year / long-term trend | `type="1Y"` or `type="3Y"` |
| last 24 hours (bitfinex_long only) | `type="h24"` |

---

## Intent Mapping

| User intent | Tool / Scenario |
|-------------|----------------|
| How's the market today / daily overview | Scenario 1: Market Overview |
| Capital flow / on-chain trends / smart money | Scenario 2: Capital Flow |
| Macro / M2 / US Treasuries / good time to enter | Scenario 3: Macro Assessment |
| Futures / open interest / exchange OI / leverage risk | Scenario 4: Derivatives |
| search [keyword] | Scenario 5: `search_news` |
| Latest news / newsflash list | `get_newsflash(category="newsflash")` |
| Last 24 hours newsflashes | `get_newsflash_24h()` |
| Important newsflashes | `get_newsflash(category="important")` |
| Original / first-report / on-chain / financing / prediction / AI newsflashes | `get_newsflash(category=<type>)` |
| Article list | `get_articles(category="")` |
| Last 24 hours articles | `get_articles_24h()` |
| Important / original articles | `get_articles(category=<type>)` |
| BTC ETF inflow | `get_btc_etf_flow()` |
| IBIT FBTC | `get_ibit_fbtc_flow()` |
| Stablecoin market cap / USDT USDC | `get_stablecoin_marketcap()` |
| Dollar index / DXY | `get_dxy_index(type="1M")` |
| Bitfinex longs / leveraged positions | `get_bitfinex_long_positions(symbol="btc")` |
| Buy/sell signal / market sentiment | `get_sentiment_indicator()` |
| Top inflow tokens / on-chain trending | `get_top10_netflow(network="solana")` |
| On-chain volume / activity | `get_daily_onchain_tx()` |
| Compliant exchange assets / institutional custody | `get_compliant_exchange_total()` |

---

## Data Refresh Frequency

| Tool | Update frequency |
|------|-----------------|
| `get_newsflash` / `get_articles` / `search_news` | Real-time |
| `get_top10_netflow` | Near real-time |
| `get_btc_etf_flow` / `get_ibit_fbtc_flow` / `get_daily_onchain_tx` | Daily (T+1) |
| `get_stablecoin_marketcap` / `get_compliant_exchange_total` | Daily |
| `get_sentiment_indicator` | Daily |
| `get_us_treasury_yield` / `get_dxy_index` | Intraday minute-level |
| `get_m2_supply` | Monthly |
| `get_bitfinex_long_positions` | Daily (`type="h24"` is near real-time) |

---

## Data Size Management

### `get_daily_onchain_tx` — Large Response Handling

The full payload is ~500KB (multi-chain historical series). The MCP server handles this automatically:
- **Server writes** the full data to `/tmp/blockbeats_daily_tx.json` before returning
- **Tool returns** a compact summary table (~500 bytes) — top chains with latest date, tx count, and day-over-day change

**Strategy A — Overview (default for Scenario 1)**

Simply call the tool and read the compact summary it returns:

```
result = mcp__blockbeats-mcp__get_daily_onchain_tx()
# result is a compact table, e.g.:
# Chain       Latest Date   Transactions   vs Prev
# Solana      2026-03-22    110,234,567    +2.1%
# BNB Chain   2026-03-22     15,412,000    -0.8%
```

Display the top 3–5 chains from the returned summary.

**Strategy B — Deep Analysis (when user asks for trend/history of a specific chain)**

The full data is already on disk. Use Bash + jq to query it directly:

```bash
# Extract last 7 days for Solana
jq '.[] | select(.name=="solana") | .data[-7:]' /tmp/blockbeats_daily_tx.json
```

This avoids loading the full ~500KB into the active context window.

---

## Error Handling

| Condition | Response |
|-----------|----------|
| MCP tool returns error about missing API key | Prompt user to register blockbeats-mcp with a valid API key |
| Tool returns empty data array | Explain possible reasons: non-trading day, data delay, no data for this token |
| One parallel call fails | Display results from other calls; note which tool failed |

## Notes

- `content` field in newsflash/article responses is HTML; strip tags and display plain text only
- `create_time` field format: `Y-m-d H:i:s`
- Numeric fields (price/vol etc.) may be strings; format as numbers when displaying
- When running parallel tool calls, a failure on one must not block display of results from others
