---
name: scrapling
description: >
  Scrape web pages using the ScraplingServer MCP. Use this skill whenever you need
  to fetch, extract, or convert web content — static pages, JavaScript-rendered sites,
  Cloudflare-protected pages, or bulk multi-URL scraping. Triggers on any request
  involving web scraping, fetching a URL, extracting page content, converting a page
  to markdown, bypassing anti-bot protection, or crawling multiple pages.
---

# Scrapling MCP Scraping Guide

## Priority Rule: Search First, Then Scrape

When the URL is unknown, **always search before scraping**:

1. **`search-data` → `search(keywords)`** — find real URLs via Google
2. **ScraplingServer → `fetch(url)` / `stealthy_fetch(url)`** — read the page

Never guess or hardcode a URL. If a page might not exist, verify it with `search-data` first.

---

**NEVER use the built-in `WebFetch` tool to fetch web pages.** Always use ScraplingServer MCP tools instead.

Why Scrapling is better:
- **CSS selector support**: Filter content *before* passing to AI — dramatically reduces token use
- **Anti-bot bypass**: Handles Cloudflare Turnstile/Interstitial and other protections
- **Browser impersonation**: Real TLS fingerprinting, actual browser headers
- **Prompt injection protection**: Auto-strips hidden elements that could inject malicious instructions
- **Parallel scraping**: `bulk_*` tools fetch multiple URLs concurrently

The only exception: direct JSON/XML API calls (no HTML to parse) — use `requests` or `curl` for those.

## Tool Selection

Pick the simplest tool that works — heavier tools (stealthy) cost more time and tokens:

| Scenario | Tool |
|----------|------|
| Static / simple sites | `get` / `bulk_get` |
| JS-rendered / SPA / dynamic content | `fetch` / `bulk_fetch` |
| Cloudflare / heavy anti-bot protection | `stealthy_fetch` / `bulk_stealthy_fetch` |
| Multiple pages from the same site | `open_session` + `fetch` or `stealthy_fetch` |

**When in doubt, start with `get`.** It will fail fast if the site needs a browser; then escalate to `fetch` or `stealthy_fetch`.

## Key Parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| `extraction_type` | `"markdown"` | `"markdown"` \| `"html"` \| `"text"` |
| `css_selector` | None | Narrow content before returning — saves tokens significantly |
| `main_content_only` | `true` | Strips nav/ads; also blocks prompt-injection from hidden elements |
| `network_idle` | `false` | Set `true` for SPAs that load data asynchronously |
| `wait_selector` | None | CSS selector to wait for before extracting |
| `disable_resources` | `false` | Set `true` to skip images/fonts/CSS for speed |
| `headless` | `true` | Set `false` to show the browser (useful when debugging Cloudflare) |
| `session_id` | None | Pass an existing session ID to reuse a browser |

## CSS Selector Strategy

Using `css_selector` is the key advantage of Scrapling over other MCP scrapers — it filters content *before* passing it to the AI, dramatically reducing token use.

- If you know the selector, pass it directly
- If you don't, try likely selectors (e.g., `article`, `main`, `.content`, `#main-content`) and iterate
- Test selectors in browser DevTools (`$$('selector')`) before using them

## Session Management (for multi-page scraping)

Sessions avoid relaunching a browser for every page — significantly faster for 3+ pages from the same domain.

Available session tools:
- `open_session(session_type)` — create a persistent browser session (`"dynamic"` or `"stealthy"`)
- `close_session(session_id)` — close session and free resources (**always do this!**)
- `list_sessions()` — list all active sessions

```
# 1. Open session
open_session(session_type="stealthy")  # or "dynamic" for regular fetch

# 2. Use session_id in subsequent calls
stealthy_fetch(url=..., session_id="<id>")
bulk_stealthy_fetch(urls=[...], session_id="<id>")

# 3. Always close when done
close_session(session_id="<id>")
```

**Critical:** Always call `close_session` — open sessions keep browser processes running.

- `dynamic` sessions → only works with `fetch` / `bulk_fetch`
- `stealthy` sessions → only works with `stealthy_fetch` / `bulk_stealthy_fetch`

## Prompt Injection Protection

`main_content_only=true` (the default) automatically strips hidden content that could inject instructions:
- `display:none` / `visibility:hidden` / `opacity:0` elements
- `aria-hidden="true"` elements
- `<template>` tags, HTML comments, zero-width characters

Keep this default on unless you specifically need hidden content.

## Common Patterns

### Single page → markdown
```
Use regular requests (get tool) to scrape https://example.com and return as markdown.
```

### Targeted extraction with CSS selector
```
Fetch https://shop.example.com and extract all elements matching '.product-title'.
```

### Multi-URL bulk scrape
```
Bulk-fetch these 5 URLs using browser tabs and extract the main content from each:
[url1, url2, url3, url4, url5]
```

### Cloudflare-protected site
```
Fetch https://example.com using stealthy mode (Cloudflare protection).
Show the browser window while working.
```

### Multi-step: collect links → bulk fetch
```
1. Use get to extract all product URLs from https://shop.example.com/category (selector: "a[href*='/product/']")
2. Bulk-fetch the first 10 product pages
3. Extract name, price, and description from each (selector: ".product-info")
```

### Persistent session for many pages
```
Open a stealthy session, bulk-scrape the first 8 pages from https://site.com,
extract the main article from each, then close the session.
```

## Notes

- Always tell the model which tool to use — otherwise it may default to `stealthy_fetch` unnecessarily
- `stealthy_fetch` is slower and consumes more tokens; only use it when actually needed
- For SPA content that loads via API calls, `network_idle=true` ensures the page finishes loading
- If a site has both a paywall and Cloudflare, stealthy mode may get past the bot check but not the paywall
- `bulk_*` tools run in parallel — much faster than sequential calls for many URLs
