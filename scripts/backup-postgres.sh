#!/bin/sh
# Backup periódico de PostgreSQL para Shield (Antigravity).
# Ejecuta pg_dump comprimido cada BACKUP_INTERVAL_SECONDS (default: 6h).
# Retiene los últimos BACKUP_KEEP_DAYS días (default: 7).
set -e

INTERVAL="${BACKUP_INTERVAL_SECONDS:-21600}"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-7}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"

mkdir -p "$BACKUP_DIR"
echo "[backup-pg] Iniciando. Primer backup en 120s."
echo "[backup-pg] Intervalo: ${INTERVAL}s | Retención: ${KEEP_DAYS} días | Destino: ${BACKUP_DIR}"

sleep 120

while true; do
  TS=$(date +%Y%m%d_%H%M%S)
  echo "[backup-pg] ── ${TS} ────────────────────"

  DEST="${BACKUP_DIR}/pg_${TS}.sql.gz"
  if pg_dump \
      -h "${POSTGRES_HOST:-postgres}" \
      -U "${POSTGRES_USER}" \
      "${POSTGRES_DB}" \
    | gzip > "$DEST"; then
    SIZE=$(du -sh "$DEST" 2>/dev/null | cut -f1 || echo "?")
    echo "[backup-pg] OK → pg_${TS}.sql.gz (${SIZE})"
  else
    echo "[backup-pg] ERROR: pg_dump falló — se continuará en el próximo ciclo"
    rm -f "$DEST"
  fi

  find "$BACKUP_DIR" -name "pg_*.sql.gz" -mtime "+${KEEP_DAYS}" -delete
  TOTAL=$(find "$BACKUP_DIR" -name "pg_*.sql.gz" 2>/dev/null | wc -l || echo 0)
  echo "[backup-pg] ${TOTAL} backup(s) retenidos. Próximo en ${INTERVAL}s."

  date +%s > /tmp/backup.lastrun
  sleep "$INTERVAL"
done
