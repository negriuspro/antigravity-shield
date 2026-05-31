from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models.dns_query import DnsQuery
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/")
async def query_logs(
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    blocked: bool | None = Query(None),
    domain: str | None = Query(None),
    client_ip: str | None = Query(None),
    since: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q = select(DnsQuery).order_by(DnsQuery.queried_at.desc())
    if blocked is not None:
        q = q.where(DnsQuery.blocked == blocked)
    if domain:
        q = q.where(DnsQuery.domain.ilike(f"%{domain}%"))
    if client_ip:
        q = q.where(DnsQuery.client_ip == client_ip)
    if since:
        q = q.where(DnsQuery.queried_at >= since)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "domain": r.domain,
            "client_ip": str(r.client_ip),
            "blocked": r.blocked,
            "reason": r.reason,
            "query_type": r.query_type,
            "latency_ms": r.latency_ms,
            "queried_at": r.queried_at.isoformat(),
        }
        for r in rows
    ]
