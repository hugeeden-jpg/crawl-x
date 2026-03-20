#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
# ]
# ///
"""
News MCP Server - GDELT Global News Events + NewsAPI.org
Real-time global news search and sentiment timeline.
GDELT: no API key required. NewsAPI: free key at newsapi.org.
"""

import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ssl_utils import apply_ssl_fix  # noqa: E402
apply_ssl_fix()

import json
import time
import requests
from datetime import datetime, timezone, timedelta
from mcp.server.fastmcp import FastMCP

GDELT_DOC = "https://api.gdeltproject.org/api/v2/doc/doc"
NEWSAPI_BASE = "http://newsapi.org/v2"
CONFIG_FILE = Path.home() / ".config" / "news-mcp" / "config.json"

GDELT_APIS = {"search_news", "get_news_sentiment"}

mcp = FastMCP("news-data")


def _load_newsapi_key() -> str:
    key = os.environ.get("NEWSAPI_KEY", "")
    if key:
        return key
    if CONFIG_FILE.exists():
        cfg = json.loads(CONFIG_FILE.read_text())
        return cfg.get("newsapi_key", "")
    return ""


@mcp.tool()
def configure(newsapi_key: str) -> str:
    """
    Save NewsAPI.org API key to local config (~/.config/news-mcp/config.json).
    Get a free key at https://newsapi.org/register (100 req/day, no per-request rate limit).

    Args:
        newsapi_key: Your NewsAPI.org API key
    """
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    cfg["newsapi_key"] = newsapi_key
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    return "NewsAPI key saved to ~/.config/news-mcp/config.json"


@mcp.tool()
def search_newsapi(
    query: str,
    days: int = 7,
    language: str = "en",
    max_records: int = 20,
    sort_by: str = "publishedAt",
) -> str:
    """
    Search news articles via NewsAPI.org. No per-request rate limit (100 req/day free tier).
    Requires a free API key configured via configure().

    Args:
        query: Search keywords — company name, ticker, event (e.g. "Apple earnings", "Federal Reserve")
        days: How many past days to search, 1–30 (default: 7). Free tier max is 30 days.
        language: Language code: en, zh, de, fr, es, ar, etc. (default: en)
        max_records: Max articles to return, 1–100 (default: 20)
        sort_by: Sort order: "publishedAt" (newest first), "relevancy", "popularity" (default: publishedAt)
    """
    key = _load_newsapi_key()
    if not key:
        return (
            "NewsAPI key not configured. "
            "Get a free key at https://newsapi.org/register, "
            "then call configure(newsapi_key='...')."
        )
    try:
        max_records = max(1, min(100, max_records))
        days = max(1, min(30, days))
        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

        r = requests.get(
            f"{NEWSAPI_BASE}/everything",
            params={
                "q": query,
                "language": language,
                "sortBy": sort_by,
                "pageSize": max_records,
                "from": from_date,
                "apiKey": key,
            },
            timeout=25,
        )
        data = r.json()

        if data.get("status") != "ok":
            code = data.get("code", "")
            msg = data.get("message", str(data))
            if code == "apiKeyInvalid":
                return f"Invalid API key. {msg}"
            if code == "rateLimited":
                return "NewsAPI daily limit (100 req) reached. Resets at midnight UTC."
            return f"NewsAPI error [{code}]: {msg}"

        articles = data.get("articles", [])
        total = data.get("totalResults", 0)
        if not articles:
            return f"No articles found for '{query}' in the last {days} days."

        lines = [
            f"=== NewsAPI: '{query}' (last {days}d) — {len(articles)} of {total} results ===\n"
        ]
        for art in articles:
            pub = art.get("publishedAt", "")[:16].replace("T", " ")
            source = art.get("source", {}).get("name", "")
            title = art.get("title", "(no title)")
            desc = art.get("description") or ""
            url = art.get("url", "")

            lines.append(f"[{pub}] {source}")
            lines.append(f"  {title}")
            if desc:
                lines.append(f"  {desc[:150]}")
            lines.append(f"  {url}")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_top_headlines(
    category: str = "business",
    country: str = "us",
    query: str = "",
    max_records: int = 20,
    sources: str = "",
) -> str:
    """
    Get top headlines via NewsAPI.org. No per-request rate limit (100 req/day free tier).
    Requires a free API key configured via configure().

    Args:
        category: News category — business, entertainment, general, health, science, sports,
                  technology (default: business). Ignored when sources is set.
        country: Country code. Currently only "us" is supported by NewsAPI (default: us).
                 Ignored when sources is set.
        query: Optional keyword filter within headlines (e.g. "Fed rate", "NVIDIA")
        max_records: Max articles to return, 1–100 (default: 20)
        sources: Comma-separated NewsAPI source IDs (e.g. "bloomberg,reuters,financial-post").
                 When set, country and category are ignored (NewsAPI restriction).
                 Common IDs: bloomberg, reuters, the-wall-street-journal, financial-times,
                 cnbc, business-insider, fortune, financial-post
    """
    key = _load_newsapi_key()
    if not key:
        return (
            "NewsAPI key not configured. "
            "Get a free key at https://newsapi.org/register, "
            "then call configure(newsapi_key='...')."
        )
    try:
        max_records = max(1, min(100, max_records))
        params: dict = {"pageSize": max_records, "apiKey": key}

        if sources:
            params["sources"] = sources
        else:
            params["country"] = country
            params["category"] = category
        if query:
            params["q"] = query

        r = requests.get(f"{NEWSAPI_BASE}/top-headlines", params=params, timeout=25)
        data = r.json()

        if data.get("status") != "ok":
            code = data.get("code", "")
            msg = data.get("message", str(data))
            if code == "apiKeyInvalid":
                return f"Invalid API key. {msg}"
            if code == "rateLimited":
                return "NewsAPI daily limit (100 req) reached. Resets at midnight UTC."
            return f"NewsAPI error [{code}]: {msg}"

        articles = data.get("articles", [])
        total = data.get("totalResults", 0)
        if not articles:
            label = sources or f"{country}/{category}"
            return f"No headlines found for [{label}]{' query=' + repr(query) if query else ''}."

        label = sources if sources else f"{country} / {category}"
        lines = [f"=== Top Headlines: {label}{' · ' + query if query else ''} — {len(articles)} of {total} ===\n"]
        for art in articles:
            pub = art.get("publishedAt", "")[:16].replace("T", " ")
            source = art.get("source", {}).get("name", "")
            title = art.get("title", "(no title)")
            desc = art.get("description") or ""
            url = art.get("url", "")

            lines.append(f"[{pub}] {source}")
            lines.append(f"  {title}")
            if desc:
                lines.append(f"  {desc[:150]}")
            lines.append(f"  {url}")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def gdelt_get(params: dict) -> dict | str:
    """Call GDELT DOC API v2. Returns parsed JSON or raises on error."""
    r = requests.get(GDELT_DOC, params=params, timeout=25)
    if r.status_code == 429:
        raise RuntimeError("GDELT rate limit: please wait 5 seconds between requests.")
    r.raise_for_status()
    return r.json()


@mcp.tool()
def search_news(query: str, timespan: str = "7d", max_records: int = 20) -> str:
    """
    Search global news articles via GDELT. Covers 100+ languages, 65+ countries.
    No API key required.

    Args:
        query: Search query — company name, ticker, person, event (e.g. "Apple Inc", "Federal Reserve")
        timespan: Time window: 1d, 3d, 7d, 14d, 30d (default: 7d)
        max_records: Max articles to return, 1–250 (default: 20)
    """
    try:
        max_records = max(1, min(250, max_records))
        data = gdelt_get({
            "query": query,
            "mode": "ArtList",
            "timespan": timespan,
            "maxrecords": max_records,
            "format": "json",
            "sortby": "DateDesc",
        })
        articles = data.get("articles", [])
        if not articles:
            return f"No articles found for '{query}' in the last {timespan}."

        lines = [f"=== GDELT News: '{query}' (last {timespan}) — {len(articles)} articles ===\n"]
        for art in articles:
            # Parse seendate: "20260313T214500Z" → "2026-03-13 21:45"
            raw_date = art.get("seendate", "")
            if len(raw_date) >= 13:
                date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]} {raw_date[9:11]}:{raw_date[11:13]}"
            else:
                date_str = raw_date
            title = art.get("title", "(no title)")
            domain = art.get("domain", "")
            country = art.get("sourcecountry", "")
            language = art.get("language", "")
            url = art.get("url", "")

            lines.append(f"[{date_str}] {domain} ({country})")
            lines.append(f"  {title}")
            if language and language != "English":
                lines.append(f"  Language: {language}")
            lines.append(f"  {url}")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_news_sentiment(query: str, timespan: str = "7d") -> str:
    """
    Get hourly news sentiment timeline for a topic via GDELT.
    Tone score: positive = optimistic coverage, negative = pessimistic/critical.
    No API key required.

    Args:
        query: Topic to track — company name, person, event, country
        timespan: Time window: 1d, 3d, 7d, 14d, 30d (default: 7d)
    """
    try:
        data = gdelt_get({
            "query": query,
            "mode": "TimelineTone",
            "timespan": timespan,
            "format": "json",
        })

        timeline_list = data.get("timeline", [])
        if not timeline_list:
            return f"No sentiment data for '{query}' in the last {timespan}."

        # Find the "Average Tone" series
        tone_series = next(
            (s for s in timeline_list if "tone" in s.get("series", "").lower()),
            timeline_list[0],
        )
        points = tone_series.get("data", [])
        if not points:
            return f"Empty sentiment data for '{query}'."

        # Aggregate hourly → daily averages
        daily: dict[str, list[float]] = {}
        for pt in points:
            raw = pt.get("date", "")
            day = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}" if len(raw) >= 8 else raw
            val = pt.get("value")
            if val is not None:
                daily.setdefault(day, []).append(float(val))

        lines = [f"=== GDELT Sentiment: '{query}' (last {timespan}) ===\n"]
        lines.append(f"Tone scale: positive = bullish/optimistic, negative = bearish/critical\n")
        lines.append(f"{'Date':<12} {'Avg Tone':>10} {'Samples':>9} {'Sentiment'}")
        lines.append("-" * 50)

        for day in sorted(daily.keys()):
            vals = daily[day]
            avg = sum(vals) / len(vals)
            if avg > 1.0:
                label = "Positive"
            elif avg < -1.0:
                label = "Negative"
            else:
                label = "Neutral"
            lines.append(f"{day:<12} {avg:>10.3f} {len(vals):>9}   {label}")

        all_vals = [v for vs in daily.values() for v in vs]
        overall = sum(all_vals) / len(all_vals) if all_vals else 0
        lines.append(f"\nOverall avg tone: {overall:.3f}  ({len(all_vals)} data points)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def batch_news(requests_json: str) -> str:
    """
    Batch fetch news for multiple queries. Automatically inserts a 5-second delay between
    consecutive GDELT calls (search_news / get_news_sentiment) to respect its IP-based rate
    limit. NewsAPI calls (search_newsapi) have no per-request rate limit and are not delayed.

    Args:
        requests_json: JSON array of request objects. Each must have an "api" field plus params:
            - "search_news":        query, timespan (default "7d"), max_records (default 20)
            - "get_news_sentiment": query, timespan (default "7d")
            - "search_newsapi":     query, days (default 7), language (default "en"),
                                    max_records (default 20), sort_by (default "publishedAt")
            - "get_top_headlines":  category (default "business"), country (default "us"),
                                    query (default ""), max_records (default 20),
                                    sources (default "")

            Example:
            [
              {"api": "get_top_headlines", "category": "business", "country": "us"},
              {"api": "get_top_headlines", "sources": "bloomberg,reuters", "query": "Fed"},
              {"api": "search_newsapi", "query": "NVIDIA earnings", "days": 3},
              {"api": "search_news",    "query": "Apple Inc", "timespan": "3d"},
              {"api": "get_news_sentiment", "query": "China trade war", "timespan": "14d"}
            ]
    """
    try:
        items = json.loads(requests_json)
    except json.JSONDecodeError as e:
        return f"Error: invalid JSON — {e}"

    if not isinstance(items, list) or not items:
        return "Error: requests_json must be a non-empty JSON array."

    results = []
    prev_was_gdelt = False

    for i, item in enumerate(items):
        api = item.get("api")
        is_gdelt = api in GDELT_APIS

        # Only sleep when transitioning between or within GDELT calls
        if i > 0 and (is_gdelt or prev_was_gdelt):
            time.sleep(5)

        if api == "search_news":
            result = search_news(
                query=item.get("query", ""),
                timespan=item.get("timespan", "7d"),
                max_records=int(item.get("max_records", 20)),
            )
        elif api == "get_news_sentiment":
            result = get_news_sentiment(
                query=item.get("query", ""),
                timespan=item.get("timespan", "7d"),
            )
        elif api == "search_newsapi":
            result = search_newsapi(
                query=item.get("query", ""),
                days=int(item.get("days", 7)),
                language=item.get("language", "en"),
                max_records=int(item.get("max_records", 20)),
                sort_by=item.get("sort_by", "publishedAt"),
            )
        elif api == "get_top_headlines":
            result = get_top_headlines(
                category=item.get("category", "business"),
                country=item.get("country", "us"),
                query=item.get("query", ""),
                max_records=int(item.get("max_records", 20)),
                sources=item.get("sources", ""),
            )
        else:
            result = f"Error: unknown api '{api}'. Use 'search_news', 'get_news_sentiment', 'search_newsapi', or 'get_top_headlines'."

        results.append(f"--- [{i+1}/{len(items)}] {api}: {item.get('query', '')} ---\n{result}")
        prev_was_gdelt = is_gdelt

    return "\n\n".join(results)


if __name__ == "__main__":
    mcp.run()
