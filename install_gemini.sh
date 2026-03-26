#!/usr/bin/env bash
# install_gemini.sh — Register all crawl-x MCPs to Gemini CLI
# Usage: bash install_gemini.sh [--non-interactive]
#   --non-interactive  Skip API key prompts (for agent/CI use).

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IS_INTERACTIVE=true

for arg in "$@"; do
  [[ "$arg" == "--non-interactive" ]] && IS_INTERACTIVE=false
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

# Prompt for an API key
prompt_key() {
  local varname="$1" label="$2" existing="$3"
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
echo "║     crawl-x Gemini MCP Installer     ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── uv: auto-install if missing ───────────────────────────────────────────────

if ! command -v uv &>/dev/null; then
  info "uv not found — installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source "$HOME/.local/bin/env" 2>/dev/null || export PATH="$HOME/.local/bin:$PATH"
fi
ok "uv found: $(uv --version)"

if ! command -v gemini &>/dev/null; then
  err "Gemini CLI not found."
  exit 1
fi
ok "Gemini CLI found"

# ── Dependencies ──────────────────────────────────────────────────────────────

echo ""
info "Checking dependencies..."

if uv tool list 2>/dev/null | grep -q scrapling; then
  ok "Scrapling ready"
else
  info "Installing Scrapling..."
  uv tool install "scrapling[all]>=0.4.2"
fi

uvx scrapling install 2>/dev/null || true

if ! command -v yt-dlp &>/dev/null && ! uv tool list 2>/dev/null | grep -q yt-dlp; then
  info "Installing yt-dlp..."
  uv tool install yt-dlp
fi
ok "yt-dlp ready"

if ! command -v xreach &>/dev/null; then
  warn "xreach CLI not found (Twitter/X tools will be unavailable). Install with: npm install -g xreach-cli"
fi

# ── API keys ──────────────────────────────────────────────────────────────────

if $IS_INTERACTIVE; then
echo ""
echo "─── API Keys ──────────────────────────────────────────────────────────────"
_FRED_EXIST="$(json_get "$HOME/.config/macro-mcp/config.json"          "fred_api_key")"
_XAI_EXIST="$(json_get  "$HOME/.config/grok-mcp/config.json"           "api_key")"
_FINN_EXIST="$(json_get "$HOME/.config/market-data-mcp/config.json"    "finnhub_api_key")"
_SIMFIN_EXIST="$(json_get "$HOME/.config/market-data-mcp/config.json"   "simfin_api_key")"
_QUIV_EXIST="$(json_get "$HOME/.config/sentiment-mcp/config.json"      "quiver_api_key")"
_CGK_EXIST="$(json_get  "$HOME/.config/crypto-mcp/config.json"         "coingecko_api_key")"
_GN_EXIST="$(json_get   "$HOME/.config/crypto-mcp/config.json"         "glassnode_api_key")"
_TW_AUTH_EXIST="$(json_get "$HOME/.config/social-mcp/config.json"      "auth_token")"
_TW_CT0_EXIST="$(json_get  "$HOME/.config/social-mcp/config.json"      "ct0")"
_NEWSAPI_EXIST="$(json_get "$HOME/.config/news-mcp/config.json"        "newsapi_key")"
_BB_EXIST="$(json_get      "$HOME/.config/blockbeats-mcp/config.json"  "api_key")"

prompt_key FRED_API_KEY      "  FRED_API_KEY (macro, required) " "$_FRED_EXIST"
prompt_key FINNHUB_API_KEY   "  FINNHUB_API_KEY (market, optional)" "$_FINN_EXIST"
prompt_key SIMFIN_API_KEY    "  SIMFIN_API_KEY (market, optional)" "$_SIMFIN_EXIST"
prompt_key XAI_API_KEY       "  XAI_API_KEY (grok, optional)    " "$_XAI_EXIST"
prompt_key QUIVER_API_KEY    "  QUIVER_API_KEY (sentiment, opt) " "$_QUIV_EXIST"
prompt_key COINGECKO_API_KEY "  COINGECKO_API_KEY (crypto, opt) " "$_CGK_EXIST"
prompt_key GLASSNODE_API_KEY "  GLASSNODE_API_KEY (crypto, opt) " "$_GN_EXIST"
prompt_key TW_AUTH_TOKEN     "  TW_AUTH_TOKEN (social, optional)" "$_TW_AUTH_EXIST"
prompt_key TW_CT0            "  TW_CT0 (social, optional)       " "$_TW_CT0_EXIST"
prompt_key NEWSAPI_KEY       "  NEWSAPI_KEY (news, optional)    " "$_NEWSAPI_EXIST"
prompt_key BB_API_KEY        "  BLOCKBEATS_API_KEY (optional)   " "$_BB_EXIST"

write_config() {
  local file="$1"; shift
  python3 - "$file" "$@" <<'PY'
import json, sys, pathlib
path = pathlib.Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
cfg = json.loads(path.read_text()) if path.exists() else {}
for pair in sys.argv[2:]:
    if "=" not in pair: continue
    k, v = pair.split("=", 1)
    if v: cfg[k] = v
path.write_text(json.dumps(cfg, indent=2))
PY
}

write_config "$HOME/.config/grok-mcp/config.json"          "api_key=$XAI_API_KEY"
write_config "$HOME/.config/market-data-mcp/config.json"   "finnhub_api_key=$FINNHUB_API_KEY" "simfin_api_key=$SIMFIN_API_KEY"
write_config "$HOME/.config/macro-mcp/config.json"         "fred_api_key=$FRED_API_KEY"
write_config "$HOME/.config/sentiment-mcp/config.json"     "quiver_api_key=$QUIVER_API_KEY"
write_config "$HOME/.config/crypto-mcp/config.json"        "coingecko_api_key=$COINGECKO_API_KEY" "glassnode_api_key=$GLASSNODE_API_KEY"
write_config "$HOME/.config/social-mcp/config.json"        "auth_token=$TW_AUTH_TOKEN" "ct0=$TW_CT0"
write_config "$HOME/.config/news-mcp/config.json"          "newsapi_key=$NEWSAPI_KEY"
write_config "$HOME/.config/blockbeats-mcp/config.json"    "api_key=$BB_API_KEY"
ok "Config files updated"
fi

# ── Trust & Register ──────────────────────────────────────────────────────────

echo ""
echo "─── Registering MCPs to Gemini ────────────────────────────────────────────"

register() {
  local name="$1" script="$2"
  gemini mcp add "$name" uv run "$REPO_DIR/$script" --scope user --trust
  ok "Registered: $name"
}

register "grok-news"         "grok-mcp/server.py"
register "market-data"       "market-data-mcp/server.py"
register "crypto-data"       "crypto-mcp/server.py"
register "macro-data"        "macro-mcp/server.py"
register "sentiment-data"    "sentiment-mcp/server.py"
register "financial-scraper" "scrape-mcp/server.py"
register "social-data"       "social-mcp/server.py"
register "news-data"         "news-mcp/server.py"
register "blockbeats-mcp"    "blockbeats-mcp/server.py"

echo ""
echo "─── Linking Skills to Gemini ──────────────────────────────────────────────"

link_skill() {
  local dir="$1"
  if [[ -f "$REPO_DIR/$dir/SKILL.md" ]]; then
    gemini skill link "$REPO_DIR/$dir" --consent --scope user
    ok "Linked: $dir skill"
  else
    warn "Skill not found in $dir"
  fi
}

link_skill "grok-mcp"
link_skill "market-data-mcp"
link_skill "crypto-mcp"
link_skill "macro-mcp"
link_skill "sentiment-mcp"
link_skill "scrape-mcp"
link_skill "social-mcp"
link_skill "news-mcp"
link_skill "blockbeats-mcp"
link_skill "financial-research-agent"

echo ""
ok "All MCPs and Skills registered to Gemini CLI!"
info "Run 'gemini mcp list' and 'gemini skill list' to verify."
echo ""
