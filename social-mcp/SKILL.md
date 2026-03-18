---
name: social-mcp
description: >
  Social media data for financial research. Twitter/X raw tweet search and
  timelines via xreach CLI, Reddit subreddit browsing and post search via
  public JSON API (no auth), YouTube video info and transcript extraction
  via yt-dlp. Use for WSB sentiment, KOL tracking, and earnings call transcripts.
---

# Social Data MCP

Raw social media access: Twitter/X, Reddit, YouTube.

## Setup

Dependencies are declared inline (PEP 723) — `uv run` installs them automatically.

**Reddit:** No setup required — uses Reddit's public JSON API.

**Twitter/X (optional):** Requires [xreach-cli](https://www.npmjs.com/package/xreach-cli) and your Twitter cookie.
```bash
npm install -g xreach-cli
# Get auth_token and ct0 from x.com cookies (Cookie-Editor extension)
# Then: configure_twitter(auth_token="...", ct0="...")
```

**YouTube (optional):** Requires [yt-dlp](https://github.com/yt-dlp/yt-dlp) and Node.js.
```bash
uv tool install yt-dlp
# Node.js: https://nodejs.org/
```

Claude CLI registration:
```bash
claude mcp add "social-data" -- uv run /path/to/crawl-x/social-mcp/server.py
```

Claude Desktop config:
```json
{
  "social-data": {
    "command": "uv",
    "args": ["run", "/path/to/crawl-x/social-mcp/server.py"],
    "env": {
      "TWITTER_AUTH_TOKEN": "...",
      "TWITTER_CT0": "..."
    }
  }
}
```

## Tools

| Tool | Auth Required | Description |
|------|--------------|-------------|
| `configure_twitter(auth_token, ct0)` | — | Save Twitter cookie credentials |
| `search_tweets(query, n)` | xreach + cookie | Search tweets by keyword/ticker |
| `get_tweet(url_or_id)` | xreach + cookie | Fetch a single tweet |
| `get_user_timeline(username, n)` | xreach + cookie | Recent tweets from a user |
| `get_thread(url_or_id)` | xreach + cookie | Full conversation thread |
| `get_subreddit_posts(subreddit, sort, limit)` | None | Browse subreddit (hot/new/top) |
| `search_reddit(query, limit, subreddit)` | None | Search Reddit posts |
| `get_post_comments(post_url, limit)` | None | Read post + top comments |
| `get_video_info(url)` | yt-dlp | YouTube video metadata |
| `get_video_transcript(url, lang)` | yt-dlp | YouTube captions/transcript |
| `search_youtube(query, n)` | yt-dlp | Search YouTube videos |

## Usage Patterns

**WSB sentiment on a ticker:**
```
search_reddit("NVDA earnings", subreddit="wallstreetbets", limit=10)
get_subreddit_posts("wallstreetbets", sort="hot", limit=15)
```

**KOL Twitter tracking:**
```
get_user_timeline("elonmusk", n=10)
search_tweets("$TSLA", n=20)
```

**Earnings call transcript:**
```
search_youtube("NVDA earnings call Q4 2025", n=3)
get_video_transcript("https://www.youtube.com/watch?v=...")
```

**Reddit deep-dive (post + comments):**
```
search_reddit("Fed rate cut implications", limit=5)
get_post_comments("https://www.reddit.com/r/investing/comments/abc123/...")
```

## Notes

- Reddit: public JSON API, no OAuth needed; User-Agent header required (auto-set)
- Reddit server-side IPs may be blocked in some cloud environments; works locally
- Twitter: xreach uses your browser cookie — keep it fresh (re-export if 401 errors)
- YouTube transcripts require Node.js for yt-dlp's JS decryption; deno also works
- All tools return `str`; Reddit/YouTube errors start with `Error:`, Twitter errors start with `xreach`
