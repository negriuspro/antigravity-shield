from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.dns_query import DnsQuery
from app.models.device import Device, DeviceStatus
from app.auth.dependencies import get_current_user
from app.schemas.stats import DashboardStats
from app.services.adguard import AdGuardClient

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardStats)
async def dashboard(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_24h = now - timedelta(hours=24)
    last_30d = now - timedelta(days=30)

    total_today = await db.scalar(select(func.count()).where(DnsQuery.queried_at >= today_start)) or 0
    blocked_today = await db.scalar(select(func.count()).where(DnsQuery.queried_at >= today_start, DnsQuery.blocked == True)) or 0

    total_24h = await db.scalar(select(func.count()).where(DnsQuery.queried_at >= last_24h)) or 0
    blocked_24h = await db.scalar(select(func.count()).where(DnsQuery.queried_at >= last_24h, DnsQuery.blocked == True)) or 0

    total_30d = await db.scalar(select(func.count()).where(DnsQuery.queried_at >= last_30d)) or 0
    blocked_30d = await db.scalar(select(func.count()).where(DnsQuery.queried_at >= last_30d, DnsQuery.blocked == True)) or 0

    active_clients = await db.scalar(
        select(func.count()).where(Device.status == DeviceStatus.online)
    ) or 0
    total_clients = await db.scalar(select(func.count(Device.id))) or 0

    top_blocked = await db.execute(
        select(DnsQuery.domain, func.count().label("count"))
        .where(DnsQuery.queried_at >= last_24h, DnsQuery.blocked == True)
        .group_by(DnsQuery.domain)
        .order_by(func.count().desc())
        .limit(10)
    )
    top_allowed = await db.execute(
        select(DnsQuery.domain, func.count().label("count"))
        .where(DnsQuery.queried_at >= last_24h, DnsQuery.blocked == False)
        .group_by(DnsQuery.domain)
        .order_by(func.count().desc())
        .limit(10)
    )

    hourly = await db.execute(
        select(
            func.date_trunc("hour", DnsQuery.queried_at).label("hour"),
            func.count().label("total"),
            func.sum(func.cast(DnsQuery.blocked, type_=text("integer"))).label("blocked"),
        )
        .where(DnsQuery.queried_at >= last_24h)
        .group_by(text("hour"))
        .order_by(text("hour"))
    )

    return DashboardStats(
        total_queries_today=total_today,
        blocked_today=blocked_today,
        allowed_today=total_today - blocked_today,
        block_rate_today=round(blocked_today / total_today * 100, 2) if total_today else 0.0,
        total_queries_24h=total_24h,
        blocked_24h=blocked_24h,
        total_queries_30d=total_30d,
        blocked_30d=blocked_30d,
        active_clients=active_clients,
        total_clients=total_clients,
        top_blocked_domains=[{"domain": r.domain, "count": r.count} for r in top_blocked],
        top_allowed_domains=[{"domain": r.domain, "count": r.count} for r in top_allowed],
        queries_per_hour=[
            {"hour": r.hour.isoformat(), "total": r.total, "blocked": r.blocked or 0}
            for r in hourly
        ],
    )
