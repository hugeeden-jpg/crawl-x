---
name: grok-news
description: Fetch real-time X/Twitter posts, market sentiment, KOL mentions, and financial news using the Grok API with live X search. Use when asked to get X/Twitter news, market sentiment for a stock or crypto, track what influencers are saying, or gather financial news summaries. Requires XAI_API_KEY configured.
version: 1.0.0
tools: [set_api_key, search_x_news, get_ticker_sentiment, get_financial_news, get_kol_mentions]
---

# Grok News MCP Skill

This skill gives you access to real-time X (Twitter) data and financial news through the Grok API's built-in live search. Grok has native access to X posts, making it the most direct way to query the platform without a Twitter API subscription.

## Setup (once)

```bash
cd /Users/eden/crawl-x/grok-mcp
pip install -r requirements.txt
```

Configure your API key (one of two ways):

**Option A – environment variable (preferred for automation):**
```bash
export XAI_API_KEY="xai-xxxxxxxxxxxxxxxx"
```

**Option B – via tool call (persists to `~/.config/grok-mcp/config.json`):**
```
set_api_key("xai-xxxxxxxxxxxxxxxx")
```

Get your API key at: https://console.x.ai

### Claude Desktop / MCP config

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "grok-news": {
      "command": "python",
      "args": ["/Users/eden/crawl-x/grok-mcp/server.py"],
      "env": {
        "XAI_API_KEY": "xai-xxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

---

## Tools Reference

### `set_api_key(api_key)`

Saves the xAI API key to `~/.config/grok-mcp/config.json`.

```
set_api_key("xai-xxxxxxxxxxxxxxxx")
```

Only needed once. After saving, all other tools pick it up automatically. Environment variable `XAI_API_KEY` always takes precedence over the config file.

---

### `search_x_news(query, hours=24)`

Searches X posts for a given topic and returns a structured summary: top opinions, overall sentiment (bullish/bearish/neutral with ratio), notable signals, and trending hashtags.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | str | required | Search terms, e.g. `"$NVDA earnings"`, `"BTC halving"`, `"美联储 降息"` |
| `hours` | int | 24 | How far back to search |

**Examples:**
```
search_x_news("$TSLA")                          # TSLA discussion in the last 24h
search_x_news("BTC 比特币", hours=6)            # BTC in last 6 hours
search_x_news("美联储 利率", hours=48)          # Fed rate talk in last 2 days
search_x_news("NVDA earnings beat", hours=12)   # Post-earnings reaction
```

**When to use:** Broad topic discovery, checking what the crowd is saying, catching breaking narratives before they hit mainstream news.

---

### `get_ticker_sentiment(ticker, asset_type="stock")`

Returns a structured sentiment analysis for a specific ticker: sentiment score (0-100), bull/bear ratio, dominant narratives, anomaly detection, and recent catalysts.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `ticker` | str | required | Symbol without `$`, e.g. `TSLA`, `BTC`, `NVDA`, `ETH` |
| `asset_type` | str | `"stock"` | `"stock"` or `"crypto"` |

**Examples:**
```
get_ticker_sentiment("TSLA")                        # Tesla stock sentiment
get_ticker_sentiment("BTC", asset_type="crypto")    # Bitcoin sentiment
get_ticker_sentiment("NVDA")                        # NVIDIA sentiment
get_ticker_sentiment("ETH", asset_type="crypto")    # Ethereum sentiment
```

**Output includes:**
- Score: 0=extreme fear → 50=neutral → 100=extreme greed
- Bull/bear split percentage
- 2-3 core narratives circulating
- Anomaly flags (unusual spike, celebrity post, suspected pump)
- Recent events driving the sentiment

**When to use:** Before making a trading decision, checking crowd positioning, detecting sentiment divergence from price action.

---

### `get_financial_news(topic, source="both")`

Aggregates the latest financial news for a topic from X and/or the web. Returns today's top stories, potential market impact, and key upcoming events to watch.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `topic` | str | required | e.g. `"美联储政策"`, `"纳斯达克"`, `"黄金"`, `"A股"`, `"Federal Reserve"` |
| `source` | str | `"both"` | `"x"` (X only), `"web"` (news sites only), `"both"` |

**Examples:**
```
get_financial_news("美联储降息")                       # Fed cut news in Chinese
get_financial_news("NVIDIA earnings", source="web")    # Web news only
get_financial_news("BTC ETF", source="x")              # X posts only
get_financial_news("纳斯达克 科技股", source="both")   # All sources
```

**When to use:** Morning briefings, pre-market research, tracking a macro theme, monitoring a sector.

---

### `get_kol_mentions(handle)`

Fetches the latest posts from a specific person on X, focused on investment-relevant content. Returns recent statements, any change in stance, and market reaction.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `handle` | str | required | Full name or @handle, e.g. `"Elon Musk"`, `"@elonmusk"`, `"Michael Saylor"` |

**Examples:**
```
get_kol_mentions("@elonmusk")           # Elon Musk latest posts
get_kol_mentions("Michael Saylor")      # MicroStrategy CEO on BTC
get_kol_mentions("@CathieDWood")        # ARK Invest founder
get_kol_mentions("Warren Buffett")      # Berkshire Hathaway
get_kol_mentions("@federalreserve")     # Fed official account
```

**When to use:** Tracking influential figures before/after major announcements, checking if a KOL's stance on an asset has shifted.

---

## Workflow Patterns

### Pattern 1: Quick pre-trade check
```
1. get_ticker_sentiment("NVDA")           → get crowd sentiment score
2. search_x_news("$NVDA", hours=6)        → drill into what's being said
3. get_kol_mentions("@jimcramer")         → check notable voices
```

### Pattern 2: Morning macro brief
```
1. get_financial_news("美联储", source="both")      → macro backdrop
2. get_financial_news("纳斯达克 期货", source="x")  → overnight futures mood
3. search_x_news("今日市场 开盘", hours=3)          → fresh open chatter
```

### Pattern 3: Crypto sentiment scan
```
1. get_ticker_sentiment("BTC", asset_type="crypto")
2. get_ticker_sentiment("ETH", asset_type="crypto")
3. get_financial_news("加密市场", source="both")
4. get_kol_mentions("Michael Saylor")
```

### Pattern 4: Breaking news follow-up
```
1. search_x_news("<event keyword>", hours=2)     → immediate reaction
2. get_financial_news("<event keyword>")          → broader coverage
3. get_ticker_sentiment("<affected ticker>")      → sentiment impact
```

---

## Limitations

- **No raw structured data**: Returns Grok's natural language summary, not JSON tweet objects. For bulk structured data (tweet counts, likes, timestamps), use the Twitter API directly.
- **Not suitable for backtesting**: Can't retrieve historical sentiment data on demand.
- **Rate and cost**: Each call consumes Grok API tokens. For high-frequency polling, implement caching on your side.
- **Grok-3 required**: The live X search feature is only available on `grok-3`. The model is hardcoded in the server.
- **Search recency**: Grok's live search prioritizes recent content but exact cutoff timing is not guaranteed.

---

## Guardrails

- Do not use to harvest personal information about private individuals.
- Do not use sentiment data as sole basis for financial decisions — always combine with fundamental analysis.
- Respect xAI usage policies; do not attempt to extract raw X data in bulk through this interface.
- If `XAI_API_KEY` is missing, tools will raise a clear error — call `set_api_key` first or set the environment variable.
