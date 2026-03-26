#!/usr/bin/env bash
# install.sh — Register all crawl-x MCPs to Claude CLI
# Usage: bash install.sh [--desktop] [--non-interactive]
#   --desktop          Also generate claude_desktop_config.json
#   --non-interactive  Skip API key prompts (for agent/CI use).
#                      Configure keys afterwards via each MCP's configure tool.

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_MODE=false
IS_INTERACTIVE=true

for arg in "$@"; do
  [[ "$arg" == "--desktop" ]]         && DESKTOP_MODE=true
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

# ── API keys ──────────────────────────────────────────────────────────────────

if $IS_INTERACTIVE; then

# Prompt for a required key; loops until a non-empty value is provided
prompt_required_key() {
  local varname="$1" label="$2" existing="$3"
  while true; do
    prompt_key "$varname" "$label" "$existing"
    local val="${!varname}"
    [[ -n "$val" ]] && break
    warn "This key is required — please enter a value (or Ctrl-C to abort)."
  done
}

echo ""
echo "─── API Keys ──────────────────────────────────────────────────────────────"
echo "  Press Enter to keep an existing value, or type a new one to replace it."
echo "  [required] keys must be set for the MCP to function."
echo "  [optional] keys unlock additional data sources."
echo ""

# Read existing values from config files
_FRED_EXIST="$(json_get "$HOME/.config/macro-mcp/config.json"          "fred_api_key")"
_XAI_EXIST="$(json_get  "$HOME/.config/grok-mcp/config.json"           "api_key")"
_FINN_EXIST="$(json_get "$HOME/.config/market-data-mcp/config.json"    "finnhub_api_key")"
_QUIV_EXIST="$(json_get "$HOME/.config/sentiment-mcp/config.json"      "quiver_api_key")"
_CGK_EXIST="$(json_get  "$HOME/.config/crypto-mcp/config.json"         "coingecko_api_key")"
_GN_EXIST="$(json_get   "$HOME/.config/crypto-mcp/config.json"         "glassnode_api_key")"
_SIMFIN_EXIST="$(json_get "$HOME/.config/market-data-mcp/config.json"   "simfin_api_key")"
_TW_AUTH_EXIST="$(json_get "$HOME/.config/social-mcp/config.json"      "auth_token")"
_TW_CT0_EXIST="$(json_get  "$HOME/.config/social-mcp/config.json"      "ct0")"
_NEWSAPI_EXIST="$(json_get "$HOME/.config/news-mcp/config.json"        "newsapi_key")"
_BB_EXIST="$(json_get      "$HOME/.config/blockbeats-mcp/config.json"  "api_key")"
_BLS_EXIST="$(json_get     "$HOME/.config/macro-mcp/config.json"       "bls_api_key")"
_CMC_EXIST="$(json_get     "$HOME/.config/cmc-mcp/config.json"         "cmc_api_key")"

# ── FRED (required) ──────────────────────────────────────────────────────────
echo "┌─ [required] FRED_API_KEY — macro-mcp (Fed rates, CPI, GDP, M2, treasury yields)"
echo "│  Free key — no credit card needed."
echo "│  1. Visit: https://fred.stlouisfed.org/docs/api/api_key.html"
echo "│  2. Sign in (or register for free) → My Account → API Keys → Request API Key"
echo "└─"
prompt_required_key FRED_API_KEY "  FRED_API_KEY" "$_FRED_EXIST"
echo ""

# ── Finnhub (optional but strongly recommended) ──────────────────────────────
echo "┌─ [optional] FINNHUB_API_KEY — market-data-mcp (real-time quotes, earnings, news)"
echo "│  Free tier available — strongly recommended for live stock data."
echo "│  1. Visit: https://finnhub.io"
echo "│  2. Sign up → Dashboard → copy the API Key shown on the page"
echo "└─"
prompt_key FINNHUB_API_KEY    "  FINNHUB_API_KEY    (market-data, optional)" "$_FINN_EXIST"
echo ""

# ── SimFin (optional) ────────────────────────────────────────────────────────
echo "┌─ [optional] SIMFIN_API_KEY — market-data-mcp (standardized cross-company financials)"
echo "│  Free tier available (2000 req/day). Register at https://simfin.com"
echo "│  1. Visit: https://simfin.com → Sign up (free)"
echo "│  2. Confirm your email → Account → API Key"
echo "└─"
prompt_key SIMFIN_API_KEY     "  SIMFIN_API_KEY     (market-data, optional)" "$_SIMFIN_EXIST"
echo ""

# ── XAI / Grok (optional) ────────────────────────────────────────────────────
echo "┌─ [optional] XAI_API_KEY — grok-mcp (AI-synthesised X/Twitter news via Grok)"
echo "│  Requires an xAI account with active credits."
echo "│  Note: raw tweet search is already covered by social-data/xreach without a key."
echo "│  1. Visit: https://console.x.ai"
echo "│  2. Sign in → API Keys → Create new key"
echo "└─"
prompt_key XAI_API_KEY        "  XAI_API_KEY        (grok-mcp, optional)  " "$_XAI_EXIST"
echo ""

# ── Quiver (optional) ────────────────────────────────────────────────────────
echo "┌─ [optional] QUIVER_API_KEY — sentiment-mcp (congressional trades, insider sentiment)"
echo "│  1. Visit: https://www.quiverquant.com"
echo "│  2. Sign up → Account → API key"
echo "└─"
prompt_key QUIVER_API_KEY     "  QUIVER_API_KEY     (sentiment, optional) " "$_QUIV_EXIST"
echo ""

# ── CoinGecko (optional) ─────────────────────────────────────────────────────
echo "┌─ [optional] COINGECKO_API_KEY — crypto-mcp (higher rate limits)"
echo "│  Public endpoints work without a key; a key raises the rate limit."
echo "│  1. Visit: https://www.coingecko.com/en/api"
echo "│  2. Sign up → Get Demo API Key (free)"
echo "└─"
prompt_key COINGECKO_API_KEY  "  COINGECKO_API_KEY  (crypto, optional)   " "$_CGK_EXIST"
echo ""

# ── Glassnode (optional) ─────────────────────────────────────────────────────
echo "┌─ [optional] GLASSNODE_API_KEY — crypto-mcp (on-chain metrics)"
echo "│  Requires a paid Glassnode account."
echo "│  1. Visit: https://studio.glassnode.com"
echo "│  2. Sign in → Account Settings → API → Generate key"
echo "└─"
prompt_key GLASSNODE_API_KEY  "  GLASSNODE_API_KEY  (crypto, optional)   " "$_GN_EXIST"
echo ""

# ── Twitter cookies (optional) ───────────────────────────────────────────────
echo "┌─ [optional] TWITTER_AUTH_TOKEN + TWITTER_CT0 — social-mcp (Twitter/X search)"
echo "│  These are session cookies from a logged-in twitter.com tab."
echo "│  How to get them (Cookie Picker extension — recommended):"
echo "│    1. Install 'Cookie Picker' from the Chrome Web Store"
echo "│    2. Log in to twitter.com in Chrome"
echo "│    3. Click the Cookie Picker icon → find 'auth_token', copy its value"
echo "│    4. Do the same for 'ct0'"
echo "│  Alternative: DevTools (F12) → Application → Cookies → https://twitter.com"
echo "└─"
prompt_key TWITTER_AUTH_TOKEN "  TWITTER_AUTH_TOKEN (social, optional)   " "$_TW_AUTH_EXIST"
prompt_key TWITTER_CT0        "  TWITTER_CT0        (social, optional)   " "$_TW_CT0_EXIST"

# ── NewsAPI.org (optional) ────────────────────────────────────────────────────
echo ""
echo "┌─ [optional] NEWSAPI_KEY — news-mcp (article search + top headlines)"
echo "│  Free tier: 100 req/day, no per-request rate limit."
echo "│  1. Visit: https://newsapi.org/register"
echo "│  2. Register for free → copy the API key shown on the dashboard"
echo "└─"
prompt_key NEWSAPI_KEY "  NEWSAPI_KEY        (news-mcp, optional) " "$_NEWSAPI_EXIST"

# ── BlockBeats (optional) ─────────────────────────────────────────────────────
echo ""
echo "┌─ [optional] BLOCKBEATS_API_KEY — blockbeats-mcp (crypto news, on-chain, ETF data)"
echo "│  Requires a BlockBeats Pro subscription."
echo "│  1. Visit: https://www.theblockbeats.info/"
echo "│  2. Subscribe → Account → API Key"
echo "└─"
prompt_key BLOCKBEATS_API_KEY "  BLOCKBEATS_API_KEY (blockbeats, optional)" "$_BB_EXIST"

# ── BLS Bureau of Labor Statistics (optional) ─────────────────────────────
echo ""
echo "┌─ [optional] BLS_API_KEY — macro-data (CPI/PPI/NFP/JOLTS via BLS direct API)"
echo "│  Free key, raises rate limits. Works without a key at lower limits."
echo "│  1. Visit: https://www.bls.gov/developers/api_signature_v2.htm"
echo "│  2. Register for free → receive key by email"
echo "└─"
prompt_key BLS_API_KEY "  BLS_API_KEY         (macro, optional)    " "$_BLS_EXIST"

# ── CoinMarketCap (optional) ──────────────────────────────────────────────
echo ""
echo "┌─ [optional] CMC_API_KEY — cmc-data (crypto rankings, global metrics, CMC Fear & Greed)"
echo "│  Free Basic plan: 10,000 credits/month (~300 req/day). No credit card."
echo "│  1. Visit: https://coinmarketcap.com/api/"
echo "│  2. Sign up → My Account → API Keys → Copy key"
echo "└─"
prompt_key CMC_API_KEY "  CMC_API_KEY         (cmc, optional)       " "$_CMC_EXIST"

# ── write API keys to each MCP's config file ─────────────────────────────────

echo ""
echo "─── Saving API keys to config files ──────────────────────────────────────"

# Write a JSON config file, merging new non-empty values over any existing ones
write_config() {
  local file="$1"; shift   # remaining args: key=value pairs
  python3 - "$file" "$@" <<'PY'
import json, sys, pathlib
path = pathlib.Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
cfg = json.loads(path.read_text()) if path.exists() else {}
for pair in sys.argv[2:]:
    k, v = pair.split("=", 1)
    if v:           # only overwrite when a value was provided
        cfg[k] = v
path.write_text(json.dumps(cfg, indent=2))
PY
}

write_config "$HOME/.config/grok-mcp/config.json"          "api_key=$XAI_API_KEY"
write_config "$HOME/.config/market-data-mcp/config.json"   "finnhub_api_key=$FINNHUB_API_KEY" \
                                                            "simfin_api_key=$SIMFIN_API_KEY"
write_config "$HOME/.config/macro-mcp/config.json"         "fred_api_key=$FRED_API_KEY" \
                                                            "bls_api_key=$BLS_API_KEY"
write_config "$HOME/.config/cmc-mcp/config.json"           "cmc_api_key=$CMC_API_KEY"
write_config "$HOME/.config/sentiment-mcp/config.json"     "quiver_api_key=$QUIVER_API_KEY"
write_config "$HOME/.config/crypto-mcp/config.json"        "coingecko_api_key=$COINGECKO_API_KEY" \
                                                            "glassnode_api_key=$GLASSNODE_API_KEY"
write_config "$HOME/.config/social-mcp/config.json"        "auth_token=$TWITTER_AUTH_TOKEN" \
                                                            "ct0=$TWITTER_CT0"
write_config "$HOME/.config/news-mcp/config.json"          "newsapi_key=$NEWSAPI_KEY"
write_config "$HOME/.config/blockbeats-mcp/config.json"    "api_key=$BLOCKBEATS_API_KEY"
ok "Config files updated"

else
  info "Non-interactive mode: skipping API key prompts."
  echo ""
  echo "  API keys are stored in JSON config files under ~/.config/, NOT in"
  echo "  .env files or Claude MCP environment variables. Do NOT use"
  echo "  'claude mcp add -e KEY=...' — keys written there will be ignored."
  echo ""
  echo "  To configure keys, call each MCP's configure tool after installation:"
  echo ""
  echo "  macro-data    → mcp__macro-data__configure(fred_api_key=\"...\")"
  echo "    stores to:    ~/.config/macro-mcp/config.json"
  echo ""
  echo "  market-data   → mcp__market-data__configure(finnhub_api_key=\"...\", simfin_api_key=\"...\")"
  echo "    stores to:    ~/.config/market-data-mcp/config.json"
  echo ""
  echo "  grok-news     → mcp__grok-news__set_api_key(api_key=\"...\")"
  echo "    stores to:    ~/.config/grok-mcp/config.json"
  echo ""
  echo "  sentiment-data → mcp__sentiment-data__configure(quiver_api_key=\"...\")"
  echo "    stores to:    ~/.config/sentiment-mcp/config.json"
  echo ""
  echo "  crypto-data   → mcp__crypto-data__configure(coingecko_api_key=\"...\", glassnode_api_key=\"...\")"
  echo "    stores to:    ~/.config/crypto-mcp/config.json"
  echo ""
  echo "  social-data   → mcp__social-data__configure_twitter(auth_token=\"...\", ct0=\"...\")"
  echo "    stores to:    ~/.config/social-mcp/config.json"
  echo ""
  echo "  news-data     → mcp__news-data__configure(newsapi_key=\"...\")"
  echo "    stores to:    ~/.config/news-mcp/config.json"
  echo ""
  echo "  blockbeats-mcp → mcp__blockbeats-mcp__configure(api_key=\"...\")"
  echo "    stores to:    ~/.config/blockbeats-mcp/config.json"
  echo ""
  echo "  macro-data    → mcp__macro-data__configure_bls(bls_api_key=\"...\")"
  echo "    stores to:    ~/.config/macro-mcp/config.json"
  echo ""
  echo "  cmc-data      → mcp__cmc-data__configure(cmc_api_key=\"...\")"
  echo "    stores to:    ~/.config/cmc-mcp/config.json"
  echo ""
fi

# ── register MCPs ─────────────────────────────────────────────────────────────

echo ""
echo "─── Registering MCPs ──────────────────────────────────────────────────────"

register() {
  local name="$1" script="$2"
  claude mcp remove -s user "$name" 2>/dev/null || true
  claude mcp add -s user "$name" -- uv run "$REPO_DIR/$script"
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
register "binance-mcp"       "binance-mcp/server.py"
register "cmc-data"          "cmc-mcp/server.py"

# ── optionally generate Claude Desktop config ─────────────────────────────────

if $DESKTOP_MODE; then
  echo ""
  echo "─── Generating claude_desktop_config.json ─────────────────────────────────"

  # API keys are stored in ~/.config/<mcp>/config.json by write_config above.
  # No env vars needed in the Desktop config.
  cat > "$REPO_DIR/claude_desktop_config.json" <<JSON
{
  "mcpServers": {
    "grok-news":         {"command": "uv", "args": ["run", "$REPO_DIR/grok-mcp/server.py"]},
    "market-data":       {"command": "uv", "args": ["run", "$REPO_DIR/market-data-mcp/server.py"]},
    "crypto-data":       {"command": "uv", "args": ["run", "$REPO_DIR/crypto-mcp/server.py"]},
    "macro-data":        {"command": "uv", "args": ["run", "$REPO_DIR/macro-mcp/server.py"]},
    "sentiment-data":    {"command": "uv", "args": ["run", "$REPO_DIR/sentiment-mcp/server.py"]},
    "financial-scraper": {"command": "uv", "args": ["run", "$REPO_DIR/scrape-mcp/server.py"]},
    "social-data":       {"command": "uv", "args": ["run", "$REPO_DIR/social-mcp/server.py"]},
    "news-data":         {"command": "uv", "args": ["run", "$REPO_DIR/news-mcp/server.py"]},
    "blockbeats-mcp":    {"command": "uv", "args": ["run", "$REPO_DIR/blockbeats-mcp/server.py"]},
    "binance-mcp":       {"command": "uv", "args": ["run", "$REPO_DIR/binance-mcp/server.py"]},
    "cmc-data":          {"command": "uv", "args": ["run", "$REPO_DIR/cmc-mcp/server.py"]}
  }
}
JSON

  ok "Generated: $REPO_DIR/claude_desktop_config.json"
  warn "Copy relevant sections to:"
  warn "  ~/Library/Application Support/Claude/claude_desktop_config.json"
fi

# ── install skills to ~/.claude/skills/ ──────────────────────────────────────

echo ""
echo "─── Installing Skills ─────────────────────────────────────────────────────"

SKILLS_DIR="$HOME/.claude/skills"

install_skill() {
  local name="$1" src="$2"
  local dest="$SKILLS_DIR/$name"
  mkdir -p "$dest"
  cp "$REPO_DIR/$src" "$dest/SKILL.md"
  ok "Skill installed: $name"
}

install_skill "financial-research-agent" "financial-research-agent/SKILL.md"
install_skill "grok-news"                "grok-mcp/SKILL.md"
install_skill "market-data-mcp"          "market-data-mcp/SKILL.md"
install_skill "macro-mcp"                "macro-mcp/SKILL.md"
install_skill "sentiment-mcp"            "sentiment-mcp/SKILL.md"
install_skill "crypto-mcp"               "crypto-mcp/SKILL.md"
install_skill "scrape-mcp"               "scrape-mcp/SKILL.md"
install_skill "social-mcp"               "social-mcp/SKILL.md"
install_skill "news-mcp"                 "news-mcp/SKILL.md"
install_skill "blockbeats-skill"         "blockbeats-mcp/SKILL.md"
install_skill "binance-mcp"              "binance-mcp/SKILL.md"
install_skill "cmc-mcp"                  "cmc-mcp/SKILL.md"

# ── done ──────────────────────────────────────────────────────────────────────

echo ""
echo "─── Registered MCPs ───────────────────────────────────────────────────────"
claude mcp list
echo ""
ok "All done! Restart Claude CLI or Desktop to load the new MCPs."
echo ""
