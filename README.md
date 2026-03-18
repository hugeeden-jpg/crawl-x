[中文](README_zh.md)

# crawl-x — Financial Intelligence MCP Suite

A collection of MCP (Model Context Protocol) servers that give Claude real-time access to market data, macroeconomic indicators, crypto analytics, sentiment analysis, insider/congressional trades, and X/Twitter news.

## MCPs Overview

| MCP | Server Name | Description | API Key |
|-----|-------------|-------------|---------|
| `market-data-mcp` | `market-data` | Stock quotes, financials, news, earnings | Finnhub (optional) |
| `macro-mcp` | `macro-data` | FRED economic data, SEC EDGAR filings | FRED (required) |
| `crypto-mcp` | `crypto-data` | CoinGecko prices, DeFi TVL, Glassnode on-chain | optional |
| `sentiment-mcp` | `sentiment-data` | Fear & Greed Index, congressional/insider sentiment (Quiver) | optional |
| `scrape-mcp` | `financial-scraper` | OpenInsider trades, Capitol Trades, CME FedWatch | none |
| `grok-mcp` | `grok-news` | X/Twitter news and sentiment via Grok API | XAI (optional) |
| `social-mcp` | `social-data` | Reddit (public), Twitter/X (xreach), YouTube (yt-dlp) | optional |

---

## Prerequisites

**1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Install [Claude Code](https://claude.ai/code)** (for CLI usage)

```bash
npm install -g @anthropic-ai/claude-code
```

---

## Installation

```bash
git clone https://github.com/you/crawl-x
cd crawl-x
bash install.sh
```

The script will:
- Check that `uv` and `claude` CLI are available
- Install Scrapling (required by `scrape-mcp` for Capitol Trades and CME FedWatch)
- Prompt for API keys (press Enter to skip optional ones)
- Register all MCPs to Claude CLI via `claude mcp add`

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
| `QUIVER_API_KEY` | sentiment-mcp | [quiverquant.com](https://www.quiverquant.com) |
| `COINGECKO_API_KEY` | crypto-mcp | [coingecko.com/api](https://www.coingecko.com/en/api) |
| `GLASSNODE_API_KEY` | crypto-mcp | [glassnode.com](https://glassnode.com) |
| `TWITTER_AUTH_TOKEN` | social-mcp | x.com cookie (Cookie-Editor → `auth_token`) |
| `TWITTER_CT0` | social-mcp | x.com cookie (Cookie-Editor → `ct0`) |

Keys can be passed during `install.sh` or configured later via each MCP's `configure()` tool.

> **Twitter cookie setup:** Install the [Cookie-Editor](https://cookie-editor.com/) browser extension, log in to x.com, and copy the `auth_token` and `ct0` cookie values. Then run `configure_twitter(auth_token=..., ct0=...)` in Claude, or pass them as env vars to `install.sh`.

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
| `get_news_sentiment` | News sentiment and buzz score (Finnhub) |

### macro-data
| Tool | Description |
|------|-------------|
| `search_fred_series` | Search FRED economic series by keyword |
| `get_fred_data` | Fetch a FRED time series |
| `get_key_indicators` | Fed rate, 10Y yield, CPI, unemployment |
| `search_edgar_company` | Search SEC EDGAR company database |
| `get_recent_filings` | Recent 10-K/10-Q/8-K filings for a company |
| `get_13f_holdings` | 13F filing metadata and archive link for a fund |
| `get_filing_text` | Metadata and archive URL for a specific SEC filing |

### crypto-data
| Tool | Description |
|------|-------------|
| `get_crypto_price` | Price and 24h stats for a coin |
| `get_crypto_market_data` | ATH, supply, price changes over multiple periods |
| `get_global_market` | Global crypto market overview |
| `get_trending_coins` | Trending coins on CoinGecko |
| `get_defi_tvl_overview` | Top DeFi protocols by TVL |
| `get_protocol_tvl` | TVL history and chain breakdown for a protocol |
| `get_chain_tvl` | TVL trend for a specific blockchain |
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

### grok-news
| Tool | Description |
|------|-------------|
| `search_x_news` | Search X/Twitter for news and posts |
| `get_ticker_sentiment` | Sentiment analysis for a ticker on X |
| `get_financial_news` | Financial news from X and/or web |
| `get_kol_mentions` | Key opinion leader mentions |

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

---

## Testing

The test suite covers all 7 MCPs.

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
