from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from uuid import UUID

from app.database import get_db
from app.models.device import Device
from app.models.dns_query import DnsQuery
from app.auth.dependencies import get_current_user, require_admin
from app.schemas.device import DeviceOut, DeviceUpdate, DeviceStats

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/", response_model=list[DeviceOut])
async def list_devices(
    status: str | None = Query(None),
    group: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q = select(Device)
    if status:
        q = q.where(Device.status == status)
    if group:
        q = q.where(Device.group_name == group)
    q = q.order_by(Device.last_seen.desc().nullslast())
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{device_id}", response_model=DeviceOut)
async def get_device(device_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.patch("/{device_id}", response_model=DeviceOut)
async def update_device(
    device_id: UUID,
    body: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(device, field, value)
    await db.commit()
    await db.refresh(device)
    return device


@router.get("/{device_id}/stats", response_model=DeviceStats)
async def device_stats(device_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    total = await db.scalar(select(func.count()).where(DnsQuery.device_id == device_id))
    blocked = await db.scalar(select(func.count()).where(DnsQuery.device_id == device_id, DnsQuery.blocked == True))
    allowed = total - blocked
    return DeviceStats(
        device_id=device_id,
        total_queries=total or 0,
        blocked_queries=blocked or 0,
        allowed_queries=allowed,
        block_rate=round(blocked / total * 100, 2) if total else 0.0,
    )


@router.post("/{device_id}/block", status_code=204)
async def block_device(device_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    await db.execute(update(Device).where(Device.id == device_id).values(is_blocked=True))
    await db.commit()


@router.post("/{device_id}/unblock", status_code=204)
async def unblock_device(device_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    await db.execute(update(Device).where(Device.id == device_id).values(is_blocked=False))
    await db.commit()
