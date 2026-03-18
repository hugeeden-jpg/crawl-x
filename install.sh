#!/usr/bin/env bash
# install.sh — Register all crawl-x MCPs to Claude CLI
# Usage: bash install.sh [--desktop]
#   --desktop  Also generate claude_desktop_config.json

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_MODE=false

for arg in "$@"; do
  [[ "$arg" == "--desktop" ]] && DESKTOP_MODE=true
done

# ── helpers ──────────────────────────────────────────────────────────────────

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}!${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*"; }

# ── pre-flight checks ─────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════╗"
echo "║     crawl-x MCP Installer            ║"
echo "╚══════════════════════════════════════╝"
echo ""

if ! command -v uv &>/dev/null; then
  err "uv not found. Install it first: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi
ok "uv found: $(uv --version)"

if ! command -v claude &>/dev/null; then
  err "claude CLI not found. Install Claude Code first."
  exit 1
fi
ok "claude CLI found"

# ── Scrapling (required by scrape-mcp for Capitol Trades / CME FedWatch) ─────

echo ""
echo "Checking Scrapling..."
if uv tool list 2>/dev/null | grep -q scrapling; then
  ok "Scrapling already installed"
else
  warn "Installing Scrapling (needed for scrape-mcp)..."
  uv tool install "scrapling[all]>=0.4.2"
  uv run scrapling install --no-camo 2>/dev/null || true
  ok "Scrapling installed"
fi

# ── Optional social-mcp dependencies ─────────────────────────────────────────

echo ""
echo "Checking optional social-mcp dependencies..."
if command -v xreach &>/dev/null; then
  ok "xreach CLI found (Twitter/X support enabled)"
else
  warn "xreach CLI not found (Twitter/X tools will be unavailable)"
  warn "  Install: npm install -g xreach-cli"
fi
if command -v yt-dlp &>/dev/null; then
  ok "yt-dlp found (YouTube support enabled)"
else
  warn "yt-dlp not found (YouTube tools will be unavailable)"
  warn "  Install: uv tool install yt-dlp"
fi

# ── API keys (optional, can be set later) ────────────────────────────────────

echo ""
echo "─── API Keys (press Enter to skip) ───────────────────────────────────────"
echo "  Required: FRED_API_KEY (macro-mcp)"
echo "  Optional: XAI_API_KEY (grok-mcp — AI-synthesized X analysis; raw tweets via social-data/xreach)"
echo "  Optional: FINNHUB_API_KEY, QUIVER_API_KEY, COINGECKO_API_KEY, GLASSNODE_API_KEY"
echo "  Optional: TWITTER_AUTH_TOKEN, TWITTER_CT0 (social-mcp — see SKILL.md for cookie setup)"
echo ""

read -rp "FRED_API_KEY         (macro-mcp, required)  : " FRED_API_KEY
read -rp "XAI_API_KEY          (grok-mcp, optional)   : " XAI_API_KEY
read -rp "FINNHUB_API_KEY      (market-data, optional): " FINNHUB_API_KEY
read -rp "QUIVER_API_KEY       (sentiment, optional)  : " QUIVER_API_KEY
read -rp "COINGECKO_API_KEY    (crypto, optional)     : " COINGECKO_API_KEY
read -rp "GLASSNODE_API_KEY    (crypto, optional)     : " GLASSNODE_API_KEY
read -rp "TWITTER_AUTH_TOKEN   (social, optional)     : " TWITTER_AUTH_TOKEN
read -rp "TWITTER_CT0          (social, optional)     : " TWITTER_CT0

# ── helper: build -e KEY=VAL flags (skip empty values) ───────────────────────

env_flags() {
  local flags=()
  for pair in "$@"; do
    local key="${pair%%=*}"
    local val="${pair#*=}"
    [[ -n "$val" ]] && flags+=(-e "${key}=${val}")
  done
  echo "${flags[@]}"
}

# ── register MCPs ─────────────────────────────────────────────────────────────

echo ""
echo "─── Registering MCPs ──────────────────────────────────────────────────────"

register() {
  local name="$1"
  local script="$2"
  shift 2
  claude mcp remove "$name" 2>/dev/null || true
  # shellcheck disable=SC2068
  claude mcp add "$name" $@ -- uv run "$REPO_DIR/$script"
  ok "Registered: $name"
}

register "grok-news"         "grok-mcp/server.py"         $(env_flags "XAI_API_KEY=$XAI_API_KEY")
register "market-data"       "market-data-mcp/server.py"  $(env_flags "FINNHUB_API_KEY=$FINNHUB_API_KEY")
register "crypto-data"       "crypto-mcp/server.py"       $(env_flags "COINGECKO_API_KEY=$COINGECKO_API_KEY" "GLASSNODE_API_KEY=$GLASSNODE_API_KEY")
register "macro-data"        "macro-mcp/server.py"        $(env_flags "FRED_API_KEY=$FRED_API_KEY")
register "sentiment-data"    "sentiment-mcp/server.py"    $(env_flags "QUIVER_API_KEY=$QUIVER_API_KEY")
register "financial-scraper" "scrape-mcp/server.py"
register "social-data"       "social-mcp/server.py"       $(env_flags "TWITTER_AUTH_TOKEN=$TWITTER_AUTH_TOKEN" "TWITTER_CT0=$TWITTER_CT0")

# ── optionally generate Claude Desktop config ─────────────────────────────────

if $DESKTOP_MODE; then
  echo ""
  echo "─── Generating claude_desktop_config.json ─────────────────────────────────"

  # Build {"KEY":"VAL",...} object, skipping empty values
  env_obj() {
    local pairs=()
    for pair in "$@"; do
      local key="${pair%%=*}"; local val="${pair#*=}"
      [[ -n "$val" ]] && pairs+=("\"$key\": \"$val\"")
    done
    if [[ ${#pairs[@]} -eq 0 ]]; then
      echo "{}"
    else
      local IFS=','; echo "{${pairs[*]}}"
    fi
  }

  cat > "$REPO_DIR/claude_desktop_config.json" <<JSON
{
  "mcpServers": {
    "grok-news": {
      "command": "uv",
      "args": ["run", "$REPO_DIR/grok-mcp/server.py"],
      "env": $(env_obj "XAI_API_KEY=$XAI_API_KEY")
    },
    "market-data": {
      "command": "uv",
      "args": ["run", "$REPO_DIR/market-data-mcp/server.py"],
      "env": $(env_obj "FINNHUB_API_KEY=$FINNHUB_API_KEY")
    },
    "crypto-data": {
      "command": "uv",
      "args": ["run", "$REPO_DIR/crypto-mcp/server.py"],
      "env": $(env_obj "COINGECKO_API_KEY=$COINGECKO_API_KEY" "GLASSNODE_API_KEY=$GLASSNODE_API_KEY")
    },
    "macro-data": {
      "command": "uv",
      "args": ["run", "$REPO_DIR/macro-mcp/server.py"],
      "env": $(env_obj "FRED_API_KEY=$FRED_API_KEY")
    },
    "sentiment-data": {
      "command": "uv",
      "args": ["run", "$REPO_DIR/sentiment-mcp/server.py"],
      "env": $(env_obj "QUIVER_API_KEY=$QUIVER_API_KEY")
    },
    "financial-scraper": {
      "command": "uv",
      "args": ["run", "$REPO_DIR/scrape-mcp/server.py"],
      "env": {}
    },
    "social-data": {
      "command": "uv",
      "args": ["run", "$REPO_DIR/social-mcp/server.py"],
      "env": $(env_obj "TWITTER_AUTH_TOKEN=$TWITTER_AUTH_TOKEN" "TWITTER_CT0=$TWITTER_CT0")
    }
  }
}
JSON

  ok "Generated: $REPO_DIR/claude_desktop_config.json"
  warn "Copy relevant sections to:"
  warn "  ~/Library/Application Support/Claude/claude_desktop_config.json"
fi

# ── done ──────────────────────────────────────────────────────────────────────

echo ""
echo "─── Registered MCPs ───────────────────────────────────────────────────────"
claude mcp list
echo ""
ok "All done! Restart Claude CLI or Desktop to load the new MCPs."
echo ""
