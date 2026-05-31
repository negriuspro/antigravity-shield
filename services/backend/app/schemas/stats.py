from pydantic import BaseModel
from datetime import datetime


class DashboardStats(BaseModel):
    total_queries_today: int
    blocked_today: int
    allowed_today: int
    block_rate_today: float
    total_queries_24h: int
    blocked_24h: int
    total_queries_30d: int
    blocked_30d: int
    active_clients: int
    total_clients: int
    top_blocked_domains: list[dict]
    top_allowed_domains: list[dict]
    queries_per_hour: list[dict]


class TrafficPoint(BaseModel):
    timestamp: datetime
    total: int
    blocked: int
    allowed: int
