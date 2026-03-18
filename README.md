# crawl-x — Financial Intelligence MCP Suite

A collection of MCP (Model Context Protocol) servers that give Claude real-time access to market data, macroeconomic indicators, crypto analytics, sentiment analysis, insider/congressional trades, and X/Twitter news.

## MCPs Overview

| MCP | Server Name | Description | API Key |
|-----|-------------|-------------|---------|
| `market-data-mcp` | `market-data` | Stock quotes, financials, news, earnings | Finnhub (optional) |
| `macro-mcp` | `macro-data` | FRED economic data, SEC EDGAR filings | FRED (required) |
| `crypto-mcp` | `crypto-data` | CoinGecko prices, DeFi TVL, Glassnode on-chain | optional |
| `sentiment-mcp` | `sentiment-data` | Reddit, Fear & Greed Index, congressional/insider sentiment | optional |
| `scrape-mcp` | `financial-scraper` | OpenInsider trades, Capitol Trades, CME FedWatch | none |
| `grok-mcp` | `grok-news` | X/Twitter news and sentiment via Grok API | XAI (required) |

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

---

## API Keys

| Key | Used By | Where to Get |
|-----|---------|--------------|
| `XAI_API_KEY` | grok-mcp | [console.x.ai](https://console.x.ai) |
| `FRED_API_KEY` | macro-mcp | [fred.stlouisfed.org/docs/api](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `FINNHUB_API_KEY` | market-data-mcp | [finnhub.io](https://finnhub.io) |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | sentiment-mcp | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) |
| `QUIVER_API_KEY` | sentiment-mcp | [quiverquant.com](https://www.quiverquant.com) |
| `COINGECKO_API_KEY` | crypto-mcp | [coingecko.com/api](https://www.coingecko.com/en/api) |
| `GLASSNODE_API_KEY` | crypto-mcp | [glassnode.com](https://glassnode.com) |

Keys can be passed during `install.sh` or configured later via each MCP's `configure()` tool.

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
| `get_market_news` | General or category market news |
| `get_company_news` | News for a specific ticker |
| `get_earnings_calendar` | Upcoming earnings dates |

### macro-data
| Tool | Description |
|------|-------------|
| `search_fred_series` | Search FRED economic series by keyword |
| `get_fred_data` | Fetch a FRED time series |
| `get_key_indicators` | Fed rate, 10Y yield, CPI, unemployment |
| `search_edgar_company` | Search SEC EDGAR company database |
| `get_recent_filings` | Recent 10-K/10-Q filings for a company |
| `get_13f_holdings` | Institutional holdings from 13-F |
| `get_filing_text` | Full text of an SEC filing |

### crypto-data
| Tool | Description |
|------|-------------|
| `get_crypto_price` | Price and 24h stats for a coin |
| `get_crypto_market_data` | Top coins by market cap |
| `get_global_market` | Global crypto market overview |
| `get_trending_coins` | Trending coins on CoinGecko |
| `get_defi_tvl_overview` | Top DeFi protocols by TVL |
| `get_protocol_tvl` | TVL history for a protocol |
| `get_chain_tvl` | TVL by blockchain |
| `get_onchain_metric` | Glassnode on-chain metrics |
| `get_exchange_flows` | Exchange inflow/outflow data |

### sentiment-data
| Tool | Description |
|------|-------------|
| `get_reddit_posts` | Top posts from a subreddit |
| `get_reddit_ticker_mentions` | Ticker mentions on Reddit |
| `get_fear_greed_index` | Crypto Fear & Greed Index history |
| `get_congressional_trades` | Congressional trades via Quiver |
| `get_wsb_mentions` | WallStreetBets mention data |
| `get_insider_sentiment` | Insider buy/sell sentiment |

### financial-scraper
| Tool | Description |
|------|-------------|
| `get_insider_trades` | SEC Form 4 trades from OpenInsider |
| `get_congressional_trades` | Live congressional trades from Capitol Trades |
| `get_fed_rate_probabilities` | CME FedWatch rate probabilities |

### grok-news
| Tool | Description |
|------|-------------|
| `search_x_news` | Search X/Twitter for news and posts |
| `get_ticker_sentiment` | Sentiment analysis for a ticker on X |
| `get_financial_news` | Financial news headlines from X |
| `get_kol_mentions` | Key opinion leader mentions |

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
└── financial-research-agent/     # Master agent skill
    └── SKILL.md
```

Each `server.py` uses [PEP 723 inline script dependencies](https://peps.python.org/pep-0723/) — `uv run` installs all dependencies automatically on first launch, no manual `pip install` needed.
