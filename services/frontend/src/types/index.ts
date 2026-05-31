export interface DashboardStats {
  total_queries_today: number;
  blocked_today: number;
  allowed_today: number;
  block_rate_today: number;
  total_queries_24h: number;
  blocked_24h: number;
  total_queries_30d: number;
  blocked_30d: number;
  active_clients: number;
  total_clients: number;
  top_blocked_domains: { domain: string; count: number }[];
  top_allowed_domains: { domain: string; count: number }[];
  queries_per_hour: { hour: string; total: number; blocked: number }[];
}

export interface Device {
  id: string;
  mac: string;
  ip: string;
  hostname: string | null;
  manufacturer: string | null;
  device_type: string | null;
  status: "online" | "offline" | "unknown";
  group_name: string | null;
  is_blocked: boolean;
  last_seen: string | null;
  first_seen: string;
}

export interface Rule {
  id: string;
  name: string;
  pattern: string;
  rule_type: "domain" | "regex" | "wildcard" | "ip";
  action: "block" | "allow" | "redirect";
  enabled: boolean;
  group_name: string | null;
  priority: number;
  hit_count: number;
  created_at: string;
  expires_at: string | null;
  comment: string | null;
}

export interface DnsLog {
  id: number;
  domain: string;
  client_ip: string;
  blocked: boolean;
  reason: string | null;
  query_type: string | null;
  latency_ms: number | null;
  queried_at: string;
}

export interface AlertEvent {
  id: number;
  title: string;
  message: string;
  severity: "info" | "warning" | "critical";
  source: string | null;
  resolved: boolean;
  created_at: string;
}
