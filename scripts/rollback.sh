#!/bin/bash
# ============================================================
# ADBLOCK NETWORK — Rollback Script
# Usage: bash scripts/rollback.sh [--auto] [--backup <timestamp>]
#
# Restores the last pre-update backup:
#   - PostgreSQL: restore from .sql.gz dump
#   - AdGuard conf: restore bind-mount directory from .tar.gz
#   - AdGuard work: restore named volume from .tar.gz
#
# Called automatically by update.sh with --auto on failure.
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${GREEN}[ROLLBACK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}     $*"; }
error() { echo -e "${RED}[ERROR]${NC}    $*"; exit 1; }
step()  { echo -e "${BLUE}[STEP]${NC}     $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

[[ ! -f ".env" ]] && error ".env not found."
set -a; source .env; set +a

# ─── Args ─────────────────────────────────────────────────────
AUTO_MODE=false
SPECIFIC_BACKUP=""
for i in "$@"; do
  case $i in
    --auto)     AUTO_MODE=true ;;
    --backup=*) SPECIFIC_BACKUP="${i#*=}" ;;
    --backup)   SPECIFIC_BACKUP="${2:-}"; shift ;;
  esac
done

BACKUP_DIR="$SCRIPT_DIR/backups"

# ─── Confirm (interactive mode only) ─────────────────────────
if ! $AUTO_MODE; then
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${RED}  ⚠  ROLLBACK stops all services and restores from backup${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  # List available backups
  echo "  Available backups:"
  ls -t "$BACKUP_DIR"/postgres_*.sql.gz 2>/dev/null | head -5 | while IFS= read -r f; do
    echo "    $(basename "$f" | sed 's/postgres_//;s/.sql.gz//') — $(du -sh "$f" | cut -f1)"
  done
  echo ""
  read -rp "Type 'yes' to confirm rollback: " CONFIRM
  [[ "$CONFIRM" != "yes" ]] && { info "Rollback cancelled."; exit 0; }
fi

# ─── Find backups ─────────────────────────────────────────────
if [[ -n "$SPECIFIC_BACKUP" ]]; then
  PG_BACKUP="$BACKUP_DIR/postgres_${SPECIFIC_BACKUP}.sql.gz"
  AG_CONF_BACKUP="$BACKUP_DIR/adguard_conf_${SPECIFIC_BACKUP}.tar.gz"
  AG_WORK_BACKUP="$BACKUP_DIR/adguard_work_${SPECIFIC_BACKUP}.tar.gz"
else
  PG_BACKUP=$(ls -t "$BACKUP_DIR"/postgres_*.sql.gz 2>/dev/null | head -1 || true)
  AG_CONF_BACKUP=$(ls -t "$BACKUP_DIR"/adguard_conf_*.tar.gz 2>/dev/null | head -1 || true)
  AG_WORK_BACKUP=$(ls -t "$BACKUP_DIR"/adguard_work_*.tar.gz 2>/dev/null | head -1 || true)
fi

[[ -z "$PG_BACKUP" || ! -f "$PG_BACKUP" ]] && error "No PostgreSQL backup found in $BACKUP_DIR/"

BACKUP_TS=$(basename "$PG_BACKUP" | sed 's/postgres_//;s/.sql.gz//')
info "Rolling back to: $BACKUP_TS"

# ─── Stop all services ────────────────────────────────────────
step "Stopping all services..."
docker compose down --timeout 30 2>/dev/null || true
info "Services stopped."

# ─── Restore AdGuard conf (bind-mount directory) ──────────────
AG_CONF_DIR="$SCRIPT_DIR/infra/adguard/conf"
if [[ -n "$AG_CONF_BACKUP" && -f "$AG_CONF_BACKUP" ]]; then
  step "Restoring AdGuard config from $AG_CONF_BACKUP ..."
  rm -rf "${AG_CONF_DIR:?}/"*
  tar xzf "$AG_CONF_BACKUP" -C "$SCRIPT_DIR/infra/adguard/"
  info "AdGuard config restored to $AG_CONF_DIR/"
else
  warn "No AdGuard conf backup found — config will not be restored."
fi

# ─── Start PostgreSQL only ────────────────────────────────────
step "Starting PostgreSQL for restore..."
docker compose up -d postgres

# Wait for postgres to be ready
ELAPSED=0
until docker compose exec -T postgres pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; do
  sleep 3
  ELAPSED=$((ELAPSED + 3))
  [[ $ELAPSED -gt 60 ]] && error "PostgreSQL did not become ready in 60s"
done
info "PostgreSQL ready."

# ─── Restore PostgreSQL ───────────────────────────────────────
step "Restoring PostgreSQL from $PG_BACKUP ..."

# Terminate any active connections
docker compose exec -T postgres psql -U "$POSTGRES_USER" postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();" \
  >/dev/null 2>&1 || true

# Drop and recreate the database
docker compose exec -T postgres psql -U "$POSTGRES_USER" postgres -c \
  "DROP DATABASE IF EXISTS ${POSTGRES_DB};" >/dev/null 2>&1 || true
docker compose exec -T postgres psql -U "$POSTGRES_USER" postgres -c \
  "CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};" >/dev/null 2>&1

# Restore dump
zcat "$PG_BACKUP" | docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" "$POSTGRES_DB" 2>&1 | tail -5 || \
  error "PostgreSQL restore failed!"

info "PostgreSQL restored."

# ─── Restore AdGuard work volume ──────────────────────────────
if [[ -n "$AG_WORK_BACKUP" && -f "$AG_WORK_BACKUP" ]]; then
  step "Restoring AdGuard work volume..."
  # Start adguardhome briefly to create volume, then stop
  docker compose up -d adguardhome 2>/dev/null || true
  sleep 5
  docker compose stop adguardhome 2>/dev/null || true

  CONTAINER_ID=$(docker compose ps -q adguardhome 2>/dev/null | head -1)
  if [[ -n "$CONTAINER_ID" ]]; then
    docker run --rm \
      --volumes-from "$CONTAINER_ID" \
      -v "$BACKUP_DIR:/src:ro" \
      alpine:3.19 sh -c \
        "rm -rf /opt/adguardhome/work/* && tar xzf /src/$(basename "$AG_WORK_BACKUP") -C /"
    info "AdGuard work volume restored."
  else
    warn "Could not restore AdGuard work volume — container not found."
  fi
fi

# ─── Start all services ───────────────────────────────────────
step "Starting all services..."
docker compose up -d --remove-orphans

# Wait for AdGuard to be ready
ELAPSED=0
until curl -sf http://localhost:3000 >/dev/null 2>&1 || [[ $ELAPSED -gt 90 ]]; do
  sleep 5; ELAPSED=$((ELAPSED + 5))
done

# ─── Verify DNS ───────────────────────────────────────────────
step "Verifying DNS..."
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

if command -v dig &>/dev/null; then
  DIG_OUT=$(dig +short +time=5 "@${SERVER_IP}" cloudflare.com 2>/dev/null | head -1 || true)
  if [[ -n "$DIG_OUT" ]]; then
    info "DNS OK → cloudflare.com = $DIG_OUT"
  else
    warn "DNS not responding yet. Run: docker compose logs adguardhome"
  fi
fi

# ─── Final status ─────────────────────────────────────────────
echo ""
docker compose ps
echo ""
info "════════════════════════════════════════"
info "  Rollback to $BACKUP_TS complete"
info "════════════════════════════════════════"
echo -e "  AdGuard:   ${GREEN}http://127.0.0.1:3000${NC}"
echo -e "  Dashboard: ${GREEN}https://$SERVER_IP${NC}"
echo -e "  Grafana:   ${GREEN}https://$SERVER_IP/grafana${NC}"
