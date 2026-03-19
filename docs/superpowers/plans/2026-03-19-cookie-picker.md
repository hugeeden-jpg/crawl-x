# Cookie Picker Chrome Extension Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Manifest V3 Chrome popup extension that reads all cookies for the active tab, lets the user select key-value pairs with per-host defaults, and copies them as `key=value; key=value`.

**Architecture:** Popup-only MV3 extension (no background worker, no content script). `popup.js` calls `chrome.cookies.getAll({url})` on load, reads `config.json` via `fetch(chrome.runtime.getURL(...))` to determine default-checked keys, then renders the full UI. All logic lives in `popup.js`; styles in `popup.css`; structure in `popup.html`.

**Tech Stack:** Vanilla JS (ES2020), HTML5, CSS3, Chrome Extensions Manifest V3 (`chrome.cookies`, `chrome.tabs`, `navigator.clipboard`)

---

## File Map

| File | Responsibility |
|------|----------------|
| `extensions/cookie-picker/manifest.json` | MV3 manifest — permissions, popup entry, web_accessible_resources |
| `extensions/cookie-picker/config.json` | Per-host default-checked cookie keys |
| `extensions/cookie-picker/popup.html` | Static shell — search, select-all, list container, copy button |
| `extensions/cookie-picker/popup.css` | Layout, colors, truncation, disabled states, copy feedback animation |
| `extensions/cookie-picker/popup.js` | All runtime logic: load cookies, apply config, filter, copy |

---

## How to Load the Extension in Chrome

Every task ends with manual verification. Load once; reload as needed:

1. Open `chrome://extensions`
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked" → select `extensions/cookie-picker/`
4. Pin the extension icon to the toolbar
5. To reload after a code change: click the circular-arrow reload icon on the extension card

---

## Task 1: Scaffold — manifest + config + empty files

**Files:**
- Create: `extensions/cookie-picker/manifest.json`
- Create: `extensions/cookie-picker/config.json`
- Create: `extensions/cookie-picker/popup.html` (empty shell)
- Create: `extensions/cookie-picker/popup.css` (empty)
- Create: `extensions/cookie-picker/popup.js` (empty)

- [ ] **Step 1: Create directory**

```bash
mkdir -p /Users/eden/crawl-x/extensions/cookie-picker
```

- [ ] **Step 2: Create manifest.json**

```json
{
  "manifest_version": 3,
  "name": "Cookie Picker",
  "version": "1.0.0",
  "description": "Select and copy cookies as key=value strings",
  "action": {
    "default_popup": "popup.html",
    "default_title": "Cookie Picker"
  },
  "permissions": ["cookies", "activeTab"],
  "host_permissions": ["<all_urls>"],
  "web_accessible_resources": [
    {
      "resources": ["config.json"],
      "matches": ["<all_urls>"]
    }
  ]
}
```

- [ ] **Step 3: Create config.json**

```json
{
  "defaults": {
    "x.com": ["auth_token", "ct0"],
    "twitter.com": ["auth_token", "ct0"]
  }
}
```

- [ ] **Step 4: Create empty popup.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <script src="popup.js"></script>
</body>
</html>
```

- [ ] **Step 5: Create empty popup.css and popup.js**

```bash
touch /Users/eden/crawl-x/extensions/cookie-picker/popup.css
touch /Users/eden/crawl-x/extensions/cookie-picker/popup.js
```

- [ ] **Step 6: Load unpacked in Chrome, verify no errors**

Go to `chrome://extensions` → Load unpacked → select `extensions/cookie-picker/`.
Expected: Extension appears in the list with no errors. Clicking the icon opens a blank popup.

- [ ] **Step 7: Commit**

```bash
git add extensions/cookie-picker/
git commit -m "feat(cookie-picker): scaffold MV3 extension with manifest and config"
```

---

## Task 2: Static HTML structure + CSS layout

**Files:**
- Modify: `extensions/cookie-picker/popup.html`
- Modify: `extensions/cookie-picker/popup.css`

- [ ] **Step 1: Write popup.html with full structure**

Replace the empty popup.html with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div id="app">
    <!-- Header -->
    <div id="header">
      <span id="title">Cookie Picker</span>
      <span id="hostname"></span>
    </div>

    <!-- Error state (hidden by default) -->
    <div id="error" class="hidden">
      <span id="error-message"></span>
    </div>

    <!-- Main content (hidden when error shown) -->
    <div id="content">
      <!-- Search -->
      <div id="search-wrap">
        <input id="search" type="text" placeholder="Search key..." autocomplete="off" spellcheck="false">
      </div>

      <!-- Select all -->
      <div id="select-all-wrap">
        <label id="select-all-label">
          <input id="select-all" type="checkbox">
          <span id="select-all-text">Select all</span>
          <span id="count"></span>
        </label>
      </div>

      <!-- Cookie list -->
      <div id="list-wrap">
        <div id="cookie-list"></div>
        <div id="empty-search" class="hidden">No cookies match</div>
      </div>

      <!-- Copy button -->
      <div id="footer">
        <button id="copy-btn" disabled>Copy selected</button>
      </div>
    </div>
  </div>

  <script src="popup.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write popup.css**

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 13px;
  width: 380px;
  background: #fff;
  color: #1a1a1a;
}

#app { display: flex; flex-direction: column; }

/* Header */
#header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px 8px;
  border-bottom: 1px solid #e5e5e5;
  background: #f8f8f8;
}
#title { font-weight: 600; font-size: 14px; }
#hostname { font-size: 11px; color: #666; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Error */
#error {
  padding: 24px 16px;
  text-align: center;
  color: #666;
  font-size: 13px;
}

/* Search */
#search-wrap { padding: 8px 10px; border-bottom: 1px solid #e5e5e5; }
#search {
  width: 100%;
  padding: 5px 8px;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-size: 13px;
  outline: none;
}
#search:focus { border-color: #4a90e2; }

/* Select all */
#select-all-wrap {
  padding: 6px 10px;
  border-bottom: 1px solid #e5e5e5;
  background: #fafafa;
}
#select-all-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
}
#select-all-label input { cursor: pointer; }
#select-all-label input:disabled { cursor: not-allowed; opacity: 0.5; }
#select-all-text { font-weight: 500; }
#count { color: #888; font-size: 12px; }

/* Cookie list */
#list-wrap {
  max-height: 340px;
  overflow-y: auto;
}
#cookie-list { display: flex; flex-direction: column; }

.cookie-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 10px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
}
.cookie-row:hover { background: #f5f9ff; }
.cookie-row input[type="checkbox"] { flex-shrink: 0; cursor: pointer; }
.cookie-key { font-weight: 500; min-width: 100px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cookie-value { color: #888; font-size: 12px; font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }

#empty-search {
  padding: 20px;
  text-align: center;
  color: #999;
  font-size: 12px;
}

/* Footer */
#footer {
  padding: 8px 10px;
  border-top: 1px solid #e5e5e5;
  background: #fafafa;
}
#copy-btn {
  width: 100%;
  padding: 7px;
  background: #4a90e2;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
#copy-btn:hover:not(:disabled) { background: #357abd; }
#copy-btn:disabled { background: #b0c8e8; cursor: not-allowed; }
#copy-btn.copied { background: #34a853; }

/* Utility */
.hidden { display: none !important; }
```

- [ ] **Step 3: Reload extension, open popup, verify static layout**

Expected: Popup shows header, search box, "Select all" row, empty list area, and a disabled grey "Copy selected" button. No JS errors in the extension popup devtools (right-click popup → Inspect).

- [ ] **Step 4: Commit**

```bash
git add extensions/cookie-picker/popup.html extensions/cookie-picker/popup.css
git commit -m "feat(cookie-picker): add static popup HTML structure and CSS layout"
```

---

## Task 3: Cookie loading + config-based default selection

**Files:**
- Modify: `extensions/cookie-picker/popup.js`

This task implements the core data layer: get the active tab URL, fetch `config.json`, read all cookies, determine which are pre-checked.

- [ ] **Step 1: Write popup.js — load phase**

```js
// popup.js

let allCookies = [];      // [{name, value, checked}]
let filteredCookies = []; // subset visible after search
let copyTimer = null;

async function loadConfig() {
  try {
    const url = chrome.runtime.getURL('config.json');
    const res = await fetch(url);
    const data = await res.json();
    return data.defaults || {};
  } catch {
    return {};
  }
}

async function getActiveTabUrl() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab?.url || '';
}

function hostnameFrom(url) {
  try { return new URL(url).hostname.toLowerCase(); } catch { return ''; }
}

function defaultKeysForHost(hostname, defaults) {
  for (const [host, keys] of Object.entries(defaults)) {
    if (host.toLowerCase() === hostname) {
      return keys.map(k => k.toLowerCase());
    }
  }
  return null; // no match → nothing pre-checked
}

async function init() {
  const [tabUrl, defaults] = await Promise.all([getActiveTabUrl(), loadConfig()]);
  const hostname = hostnameFrom(tabUrl);

  document.getElementById('hostname').textContent = hostname || '—';

  let cookies;
  try {
    cookies = await chrome.cookies.getAll({ url: tabUrl });
  } catch (e) {
    showError('Cannot read cookies on this page');
    return;
  }

  if (!cookies || cookies.length === 0) {
    showError('No cookies found for this page');
    return;
  }

  const defaultKeys = defaultKeysForHost(hostname, defaults);

  allCookies = cookies.map(c => ({
    name: c.name,
    value: c.value,
    checked: defaultKeys !== null
      ? defaultKeys.includes(c.name.toLowerCase())
      : false,
  }));

  filteredCookies = [...allCookies];
  renderList();
  updateControls();
}

function showError(msg) {
  document.getElementById('content').classList.add('hidden');
  document.getElementById('error-message').textContent = msg;
  document.getElementById('error').classList.remove('hidden');
}

document.addEventListener('DOMContentLoaded', init);
```

- [ ] **Step 2: Add stub renderList and updateControls (just console.log for now)**

Append to popup.js:

```js
function renderList() {
  console.log('cookies loaded:', allCookies.length, allCookies);
}

function updateControls() {
  // stub
}
```

- [ ] **Step 3: Reload and manually verify on x.com**

Navigate to `https://x.com` in a tab. Click the extension icon.
Open popup DevTools (right-click popup → Inspect → Console).
Expected: `cookies loaded: N [...]` log with at least `auth_token` and `ct0` having `checked: true`.

- [ ] **Step 4: Verify error state on chrome:// page**

Navigate to `chrome://extensions`, click the icon.
Expected: Popup shows "Cannot read cookies on this page" with no list or buttons.

- [ ] **Step 5: Commit**

```bash
git add extensions/cookie-picker/popup.js
git commit -m "feat(cookie-picker): load cookies and apply config-based default selection"
```

---

## Task 4: Render cookie list + search filter + select-all

**Files:**
- Modify: `extensions/cookie-picker/popup.js`

Replace the stub `renderList` and `updateControls` with full implementations.

- [ ] **Step 1: Replace renderList with real implementation**

Replace the stub `renderList` function:

```js
function truncate(str, n = 20) {
  return str.length > n ? str.slice(0, n) + '…' : str;
}

function renderList() {
  const list = document.getElementById('cookie-list');
  const emptySearch = document.getElementById('empty-search');
  list.innerHTML = '';

  if (filteredCookies.length === 0) {
    emptySearch.classList.remove('hidden');
    return;
  }
  emptySearch.classList.add('hidden');

  for (const cookie of filteredCookies) {
    const row = document.createElement('label');
    row.className = 'cookie-row';

    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = cookie.checked;
    cb.addEventListener('change', () => {
      // sync back to allCookies
      const master = allCookies.find(c => c.name === cookie.name);
      if (master) master.checked = cb.checked;
      cookie.checked = cb.checked;
      updateControls();
    });

    const keyEl = document.createElement('span');
    keyEl.className = 'cookie-key';
    keyEl.textContent = cookie.name;
    keyEl.title = cookie.name;

    const valEl = document.createElement('span');
    valEl.className = 'cookie-value';
    valEl.textContent = truncate(cookie.value);
    valEl.title = cookie.value;

    row.appendChild(cb);
    row.appendChild(keyEl);
    row.appendChild(valEl);
    list.appendChild(row);
  }
}
```

- [ ] **Step 2: Replace updateControls with real implementation**

Replace the stub `updateControls` function:

```js
function updateControls() {
  const selectedVisible = filteredCookies.filter(c => c.checked).length;
  const totalVisible = filteredCookies.length;
  const totalSelected = allCookies.filter(c => c.checked).length;

  // Select-all checkbox
  const selectAll = document.getElementById('select-all');
  const countEl = document.getElementById('count');
  const noResults = totalVisible === 0;

  selectAll.disabled = noResults;
  selectAll.checked = !noResults && selectedVisible === totalVisible;
  selectAll.indeterminate = !noResults && selectedVisible > 0 && selectedVisible < totalVisible;
  countEl.textContent = noResults ? '' : `(${selectedVisible} / ${totalVisible})`;

  // Copy button
  const copyBtn = document.getElementById('copy-btn');
  copyBtn.disabled = totalSelected === 0;
  if (!copyBtn.classList.contains('copied')) {
    copyBtn.textContent = totalSelected > 0
      ? `Copy selected (${totalSelected})`
      : 'Copy selected';
  }
}
```

- [ ] **Step 3: Wire up search input**

Append to popup.js:

```js
document.getElementById('search').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  filteredCookies = allCookies.filter(c => c.name.toLowerCase().includes(q));
  renderList();
  updateControls();
});
```

- [ ] **Step 4: Wire up select-all checkbox**

Append to popup.js:

```js
document.getElementById('select-all').addEventListener('change', e => {
  const checked = e.target.checked;
  filteredCookies.forEach(c => { c.checked = checked; });
  // sync back to allCookies
  const filteredNames = new Set(filteredCookies.map(c => c.name));
  allCookies.forEach(c => { if (filteredNames.has(c.name)) c.checked = checked; });
  renderList();
  updateControls();
});
```

- [ ] **Step 5: Reload and manually verify**

Navigate to `https://x.com`. Open popup.
Expected:
- List shows all cookies; `auth_token` and `ct0` are pre-checked
- Typing `_g` in search filters to only `_g*` cookies
- "Select all" checkbox selects/deselects filtered results only
- Count label updates correctly
- Unchecking all cookies disables Copy button

- [ ] **Step 6: Verify indeterminate state**

Pre-check a few but not all cookies. Expected: Select-all shows indeterminate (dash) state.

- [ ] **Step 7: Commit**

```bash
git add extensions/cookie-picker/popup.js
git commit -m "feat(cookie-picker): render cookie list with search filter and select-all logic"
```

---

## Task 5: Copy to clipboard with feedback

**Files:**
- Modify: `extensions/cookie-picker/popup.js`

- [ ] **Step 1: Add copy handler**

Append to popup.js:

```js
document.getElementById('copy-btn').addEventListener('click', async () => {
  const selected = allCookies.filter(c => c.checked);
  if (selected.length === 0) return;

  const text = selected.map(c => `${c.name}=${c.value}`).join('; ');
  await navigator.clipboard.writeText(text);

  const btn = document.getElementById('copy-btn');
  btn.textContent = 'Copied!';
  btn.classList.add('copied');

  if (copyTimer) clearTimeout(copyTimer);
  copyTimer = setTimeout(() => {
    btn.classList.remove('copied');
    updateControls(); // restores correct label
  }, 1500);
});
```

- [ ] **Step 2: Reload and manually verify copy output**

Navigate to `https://x.com`. Open popup. Check `auth_token` and `ct0`. Click "Copy selected (2)".
Expected:
- Button shows "Copied!" in green for ~1.5s then reverts to "Copy selected (2)"
- Open a text editor and paste — should see: `auth_token=<value>; ct0=<value>`

- [ ] **Step 3: Verify rapid re-click resets timer**

Click Copy, immediately click again. Expected: "Copied!" stays green; timer restarts from second click.

- [ ] **Step 4: Commit**

```bash
git add extensions/cookie-picker/popup.js
git commit -m "feat(cookie-picker): add clipboard copy with Copied! feedback and timer reset"
```

---

## Task 6: Update README to reference cookie-picker

**Files:**
- Modify: `README.md`
- Modify: `README_zh.md`

- [ ] **Step 1: Update README.md Twitter cookie setup note**

Find this line in README.md:
```
> **Twitter cookie setup:** Install the [Cookie-Editor](https://cookie-editor.com/) browser extension, log in to x.com, and copy the `auth_token` and `ct0` cookie values. Then run `configure_twitter(auth_token=..., ct0=...)` in Claude, or pass them as env vars to `install.sh`.
```

Replace with:
```
> **Twitter cookie setup:** Use the **Cookie Picker** Chrome extension included in this repo (`extensions/cookie-picker/`) — load it unpacked in Chrome, navigate to x.com, open the popup, and `auth_token` + `ct0` are pre-selected. Click "Copy selected" and paste the values into `configure_twitter(auth_token=..., ct0=...)` in Claude, or pass them as env vars to `install.sh`.
```

- [ ] **Step 2: Update README_zh.md Twitter cookie setup note**

Find this line in README_zh.md:
```
> **Twitter Cookie 配置：** 安装 [Cookie-Editor](https://cookie-editor.com/) 浏览器扩展，登录 x.com，复制 `auth_token` 和 `ct0` 的 cookie 值，然后在 Claude 中调用 `configure_twitter(auth_token=..., ct0=...)` 即可。
```

Replace with:
```
> **Twitter Cookie 配置：** 使用本项目内置的 **Cookie Picker** Chrome 扩展（`extensions/cookie-picker/`）——在 Chrome 中以"加载已解压的扩展程序"方式安装，打开 x.com，点击插件图标，`auth_token` 和 `ct0` 已默认勾选，点击"Copy selected"复制后粘贴到 `configure_twitter(auth_token=..., ct0=...)` 即可。
```

- [ ] **Step 3: Update the API Keys table in both READMEs**

In README.md, update the `TWITTER_AUTH_TOKEN` and `TWITTER_CT0` rows:

```
| `TWITTER_AUTH_TOKEN` | social-mcp | x.com cookie (Cookie Picker extension → `auth_token`) |
| `TWITTER_CT0` | social-mcp | x.com cookie (Cookie Picker extension → `ct0`) |
```

Apply the same change in README_zh.md:

```
| `TWITTER_AUTH_TOKEN` | social-mcp | x.com cookie（Cookie Picker 扩展 → `auth_token`） |
| `TWITTER_CT0` | social-mcp | x.com cookie（Cookie Picker 扩展 → `ct0`） |
```

- [ ] **Step 4: Commit**

```bash
git add README.md README_zh.md
git commit -m "docs: replace Cookie-Editor references with Cookie Picker extension"
```

---

## Final Verification Checklist

Before calling this done, verify these scenarios manually:

- [ ] x.com: `auth_token` and `ct0` pre-checked on open
- [ ] Another site (e.g. github.com): no cookies pre-checked
- [ ] Search filters correctly (case-insensitive, substring)
- [ ] Empty search shows "No cookies match", disables Select all and Copy
- [ ] Select all / deselect all works on filtered subset only
- [ ] Indeterminate state shows when partially selected
- [ ] Copy output format: `auth_token=xxx; ct0=yyy`
- [ ] Copied! button turns green, reverts after 1.5s
- [ ] Rapid re-click resets timer
- [ ] chrome://extensions tab: shows error message, no list
- [ ] Long cookie values are truncated in the list but full value is copied
