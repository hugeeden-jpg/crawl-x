#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
# ]
# ///
"""
News MCP Server - GDELT Global News Events
Real-time global news search and sentiment timeline. No API key required.
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
from mcp.server.fastmcp import FastMCP

GDELT_DOC = "https://api.gdeltproject.org/api/v2/doc/doc"

mcp = FastMCP("news-data")


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
    Batch fetch news for multiple queries, with automatic 5-second rate limiting between requests.

    Args:
        requests_json: JSON array of request objects. Each object must have an "api" field
            ("search_news" or "get_news_sentiment") plus the corresponding parameters:
            - search_news: query (required), timespan (optional, default "7d"), max_records (optional, default 20)
            - get_news_sentiment: query (required), timespan (optional, default "7d")

            Example:
            [
              {"api": "search_news", "query": "Apple Inc", "timespan": "3d", "max_records": 10},
              {"api": "get_news_sentiment", "query": "Federal Reserve", "timespan": "7d"}
            ]
    """
    try:
        items = json.loads(requests_json)
    except json.JSONDecodeError as e:
        return f"Error: invalid JSON — {e}"

    if not isinstance(items, list) or not items:
        return "Error: requests_json must be a non-empty JSON array."

    results = []
    for i, item in enumerate(items):
        if i > 0:
            time.sleep(5)

        api = item.get("api")
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
        else:
            result = f"Error: unknown api '{api}'. Use 'search_news' or 'get_news_sentiment'."

        results.append(f"--- [{i+1}/{len(items)}] {api}: {item.get('query', '')} ---\n{result}")

    return "\n\n".join(results)


if __name__ == "__main__":
    mcp.run()
