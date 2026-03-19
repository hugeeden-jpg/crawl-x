# Cookie Picker Chrome Extension — Design Spec

Date: 2026-03-19

## Overview

A Chrome extension (Manifest V3) that reads all cookies for the current tab, lets the user select individual key-value pairs, and copies them to the clipboard as a `key=value; key=value` string. Replaces the Cookie-Editor dependency documented in the crawl-x README for extracting Twitter `auth_token` and `ct0` cookies.

## Location

```
extensions/cookie-picker/
├── manifest.json
├── popup.html
├── popup.js
├── popup.css
└── config.json
```

## Architecture

- **Manifest V3 popup only** — no background service worker, no content script
- Uses `chrome.cookies.getAll({url})` to read all cookies for the active tab's URL, including `HttpOnly` cookies
- Permissions: `cookies`, `activeTab`
- No persistent state beyond `config.json`

## UI

Fixed popup width 380px. Cookie list area scrollable up to 400px height.

```
┌─────────────────────────────────────┐
│  Cookie Picker          [x.com]     │
├─────────────────────────────────────┤
│  Search key...                      │
├─────────────────────────────────────┤
│  [x] Select all (12 / 24)          │
├─────────────────────────────────────┤
│  [x] auth_token    abc123...        │
│  [x] ct0           xyz789...        │
│  [ ] _ga           GA1.2...         │
│  [ ] _gid          GA1.2...         │
│  ...                                │
├─────────────────────────────────────┤
│       [ Copy selected (2) ]         │
└─────────────────────────────────────┘
```

### Behavior

- **Search box**: real-time filter on cookie key (case-insensitive substring match)
- **Select all checkbox**: selects/deselects only the currently visible (filtered) cookies; shows count `(selected / total_visible)`
- **Value display**: truncated to 20 characters + `…` in the list; full value is copied
- **Copy button**: copies selected cookies as `key=value; key=value` (semicolon-space separated)
- **Copy feedback**: button label changes to `Copied!` for 1.5s then reverts

## Default Selection Config

`config.json` is bundled with the extension and read at popup load time. It maps hostnames to arrays of cookie keys that should be pre-checked by default.

```json
{
  "defaults": {
    "x.com": ["auth_token", "ct0"],
    "twitter.com": ["auth_token", "ct0"]
  }
}
```

- Matching is exact hostname (e.g. `x.com` does not match `api.x.com`)
- Keys listed in `defaults` that exist in the page's cookies are pre-checked
- All other cookies are unchecked by default
- If the current hostname has no entry, all cookies are unchecked by default
- To add a new site: edit `config.json`, then reload the extension at `chrome://extensions`

## Copy Format

```
auth_token=abc123def456; ct0=xyz789uvw012
```

Semicolon + space separator. Compatible with xreach CLI and curl `--cookie` header.

## Error States

- No cookies found: show "No cookies found for this page"
- `activeTab` permission not granted (e.g. internal chrome:// pages): show "Cannot read cookies on this page"
