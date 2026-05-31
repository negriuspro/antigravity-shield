-- ============================================================
-- ANTIGRAVITY SHIELD — Database Initialization
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Enums
CREATE TYPE device_status AS ENUM ('online', 'offline', 'unknown');
CREATE TYPE rule_action AS ENUM ('block', 'allow', 'redirect');
CREATE TYPE rule_type AS ENUM ('domain', 'regex', 'wildcard', 'ip');
CREATE TYPE alert_channel AS ENUM ('email', 'telegram', 'discord', 'webhook');
CREATE TYPE alert_severity AS ENUM ('info', 'warning', 'critical');
CREATE TYPE user_role AS ENUM ('admin', 'viewer');

-- ──────────────────────────────────────────────────────────
-- USERS
-- ──────────────────────────────────────────────────────────
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    username    VARCHAR(100) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role        user_role NOT NULL DEFAULT 'viewer',
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login  TIMESTAMPTZ
);

-- ──────────────────────────────────────────────────────────
-- DEVICES
-- ──────────────────────────────────────────────────────────
CREATE TABLE devices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mac             MACADDR UNIQUE NOT NULL,
    ip              INET NOT NULL,
    hostname        VARCHAR(255),
    manufacturer    VARCHAR(255),
    device_type     VARCHAR(100),
    status          device_status NOT NULL DEFAULT 'unknown',
    group_name      VARCHAR(100),
    is_blocked      BOOLEAN NOT NULL DEFAULT false,
    last_seen       TIMESTAMPTZ,
    first_seen      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX idx_devices_mac ON devices(mac);
CREATE INDEX idx_devices_ip ON devices(ip);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_seen ON devices(last_seen DESC);

-- ──────────────────────────────────────────────────────────
-- DNS QUERIES
-- ──────────────────────────────────────────────────────────
CREATE TABLE dns_queries (
    id          BIGSERIAL PRIMARY KEY,
    device_id   UUID REFERENCES devices(id) ON DELETE SET NULL,
    client_ip   INET NOT NULL,
    domain      VARCHAR(255) NOT NULL,
    query_type  VARCHAR(10),
    blocked     BOOLEAN NOT NULL DEFAULT false,
    reason      VARCHAR(255),
    upstream    VARCHAR(100),
    latency_ms  INTEGER,
    queried_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (queried_at);

-- Monthly partitions (auto-created by backend on startup)
CREATE TABLE dns_queries_default PARTITION OF dns_queries DEFAULT;

CREATE INDEX idx_dns_queried_at ON dns_queries(queried_at DESC);
CREATE INDEX idx_dns_domain ON dns_queries(domain);
CREATE INDEX idx_dns_client_ip ON dns_queries(client_ip);
CREATE INDEX idx_dns_blocked ON dns_queries(blocked);
CREATE INDEX idx_dns_device_id ON dns_queries(device_id);

-- ──────────────────────────────────────────────────────────
-- BLOCKED REQUESTS (summary table)
-- ──────────────────────────────────────────────────────────
CREATE TABLE blocked_requests (
    id          BIGSERIAL PRIMARY KEY,
    domain      VARCHAR(255) NOT NULL,
    count       INTEGER NOT NULL DEFAULT 1,
    first_seen  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    list_name   VARCHAR(255)
);

CREATE UNIQUE INDEX idx_blocked_domain ON blocked_requests(domain);
CREATE INDEX idx_blocked_last_seen ON blocked_requests(last_seen DESC);

-- ──────────────────────────────────────────────────────────
-- RULES
-- ──────────────────────────────────────────────────────────
CREATE TABLE rules (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    pattern     TEXT NOT NULL,
    rule_type   rule_type NOT NULL DEFAULT 'domain',
    action      rule_action NOT NULL DEFAULT 'block',
    enabled     BOOLEAN NOT NULL DEFAULT true,
    group_name  VARCHAR(100),
    priority    INTEGER NOT NULL DEFAULT 0,
    hit_count   BIGINT NOT NULL DEFAULT 0,
    created_by  UUID REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ,
    comment     TEXT
);

CREATE INDEX idx_rules_enabled ON rules(enabled);
CREATE INDEX idx_rules_action ON rules(action);
CREATE INDEX idx_rules_group ON rules(group_name);

-- ──────────────────────────────────────────────────────────
-- TRAFFIC STATS (hourly aggregation)
-- ──────────────────────────────────────────────────────────
CREATE TABLE traffic_stats (
    id              BIGSERIAL PRIMARY KEY,
    device_id       UUID REFERENCES devices(id) ON DELETE CASCADE,
    hour            TIMESTAMPTZ NOT NULL,
    total_queries   INTEGER NOT NULL DEFAULT 0,
    blocked_queries INTEGER NOT NULL DEFAULT 0,
    allowed_queries INTEGER NOT NULL DEFAULT 0,
    bytes_saved     BIGINT NOT NULL DEFAULT 0,
    unique_domains  INTEGER NOT NULL DEFAULT 0,
    UNIQUE (device_id, hour)
);

CREATE INDEX idx_traffic_hour ON traffic_stats(hour DESC);
CREATE INDEX idx_traffic_device ON traffic_stats(device_id);

-- ──────────────────────────────────────────────────────────
-- ALERTS CONFIG
-- ──────────────────────────────────────────────────────────
CREATE TABLE alert_configs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    channel     alert_channel NOT NULL,
    enabled     BOOLEAN NOT NULL DEFAULT true,
    config      JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────
-- ALERT EVENTS
-- ──────────────────────────────────────────────────────────
CREATE TABLE alert_events (
    id          BIGSERIAL PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    message     TEXT NOT NULL,
    severity    alert_severity NOT NULL DEFAULT 'info',
    source      VARCHAR(100),
    resolved    BOOLEAN NOT NULL DEFAULT false,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_alerts_severity ON alert_events(severity);
CREATE INDEX idx_alerts_resolved ON alert_events(resolved);
CREATE INDEX idx_alerts_created ON alert_events(created_at DESC);

-- ──────────────────────────────────────────────────────────
-- Seed: default admin user (password: changeme123 — change on first login)
-- ──────────────────────────────────────────────────────────
INSERT INTO users (email, username, hashed_password, role)
VALUES (
    'admin@antigravity.local',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LoFz0PcVvXhAMwJbe',
    'admin'
);
