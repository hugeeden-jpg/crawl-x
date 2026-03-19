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

function truncate(str, n = 20) {
  return str.length > n ? str.slice(0, n) + '\u2026' : str;
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

function updateControls() {
  const selectedVisible = filteredCookies.filter(c => c.checked).length;
  const totalVisible = filteredCookies.length;
  const totalSelected = allCookies.filter(c => c.checked).length;

  const selectAll = document.getElementById('select-all');
  const countEl = document.getElementById('count');
  const noResults = totalVisible === 0;

  selectAll.disabled = noResults;
  selectAll.checked = !noResults && selectedVisible === totalVisible;
  selectAll.indeterminate = !noResults && selectedVisible > 0 && selectedVisible < totalVisible;
  countEl.textContent = noResults ? '' : '(' + selectedVisible + ' / ' + totalVisible + ')';

  const copyBtn = document.getElementById('copy-btn');
  copyBtn.disabled = totalSelected === 0;
  if (!copyBtn.classList.contains('copied')) {
    copyBtn.textContent = totalSelected > 0
      ? 'Copy selected (' + totalSelected + ')'
      : 'Copy selected';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  init();

  document.getElementById('search').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    filteredCookies = allCookies.filter(c => c.name.toLowerCase().includes(q));
    renderList();
    updateControls();
  });

  document.getElementById('select-all').addEventListener('change', e => {
    const checked = e.target.checked;
    filteredCookies.forEach(c => { c.checked = checked; });
    const filteredNames = new Set(filteredCookies.map(c => c.name));
    allCookies.forEach(c => { if (filteredNames.has(c.name)) c.checked = checked; });
    renderList();
    updateControls();
  });
});
