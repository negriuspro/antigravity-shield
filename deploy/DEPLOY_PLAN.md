# Plan de Despliegue — AdBlock Network
# Hardware: 6 GB RAM · 4 GB Swap · 200 GB SSD · Ubuntu Desktop

---

## Presupuesto de Memoria

| Servicio           | mem_limit | Función                       |
|--------------------|-----------|-------------------------------|
| nginx              | 64 MB     | Reverse proxy                 |
| adguardhome        | 256 MB    | DNS filtrado (core)           |
| adguard-exporter   | 64 MB     | Métricas DNS                  |
| postgres           | 512 MB    | Base de datos                 |
| redis              | 192 MB    | Cache (maxmemory=128mb)       |
| backend            | 256 MB    | API FastAPI                   |
| frontend           | 256 MB    | Dashboard Next.js             |
| ag-network         | 192 MB    | Analytics de red              |
| ag-ai              | 192 MB    | Detección IA                  |
| prometheus         | 512 MB    | Métricas (15d retención)      |
| grafana            | 256 MB    | Dashboards                    |
| loki               | 256 MB    | Logs                          |
| cadvisor           | 64 MB     | Métricas de containers        |
| ag-controller      | (host)    | Descubrimiento de red         |
| node-exporter      | (host)    | Métricas del SO               |
| **Total containers** | **~3.07 GB** |                           |
| Ubuntu Desktop     | ~800 MB   | SO + gestión                  |
| Docker daemon      | ~200 MB   | Engine                        |
| **Total estimado** | **~4.1 GB** | Queda 1.9 GB libre           |

**Swap 4 GB**: buffer para picos de carga (compilaciones, updates de listas).

---

## Paso 1 — Preparar Ubuntu Desktop

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y curl git dnsutils jq net-tools ufw htop

# Verificar que systemd-resolved no ocupa el puerto 53
sudo ss -tlnpu | grep :53
# Si aparece systemd-resolved, liberarlo:
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
sudo sed -i 's/#DNS=/DNS=1.1.1.1/' /etc/systemd/resolved.conf
sudo sed -i 's/#FallbackDNS=/FallbackDNS=8.8.8.8/' /etc/systemd/resolved.conf
sudo ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf
```

> **Crítico**: El puerto 53 debe estar libre antes de iniciar AdGuard.
> `systemd-resolved` lo ocupa por defecto en Ubuntu Desktop.

---

## Paso 2 — Instalar Docker Engine

```bash
# Método oficial — NO usar apt install docker.io (versión vieja)
curl -fsSL https://get.docker.com | bash

# Agregar usuario al grupo docker (sin sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verificar
docker --version           # >= 25.0
docker compose version     # >= 2.20
```

---

## Paso 3 — Clonar y Configurar

```bash
# Clonar el proyecto
sudo mkdir -p /opt/adblock-network
sudo chown $USER:$USER /opt/adblock-network
git clone <tu-repo> /opt/adblock-network
cd /opt/adblock-network

# Configurar variables de entorno
cp .env.example .env
nano .env
```

**Variables mínimas a editar en `.env`:**

```bash
TZ=America/Bogota

POSTGRES_PASSWORD=una_contraseña_fuerte_32_chars
REDIS_PASSWORD=otra_contraseña_fuerte
ADGUARD_USER=admin
ADGUARD_PASSWORD=contraseña_adguard_segura
BACKEND_SECRET_KEY=$(openssl rand -hex 32)
GRAFANA_ADMIN_PASSWORD=contraseña_grafana
```

---

## Paso 4 — Tuning del Sistema (Kernel)

```bash
# Aplicar optimizaciones de red y memoria para hardware viejo
sudo tee /etc/sysctl.d/99-adblock.conf << 'EOF'
# Red — buffers DNS y TCP
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Swap — usar swap solo cuando la RAM está al 80%
vm.swappiness = 20

# DNS — aumentar socket buffer para AdGuard bajo carga
net.core.netdev_max_backlog = 5000

# Archivos — AdGuard necesita muchos file descriptors
fs.file-max = 1048576
EOF

sudo sysctl --system

# Límites del proceso AdGuard
sudo tee /etc/security/limits.d/adblock.conf << 'EOF'
*  soft  nofile  65536
*  hard  nofile  131072
EOF
```

---

## Paso 5 — Firewall UFW

```bash
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH (ajustar al puerto que uses)
sudo ufw allow 22/tcp comment 'SSH'

# HTTP/HTTPS — Dashboard y proxies
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# DNS — para TODA la red local
sudo ufw allow 53/tcp comment 'DNS-TCP'
sudo ufw allow 53/udp comment 'DNS-UDP'

# DNS-over-TLS (opcional, clientes avanzados)
sudo ufw allow 853/tcp comment 'DNS-over-TLS'

sudo ufw --force enable
sudo ufw status
```

---

## Paso 6 — IP Estática para el Servidor

```bash
# Obtener nombre del adaptador de red
ip a  # busca el nombre: eth0, enp3s0, wlan0, etc.

# Editar configuración Netplan
sudo nano /etc/netplan/01-netcfg.yaml
```

```yaml
network:
  version: 2
  ethernets:
    enp3s0:        # reemplaza con tu adaptador
      dhcp4: no
      addresses:
        - 192.168.1.50/24    # IP fija dentro de tu rango
      routes:
        - to: default
          via: 192.168.1.1   # IP de tu router
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]   # Bootstrap para setup inicial
```

```bash
sudo netplan apply
ip a  # verificar IP estática aplicada
```

---

## Paso 7 — Deploy Inicial

```bash
cd /opt/adblock-network

# Setup inicial (solo primera vez)
# Genera certificado SSL auto-firmado y configura UFW
bash scripts/setup.sh

# Iniciar todo el stack
bash scripts/deploy.sh

# Ver estado
docker compose ps
```

**Primera verificación DNS:**

```bash
SERVER_IP=192.168.1.50   # tu IP estática

# Test DNS básico
dig @$SERVER_IP google.com +short

# Test bloqueo de anuncio
dig @$SERVER_IP doubleclick.net +short
# Debe retornar 0.0.0.0 o NXDOMAIN
```

---

## Paso 8 — Configurar Router

Esta es la configuración **más importante**: hace que TODOS los dispositivos de la red WiFi usen AdGuard.

### Opción A — Router con interfaz web (recomendado)

1. Abrir el panel del router: `192.168.1.1` (o el gateway de tu red)
2. Ir a: **Configuración DHCP** → **Servidores DNS** o **DNS primario/secundario**
3. Configurar:
   ```
   DNS Primario:    192.168.1.50   ← IP de tu servidor Ubuntu
   DNS Secundario:  1.1.1.1        ← Fallback si el servidor cae
   ```
4. Guardar y reiniciar el router
5. Esperar 2-3 minutos y verificar desde otro dispositivo

**Verificar en un dispositivo de la red:**

```bash
# Windows (PowerShell)
nslookup doubleclick.net
# Debe mostrar "Server: 192.168.1.50" y retornar 0.0.0.0

# Android/iOS: ajustes → WiFi → info de red → DNS = 192.168.1.50
```

### Opción B — Si el router no permite cambiar DNS DHCP

Configura cada dispositivo manualmente:
- **Windows**: Panel de control → Centro de redes → Cambiar configuración del adaptador → IPv4 → DNS manual
- **Android**: WiFi → editar red → avanzado → IP estática → DNS 1: `192.168.1.50`
- **iOS**: WiFi → i → Configurar DNS → Manual → agregar `192.168.1.50`

### Opción C — AdGuard como servidor DHCP (avanzado)

Habilitar DHCP en AdGuard Home para que él distribuya tanto IP como DNS:
1. En `AdGuardHome.yaml`, cambiar `dhcp.enabled: true`
2. Deshabilitar DHCP en el router
3. Configurar rango en AdGuard

> ⚠️ **Riesgo**: Si el servidor cae, toda la red pierde conectividad.

---

## Paso 9 — Configurar Servicio Systemd (Autostart)

```bash
sudo tee /etc/systemd/system/adblock-network.service << 'EOF'
[Unit]
Description=AdBlock Network — DNS Filter Stack
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/adblock-network
ExecStart=/usr/bin/docker compose up -d --remove-orphans
ExecStop=/usr/bin/docker compose down --timeout 30
TimeoutStartSec=120
TimeoutStopSec=60
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable adblock-network
sudo systemctl start adblock-network
sudo systemctl status adblock-network
```

---

## Paso 10 — Backup Automático con Cron

```bash
# Backup diario a las 3:00 AM
(crontab -l 2>/dev/null; echo "0 3 * * * cd /opt/adblock-network && bash scripts/backup.sh >> /var/log/adblock-backup.log 2>&1") | crontab -

# Verificar
crontab -l
```

---

## Paso 11 — Monitoreo

Después del deploy, acceder a:

| URL | Servicio |
|-----|---------|
| `https://192.168.1.50/adguard` | AdGuard Home dashboard |
| `https://192.168.1.50/grafana` | Grafana — métricas |
| `https://192.168.1.50/api/docs` | API FastAPI |
| `http://192.168.1.50:9090` | Prometheus (solo desde localhost) |

**Dashboard Grafana recomendado para AdGuard:**
- Importar ID `13451` — "AdGuard Home Dashboard"

---

## Comandos de Operación Diaria

```bash
# Estado de servicios
docker compose ps

# Ver logs de AdGuard en tiempo real
docker compose logs -f adguardhome

# Ver cuánto DNS está bloqueando
docker compose exec adguardhome cat /opt/adguardhome/work/stats.db | strings | head -20

# Actualizar stack (con backup automático)
bash scripts/update.sh

# Backup manual
bash scripts/backup.sh

# Rollback al último backup
bash scripts/rollback.sh

# Reiniciar solo AdGuard
docker compose restart adguardhome

# Ver uso de recursos en tiempo real
docker stats
```

---

## Verificación Final de Bloqueo

```bash
SERVER_IP=192.168.1.50

echo "=== DNS básico ==="
dig @$SERVER_IP google.com +short | head -3

echo "=== Bloqueo de anuncios ==="
dig @$SERVER_IP doubleclick.net +short        # debe retornar 0.0.0.0
dig @$SERVER_IP ads.google.com +short          # debe retornar 0.0.0.0
dig @$SERVER_IP tracking.pixel.fb.com +short   # debe retornar 0.0.0.0

echo "=== No bloquear sitios legítimos ==="
dig @$SERVER_IP github.com +short              # debe retornar IP real
dig @$SERVER_IP docker.io +short               # debe retornar IP real
dig @$SERVER_IP npmjs.com +short               # debe retornar IP real

echo "=== Latencia DNS ==="
time dig @$SERVER_IP cloudflare.com +short     # debe ser < 50ms en segunda consulta
```

---

## Troubleshooting Común

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| Puerto 53 ocupado | `systemd-resolved` | `sudo systemctl stop systemd-resolved` |
| AdGuard no inicia | Conf YAML inválida | `docker compose logs adguardhome` |
| Redis OOM kill | maxmemory > mem_limit | Ya corregido en este compose |
| DNS lento | Cache frío en reboot | Normal, se calienta en minutos |
| Sitio legítimo bloqueado | Falso positivo en lista | Agregar `@@||dominio.com^` en user_rules |
| No bloquea después de configurar router | Router usa DNS hardcoded | Reiniciar router, vaciar caché del cliente |
| Dashboard no carga | nginx no inició | `docker compose logs nginx` |
