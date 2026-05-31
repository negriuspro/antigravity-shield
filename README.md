# AntiGravity Shield

**Centralized ad-blocking and network management platform for home and small business networks.**

Inspired by AdGuard Home, Pi-hole, and NextDNS — built for Docker, designed to scale.

---

## Architecture

```
Internet
    │
    ▼
┌──────────────────────────────────────────────┐
│  NGINX  (Reverse Proxy + SSL Termination)    │
│  Ports: 80, 443                              │
└──────────┬───────────────────────────────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
 Frontend      Backend
 (Next.js)    (FastAPI)
     │            │
     │     ┌──────┴──────┬────────────┐
     │     ▼             ▼            ▼
     │  PostgreSQL    Redis       AdGuard Home
     │                              DNS :53
     │
     ├── ag-network  (DNS collector)
     ├── ag-controller (ARP scanner)
     └── ag-ai        (AI stub → ONNX/YOLO)

Observability: Prometheus + Grafana + Loki + Node Exporter + cAdvisor
```

## Layers

| Layer | Service | Technology | Purpose |
|-------|---------|-----------|---------|
| 1 | `adguardhome` | AdGuard Home | DNS filtering |
| 2 | `ag-network` | Python | DNS telemetry collector |
| 3 | `backend` | FastAPI + JWT | REST API + WebSockets |
| 4 | `frontend` | Next.js 14 + TailwindCSS | Dashboard UI |
| 5 | `ag-ai` | FastAPI + ONNX (stub) | AI ad detection |
| 6 | `ag-controller` | Python + ARP | Device discovery |
| 7 | Alerts | Email/Telegram/Discord | Notifications |
| 8 | `nginx` | Nginx | HTTPS + reverse proxy |
| 9 | Prometheus + Grafana + Loki | Observability stack |

## Directory Structure

```
antigravity-shield/
├── services/
│   ├── backend/           # FastAPI API
│   │   └── app/
│   │       ├── auth/      # JWT auth
│   │       ├── models/    # SQLAlchemy models
│   │       ├── schemas/   # Pydantic schemas
│   │       ├── routers/   # API endpoints
│   │       ├── services/  # AdGuard client, alerts
│   │       └── websockets/
│   ├── frontend/          # Next.js dashboard
│   │   └── src/
│   │       ├── app/       # App Router pages
│   │       ├── components/
│   │       ├── lib/       # API client
│   │       └── types/
│   ├── ag-network/        # DNS telemetry collector
│   ├── ag-controller/     # ARP device discovery
│   └── ag-ai/             # AI detection (stub v1)
├── docker/
│   ├── nginx/             # Nginx config + SSL
│   └── postgres/          # DB init SQL
├── infra/
│   ├── prometheus/        # Metrics scrape config
│   ├── grafana/           # Dashboards + provisioning
│   └── loki/              # Log aggregation config
├── scripts/
│   ├── setup.sh           # One-time server setup
│   ├── deploy.sh          # Start / update
│   ├── backup.sh          # PostgreSQL + AdGuard backup
│   └── generate-ssl.sh    # Self-signed or Let's Encrypt
├── docker-compose.yml
└── .env.example
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-org/antigravity-shield.git
cd antigravity-shield

# 2. Setup server (Ubuntu 24.04 — installs Docker + firewall)
sudo bash scripts/setup.sh

# 3. Configure
cp .env.example .env
nano .env   # Set passwords, IPs, alert tokens

# 4. Deploy
bash scripts/deploy.sh

# 5. Point your router's DNS to this server's IP
```

**Default login:** `admin` / `changeme123` (change immediately)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/token` | Login (JWT) |
| GET | `/dashboard/` | Stats overview |
| GET | `/devices/` | Device list |
| PATCH | `/devices/{id}` | Update device |
| POST | `/devices/{id}/block` | Block device |
| GET | `/rules/` | Filter rules |
| POST | `/rules/` | Create rule |
| GET | `/logs/` | DNS query log |
| GET | `/alerts/` | Alert events |
| GET | `/system/status` | System health |
| WS | `/ws/dashboard` | Real-time feed |

Interactive docs: `https://your-server/api/docs`

---

## Development Roadmap

### Phase 1 — Foundation ✅ (Current)
- [x] AdGuard Home DNS filtering
- [x] PostgreSQL schema (devices, dns_queries, rules, stats, alerts)
- [x] FastAPI backend with JWT auth, REST, WebSockets
- [x] ag-network: DNS log collector
- [x] ag-controller: ARP device discovery
- [x] Next.js dashboard (Dashboard, Devices, Rules, Logs, Alerts)
- [x] Prometheus + Grafana + Loki observability
- [x] Docker Compose full stack
- [x] Nginx HTTPS reverse proxy

### Phase 2 — Enhanced Analytics
- [ ] DNS query partitioning by month (auto partition management)
- [ ] Real-time chart via WebSocket in dashboard
- [ ] Device grouping with per-group rules
- [ ] AdGuard blocklist manager (add/remove lists via UI)
- [ ] Grafana DNS-specific dashboards
- [ ] Scheduled reports (weekly email summary)
- [ ] Bandwidth estimation per device

### Phase 3 — Advanced Control
- [ ] Per-device DNS rules and schedules
- [ ] Time-based blocking (parental controls)
- [ ] DNS-over-HTTPS / DNS-over-TLS passthrough
- [ ] Multi-user support with role-based access
- [ ] Import/export rules (AdGuard format, hosts file)
- [ ] Webhook alerts for new devices
- [ ] Automatic blocklist updates

### Phase 4 — AI Detection (ag-ai v2)
- [ ] ONNX Runtime integration
- [ ] YOLOv8 model for domain classification
- [ ] Visual banner/popup detection from screenshots
- [ ] Train custom model on DNS traffic patterns
- [ ] Anomaly detection for suspicious traffic spikes
- [ ] Auto-block confidence-based decisions

### Phase 5 — Scale & Enterprise
- [ ] Kubernetes Helm chart
- [ ] Horizontal scaling (multiple DNS resolvers)
- [ ] Multi-site support
- [ ] SAML/LDAP authentication
- [ ] Audit log for all admin actions
- [ ] Public blocklist publishing

---

## Scaling Strategy (1,000+ Devices)

### DNS Layer
- AdGuard Home handles 10,000+ req/s on modest hardware
- For higher load: deploy Unbound as recursive resolver upstream
- DNS query logging: disable for non-critical networks to reduce write load

### Database
- PostgreSQL partitioning already set up by month on `dns_queries`
- Add `pg_partman` for automatic partition creation
- For 10M+ queries/day: consider TimescaleDB (drop-in PostgreSQL replacement)
- Add read replica for analytics queries

### API / Backend
- Scale FastAPI horizontally: `docker compose scale backend=3`
- Add Redis Cluster for session + pub/sub
- Use connection pooling: PgBouncer in front of PostgreSQL

### Collector
- `ag-network` can be sharded by IP range
- Use Kafka or Redis Streams as a buffer between collection and storage

### Monitoring
- Grafana datasource can be switched to Thanos for long-term metrics
- Loki retention is configurable (`retention_period` in loki-config.yaml)

---

## AI Strategy — Visual Ad Detection

### Phase 1 (Current): Heuristic stub
- Domain classification by keyword matching
- Simulated image analysis
- API-compatible: same endpoints work when real models plug in

### Phase 2: ML domain classification
```
DNS query domain
    ↓
Feature extraction (TLD, length, entropy, age, Alexa rank)
    ↓
LightGBM / XGBoost classifier
    ↓
Block score (0.0 → 1.0)
```

### Phase 3: Visual detection
```
Screenshot (browser extension or proxy)
    ↓
YOLOv8 object detection (ONNX Runtime)
    ↓
Classes: banner_ad, popup, sponsored_content, tracking_pixel
    ↓
DOM injection: element.style.display = 'none'
```

**Model training data sources:**
- IAB ad categories taxonomy
- Open Images Dataset (banner subset)
- AdBlock Plus filter lists (ground truth for DNS)

**Runtime targets:** CPU inference <50ms, GPU <10ms per image

---

## Security

- All traffic via HTTPS (self-signed dev / Let's Encrypt prod)
- JWT with short-lived access tokens (60min) + refresh tokens (30d)
- Rate limiting: 100 req/min API, 10 req/min auth
- PostgreSQL not exposed externally
- Redis password-protected
- AdGuard admin not exposed (only via Nginx proxy)
- UFW firewall configured by setup.sh

---

## License

MIT — Open source, use freely, contributions welcome.
