#!/bin/bash
# ============================================================
# ANTIGRAVITY SHIELD — Deploy / Update Script
# Usage: bash scripts/deploy.sh [--pull] [--no-build]
# ============================================================

set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

PULL=false
NO_BUILD=false
for arg in "$@"; do
  [[ "$arg" == "--pull" ]] && PULL=true
  [[ "$arg" == "--no-build" ]] && NO_BUILD=true
done

[[ ! -f ".env" ]] && { warn ".env not found. Run setup.sh first."; exit 1; }

info "Loading environment..."
set -a; source .env; set +a

if $PULL; then
  info "Pulling latest images..."
  docker compose pull
fi

if ! $NO_BUILD; then
  info "Building services..."
  docker compose build --parallel
fi

info "Starting services..."
docker compose up -d --remove-orphans

info "Waiting for services to be healthy..."
sleep 10

docker compose ps

echo ""
info "=== AntiGravity Shield is running ==="
SERVER_IP=$(hostname -I | awk '{print $1}')
echo -e "  Dashboard:    ${GREEN}https://$SERVER_IP${NC}"
echo -e "  AdGuard:      ${GREEN}https://$SERVER_IP/adguard${NC}"
echo -e "  Grafana:      ${GREEN}https://$SERVER_IP/grafana${NC}"
echo -e "  API Docs:     ${GREEN}https://$SERVER_IP/api/docs${NC}"
echo ""
info "DNS: set your router's primary DNS to ${GREEN}$SERVER_IP${NC}"
