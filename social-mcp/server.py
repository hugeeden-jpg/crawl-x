#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
# ]
# ///
"""
Social MCP Server — Twitter/X (xreach CLI), Reddit (public JSON API), YouTube (yt-dlp)
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_brew_ca = Path("/opt/homebrew/etc/openssl@3/cert.pem")
if _brew_ca.exists():
    os.environ.setdefault("REQUESTS_CA_BUNDLE", str(_brew_ca))

import requests
from mcp.server.fastmcp import FastMCP

CONFIG_FILE = Path.home() / ".config" / "social-mcp" / "config.json"

mcp = FastMCP("social-data")


def load_config() -> dict:
    cfg = {"auth_token": "", "ct0": ""}
    if CONFIG_FILE.exists():
        file_cfg = json.loads(CONFIG_FILE.read_text())
        cfg["auth_token"] = file_cfg.get("auth_token", "")
        cfg["ct0"] = file_cfg.get("ct0", "")
    cfg["auth_token"] = os.environ.get("TWITTER_AUTH_TOKEN", cfg["auth_token"])
    cfg["ct0"] = os.environ.get("TWITTER_CT0", cfg["ct0"])
    return cfg


# ── Twitter / X ───────────────────────────────────────────────────────────────

@mcp.tool()
def configure_twitter(auth_token: str, ct0: str) -> str:
    """
    Save Twitter/X cookie credentials for xreach CLI

    Args:
        auth_token: Value of the auth_token cookie from x.com
        ct0: Value of the ct0 cookie from x.com
    """
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"auth_token": auth_token, "ct0": ct0}, indent=2))
    return f"Twitter credentials saved to {CONFIG_FILE}"


def _xreach(args: list[str]) -> str:
    """Run an xreach CLI command and return stdout, or an error string."""
    xreach = shutil.which("xreach")
    if not xreach:
        return (
            "xreach CLI not found. Install it with:\n"
            "  npm install -g xreach-cli\n"
            "Then configure cookies: configure_twitter(auth_token=..., ct0=...)"
        )
    cfg = load_config()
    cmd = [xreach] + args
    if cfg["auth_token"]:
        cmd += ["--auth-token", cfg["auth_token"]]
    if cfg["ct0"]:
        cmd += ["--ct0", cfg["ct0"]]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        out = r.stdout.strip()
        err = r.stderr.strip()
        if r.returncode != 0:
            return f"xreach error: {err or out}"
        return out
    except subprocess.TimeoutExpired:
        return "Error: xreach command timed out after 30s"
    except Exception as e:
        return f"Error running xreach: {e}"


def _format_tweets(raw: str, header: str) -> str:
    """Parse xreach JSON output into readable text.

    xreach returns {"items": [...], "cursor": ..., "hasMore": ...} for list commands,
    or a single tweet object for `xreach tweet ID`.
    Each tweet uses camelCase fields: createdAt, likeCount, retweetCount,
    user.name, user.screenName.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw  # not JSON — return as-is

    # Unwrap xreach envelope: {"items": [...]} → list of tweets
    if isinstance(data, dict) and "items" in data:
        tweets = data["items"]
    elif isinstance(data, list):
        tweets = data
    else:
        tweets = [data]  # single tweet object

    if not tweets:
        return f"=== {header} ===\n\nNo results found."

    lines = [f"=== {header} ===\n"]
    for tw in tweets:
        user_obj = tw.get("user", {}) if isinstance(tw.get("user"), dict) else {}
        author = user_obj.get("name", "")
        handle = user_obj.get("screenName", "")
        if handle and not handle.startswith("@"):
            handle = f"@{handle}"
        text = tw.get("text", tw.get("full_text", ""))
        created = str(tw.get("createdAt", tw.get("created_at", "")))[:25]
        likes = tw.get("likeCount", tw.get("favorite_count", ""))
        retweets = tw.get("retweetCount", tw.get("retweet_count", ""))
        views = tw.get("viewCount", "")
        tweet_id = tw.get("id", "")

        meta_parts = []
        if author or handle:
            meta_parts.append(f"{author} {handle}".strip())
        if created:
            meta_parts.append(f"[{created}]")
        lines.append("  ".join(meta_parts))
        lines.append(f"  {text}")

        stats = []
        if likes != "":
            stats.append(f"likes:{likes}")
        if retweets != "":
            stats.append(f"RT:{retweets}")
        if views != "":
            stats.append(f"views:{views}")
        if stats:
            lines.append("  " + "  ".join(stats))
        if tweet_id:
            lines.append(f"  https://x.com/i/web/status/{tweet_id}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def search_tweets(query: str, n: int = 10) -> str:
    """
    Search Twitter/X for recent tweets matching a query

    Args:
        query: Search query (supports $TICKER, #hashtag, from:user, etc.)
        n: Number of results (default: 10)
    """
    raw = _xreach(["search", query, "-n", str(n), "--json"])
    if raw.startswith("xreach") or raw.startswith("Error"):
        return raw
    return _format_tweets(raw, f"Twitter Search: {query}")


@mcp.tool()
def get_tweet(url_or_id: str) -> str:
    """
    Get a single tweet by URL or tweet ID

    Args:
        url_or_id: Tweet URL (https://x.com/user/status/ID) or numeric tweet ID
    """
    raw = _xreach(["tweet", url_or_id, "--json"])
    if raw.startswith("xreach") or raw.startswith("Error"):
        return raw
    return _format_tweets(raw, f"Tweet: {url_or_id}")


@mcp.tool()
def get_user_timeline(username: str, n: int = 20) -> str:
    """
    Get recent tweets from a Twitter/X user's timeline

    Args:
        username: Twitter username (with or without @)
        n: Number of tweets to fetch (default: 20)
    """
    handle = f"@{username.lstrip('@')}"
    raw = _xreach(["tweets", handle, "-n", str(n), "--json"])
    if raw.startswith("xreach") or raw.startswith("Error"):
        return raw
    return _format_tweets(raw, f"Timeline: {handle}")


@mcp.tool()
def get_thread(url_or_id: str) -> str:
    """
    Get a full Twitter/X thread by URL or tweet ID

    Args:
        url_or_id: URL or ID of any tweet in the thread
    """
    raw = _xreach(["thread", url_or_id, "--json"])
    if raw.startswith("xreach") or raw.startswith("Error"):
        return raw
    return _format_tweets(raw, f"Thread: {url_or_id}")


# ── Reddit ────────────────────────────────────────────────────────────────────

_REDDIT_HEADERS = {"User-Agent": "social-mcp/1.0"}


def _reddit_get(url: str, params: dict = None) -> dict:
    r = requests.get(url, headers=_REDDIT_HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _format_reddit_posts(posts: list, header: str) -> str:
    lines = [f"=== {header} ===\n"]
    lines.append(f"{'Score':>7}  {'Comments':>8}  {'Subreddit':<22}  Title")
    lines.append("-" * 85)
    for post in posts:
        d = post.get("data", post)
        score = d.get("score", 0)
        comments = d.get("num_comments", 0)
        sub = d.get("subreddit", "")
        title = d.get("title", "")[:72]
        ext_url = d.get("url", "")
        author = d.get("author", "")
        lines.append(f"{score:>7}  {comments:>8}  r/{sub:<20}  {title}")
        if ext_url and "reddit.com" not in ext_url:
            lines.append(f"         Link: {ext_url[:80]}")
        lines.append(f"         by u/{author}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def get_subreddit_posts(subreddit: str, sort: str = "hot", limit: int = 10) -> str:
    """
    Get posts from a subreddit (no authentication required)

    Args:
        subreddit: Subreddit name without r/ prefix (e.g. wallstreetbets, stocks)
        sort: Sorting method: hot, new, top, rising (default: hot)
        limit: Number of posts to return (default: 10, max: 25)
    """
    try:
        sort = sort.lower()
        if sort not in ("hot", "new", "top", "rising"):
            sort = "hot"
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
        data = _reddit_get(url, params={"limit": min(limit, 25)})
        posts = data.get("data", {}).get("children", [])
        if not posts:
            return f"No posts found in r/{subreddit}"
        return _format_reddit_posts(posts, f"r/{subreddit} ({sort})")
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def search_reddit(query: str, limit: int = 10, subreddit: str = "") -> str:
    """
    Search Reddit posts by keyword (no authentication required)

    Args:
        query: Search terms (e.g. 'NVDA earnings', 'Fed rate cut')
        limit: Number of results (default: 10, max: 25)
        subreddit: Restrict to this subreddit (optional, e.g. wallstreetbets)
    """
    try:
        limit = min(limit, 25)
        if subreddit:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {"q": query, "restrict_sr": "1", "limit": limit}
            header = f"Reddit Search: '{query}' in r/{subreddit}"
        else:
            url = "https://www.reddit.com/search.json"
            params = {"q": query, "limit": limit}
            header = f"Reddit Search: '{query}'"
        data = _reddit_get(url, params=params)
        posts = data.get("data", {}).get("children", [])
        if not posts:
            return f"No Reddit results for '{query}'"
        return _format_reddit_posts(posts, header)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_post_comments(post_url: str, limit: int = 20) -> str:
    """
    Get comments from a Reddit post

    Args:
        post_url: Full Reddit post URL (e.g. https://www.reddit.com/r/stocks/comments/abc123/title/)
        limit: Number of top-level comments to return (default: 20)
    """
    try:
        url = post_url.rstrip("/")
        if not url.endswith(".json"):
            url += ".json"
        data = _reddit_get(url, params={"limit": limit})
        if not isinstance(data, list) or len(data) < 2:
            return "Could not parse Reddit post response"

        post_data = data[0]["data"]["children"][0]["data"]
        title = post_data.get("title", "")
        author = post_data.get("author", "")
        score = post_data.get("score", 0)
        sub = post_data.get("subreddit", "")
        selftext = post_data.get("selftext", "").strip()

        lines = [f"=== r/{sub}: {title} ==="]
        lines.append(f"by u/{author}  |  score: {score}")
        if selftext:
            lines.append(f"\n{selftext[:800]}")
        lines.append(f"\n--- Top Comments ---")

        def fmt_comment(c, depth=0):
            if c.get("kind") == "more":
                return
            d = c.get("data", {})
            body = d.get("body", "").strip()
            if not body or body in ("[deleted]", "[removed]"):
                return
            c_author = d.get("author", "")
            c_score = d.get("score", 0)
            indent = "  " * depth
            lines.append(f"{indent}u/{c_author} ({c_score}):")
            for line in body[:400].splitlines():
                lines.append(f"{indent}  {line}")
            lines.append("")
            if depth < 2:
                replies = d.get("replies", {})
                if isinstance(replies, dict):
                    for reply in replies.get("data", {}).get("children", [])[:3]:
                        fmt_comment(reply, depth + 1)

        for c in data[1]["data"]["children"][:limit]:
            fmt_comment(c)

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ── YouTube ───────────────────────────────────────────────────────────────────

def _ytdlp_check() -> str | None:
    """Return None if yt-dlp is available, else an install instruction string."""
    if not shutil.which("yt-dlp"):
        return (
            "yt-dlp not found. Install it with:\n"
            "  uv tool install yt-dlp\n"
            "Node.js is also required for YouTube (https://nodejs.org/)."
        )
    return None


def _ytdlp_env() -> dict:
    """Subprocess env for yt-dlp: applies macOS Homebrew SSL CA bundle fix."""
    env = os.environ.copy()
    if _brew_ca.exists():
        env.setdefault("SSL_CERT_FILE", str(_brew_ca))
        env.setdefault("REQUESTS_CA_BUNDLE", str(_brew_ca))
    return env


@mcp.tool()
def get_video_info(url: str) -> str:
    """
    Get YouTube video metadata (title, channel, duration, views, description)

    Args:
        url: YouTube video URL
    """
    err = _ytdlp_check()
    if err:
        return err
    try:
        r = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-playlist", url],
            capture_output=True, text=True, timeout=30,
            env=_ytdlp_env(),
        )
        if r.returncode != 0:
            return f"yt-dlp error: {r.stderr.strip()[:500]}"
        data = json.loads(r.stdout.strip())
        dur = int(data.get("duration", 0) or 0)
        duration = f"{dur // 60}:{dur % 60:02d}"
        views = data.get("view_count")
        lines = [
            f"=== YouTube: {data.get('title', 'Unknown')} ===\n",
            f"Channel:   {data.get('uploader', data.get('channel', ''))}",
            f"Duration:  {duration}",
            f"Views:     {views:,}" if isinstance(views, int) else f"Views:     {views}",
            f"Likes:     {data.get('like_count', 'N/A')}",
            f"Uploaded:  {str(data.get('upload_date', ''))[:10] or 'N/A'}",
            f"URL:       {data.get('webpage_url', url)}",
            f"\nDescription:\n{str(data.get('description', ''))[:600]}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def _clean_vtt(vtt: str) -> str:
    """Strip VTT timing headers and deduplicate repeated caption lines."""
    lines = []
    seen: set[str] = set()
    for line in vtt.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        if "-->" in line:
            continue
        if line.startswith("align:") or line.startswith("position:"):
            continue
        # Remove inline VTT tags: <c>, </c>, <00:01:23.000>
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line:
            continue
        if line not in seen:
            seen.add(line)
            lines.append(line)
    return "\n".join(lines)


@mcp.tool()
def get_video_transcript(url: str, lang: str = "en") -> str:
    """
    Download and return the transcript/subtitles of a YouTube video

    Args:
        url: YouTube video URL
        lang: Language code (default: en). Falls back to auto-generated captions.
    """
    err = _ytdlp_check()
    if err:
        return err
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_tmpl = str(Path(tmpdir) / "%(id)s")
            r = subprocess.run(
                [
                    "yt-dlp",
                    "--write-sub", "--write-auto-sub",
                    "--sub-lang", f"{lang},en",
                    "--skip-download",
                    "--no-playlist",
                    "-o", out_tmpl,
                    url,
                ],
                capture_output=True, text=True, timeout=60,
                env=_ytdlp_env(),
            )
            vtt_files = list(Path(tmpdir).glob("*.vtt"))
            if not vtt_files:
                stderr = r.stderr.strip()
                if "has no subtitles" in stderr or "no closed captions" in stderr.lower():
                    return f"No subtitles available for this video (lang tried: {lang})"
                return f"No subtitle file downloaded.\nyt-dlp output:\n{stderr[:500]}"

            vtt_text = vtt_files[0].read_text(encoding="utf-8", errors="replace")
            text = _clean_vtt(vtt_text)
            lines = [f"=== YouTube Transcript: {url} ===\n", text]
            return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def search_youtube(query: str, n: int = 5) -> str:
    """
    Search YouTube and return video info for top results

    Args:
        query: Search query (e.g. 'NVDA earnings call 2025', 'Fed press conference')
        n: Number of results (default: 5)
    """
    err = _ytdlp_check()
    if err:
        return err
    try:
        r = subprocess.run(
            ["yt-dlp", "--dump-json", "--flat-playlist", f"ytsearch{n}:{query}"],
            capture_output=True, text=True, timeout=60,
            env=_ytdlp_env(),
        )
        if r.returncode != 0:
            return f"yt-dlp error: {r.stderr.strip()[:500]}"
        lines = [f"=== YouTube Search: {query} ===\n"]
        for raw_line in r.stdout.strip().splitlines():
            if not raw_line.strip():
                continue
            try:
                data = json.loads(raw_line)
                title = data.get("title", "Unknown")
                channel = data.get("channel", data.get("uploader", ""))
                dur = int(data.get("duration", 0) or 0)
                duration = f"{dur // 60}:{dur % 60:02d}" if dur else "?"
                vid_id = data.get("id", "")
                vid_url = (
                    f"https://www.youtube.com/watch?v={vid_id}"
                    if vid_id else data.get("url", "")
                )
                lines.append(f"{title}")
                lines.append(f"  Channel: {channel}  |  Duration: {duration}")
                lines.append(f"  {vid_url}")
                lines.append("")
            except json.JSONDecodeError:
                continue
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
