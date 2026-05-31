from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import get_db
from app.models.rule import Rule
from app.auth.dependencies import get_current_user, require_admin
from app.schemas.rule import RuleCreate, RuleUpdate, RuleOut

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/", response_model=list[RuleOut])
async def list_rules(
    action: str | None = Query(None),
    enabled: bool | None = Query(None),
    group: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q = select(Rule).order_by(Rule.priority.desc(), Rule.created_at.desc())
    if action:
        q = q.where(Rule.action == action)
    if enabled is not None:
        q = q.where(Rule.enabled == enabled)
    if group:
        q = q.where(Rule.group_name == group)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=RuleOut, status_code=201)
async def create_rule(body: RuleCreate, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    rule = Rule(**body.model_dump(), created_by=user.id)
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=RuleOut)
async def update_rule(rule_id: UUID, body: RuleUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
