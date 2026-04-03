[中文](README_zh.md)

# crawl-x — Financial Intelligence MCP Suite

A collection of MCP (Model Context Protocol) servers that give Claude real-time access to market data, macroeconomic indicators, crypto analytics, sentiment analysis, insider/congressional trades, and X/Twitter news.

## MCPs Overview

| MCP | Server Name | Description | API Key |
|-----|-------------|-------------|---------|
| `market-data-mcp` | `market-data` | Stock quotes, financials, news, earnings | Finnhub (optional) |
| `macro-mcp` | `macro-data` | FRED economic data, BLS labor stats (CPI/PPI/NFP/JOLTS), US Treasury yield curve/TGA/auctions, Fed balance sheet, SEC EDGAR filings + XBRL facts + insider Form 4 | FRED (required), BLS (optional) |
| `crypto-mcp` | `crypto-data` | CoinGecko prices, DeFi TVL, Glassnode on-chain | optional |
| `sentiment-mcp` | `sentiment-data` | Fear & Greed Index, congressional/insider sentiment (Quiver) | optional |
| `scrape-mcp` | `financial-scraper` | OpenInsider trades, Capitol Trades, CME FedWatch, Circle reserves, The Block news, QuiverQuant congress chart | none |
| `news-mcp` | `news-data` | Global news search + top headlines + sentiment timeline (GDELT + NewsAPI) | NewsAPI (optional) |
| `grok-mcp` | `grok-news` | X/Twitter news and sentiment via Grok API | XAI (optional) |
| `social-mcp` | `social-data` | Reddit (public), Twitter/X (xreach), YouTube (yt-dlp) | optional |
| `blockbeats-mcp` | `blockbeats-mcp` | Crypto newsflash/articles, BTC ETF flows, on-chain data, derivatives OI, macro (M2/DXY/treasury), sentiment indicator | BlockBeats Pro (optional) |
| `binance-mcp` | `binance-mcp` | Binance futures: funding rates, open interest, long/short ratio, liquidations, basis, top movers, OHLCV | none |
| `cmc-mcp` | `cmc-data` | CoinMarketCap rankings, quotes, global metrics, categories, trending, Fear & Greed | CMC (optional) |
| `wikipedia-mcp` | `wikipedia-data` | English Wikipedia: search, summary, full article (cached locally), sections, links, related topics, key facts, coordinates | none |
| `search-mcp` | `search-data` | Google search: find real URLs by keyword, no API key required | none |
| `polymarket-mcp` | `polymarket-mcp` | Polymarket prediction markets: odds/probabilities, volumes, trending markets, events | none |
| *(external)* | `ScraplingServer` | General-purpose web scraping: static/JS/Cloudflare pages, bulk fetch, CSS selector extraction, session management | none |

---

## Prerequisites

**[Claude Code](https://claude.ai/code)** (for CLI usage) — must be installed manually:

```bash
npm install -g @anthropic-ai/claude-code
```

**[uv](https://docs.astral.sh/uv/getting-started/installation/)** — auto-installed by `install.sh` if missing (macOS/Linux). On Windows, install manually first.

---

## Installation

```bash
git clone https://github.com/you/crawl-x
cd crawl-x
bash install.sh
```

The script will:
- Auto-install `uv` if missing (macOS/Linux via official script)
- Install Scrapling + Playwright browsers (required by `scrape-mcp` for Capitol Trades and CME FedWatch)
- Auto-install `yt-dlp` if missing (required by `social-mcp` for YouTube)
- Prompt for API keys — **press Enter to keep any already-configured value**
- Register all 15 MCPs to Claude CLI via `claude mcp add` (14 custom + ScraplingServer external)

**Agent / CI usage** — skip the interactive key prompts and configure keys afterwards via each MCP's `configure` tool:

```bash
bash install.sh --non-interactive
```

To also generate a `claude_desktop_config.json` for Claude Desktop:

```bash
bash install.sh --desktop
```

> **Note:** `claude_desktop_config.json` contains absolute paths to the repo on the machine that ran `install.sh`. If you share this file with other users, they must replace those paths with the correct location of the repo on their machine before using it.

---

## API Keys

| Key | Used By | Where to Get |
|-----|---------|--------------|
| `XAI_API_KEY` | grok-mcp | [console.x.ai](https://console.x.ai) — optional; raw tweets available via `social-data` |
| `FRED_API_KEY` | macro-mcp | [fred.stlouisfed.org/docs/api](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `FINNHUB_API_KEY` | market-data-mcp | [finnhub.io](https://finnhub.io) |
| `SIMFIN_API_KEY` | market-data-mcp | [simfin.com](https://simfin.com) — free tier (2000 req/day) |
| `NEWSAPI_KEY` | news-mcp | [newsapi.org/register](https://newsapi.org/register) — free (100 req/day) |
| `QUIVER_API_KEY` | sentiment-mcp | [quiverquant.com](https://www.quiverquant.com) |
| `COINGECKO_API_KEY` | crypto-mcp | [coingecko.com/api](https://www.coingecko.com/en/api) |
| `GLASSNODE_API_KEY` | crypto-mcp | [glassnode.com](https://glassnode.com) |
| `TWITTER_AUTH_TOKEN` | social-mcp | x.com cookie (Cookie Picker extension → `auth_token`) |
| `TWITTER_CT0` | social-mcp | x.com cookie (Cookie Picker extension → `ct0`) |
| `BLOCKBEATS_API_KEY` | blockbeats-mcp | [theblockbeats.info](https://www.theblockbeats.info/) — BlockBeats Pro subscription |
| `BLS_API_KEY` | macro-mcp | [bls.gov/developers](https://www.bls.gov/developers/api_signature_v2.htm) — free, increases rate limits |
| `CMC_API_KEY` | cmc-mcp | [coinmarketcap.com/api](https://coinmarketcap.com/api/) — free Basic plan |

Keys are stored in `~/.config/<mcp-name>/config.json` — **not** in `.env` files or Claude MCP env vars. Configure them interactively during `install.sh`, or call each MCP's `configure` tool afterwards (e.g. `mcp__macro-data__configure(fred_api_key="...")`).

> **Twitter cookie setup:** Use the **Cookie Picker** Chrome extension included in this repo (`extensions/cookie-picker/`) — load it unpacked in Chrome, navigate to x.com, open the popup, and `auth_token` + `ct0` are pre-selected. Click "Copy selected" and paste the values into `configure_twitter(auth_token=..., ct0=...)` in Claude.

---

## Claude Desktop Setup

Run `bash install.sh --desktop`, then merge the generated `claude_desktop_config.json` into:

```
~/Library/Application Support/Claude/claude_desktop_config.json   # macOS
%APPDATA%\Claude\claude_desktop_config.json                        # Windows
```

Restart Claude Desktop to load the MCPs.

---

## Available Tools

### market-data
| Tool | Description |
|------|-------------|
| `get_quote` | Real-time stock quote |
| `get_stock_info` | Company overview and key metrics |
| `get_stock_history` | OHLCV price history |
| `get_financials` | Income / balance / cash flow statements |
| `get_analyst_recommendations` | Buy/sell/hold ratings |
| `get_market_news` | General or category market news (Finnhub) |
| `get_company_news` | News for a specific ticker (Finnhub) |
| `get_earnings_calendar` | Upcoming earnings dates (Finnhub) |
| `get_economic_calendar` | Macro events: CPI, NFP, GDP, FOMC, PMI (Investing.com, no key) |
| `get_ipo_calendar` | Upcoming IPO listings with price range and exchange (Finnhub) |
| `get_dividend_calendar` | Per-stock: ex-div date, pay date, yield (yfinance). Market-wide (no ticker): all stocks going ex-div by timeframe/country (Investing.com, no key) |
| `get_options_expiry` | Options expiry dates + call/put OI + P/C ratio (yfinance) |
| `get_price_target` | Analyst consensus price target: mean/median/high/low + upside% (yfinance) |
| `get_short_interest` | Short float%, days to cover, shares short, MoM change (yfinance) |
| `get_options_chain` | Full options chain: strike/IV/bid/ask/OI + Max Pain for a given expiry (yfinance) |
| `get_news_sentiment` | News sentiment and buzz score (Finnhub) |
| `get_simfin_financials` | Standardized income / balance / cashflow / derived ratios (SimFin) |

### macro-data
| Tool | Description |
|------|-------------|
| `configure(fred_api_key)` | Save FRED API key |
| `configure_bls(bls_api_key)` | Save BLS API key (optional, increases rate limits) |
| `search_fred_series` | Search FRED economic series by keyword |
| `get_fred_data` | Fetch a FRED time series |
| `get_key_indicators` | Fed rate, 10Y yield, CPI, unemployment |
| `search_edgar_company` | Search SEC EDGAR company database |
| `get_recent_filings` | Recent 10-K/10-Q/8-K filings for a company |
| `get_13f_holdings` | 13F filing metadata and archive link for a fund |
| `get_filing_text` | Metadata and archive URL for a specific SEC filing |
| `get_cpi` | CPI headline + core (+ Food/Energy/Shelter/Medical breakdown) via BLS |
| `get_ppi` | PPI Final Demand + core + goods + services via BLS |
| `get_jobs_report` | Nonfarm Payrolls, unemployment, wages, hours, participation rate |
| `get_jolts` | Job openings, hires, quits, layoffs, openings-to-hires ratio |
| `get_bls_series` | Fetch any BLS series by ID |
| `list_bls_series` | List all pre-configured BLS series IDs |
| `get_yield_curve` | Full US Treasury nominal yield curve 1M–30Y + key spreads |
| `get_real_yield_curve` | TIPS real yield curve 5Y–30Y |
| `get_breakeven_inflation` | Breakeven inflation = nominal − real yield |
| `get_tga_balance` | Treasury General Account daily cash balance |
| `get_treasury_auctions` | Recent debt auction results (bills/notes/bonds/TIPS) |
| `get_fed_balance_sheet` | Fed total assets (WALCL) — QE/QT tracker |
| `search_filings` | Full-text search across all SEC EDGAR filings |
| `get_company_facts` | XBRL financial facts (Revenues, Assets, NetIncomeLoss, etc.) |
| `get_insider_transactions` | Form 4 insider buy/sell filings for a company |
| `get_company_info` | Company CIK, SIC, exchanges, fiscal year, address |

### binance-mcp
| Tool | Description |
|------|-------------|
| `get_funding_rate` | Current and historical funding rates for a USDT-M futures contract |
| `get_open_interest` | Open interest history — contracts + USD value |
| `get_long_short_ratio` | Top trader long/short position ratio |
| `get_liquidations_summary` | Recent forced liquidations with long/short totals |
| `get_market_stats` | 24h price stats: price, change, high, low, volume |
| `get_top_movers` | Top gainers and losers across all USDT-M futures |
| `get_futures_kline` | OHLCV candlestick data |
| `get_basis` | Futures basis vs spot index (premium/discount %) |

### cmc-data
| Tool | Description |
|------|-------------|
| `configure` | Save CMC API key |
| `get_listings` | Top cryptocurrencies by market cap, volume, or 24h change |
| `get_quote` | Real-time quotes for one or more coins (e.g. `"BTC,ETH,SOL"`) |
| `get_global_metrics` | Total market cap, BTC/ETH dominance, DeFi, stablecoins, derivatives |
| `get_category_list` | All CMC categories (DeFi, Layer-1, Meme, AI, etc.) with stats |
| `get_category` | All coins in a category with performance data |
| `get_trending` | Currently trending coins on CoinMarketCap |
| `get_fear_greed` | CMC Fear & Greed Index — last 7 days |

### wikipedia-data
| Tool | Description |
|------|-------------|
| `search_wikipedia(query, limit)` | Search Wikipedia and return matching article titles (max 20) |
| `get_summary(title, sentences)` | Introductory summary of an article (default 5 sentences) |
| `get_article(title)` | Fetch full article text, cache to `~/.cache/wikipedia-mcp/<title>.md`, return file path |
| `get_sections(title)` | All sections with 500-char preview each |
| `get_links(title, limit)` | Internal Wikipedia links within an article (default 50) |
| `get_related_topics(title, limit)` | Related categories and linked articles (default 10) |
| `extract_key_facts(title, count)` | Key facts as numbered sentences from article summary (default 5) |
| `get_coordinates(title)` | Latitude/longitude for geographic articles; graceful error for non-geographic pages |

### crypto-data
| Tool | Description |
|------|-------------|
| `get_crypto_price` | Price and 24h stats for a coin |
| `get_crypto_market_data` | ATH, supply, price changes over multiple periods |
| `get_global_market` | Global crypto market overview |
| `get_trending_coins` | Trending coins on CoinGecko |
| `get_defi_tvl_overview` | Top DeFi protocols by TVL |
| `get_protocol_tvl` | TVL history and chain breakdown for a protocol |
| `get_all_chains` | All blockchains ranked by TVL |
| `get_chain_tvl` | TVL trend for a specific blockchain (30d) |
| `get_stablecoins` | Stablecoin market: supply, peg type, mechanism |
| `get_stablecoin_detail` | Single stablecoin: chain distribution and supply history |
| `get_yields` | Top yield/lending pools by APY |
| `get_onchain_metric` | Glassnode on-chain metrics (requires key) |
| `get_exchange_flows` | Exchange inflow/outflow data (requires key) |

### sentiment-data
| Tool | Description |
|------|-------------|
| `get_fear_greed_index` | Crypto Fear & Greed Index history |
| `get_congressional_trades` | Congressional trades via Quiver (requires key) |
| `get_wsb_mentions` | WallStreetBets mention count and sentiment (requires key) |
| `get_insider_sentiment` | Insider trading summary (requires key) |

### financial-scraper
| Tool | Description |
|------|-------------|
| `get_insider_trades` | SEC Form 4 trades from OpenInsider (no key, ~2s) |
| `get_congressional_trades` | Live congressional trades from Capitol Trades (~15s) |
| `get_fed_rate_probabilities` | CME FedWatch FOMC rate probabilities (~14s) |
| `get_circle_reserves` | Circle USDC/EURC circulation, reserves, mint/burn flows (~10s) |
| `search_theblock(query, size, fetch_body, fetch_index)` | The Block crypto news search + full article body (~1-2s) |
| `get_quiverquant_congress(ticker, use_cache, output)` | QuiverQuant: congress trade chart vs price (HTML, opens in browser) + CSV; cached daily (~15s first fetch) |
| `clear_quiverquant_cache(ticker)` | Clear cached QuiverQuant files for one ticker or all |

### grok-news
| Tool | Description |
|------|-------------|
| `search_x_news` | Search X/Twitter for news and posts |
| `get_ticker_sentiment` | Sentiment analysis for a ticker on X |
| `get_financial_news` | Financial news from X and/or web |
| `get_kol_mentions` | Key opinion leader mentions |

### news-data
| Tool | Description |
|------|-------------|
| `configure(newsapi_key)` | Save NewsAPI.org key |
| `search_newsapi(query, days, ...)` | NewsAPI article search — no per-request limit (100 req/day) |
| `get_top_headlines(category, country, sources, query)` | Top headlines by category/country or specific sources (NewsAPI) |
| `search_news(query, timespan, max_records)` | Global search via GDELT — 100+ languages, 65+ countries. No key required |
| `get_news_sentiment(query, timespan)` | GDELT daily sentiment timeline (positive = optimistic) |
| `batch_news(requests_json)` | Batch any mix of the above; auto rate-limits GDELT calls |

### blockbeats-mcp
| Tool | Description |
|------|-------------|
| `configure(api_key)` | Save BlockBeats Pro API key |
| `get_newsflash(category, page, size, lang)` | Paginated newsflash: `""` all, `important`, `original`, `first`, `onchain`, `financing`, `prediction`, `ai` |
| `get_newsflash_24h(lang)` | All newsflashes from last 24h |
| `get_articles(category, page, size, lang)` | Paginated articles: `""` all, `important`, `original` |
| `get_articles_24h(lang)` | All articles from last 24h |
| `search_news(keyword, page, size, lang)` | Keyword search across all content |
| `get_btc_etf_flow(limit)` | BTC spot ETF daily/cumulative net inflow |
| `get_daily_onchain_tx()` | Daily on-chain tx by chain (compact summary; full data → `/tmp/blockbeats_daily_tx.json`) |
| `get_ibit_fbtc_flow(limit)` | IBIT and FBTC ETF net inflow |
| `get_stablecoin_marketcap(limit)` | Stablecoin market cap history (billions USD) |
| `get_compliant_exchange_total(limit)` | Compliant exchange total asset holdings |
| `get_us_treasury_yield(type, limit)` | US 10Y Treasury yield (`1D`/`1W`/`1M`) |
| `get_dxy_index(type, limit)` | Dollar Index (DXY) (`1D`/`1W`/`1M`) |
| `get_m2_supply(type, limit)` | Global M2 money supply with YoY growth |
| `get_bitfinex_long_positions(symbol, type, limit)` | Bitfinex BTC/ETH long positions |
| `get_contract_oi_data(dataType, limit)` | Derivatives OI: Binance / Bybit / Hyperliquid |
| `get_sentiment_indicator()` | Market buy/sell/hold sentiment indicator (0–100 score) |
| `get_top10_netflow(network)` | Top 10 tokens by on-chain net inflow (`solana`/`base`/`ethereum`) |

### social-data
| Tool | Description | Requires |
|------|-------------|---------|
| `configure_twitter(auth_token, ct0)` | Save Twitter cookie credentials | — |
| `search_tweets(query, n)` | Search raw tweets by keyword or $TICKER | xreach + cookie |
| `get_tweet(url_or_id)` | Fetch a single tweet | xreach + cookie |
| `get_user_timeline(username, n)` | Recent tweets from any account | xreach + cookie |
| `get_thread(url_or_id)` | Full conversation thread | xreach + cookie |
| `get_subreddit_posts(subreddit, sort, limit)` | Browse subreddit (hot/new/top) | none |
| `search_reddit(query, limit, subreddit)` | Reddit post search | none |
| `get_post_comments(post_url, limit)` | Reddit post + top comments | none |
| `get_video_info(url)` | YouTube video metadata | yt-dlp |
| `get_video_transcript(url, lang)` | YouTube captions / transcript | yt-dlp |
| `search_youtube(query, n)` | YouTube video search | yt-dlp |

### polymarket-mcp
| Tool | Description |
|------|-------------|
| `search_markets(query, category, limit, active_only)` | Search prediction markets by keyword via full-text search (`/public-search`); `category` as `events_tag` filter |
| `get_market(market_id)` | Full market detail: outcomes, odds, all volume periods, description |
| `get_events(query, category, limit, active_only)` | Event list grouping multiple related markets |
| `get_trending_markets(period, category, limit)` | Top markets by volume; period: 24h / 7d / 30d / all |

---

## Testing

The test suite covers all 8 MCPs (blockbeats-mcp excluded — requires paid Pro key).

```bash
cd tests

# Run all fast tests (~60s, no browser, skips missing API keys automatically)
uv run pytest -m "not slow"

# Include browser-based scraping tests (Capitol Trades, CME FedWatch, ~5min total)
uv run pytest

# Run a single MCP's tests
uv run pytest test_scrape.py -v
```

**Test categories:**

| Category | Coverage | Notes |
|----------|----------|-------|
| Free API (always runs) | CoinGecko, DeFi Llama, Fear & Greed, SEC EDGAR, OpenInsider, yfinance, Reddit | No keys needed |
| Key-gated (auto-skip) | FRED, Finnhub, Quiver, Glassnode, XAI, Twitter (xreach) | Skipped if key not configured |
| `slow` (opt-in) | Capitol Trades, CME FedWatch, YouTube (yt-dlp) | Browser/CLI; skip with `-m "not slow"` |

Tests handle transient rate-limit errors (HTTP 429, timeouts) from free-tier APIs by skipping rather than failing.

---

## Project Structure

```
crawl-x/
├── install.sh                    # One-command installer
├── market-data-mcp/server.py
├── macro-mcp/server.py
├── crypto-mcp/server.py
├── sentiment-mcp/server.py
├── scrape-mcp/server.py
├── grok-mcp/server.py
├── social-mcp/server.py
├── news-mcp/server.py
├── blockbeats-mcp/server.py
├── wikipedia-mcp/server.py
├── search-mcp/server.py
├── polymarket-mcp/server.py
├── scrapling-mcp/                # ScraplingServer skill (external MCP)
│   └── SKILL.md
├── financial-research-agent/     # Master agent skill
│   └── SKILL.md
└── tests/                        # Regression test suite
    ├── pyproject.toml
    ├── conftest.py
    ├── test_market_data.py
    ├── test_macro.py
    ├── test_crypto.py
    ├── test_sentiment.py
    ├── test_scrape.py
    ├── test_grok.py
    └── test_social.py
```

Each `server.py` uses [PEP 723 inline script dependencies](https://peps.python.org/pep-0723/) — `uv run` installs all dependencies automatically on first launch, no manual `pip install` needed.
