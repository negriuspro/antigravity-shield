from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone

from app.database import get_db
from app.models.alert import AlertEvent, AlertSeverity
from app.auth.dependencies import get_current_user, require_admin
from app.services.alerts import broadcast_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/")
async def list_alerts(
    resolved: bool | None = Query(None),
    severity: AlertSeverity | None = Query(None),
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q = select(AlertEvent).order_by(AlertEvent.created_at.desc()).limit(limit)
    if resolved is not None:
        q = q.where(AlertEvent.resolved == resolved)
    if severity:
        q = q.where(AlertEvent.severity == severity)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/{alert_id}/resolve", status_code=204)
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    await db.execute(
        update(AlertEvent)
        .where(AlertEvent.id == alert_id)
        .values(resolved=True, resolved_at=datetime.now(timezone.utc))
    )
    await db.commit()


@router.post("/test")
async def test_alert(_=Depends(require_admin)):
    await broadcast_alert("Test Alert", "This is a test from AntiGravity Shield", "info")
    return {"status": "sent"}
