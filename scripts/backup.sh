#!/bin/bash
# ============================================================
# ADBLOCK NETWORK — Backup Script
# Usage: bash scripts/backup.sh [--dest /path/to/dir]
#
# Backups:
#   1. PostgreSQL dump (compressed)
#   2. AdGuard conf bind-mount (infra/adguard/conf/)
#   3. Grafana data volume
# Rotation: keeps last 14 backups of each type
# ============================================================

set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[BACKUP]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}   $*"; }
error() { echo -e "${RED}[ERROR]${NC}  $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

[[ ! -f ".env" ]] && error ".env not found."
set -a; source .env; set +a

# ─── Args ─────────────────────────────────────────────────────
BACKUP_DIR="$SCRIPT_DIR/backups"
for i in "$@"; do
  case $i in
    --dest=*) BACKUP_DIR="${i#*=}" ;;
    --dest)   BACKUP_DIR="${2:-}"; shift ;;
  esac
done

DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Verify compose project name matches the name: field in docker-compose.yml
COMPOSE_PROJECT=$(docker compose ls --format json 2>/dev/null | \
  python3 -c "import sys,json; rows=json.load(sys.stdin); [print(r['Name']) for r in rows]" 2>/dev/null | \
  grep -i "adblock" | head -1 || echo "adblock")

info "=== Backup $DATE | project: $COMPOSE_PROJECT ==="

# ─── 1. PostgreSQL dump ───────────────────────────────────────
info "Dumping PostgreSQL..."
if docker compose ps postgres 2>/dev/null | grep -q "Up\|running"; then
  docker compose exec -T postgres pg_dump \
    -U "$POSTGRES_USER" \
    --clean \
    --if-exists \
    "$POSTGRES_DB" | gzip > "$BACKUP_DIR/postgres_${DATE}.sql.gz"
  info "PostgreSQL → $BACKUP_DIR/postgres_${DATE}.sql.gz ($(du -sh "$BACKUP_DIR/postgres_${DATE}.sql.gz" | cut -f1))"
else
  warn "PostgreSQL container not running — skipping DB backup."
fi

# ─── 2. AdGuard config (bind-mount directory) ─────────────────
info "Backing up AdGuard config (bind-mount)..."
AG_CONF_DIR="$SCRIPT_DIR/infra/adguard/conf"
if [[ -d "$AG_CONF_DIR" ]]; then
  tar czf "$BACKUP_DIR/adguard_conf_${DATE}.tar.gz" \
    -C "$SCRIPT_DIR/infra/adguard" conf/
  info "AdGuard conf → $BACKUP_DIR/adguard_conf_${DATE}.tar.gz"
else
  warn "AdGuard conf directory not found at $AG_CONF_DIR — skipping."
fi

# ─── 3. AdGuard work volume (DB, stats, logs) ─────────────────
info "Backing up AdGuard work volume..."
docker run --rm \
  --volumes-from "$(docker compose ps -q adguardhome 2>/dev/null | head -1)" \
  -v "$BACKUP_DIR:/dest" \
  alpine:3.19 \
  tar czf "/dest/adguard_work_${DATE}.tar.gz" \
    -C / opt/adguardhome/work/ 2>/dev/null || warn "AdGuard work backup skipped (container not running?)"

# ─── 4. Verify backups (basic integrity) ──────────────────────
for f in "$BACKUP_DIR"/*_"${DATE}"*; do
  [[ -f "$f" ]] || continue
  if [[ "$f" == *.sql.gz ]]; then
    zcat "$f" | head -c 100 | grep -q "PostgreSQL\|pg_dump\|--" || warn "Suspicious SQL backup: $f"
  fi
  [[ $(stat -c%s "$f") -gt 100 ]] || warn "Suspiciously small backup file: $f ($(stat -c%s "$f") bytes)"
done

# ─── 5. Rotate old backups (keep last 14) ─────────────────────
info "Rotating old backups..."
for pattern in "postgres_*.sql.gz" "adguard_conf_*.tar.gz" "adguard_work_*.tar.gz"; do
  # shellcheck disable=SC2086
  mapfile -t files < <(ls -t "$BACKUP_DIR"/$pattern 2>/dev/null)
  if [[ ${#files[@]} -gt 14 ]]; then
    printf '%s\n' "${files[@]:14}" | xargs -r rm -f
    info "Rotated $((${#files[@]} - 14)) old $pattern file(s)"
  fi
done

# ─── 6. Summary ───────────────────────────────────────────────
echo ""
info "════════════════════════════════"
info "  Backup complete — $DATE"
info "════════════════════════════════"
echo "  Location: $BACKUP_DIR"
echo "  Files:"
ls -lh "$BACKUP_DIR/"*"_${DATE}"* 2>/dev/null | awk '{print "    " $5 "  " $9}' || true
echo ""
DISK_USED=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
info "Total backup dir size: $DISK_USED"
