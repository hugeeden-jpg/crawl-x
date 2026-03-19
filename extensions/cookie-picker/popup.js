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

// Stubs — will be replaced in Task 4
function renderList() {
  console.log('cookies loaded:', allCookies.length);
}

function updateControls() {
  // stub
}

document.addEventListener('DOMContentLoaded', init);
