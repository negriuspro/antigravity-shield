#!/bin/bash
# ============================================================
# ANTIGRAVITY SHIELD — Initial Setup Script
# Run once on a fresh Ubuntu Server 24.04
# Usage: sudo bash scripts/setup.sh
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

[[ $EUID -ne 0 ]] && error "Run as root: sudo bash scripts/setup.sh"

info "=== AntiGravity Shield Setup ==="

# --- System update ---
info "Updating system packages..."
apt-get update -qq && apt-get upgrade -y -qq

# --- Docker Engine ---
if ! command -v docker &>/dev/null; then
  info "Installing Docker Engine..."
  apt-get install -y -qq ca-certificates curl gnupg lsb-release
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  info "Docker installed."
else
  info "Docker already installed: $(docker --version)"
fi

# --- Add current user to docker group ---
if [[ -n "${SUDO_USER:-}" ]]; then
  usermod -aG docker "$SUDO_USER"
  info "User $SUDO_USER added to docker group (re-login required)"
fi

# --- .env file ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  warn ".env created from .env.example — EDIT IT before deploying!"
else
  info ".env already exists"
fi

# --- SSL self-signed cert (development) ---
SSL_DIR="$SCRIPT_DIR/docker/nginx/ssl"
if [[ ! -f "$SSL_DIR/shield.crt" ]]; then
  info "Generating self-signed SSL certificate..."
  mkdir -p "$SSL_DIR"
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/shield.key" \
    -out "$SSL_DIR/shield.crt" \
    -subj "/C=US/ST=Local/L=Local/O=AntiGravity/CN=shield.local" 2>/dev/null
  info "Self-signed cert created. Replace with Let's Encrypt for production."
fi

# --- UFW Firewall ---
if command -v ufw &>/dev/null; then
  info "Configuring UFW firewall..."
  ufw --force reset
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow ssh
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw allow 53/tcp
  ufw allow 53/udp
  ufw allow 853/tcp   # DNS-over-TLS
  ufw --force enable
  info "UFW configured."
fi

# --- Sysctl tuning (idempotent — uses drop-in file, not /etc/sysctl.conf) ---
tee /etc/sysctl.d/99-adblock.conf > /dev/null << 'EOF'
# AdBlock Network tuning — written by setup.sh, safe to re-run
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
vm.swappiness=20
net.core.netdev_max_backlog=5000
fs.file-max=1048576
EOF
sysctl --system >/dev/null 2>&1
info "Kernel tuning applied via /etc/sysctl.d/99-adblock.conf"

# --- Router DNS setup reminder ---
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  NEXT STEPS:${NC}"
echo -e "  1. Edit ${GREEN}.env${NC} with your passwords and config"
echo -e "  2. Run ${GREEN}bash scripts/deploy.sh${NC} to start all services"
echo -e "  3. Set your router's DNS to this server's IP"
echo -e "  4. Open https://shield.local/adguard to finish AdGuard setup"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
