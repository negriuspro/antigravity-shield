#!/bin/bash
# ============================================================
# ANTIGRAVITY SHIELD — Backup Script
# Usage: bash scripts/backup.sh
# Backups: PostgreSQL dump + AdGuard config
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

set -a; source .env; set +a

BACKUP_DIR="$SCRIPT_DIR/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

echo "[BACKUP] Starting backup $DATE..."

# PostgreSQL
echo "[BACKUP] Dumping PostgreSQL..."
docker compose exec -T postgres pg_dump \
  -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# AdGuard config
echo "[BACKUP] Backing up AdGuard config..."
docker run --rm \
  -v antigravity-shield_adguard_conf:/source:ro \
  -v "$BACKUP_DIR:/dest" \
  alpine tar czf "/dest/adguard_conf_$DATE.tar.gz" -C /source .

# Rotate: keep last 14 backups
ls -t "$BACKUP_DIR"/postgres_*.sql.gz 2>/dev/null | tail -n +15 | xargs -r rm
ls -t "$BACKUP_DIR"/adguard_conf_*.tar.gz 2>/dev/null | tail -n +15 | xargs -r rm

echo "[BACKUP] Done. Files in $BACKUP_DIR/"
ls -lh "$BACKUP_DIR/" | tail -5
