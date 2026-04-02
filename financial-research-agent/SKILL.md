---
name: financial-research-agent
description: >
  Master financial research agent with access to stock market data, macroeconomic
  indicators, social sentiment, crypto/DeFi analytics, SEC filings, and scraped
  financial data. Use this skill to answer any question about stocks, crypto, macro,
  Fed policy, insider trading, congressional trades, or market sentiment.
---

# Financial Research Agent

Full-stack financial research via 13 MCP servers.

## MCP Ecosystem Map

| MCP Server | Data Sources | Use For |
|------------|-------------|---------|
| `grok-news` | X/Twitter via Grok AI | AI-synthesized X sentiment, trend analysis (requires XAI key, optional) |
| `market-data` | yfinance + Finnhub + SimFin | Stock quotes, history, financials, earnings, standardized cross-company statements |
| `macro-data` | FRED + BLS + US Treasury + SEC EDGAR | Fed rates, CPI/PPI/NFP/JOLTS (BLS direct), full yield curve, TGA balance, treasury auctions, Fed balance sheet, XBRL facts, insider Form 4 |
| `news-data` | GDELT + NewsAPI.org | Global news search, top headlines, sentiment timeline. GDELT free; NewsAPI free key (100 req/day) |
| `sentiment-data` | Alternative.me + Quiver | Fear/Greed, congressional trades, insider sentiment |
| `crypto-data` | CoinGecko + DeFi Llama + Glassnode | Crypto prices, DeFi TVL, on-chain metrics |
| `financial-scraper` | OpenInsider + Capitol Trades + CME FedWatch + Circle + The Block + QuiverQuant | Insider trades, political trades, rate probabilities, USDC reserves, crypto news, congress trading chart |
| `social-data` | Reddit (public JSON) + Twitter/X (xreach) + YouTube (yt-dlp) | Raw social posts, WSB, KOL timelines, earnings transcripts |
| `blockbeats-mcp` | BlockBeats Pro API | Crypto newsflash/articles, keyword search, BTC ETF flows, on-chain tx, stablecoin market cap, derivatives OI, macro (M2/DXY/treasury), sentiment indicator |
| `binance-mcp` | Binance FAPI (public) | Futures funding rates, open interest, long/short ratio, liquidations, basis, top movers, OHLCV |
| `cmc-data` | CoinMarketCap | Crypto rankings, real-time quotes, global metrics, category/sector analysis, trending coins, CMC Fear & Greed |
| `wikipedia-data` | English Wikipedia | Factual lookups, concept background, company/person profiles, geographic coordinates, article deep-dives (full text cached locally) |
| `search-data` | Google (Scrapling) | Find real URLs by keyword — use before fetching any unknown page |

## API Key Configuration

All API keys are stored in `~/.config/<mcp>/config.json`. Use the `configure()` tool of each MCP, or run `bash ~/crawl-x/install.sh` to set them interactively.

| MCP | Key | Config File | Required | Get It |
|-----|-----|-------------|----------|--------|
| `macro-data` | `fred_api_key` | `~/.config/macro-mcp/config.json` | **Required** | https://fred.stlouisfed.org/docs/api/api_key.html |
| `market-data` | `finnhub_api_key` | `~/.config/market-data-mcp/config.json` | Optional | https://finnhub.io/register |
| `market-data` | `simfin_api_key` | `~/.config/market-data-mcp/config.json` | Optional | https://simfin.com (free tier: 2000 req/day) |
| `grok-news` | `api_key` (XAI) | `~/.config/grok-mcp/config.json` | Optional | https://console.x.ai/ |
| `sentiment-data` | `quiver_api_key` | `~/.config/sentiment-mcp/config.json` | Optional | https://www.quiverquant.com/quiverapi/ |
| `crypto-data` | `coingecko_api_key` | `~/.config/crypto-mcp/config.json` | Optional | https://www.coingecko.com/en/api |
| `crypto-data` | `glassnode_api_key` | `~/.config/crypto-mcp/config.json` | Optional | https://glassnode.com |
| `social-data` | `auth_token` + `ct0` | `~/.config/social-mcp/config.json` | Optional | x.com cookies — use **Cookie Picker** extension (`extensions/cookie-picker/`), load unpacked in Chrome, open on x.com, `auth_token` + `ct0` are pre-selected; also install xreach: `npm install -g xreach-cli` |
| `news-data` | `newsapi_key` | `~/.config/news-mcp/config.json` | Optional | https://newsapi.org/register — free (100 req/day) |
| `blockbeats-mcp` | `api_key` | `~/.config/blockbeats-mcp/config.json` | Optional | https://www.theblockbeats.info/ — BlockBeats Pro subscription |
| `macro-data` | `bls_api_key` | `~/.config/macro-mcp/config.json` | Optional | https://www.bls.gov/developers/ — free registration |
| `cmc-data` | `cmc_api_key` | `~/.config/cmc-mcp/config.json` | Optional | https://coinmarketcap.com/api/ — free Basic plan |

**Without any keys:** `macro-data` (FRED) is the only hard requirement. `crypto-data`, `financial-scraper`, and `social-data` (Reddit/YouTube) all work without keys.

**Quick config via tool call:**
```
macro-data:     configure(fred_api_key="...")
market-data:    configure(finnhub_api_key="...", simfin_api_key="...")
grok-news:      configure(api_key="xai-...")
sentiment-data: configure(quiver_api_key="...")
crypto-data:    configure(coingecko_api_key="...", glassnode_api_key="...")
social-data:    configure_twitter(auth_token="...", ct0="...")
news-data:      configure(newsapi_key="...")
blockbeats-mcp: configure(api_key="...")
macro-data:     configure_bls(bls_api_key="...")
cmc-data:       configure(cmc_api_key="...")
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "grok-news":         {"command": "uv", "args": ["run", "/path/to/crawl-x/grok-mcp/server.py"]},
    "market-data":       {"command": "uv", "args": ["run", "/path/to/crawl-x/market-data-mcp/server.py"]},
    "macro-data":        {"command": "uv", "args": ["run", "/path/to/crawl-x/macro-mcp/server.py"]},
    "sentiment-data":    {"command": "uv", "args": ["run", "/path/to/crawl-x/sentiment-mcp/server.py"]},
    "crypto-data":       {"command": "uv", "args": ["run", "/path/to/crawl-x/crypto-mcp/server.py"]},
    "financial-scraper": {"command": "uv", "args": ["run", "/path/to/crawl-x/scrape-mcp/server.py"]},
    "social-data":       {"command": "uv", "args": ["run", "/path/to/crawl-x/social-mcp/server.py"]},
    "news-data":         {"command": "uv", "args": ["run", "/path/to/crawl-x/news-mcp/server.py"]},
    "blockbeats-mcp":    {"command": "uv", "args": ["run", "/path/to/crawl-x/blockbeats-mcp/server.py"]},
    "binance-mcp":       {"command": "uv", "args": ["run", "/path/to/crawl-x/binance-mcp/server.py"]},
    "cmc-data":          {"command": "uv", "args": ["run", "/path/to/crawl-x/cmc-mcp/server.py"]},
    "search-data":       {"command": "uv", "args": ["run", "/path/to/crawl-x/search-mcp/server.py"]}
  }
}
```

> **No `env` fields needed.** All API keys are stored in `~/.config/<mcp>/config.json` by `install.sh`.
> Replace `/path/to/crawl-x` with the actual repo path, or run `bash install.sh --desktop` to auto-generate this file.
```

## MCP Decision Tree

**General rule — unknown URLs or web content not covered by any MCP:**
> 1. **`search-data` → `search(keywords)`** — find real URLs via Google; never guess or hardcode a URL
> 2. **`ScraplingServer` → `fetch(url)` / `stealthy_fetch(url)`** — read the page content as needed

**Question type → MCP to use:**

- "What is the stock price / market cap / PE ratio of X?" → `market-data` → `get_quote`, `get_stock_info`
- "Show me the price history / chart of X" → `market-data` → `get_stock_history`
- "What do analysts say about X?" → `market-data` → `get_analyst_recommendations`, `get_news_sentiment`
- "What are the latest earnings for X?" → `market-data` → `get_earnings_calendar`, `get_financials`
- "What economic events are coming up? CPI / NFP / FOMC this week?" → `market-data` → `get_economic_calendar` (no key required — Investing.com)
- "What IPOs are coming up?" → `market-data` → `get_ipo_calendar`
- "When does AAPL go ex-dividend? What is the yield?" → `market-data` → `get_dividend_calendar("AAPL")`
- "What stocks go ex-dividend this week? Show me dividend calendar." → `market-data` → `get_dividend_calendar(timeframe="thisWeek", country="US")`
- "What are the options expiry dates for SPY? What is the put/call ratio?" → `market-data` → `get_options_expiry`
- "What is the analyst price target for X? What is the upside?" → `market-data` → `get_price_target`
- "How much short interest does X have? Is it a short squeeze candidate?" → `market-data` → `get_short_interest`
- "Show me the options chain for X / what strikes have the most OI / where is Max Pain?" → `market-data` → `get_options_chain(ticker, expiry)`
- "What is the Fed doing / interest rates / inflation?" → `macro-data` → `get_key_indicators`, `get_fred_data`
- "What is X's 10-K / 10-Q / SEC filing?" → `macro-data` → `search_edgar_company`, `get_recent_filings`
- "Who owns what? What did fund X buy?" → `macro-data` → `get_13f_holdings`
- "What is Reddit / WSB saying about X?" → `social-data` → `search_reddit(query, subreddit="wallstreetbets")` (not sentiment-data)
- "Is the crypto market fearful or greedy?" → `sentiment-data` → `get_fear_greed_index`
- "What are politicians buying/selling?" → `sentiment-data` → `get_congressional_trades` OR `financial-scraper` → `get_congressional_trades`
- "Show me a chart of congressional trades for X / did politicians trade before the price moved?" → `financial-scraper` → `get_quiverquant_congress(ticker)` — produces interactive HTML chart (opens in browser) + CSV with full history
- "Find the URL / homepage / docs / API endpoint for X" → **`search-data` → `search(query)` FIRST**, then `ScraplingServer` → `fetch/stealthy_fetch(url)` to read the page — never guess URLs
- "What is X trading for? What is Bitcoin doing?" → `crypto-data` → `get_crypto_price`, `get_global_market`
- "What is DeFi TVL? What is Uniswap's TVL?" → `crypto-data` → `get_defi_tvl_overview`, `get_protocol_tvl`
- "What are on-chain signals for BTC/ETH?" → `crypto-data` → `get_onchain_metric`, `get_exchange_flows`
- "What is X/Twitter saying about $TICKER?" → `social-data` → `search_tweets(query)` (raw); `grok-news` → `get_ticker_sentiment` (AI synthesis, needs XAI key)
- "What did [KOL] post recently?" → `social-data` → `get_user_timeline(username)`
- "What is the overall X sentiment narrative?" → `grok-news` → `search_x_news`, `get_ticker_sentiment` (needs XAI key)
- "Are insiders buying or selling X?" → `financial-scraper` → `get_insider_trades`
- "What are Fed rate hike probabilities?" → `financial-scraper` → `get_fed_rate_probabilities`
- "What are USDC/EURC reserves? Circle transparency?" → `financial-scraper` → `get_circle_reserves`
- "Find The Block articles about X / crypto news?" → `financial-scraper` → `search_theblock`
- "What is the stablecoin market? USDT vs USDC supply?" → `crypto-data` → `get_stablecoins`
- "USDC chain distribution / supply history?" → `crypto-data` → `get_stablecoin_detail`
- "What are the best DeFi yields / lending rates?" → `crypto-data` → `get_yields`
- "All chains TVL ranking?" → `crypto-data` → `get_all_chains`
- "Get the earnings call transcript for X" → `social-data` → `search_youtube(query)` → `get_video_transcript(url)`
- "Search global/multilingual news about X" → `news-data` → `search_news(query)` (GDELT, 100+ languages)
- "Search English news about X with no rate limit" → `news-data` → `search_newsapi(query, days)` (NewsAPI)
- "Top US business/tech/finance headlines" → `news-data` → `get_top_headlines(category, country)` or `get_top_headlines(sources="bloomberg,reuters")`
- "What is the news sentiment trend for X?" → `news-data` → `get_news_sentiment(query)` (GDELT)
- "Fetch news for multiple topics at once" → `news-data` → `batch_news(requests_json)` (auto rate-limits GDELT calls; no delay for NewsAPI)
- "Get standardized financials / compare income statements across companies?" → `market-data` → `get_simfin_financials(ticker, statement, period)`
- "Crypto market overview / daily market summary / how's the market today?" → `blockbeats-mcp` → `get_sentiment_indicator`, `get_newsflash(category="important")`, `get_btc_etf_flow`
- "BTC ETF inflow / IBIT FBTC flows?" → `blockbeats-mcp` → `get_btc_etf_flow`, `get_ibit_fbtc_flow`
- "On-chain transaction volume / daily tx by chain?" → `blockbeats-mcp` → `get_daily_onchain_tx`
- "Stablecoin market cap / USDT USDC supply trend?" → `blockbeats-mcp` → `get_stablecoin_marketcap`
- "M2 money supply / DXY dollar index / US 10Y treasury?" → `blockbeats-mcp` → `get_m2_supply`, `get_dxy_index`, `get_us_treasury_yield`
- "Derivatives OI / Binance Bybit open interest / Hyperliquid OI?" → `blockbeats-mcp` → `get_contract_oi_data`
- "Bitfinex longs / leveraged long positions?" → `blockbeats-mcp` → `get_bitfinex_long_positions`
- "Top on-chain net inflow tokens / Solana trending tokens?" → `blockbeats-mcp` → `get_top10_netflow`
- "BlockBeats crypto newsflash / latest crypto news (Chinese source)?" → `blockbeats-mcp` → `get_newsflash`, `get_newsflash_24h`
- "Search BlockBeats news by keyword?" → `blockbeats-mcp` → `search_news(keyword)`
- "What are the derived ratios (P/E, ROIC, FCF, margins) for X?" → `market-data` → `get_simfin_financials(ticker, statement="derived")`

## Tools Quick Reference

### grok-news
| Tool | Description |
|------|-------------|
| `search_x_news(query, hours)` | X/Twitter news + web search |
| `get_ticker_sentiment(ticker, asset_type)` | Sentiment analysis for stock/crypto |
| `get_financial_news(topic, source)` | Financial news summary |
| `get_kol_mentions(handle)` | KOL recent posts |

### market-data
| Tool | Description |
|------|-------------|
| `get_quote(ticker)` | Price, change%, vol, mkt cap |
| `get_stock_info(ticker)` | Profile, PE, EPS, beta |
| `get_stock_history(ticker, period, interval)` | OHLCV history |
| `get_financials(ticker, statement)` | income/balance/cashflow |
| `get_analyst_recommendations(ticker)` | Buy/hold/sell + changes |
| `get_market_news(category)` | Market news |
| `get_company_news(ticker, days)` | Company news |
| `get_earnings_calendar(days_ahead)` | Upcoming earnings |
| `get_economic_calendar(days_ahead, currency)` | Macro events: CPI, NFP, GDP, FOMC, PMI (Investing.com, no key) |
| `get_ipo_calendar(days_ahead)` | Upcoming IPO listings with price and exchange |
| `get_dividend_calendar(ticker, timeframe, country)` | Per-stock: ex-div date, pay date, yield (yfinance). Market-wide (no ticker): all stocks going ex-div scraped from Investing.com |
| `get_options_expiry(ticker)` | Options expiry dates + OI + P/C ratio (yfinance) |
| `get_price_target(ticker)` | Analyst consensus target: mean/median/high/low + upside% |
| `get_short_interest(ticker)` | Short float%, days to cover, shares short, MoM change |
| `get_options_chain(ticker, expiry, option_type)` | Full chain: IV/bid/ask/OI + Max Pain (yfinance; OI best-effort) |
| `get_news_sentiment(ticker)` | Finnhub buzz + sentiment |
| `get_simfin_financials(ticker, statement, period)` | Standardized statements: income/balance/cashflow/derived (SimFin key) |

### macro-data
| Tool | Description |
|------|-------------|
| `get_key_indicators()` | Fed Funds, CPI, GDP, etc. |
| `search_fred_series(keywords)` | Find FRED series |
| `get_fred_data(series_id, start, end)` | Any FRED time series |
| `search_edgar_company(name)` | Get CIK + ticker |
| `get_recent_filings(ticker_or_cik, form_type)` | List SEC filings |
| `get_13f_holdings(cik, period)` | Fund holdings |
| `get_filing_text(accession_number)` | Filing text |

### sentiment-data
| Tool | Description |
|------|-------------|
| `get_fear_greed_index(days)` | Crypto F&G index |
| `get_congressional_trades(ticker, days)` | Congress trades (Quiver) |
| `get_wsb_mentions(ticker)` | WSB mention count |
| `get_insider_sentiment(ticker)` | Insider buy/sell |

### crypto-data
| Tool | Description |
|------|-------------|
| `get_crypto_price(coin_id)` | Price, change%, cap |
| `get_crypto_market_data(coin_id)` | ATH, supply, returns |
| `get_global_market()` | Total cap, BTC dom |
| `get_trending_coins()` | Top 7 trending |
| `get_defi_tvl_overview(limit)` | Top protocols by TVL |
| `get_protocol_tvl(protocol)` | Protocol TVL history |
| `get_all_chains(limit)` | All chains ranked by TVL |
| `get_chain_tvl(chain)` | Chain TVL trend (30d) |
| `get_stablecoins(limit)` | Stablecoin market: supply, peg type, mechanism |
| `get_stablecoin_detail(coin, chain_limit, history_days)` | Single stablecoin: chain distribution, supply history |
| `get_yields(chain, min_tvl, limit)` | Top yield/lending pools by APY |
| `get_onchain_metric(metric, asset)` | Glassnode metric |
| `get_exchange_flows(asset)` | Exchange flows |

### financial-scraper
| Tool | Description |
|------|-------------|
| `get_insider_trades(ticker, trade_type, days)` | OpenInsider |
| `get_congressional_trades(ticker, politician, days)` | Capitol Trades |
| `get_fed_rate_probabilities()` | CME FedWatch |
| `get_circle_reserves()` | Circle: USDC/EURC circulation, reserves, mint/burn flows |
| `search_theblock(query, size, fetch_body, fetch_index)` | The Block: crypto news search + full article body |
| `get_quiverquant_congress(ticker, use_cache, output)` | QuiverQuant: congress trade chart (HTML, opens in browser) + CSV; cached by date |
| `clear_quiverquant_cache(ticker)` | Clear cached QuiverQuant files for a ticker (or all) |

### news-data

| Tool | Description |
|------|-------------|
| `configure(newsapi_key)` | Save NewsAPI.org key (~/.config/news-mcp/config.json) |
| `search_newsapi(query, days, language, max_records, sort_by)` | NewsAPI article search — no per-request limit (100 req/day). days max 30 |
| `get_top_headlines(category, country, query, max_records, sources)` | NewsAPI top headlines. country only supports "us"; sources cannot mix with country/category |
| `search_news(query, timespan, max_records)` | GDELT global news (100+ languages, 65+ countries). No key — 1 req/5s limit |
| `get_news_sentiment(query, timespan)` | GDELT daily sentiment timeline. Positive = bullish, negative = bearish |
| `batch_news(requests_json)` | Batch search_news/get_news_sentiment/search_newsapi/get_top_headlines; auto 5s delay around GDELT calls only |

### social-data
| Tool | Description |
|------|-------------|
| `configure_twitter(auth_token, ct0)` | Save Twitter cookie credentials |
| `search_tweets(query, n)` | Search raw tweets by keyword/ticker |
| `get_tweet(url_or_id)` | Fetch a single tweet |
| `get_user_timeline(username, n)` | KOL/account recent tweets |
| `get_thread(url_or_id)` | Full Twitter thread |
| `get_subreddit_posts(subreddit, sort, limit)` | Subreddit hot/new/top posts |
| `search_reddit(query, limit, subreddit)` | Reddit post search |
| `get_post_comments(post_url, limit)` | Reddit post + top comments |
| `get_video_info(url)` | YouTube video metadata |
| `get_video_transcript(url, lang)` | YouTube captions/transcript |
| `search_youtube(query, n)` | YouTube video search |

### blockbeats-mcp
| Tool | Description |
|------|-------------|
| `get_newsflash(category, page, size, lang)` | Paginated newsflash list: `""` all, `important`, `original`, `first`, `onchain`, `financing`, `prediction`, `ai` |
| `get_newsflash_24h(lang)` | All newsflashes from last 24h |
| `get_articles(category, page, size, lang)` | Paginated article list: `""` all, `important`, `original` |
| `get_articles_24h(lang)` | All articles from last 24h |
| `search_news(keyword, page, size, lang)` | Keyword search across all BlockBeats content |
| `get_btc_etf_flow(limit)` | BTC spot ETF daily/cumulative net inflow |
| `get_daily_onchain_tx()` | Daily on-chain tx by chain (writes full data to `/tmp/blockbeats_daily_tx.json`) |
| `get_ibit_fbtc_flow(limit)` | IBIT and FBTC ETF net inflow side-by-side |
| `get_stablecoin_marketcap(limit)` | Stablecoin market cap history (billions USD) |
| `get_compliant_exchange_total(limit)` | Compliant exchange total asset holdings |
| `get_us_treasury_yield(type, limit)` | US 10Y treasury yield: `1D`/`1W`/`1M` |
| `get_dxy_index(type, limit)` | Dollar Index (DXY): `1D`/`1W`/`1M` |
| `get_m2_supply(type, limit)` | Global M2 money supply with YoY growth: `3M`/`6M`/`1Y`/`3Y` |
| `get_bitfinex_long_positions(symbol, type, limit)` | Bitfinex BTC/ETH long positions |
| `get_contract_oi_data(dataType, limit)` | Derivatives OI: Binance / Bybit / Hyperliquid |
| `get_sentiment_indicator()` | Market buy/sell/hold sentiment (11 sub-indicators, score 0–100) |
| `get_top10_netflow(network)` | Top 10 tokens by on-chain net inflow: `solana`/`base`/`ethereum` |

### search-data
| Tool | Description |
|------|-------------|
| `search(query, num_results, language)` | Google search — returns ranked list of title/URL/snippet. No API key. |

## Workflow Patterns

> **Note:** The workflows below are illustrative examples only. You are not required to follow them step by step — use your judgment to select the most relevant tools based on what the user actually needs.

### A: Stock Deep-Dive (e.g. NVDA)
```
1. market-data: get_quote("NVDA") — current snapshot
2. market-data: get_stock_info("NVDA") — fundamentals
3. market-data: get_stock_history("NVDA", "6mo") — technical context
4. market-data: get_financials("NVDA") — income statement
5. market-data: get_analyst_recommendations("NVDA") — consensus
6. social-data: search_reddit("NVDA", subreddit="wallstreetbets") — Reddit buzz
7. financial-scraper: get_insider_trades("NVDA", "P") — insider buying
8. social-data: search_tweets("$NVDA") — raw X posts
9. grok-news: get_ticker_sentiment("NVDA") — X sentiment (needs XAI key)
10. market-data: get_company_news("NVDA", days=7) — recent news
```

### B: Morning Macro Brief
```
1. macro-data: get_key_indicators() — overnight rates, CPI, GDP snapshot
2. macro-data: get_fred_data("T10Y2Y") — yield curve
3. market-data: get_market_news("general") — overnight news
4. grok-news: get_financial_news("market open today") — X + web headlines
5. financial-scraper: get_fed_rate_probabilities() — rate expectations
```

### C: Crypto Research
```
1. crypto-data: get_global_market() — total market cap, BTC dominance
2. crypto-data: get_crypto_price("bitcoin") — BTC snapshot
3. crypto-data: get_trending_coins() — what's hot
4. sentiment-data: get_fear_greed_index(7) — mood over past week
5. crypto-data: get_onchain_metric("addresses/active_count") — network activity
6. crypto-data: get_exchange_flows("BTC") — smart money moving in/out
7. grok-news: get_ticker_sentiment("BTC", "crypto") — X sentiment
```

### D: Insider / Smart Money Tracking
```
1. financial-scraper: get_insider_trades(trade_type="P", days=7) — recent big buys
2. financial-scraper: get_congressional_trades(days=14) — political trades (Capitol Trades)
3. sentiment-data: get_congressional_trades(days=30) — political trades (Quiver API)
4. financial-scraper: get_quiverquant_congress("AAPL") — congress trade chart vs price + full CSV
5. sentiment-data: get_insider_sentiment("AAPL") — specific stock
6. macro-data: get_13f_holdings("0001067983") — Berkshire latest
```

### E: Earnings Play
```
1. market-data: get_earnings_calendar(14) — upcoming earnings
2. market-data: get_analyst_recommendations("AAPL") — analyst sentiment
3. market-data: get_news_sentiment("AAPL") — Finnhub buzz score
4. social-data: search_reddit("AAPL earnings", subreddit="wallstreetbets") — retail positioning
5. market-data: get_financials("AAPL", "income") — historical trend
6. social-data: search_tweets("$AAPL earnings") — X chatter
```

### G: Social Sentiment Deep-Dive (e.g. NVDA)
```
1. social-data: search_reddit("NVDA earnings", subreddit="wallstreetbets", limit=10)
2. social-data: get_subreddit_posts("stocks", sort="hot", limit=10)
3. social-data: search_tweets("$NVDA", n=15)
4. social-data: get_user_timeline("nvidia", n=10)
5. social-data: search_youtube("NVDA earnings call 2025", n=3) → get_video_transcript(url)
6. sentiment-data: get_fear_greed_index(7)
```

### F: DeFi Protocol Due Diligence
```
1. crypto-data: get_defi_tvl_overview(20) — DeFi landscape
2. crypto-data: get_protocol_tvl("aave") — specific protocol
3. crypto-data: get_chain_tvl("ethereum") — underlying chain health
4. crypto-data: get_crypto_price("ethereum") — ETH context
5. grok-news: search_x_news("Aave protocol update") — community news
```

### H: Stablecoin Research
```
1. crypto-data: get_stablecoins(20) — market overview: supply, peg type, mechanism
2. crypto-data: get_stablecoin_detail("USDC") — chain distribution, supply history
3. financial-scraper: get_circle_reserves() — USDC/EURC reserve composition and flows
4. financial-scraper: search_theblock("USDC stablecoin", size=5) — recent news
5. crypto-data: get_yields(chain="ethereum", min_tvl=1000000) — yield opportunities
```

## Rate Limits Reference

| MCP | Source | Free Tier Limit |
|-----|--------|----------------|
| market-data | yfinance | Unlimited (15-min delayed) |
| market-data | Finnhub | 60 calls/minute |
| market-data | SimFin | 2000 req/day (free tier) |
| news-data | GDELT | 1 req/5s (IP-based); batch_news handles automatically |
| news-data | NewsAPI.org | 100 req/day, no per-request limit |
| macro-data | FRED | 120 calls/minute |
| macro-data | SEC EDGAR | ~10 calls/second (be polite) |
| sentiment-data | Alternative.me | No stated limit |
| sentiment-data | Quiver | Limited/day on free tier |
| crypto-data | CoinGecko | 30/min (no key) / 500/min (key) |
| crypto-data | DeFi Llama | Generous, no stated limit |
| crypto-data | Glassnode | Daily resolution on free tier |
| grok-news | xAI Grok | Per your API plan (optional — raw tweets via social-data) |
| social-data | Reddit JSON API | ~60 requests/min (no key, User-Agent required) |
| social-data | Twitter xreach | Per your account limits |
| social-data | YouTube yt-dlp | Generous (public videos) |
| blockbeats-mcp | BlockBeats Pro API | Per your subscription plan |

## Data Freshness

| Source | Freshness |
|--------|-----------|
| yfinance | 15-min delayed (US markets) |
| Finnhub | Real-time (paid) / delayed (free) |
| SimFin | Updated daily (free tier) |
| GDELT | Real-time (~15min lag) |
| FRED | Varies: daily/weekly/monthly/quarterly |
| Reddit (social-data) | Real-time |
| Twitter/X (social-data) | Real-time |
| YouTube (social-data) | Real-time (public videos) |
| Alternative.me Fear/Greed | Updated daily |
| CoinGecko | ~1-5 min |
| DeFi Llama | ~1 hour |
| Glassnode (free) | 24h resolution |
| OpenInsider | Within 2 business days of SEC filing |
| Capitol Trades | Within 45 days of transaction |
| QuiverQuant Congress | Cached per-day locally; source updated within ~1 day of disclosure |
| CME FedWatch | Real-time |

## Limitations

- No historical backtesting or strategy simulation
- `grok-news` requires a paid XAI API key; use `social-data` for raw tweets without cost
- Glassnode free tier: limited to ~10 metrics, daily resolution only
- Scraping targets (OpenInsider, Capitol Trades, CME) may change HTML/API structure
- EDGAR 13F parsing requires knowing the CIK number
- yfinance data accuracy not guaranteed; verify critical data with official sources

## Troubleshooting

### macOS SSL Certificate Errors
If tools fail with SSL/certificate errors (Finnhub, CoinGecko, The Block, Grok, etc.):
- **Do NOT suggest `pip install certifi`** — certifi is already installed as a dependency of requests. This will do nothing.
- **Root cause**: `curl_cffi` (used by yfinance/Scrapling) looks for a CA bundle at a path that may not exist on the user's machine. The fix is to set the `CURL_CA_BUNDLE` env var pointing to a valid cert file.
- **Fix**: Pull the latest code and restart Claude Desktop / CLI:
  ```bash
  cd ~/crawl-x && git pull
  ```
  The repo includes `ssl_utils.py` which auto-detects the correct CA bundle (Homebrew Apple Silicon → Homebrew Intel → certifi fallback). Restarting reloads the updated MCP servers.
- If the issue persists after pulling, the user can manually verify the cert path: `python3 -c "import certifi; print(certifi.where())"`

## Guardrails

- All data is for research purposes only — not a basis for investment decisions
- Respect rate limits; add delays if running batch queries
- SEC EDGAR terms: identify yourself in User-Agent (auto-set: `financial-research-mcp/1.0`)
- Reddit ToS: read-only access, do not spam or scrape user data
- This research infrastructure does not provide financial advice
