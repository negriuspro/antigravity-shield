#!/bin/bash
# ============================================================
# ANTIGRAVITY SHIELD — Rolling Update Script
# Usage: bash scripts/update.sh [--service <name>] [--no-backup]
#
# Pulls new image versions, recreates containers one at a time,
# runs health checks, and auto-rolls back on failure.
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${GREEN}[UPDATE]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}   $*"; }
error()   { echo -e "${RED}[ERROR]${NC}  $*"; }
step()    { echo -e "${BLUE}[STEP]${NC}   $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

[[ ! -f ".env" ]] && { error ".env not found. Run setup.sh first."; exit 1; }
set -a; source .env; set +a

# ─── Args ─────────────────────────────────────────────────────
TARGET_SERVICE=""
SKIP_BACKUP=false
for i in "$@"; do
  case $i in
    --service) TARGET_SERVICE="${2:-}"; shift 2 ;;
    --service=*) TARGET_SERVICE="${i#*=}" ;;
    --no-backup) SKIP_BACKUP=true ;;
  esac
done

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ROLLBACK_STATE="$SCRIPT_DIR/.rollback_state"

# ─── Save rollback state ──────────────────────────────────────
save_rollback_state() {
  step "Saving rollback state..."
  docker compose images --format json 2>/dev/null | \
    python3 -c "
import sys, json
rows = []
for line in sys.stdin:
    line = line.strip()
    if line:
        rows.append(json.loads(line))
print(json.dumps(rows, indent=2))
" > "$ROLLBACK_STATE" 2>/dev/null || docker compose images > "$ROLLBACK_STATE"
  echo "TIMESTAMP=$TIMESTAMP" >> "$ROLLBACK_STATE"
  info "Rollback state saved → $ROLLBACK_STATE"
}

# ─── Health check ─────────────────────────────────────────────
wait_healthy() {
  local service="$1"
  local max_wait="${2:-60}"
  local interval=5
  local elapsed=0

  step "Health check: $service (timeout ${max_wait}s)..."
  while [[ $elapsed -lt $max_wait ]]; do
    local status
    status=$(docker compose ps --format json "$service" 2>/dev/null | \
             python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('Health','unknown'))" 2>/dev/null || echo "unknown")
    [[ "$status" == "healthy" ]] && { info "$service is healthy."; return 0; }
    [[ "$status" == "exited" ]]  && { error "$service exited unexpectedly!"; return 1; }
    sleep $interval
    elapsed=$((elapsed + interval))
    echo -n "."
  done
  echo ""
  warn "$service did not report healthy in ${max_wait}s (status: $status). Continuing..."
  return 0   # Non-fatal — not all services have healthchecks
}

# ─── Auto rollback ────────────────────────────────────────────
rollback_on_failure() {
  error "Update failed! Initiating auto-rollback..."
  bash "$SCRIPT_DIR/scripts/rollback.sh" --auto
}

# ─── Pre-flight backup ────────────────────────────────────────
if ! $SKIP_BACKUP; then
  step "Creating pre-update backup..."
  bash "$SCRIPT_DIR/scripts/backup.sh" || warn "Backup failed — continuing anyway."
fi

save_rollback_state

# ─── Pull images ──────────────────────────────────────────────
step "Pulling latest images..."
if [[ -n "$TARGET_SERVICE" ]]; then
  docker compose pull "$TARGET_SERVICE" || warn "Pull failed for $TARGET_SERVICE, using cached image."
else
  docker compose pull || warn "Some images could not be pulled, using cached versions."
fi

info "Images pulled."

# ─── Rolling update ───────────────────────────────────────────
# Update critical infra first, then app services
INFRA_SERVICES=(postgres redis)
APP_SERVICES=(backend frontend ag-network ag-controller ag-ai)
OBS_SERVICES=(prometheus grafana loki node-exporter cadvisor)
DNS_SERVICES=(adguardhome adguard-exporter)

update_service() {
  local svc="$1"
  # Skip if service not in compose file
  docker compose config --services 2>/dev/null | grep -q "^${svc}$" || return 0

  step "Updating $svc..."
  docker compose up -d --no-deps "$svc" || { rollback_on_failure; exit 1; }
  sleep 5
  wait_healthy "$svc" 45
}

if [[ -n "$TARGET_SERVICE" ]]; then
  update_service "$TARGET_SERVICE"
else
  info "Rolling update — order: infra → DNS → app → observability"

  for svc in "${INFRA_SERVICES[@]}"; do update_service "$svc"; done
  for svc in "${DNS_SERVICES[@]}";  do update_service "$svc"; done
  for svc in "${APP_SERVICES[@]}";  do update_service "$svc"; done

  # Update observability last (least critical)
  for svc in "${OBS_SERVICES[@]}"; do update_service "$svc"; done

  # Reload nginx config gracefully (no downtime)
  docker compose config --services 2>/dev/null | grep -q "^nginx$" && \
    docker compose exec -T nginx nginx -t >/dev/null 2>&1 && \
    docker compose exec -T nginx nginx -s reload 2>/dev/null && \
    info "Nginx config reloaded." || true
fi

# ─── Clean up dangling images ─────────────────────────────────
step "Removing dangling images..."
docker image prune -f >/dev/null 2>&1 && info "Dangling images removed."

# ─── Summary ──────────────────────────────────────────────────
echo ""
info "════════════════════════════════════════"
info "  Update complete — $(date '+%Y-%m-%d %H:%M:%S')"
info "════════════════════════════════════════"
docker compose ps
echo ""
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
echo -e "  Dashboard: ${GREEN}https://$SERVER_IP${NC}"
echo -e "  AdGuard:   ${GREEN}https://$SERVER_IP/adguard${NC}"
echo -e "  Grafana:   ${GREEN}https://$SERVER_IP/grafana${NC}"
