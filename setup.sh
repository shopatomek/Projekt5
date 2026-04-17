#!/usr/bin/env bash
# =============================================================================
# setup.sh — AI-Powered BI Dashboard
# =============================================================================
# Automated first-run setup script.
#
# What this script does:
#   1. Verifies prerequisites (Docker, Docker Compose, Git)
#   2. Copies .env.example → .env if not already present
#   3. Prompts for GROQ_API_KEY (required) and Telegram credentials (optional)
#   4. Builds Docker images and starts all services
#   5. Waits for PostgreSQL health check to pass
#   6. Waits for the FastAPI backend to become responsive
#   7. Prints service URLs and next steps
#
# Usage:
#   bash setup.sh
#
# For CI / non-interactive environments (GROQ_API_KEY already in .env):
#   SKIP_PROMPTS=true bash setup.sh
# =============================================================================

set -euo pipefail

# ── Colour helpers ─────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
header()  { echo -e "\n${BOLD}${CYAN}$*${NC}"; }

# ── Script directory (works even if called from another path) ──────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Skip-prompts flag for CI ───────────────────────────────────────────────────
SKIP_PROMPTS="${SKIP_PROMPTS:-false}"

# =============================================================================
# 1. PREREQUISITES CHECK
# =============================================================================
header "1/5  Checking prerequisites…"

check_command() {
    local cmd="$1"
    local hint="$2"
    if ! command -v "$cmd" &>/dev/null; then
        error "'$cmd' not found. $hint"
        exit 1
    fi
    success "$cmd found: $(command -v "$cmd")"
}

check_command "docker"  "Install Docker Desktop: https://docs.docker.com/get-docker/"
check_command "git"     "Install Git: https://git-scm.com/downloads"

# Docker Compose — standalone binary OR plugin
if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif docker-compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    error "'docker compose' (plugin) or 'docker-compose' not found."
    error "Install: https://docs.docker.com/compose/install/"
    exit 1
fi
success "Docker Compose found: $COMPOSE_CMD"

# Docker daemon running?
if ! docker info &>/dev/null; then
    error "Docker daemon is not running. Please start Docker Desktop and try again."
    exit 1
fi
success "Docker daemon is running"

# =============================================================================
# 2. ENVIRONMENT CONFIGURATION
# =============================================================================
header "2/5  Configuring environment…"

if [[ ! -f ".env" ]]; then
    cp .env.example .env
    info "Created .env from .env.example"
else
    info ".env already exists — skipping copy"
fi

if [[ "$SKIP_PROMPTS" != "true" ]]; then

    # ── GROQ_API_KEY ──────────────────────────────────────────────────────────
    CURRENT_GROQ="$(grep -E '^GROQ_API_KEY=' .env | cut -d'=' -f2- | tr -d '[:space:]')"
    if [[ -z "$CURRENT_GROQ" || "$CURRENT_GROQ" == "your_groq_api_key_here" ]]; then
        echo
        echo -e "  ${BOLD}GROQ_API_KEY${NC} is required for AI features (sentiment, summaries, RAG)."
        echo -e "  Free tier: 14,400 requests/day — ${CYAN}https://console.groq.com${NC}"
        echo
        read -rp "  Enter your GROQ_API_KEY (or press Enter to skip and set later): " INPUT_GROQ
        if [[ -n "$INPUT_GROQ" ]]; then
            # Replace placeholder or empty value in .env (portable sed)
            sed -i.bak "s|^GROQ_API_KEY=.*|GROQ_API_KEY=${INPUT_GROQ}|" .env && rm -f .env.bak
            success "GROQ_API_KEY saved to .env"
        else
            warn "GROQ_API_KEY not set — AI features will be unavailable until you add it to .env"
        fi
    else
        success "GROQ_API_KEY already configured"
    fi

    # ── TELEGRAM (optional) ───────────────────────────────────────────────────
    CURRENT_TG_TOKEN="$(grep -E '^TELEGRAM_BOT_TOKEN=' .env | cut -d'=' -f2- | tr -d '[:space:]')"
    if [[ -z "$CURRENT_TG_TOKEN" ]]; then
        echo
        echo -e "  ${BOLD}Telegram Bot${NC} (optional) — sends hourly AI summaries and anomaly alerts."
        echo -e "  Create a bot via ${CYAN}@BotFather${NC} on Telegram to get a token."
        echo
        read -rp "  Enter TELEGRAM_BOT_TOKEN (or press Enter to skip): " INPUT_TG_TOKEN
        if [[ -n "$INPUT_TG_TOKEN" ]]; then
            read -rp "  Enter TELEGRAM_CHAT_ID: " INPUT_TG_CHAT
            sed -i.bak "s|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=${INPUT_TG_TOKEN}|" .env && rm -f .env.bak
            sed -i.bak "s|^TELEGRAM_CHAT_ID=.*|TELEGRAM_CHAT_ID=${INPUT_TG_CHAT}|" .env   && rm -f .env.bak
            success "Telegram credentials saved to .env"
        else
            info "Telegram skipped — alerts disabled (data pipeline still works without it)"
        fi
    else
        success "Telegram already configured"
    fi

else
    info "SKIP_PROMPTS=true — skipping interactive prompts"
fi

# =============================================================================
# 3. BUILD & START
# =============================================================================
header "3/5  Building images and starting services…"
info "This may take 3–8 minutes on first run (downloading base images, installing dependencies)."
echo

$COMPOSE_CMD up -d --build

success "All containers started"

# =============================================================================
# 4. HEALTH CHECKS
# =============================================================================
header "4/5  Waiting for services to become healthy…"

# ── Wait for PostgreSQL ───────────────────────────────────────────────────────
info "Waiting for PostgreSQL…"
POSTGRES_RETRIES=30
POSTGRES_WAIT=2
for i in $(seq 1 "$POSTGRES_RETRIES"); do
    if $COMPOSE_CMD exec -T postgres pg_isready -U "$(grep -E '^POSTGRES_USER=' .env | cut -d'=' -f2)" &>/dev/null; then
        success "PostgreSQL is ready"
        break
    fi
    if [[ "$i" -eq "$POSTGRES_RETRIES" ]]; then
        error "PostgreSQL did not become ready in time."
        error "Check logs: docker logs dashboard-postgres"
        exit 1
    fi
    echo -n "."
    sleep "$POSTGRES_WAIT"
done

# ── Wait for FastAPI backend ──────────────────────────────────────────────────
info "Waiting for FastAPI backend…"
BACKEND_RETRIES=40
BACKEND_WAIT=3
for i in $(seq 1 "$BACKEND_RETRIES"); do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/" 2>/dev/null || true)
    if [[ "$HTTP_STATUS" == "200" ]]; then
        success "Backend API is ready (http://localhost:8000)"
        break
    fi
    if [[ "$i" -eq "$BACKEND_RETRIES" ]]; then
        warn "Backend did not respond in time — it may still be starting up."
        warn "Check logs: docker logs dashboard-backend"
        break
    fi
    echo -n "."
    sleep "$BACKEND_WAIT"
done

# ── Container status summary ──────────────────────────────────────────────────
echo
info "Container status:"
$COMPOSE_CMD ps

# =============================================================================
# 5. NEXT STEPS
# =============================================================================
header "5/5  Setup complete!"
echo
echo -e "  ${BOLD}Services are running at:${NC}"
echo
echo -e "  ${GREEN}●${NC}  React Dashboard   →  ${CYAN}http://localhost:3000${NC}"
echo -e "  ${GREEN}●${NC}  API Docs (Swagger) →  ${CYAN}http://localhost:8000/docs${NC}"
echo -e "  ${GREEN}●${NC}  Metabase BI        →  ${CYAN}http://localhost:3001${NC}  ${YELLOW}(first-run wizard)${NC}"
echo -e "  ${GREEN}●${NC}  n8n Workflows      →  ${CYAN}http://localhost:5678${NC}  ${YELLOW}(first-run setup required)${NC}"
echo -e "  ${GREEN}●${NC}  pgAdmin            →  ${CYAN}http://localhost:5050${NC}"
echo -e "  ${GREEN}●${NC}  dbt Docs           →  ${CYAN}http://localhost:8080${NC}"
echo

echo -e "  ${BOLD}Required manual step — n8n workflow activation:${NC}"
echo -e "  1. Open ${CYAN}http://localhost:5678${NC} and log in"
echo -e "  2. Create a Postgres credential → see ${BOLD}N8N_SETUP_AND_ARCHITECTURE.md${NC}"
echo -e "  3. Import ${BOLD}n8n/workflows/workflow.json${NC}"
echo -e "  4. Assign the credential to all Postgres nodes"
echo -e "  5. Activate each workflow"
echo
echo -e "  Crypto data already flows via the backend scheduler (check:"
echo -e "  ${CYAN}docker logs dashboard-backend | grep Binance${NC})"
echo
echo -e "  ${BOLD}Useful commands:${NC}"
echo -e "  Stop all:          ${CYAN}docker compose down${NC}"
echo -e "  View logs:         ${CYAN}docker compose logs -f${NC}"
echo -e "  Run dbt manually:  ${CYAN}docker compose run --rm dbt dbt run${NC}"
echo -e "  DQ report:         ${CYAN}curl http://localhost:8000/api/dq/report${NC}"
echo -e "  RAG search:        ${CYAN}curl -X POST http://localhost:8000/api/rag/query${NC}"
echo -e "                     ${CYAN}  -H 'Content-Type: application/json'${NC}"
echo -e "                     ${CYAN}  -d '{\"question\": \"bitcoin market trend\"}'${NC}"
echo
echo -e "  For n8n setup details:  ${BOLD}N8N_SETUP_AND_ARCHITECTURE.md${NC}"
echo -e "  For architecture notes: ${BOLD}INTERNALS.md${NC}"
echo