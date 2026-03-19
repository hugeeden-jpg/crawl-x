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

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}!${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*"; }
info() { echo -e "${CYAN}→${NC} $*"; }

# Read a key from a JSON config file (requires python3)
json_get() {
  local file="$1" key="$2"
  [[ -f "$file" ]] || return 0
  python3 -c "import json,sys; d=json.load(open('$file')); print(d.get('$key',''),end='')" 2>/dev/null || true
}

# Prompt for an API key; if already set, show hint and preserve on Enter
prompt_key() {
  local varname="$1"    # variable name to set
  local label="$2"      # display label
  local existing="$3"   # current value from config

  local hint=""
  if [[ -n "$existing" ]]; then
    local masked="${existing:0:6}****"
    hint=" [already set: ${masked}, Enter to keep]"
  fi

  read -rp "${label}${hint}: " input
  if [[ -z "$input" && -n "$existing" ]]; then
    printf -v "$varname" '%s' "$existing"
  else
    printf -v "$varname" '%s' "$input"
  fi
}

# ── banner ────────────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════╗"
echo "║     crawl-x MCP Installer            ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── uv: auto-install if missing ───────────────────────────────────────────────

if ! command -v uv &>/dev/null; then
  OS="$(uname -s 2>/dev/null || echo unknown)"
  case "$OS" in
    Darwin|Linux)
      info "uv not found — installing via official script..."
      curl -LsSf https://astral.sh/uv/install.sh | sh
      # Make uv available in the current shell session
      source "$HOME/.local/bin/env" 2>/dev/null || export PATH="$HOME/.local/bin:$PATH"
      if ! command -v uv &>/dev/null; then
        err "uv install succeeded but 'uv' still not in PATH."
        err "Please open a new terminal and re-run this script."
        exit 1
      fi
      ok "uv installed: $(uv --version)"
      ;;
    MINGW*|MSYS*|CYGWIN*)
      err "Windows detected. Please install uv manually:"
      err "  https://docs.astral.sh/uv/getting-started/installation/"
      exit 1
      ;;
    *)
      err "uv not found. Install it first: https://docs.astral.sh/uv/getting-started/installation/"
      exit 1
      ;;
  esac
else
  ok "uv found: $(uv --version)"
fi

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
  info "Installing Scrapling (needed for scrape-mcp)..."
  uv tool install "scrapling[all]>=0.4.2"
  ok "Scrapling installed"
fi

# Install Playwright browsers inside the Scrapling tool environment
info "Installing Scrapling browser dependencies..."
if uvx scrapling install 2>&1; then
  ok "Scrapling browser (Playwright) ready"
else
  err "Scrapling browser install failed (see output above)"
fi

# ── yt-dlp (required by social-mcp for YouTube) ───────────────────────────────

echo ""
echo "Checking yt-dlp..."
if command -v yt-dlp &>/dev/null || uv tool list 2>/dev/null | grep -q yt-dlp; then
  ok "yt-dlp already installed"
else
  info "Installing yt-dlp (needed for social-mcp YouTube tools)..."
  uv tool install yt-dlp
  ok "yt-dlp installed"
fi

# ── xreach (optional, Twitter/X) ─────────────────────────────────────────────

echo ""
echo "Checking xreach..."
if command -v xreach &>/dev/null; then
  ok "xreach CLI found (Twitter/X support enabled)"
else
  warn "xreach CLI not found (Twitter/X tools will be unavailable)"
  warn "  Install: npm install -g xreach-cli"
fi

# ── API keys (reads existing config, press Enter to keep) ────────────────────

echo ""
echo "─── API Keys (press Enter to keep existing value, or enter a new one) ────"
echo "  Required: FRED_API_KEY (macro-mcp)"
echo "  Optional: all others"
echo ""

# Read existing values from config files
_FRED_EXIST="$(json_get "$HOME/.config/macro-mcp/config.json"          "fred_api_key")"
_XAI_EXIST="$(json_get  "$HOME/.config/grok-mcp/config.json"           "api_key")"
_FINN_EXIST="$(json_get "$HOME/.config/market-data-mcp/config.json"    "finnhub_api_key")"
_QUIV_EXIST="$(json_get "$HOME/.config/sentiment-mcp/config.json"      "quiver_api_key")"
_CGK_EXIST="$(json_get  "$HOME/.config/crypto-mcp/config.json"         "coingecko_api_key")"
_GN_EXIST="$(json_get   "$HOME/.config/crypto-mcp/config.json"         "glassnode_api_key")"
_TW_AUTH_EXIST="$(json_get "$HOME/.config/social-mcp/config.json"      "auth_token")"
_TW_CT0_EXIST="$(json_get  "$HOME/.config/social-mcp/config.json"      "ct0")"

prompt_key FRED_API_KEY       "FRED_API_KEY         (macro-mcp, required)  " "$_FRED_EXIST"
prompt_key XAI_API_KEY        "XAI_API_KEY          (grok-mcp, optional)   " "$_XAI_EXIST"
prompt_key FINNHUB_API_KEY    "FINNHUB_API_KEY      (market-data, optional)" "$_FINN_EXIST"
prompt_key QUIVER_API_KEY     "QUIVER_API_KEY       (sentiment, optional)  " "$_QUIV_EXIST"
prompt_key COINGECKO_API_KEY  "COINGECKO_API_KEY    (crypto, optional)     " "$_CGK_EXIST"
prompt_key GLASSNODE_API_KEY  "GLASSNODE_API_KEY    (crypto, optional)     " "$_GN_EXIST"
prompt_key TWITTER_AUTH_TOKEN "TWITTER_AUTH_TOKEN   (social, optional)     " "$_TW_AUTH_EXIST"
prompt_key TWITTER_CT0        "TWITTER_CT0          (social, optional)     " "$_TW_CT0_EXIST"

# ── register MCPs ─────────────────────────────────────────────────────────────

echo ""
echo "─── Registering MCPs ──────────────────────────────────────────────────────"

register() {
  local name="$1"
  local script="$2"
  shift 2
  claude mcp remove "$name" 2>/dev/null || true
  # $@ contains pre-built -e KEY=VAL pairs; name comes first, then flags, then -- cmd
  claude mcp add "$name" "$@" -- uv run "$REPO_DIR/$script"
  ok "Registered: $name"
}

# Build -e KEY=VAL args, skipping empty values
e() { [[ -n "$2" ]] && printf -- '-e\n%s=%s\n' "$1" "$2"; }

mapfile -t grok_env    < <(e XAI_API_KEY        "$XAI_API_KEY")
mapfile -t market_env  < <(e FINNHUB_API_KEY    "$FINNHUB_API_KEY")
mapfile -t crypto_env  < <(e COINGECKO_API_KEY  "$COINGECKO_API_KEY"; e GLASSNODE_API_KEY "$GLASSNODE_API_KEY")
mapfile -t macro_env   < <(e FRED_API_KEY        "$FRED_API_KEY")
mapfile -t quiver_env  < <(e QUIVER_API_KEY      "$QUIVER_API_KEY")
mapfile -t social_env  < <(e TWITTER_AUTH_TOKEN  "$TWITTER_AUTH_TOKEN"; e TWITTER_CT0 "$TWITTER_CT0")

register "grok-news"         "grok-mcp/server.py"         "${grok_env[@]}"
register "market-data"       "market-data-mcp/server.py"  "${market_env[@]}"
register "crypto-data"       "crypto-mcp/server.py"       "${crypto_env[@]}"
register "macro-data"        "macro-mcp/server.py"        "${macro_env[@]}"
register "sentiment-data"    "sentiment-mcp/server.py"    "${quiver_env[@]}"
register "financial-scraper" "scrape-mcp/server.py"
register "social-data"       "social-mcp/server.py"       "${social_env[@]}"

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
