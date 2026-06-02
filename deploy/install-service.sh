#!/bin/bash
# Instala el servicio systemd para antigravity-shield
# Uso: sudo bash deploy/install-service.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[*] Instalando antigravity-shield.service..."
cp "$SCRIPT_DIR/deploy/antigravity-shield.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable antigravity-shield.service
echo "[OK] Servicio instalado y habilitado."
echo "     Levanta con: sudo systemctl start antigravity-shield"
