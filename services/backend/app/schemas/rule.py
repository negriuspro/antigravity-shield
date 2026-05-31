from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from app.models.rule import RuleAction, RuleType


class RuleCreate(BaseModel):
    name: str
    pattern: str
    rule_type: RuleType = RuleType.domain
    action: RuleAction = RuleAction.block
    group_name: str | None = None
    priority: int = 0
    comment: str | None = None
    expires_at: datetime | None = None


class RuleUpdate(BaseModel):
    name: str | None = None
    pattern: str | None = None
    action: RuleAction | None = None
    enabled: bool | None = None
    group_name: str | None = None
    comment: str | None = None


class RuleOut(BaseModel):
    id: UUID
    name: str
    pattern: str
    rule_type: RuleType
    action: RuleAction
    enabled: bool
    group_name: str | None
    priority: int
    hit_count: int
    created_at: datetime
    expires_at: datetime | None
    comment: str | None

    model_config = {"from_attributes": True}
