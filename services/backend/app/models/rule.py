import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, BigInteger, Text, ForeignKey, DateTime, Enum as PgEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class RuleAction(str, enum.Enum):
    block = "block"
    allow = "allow"
    redirect = "redirect"


class RuleType(str, enum.Enum):
    domain = "domain"
    regex = "regex"
    wildcard = "wildcard"
    ip = "ip"


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    rule_type: Mapped[RuleType] = mapped_column(PgEnum(RuleType, name="rule_type"), default=RuleType.domain)
    action: Mapped[RuleAction] = mapped_column(PgEnum(RuleAction, name="rule_action"), default=RuleAction.block)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    group_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    hit_count: Mapped[int] = mapped_column(BigInteger, default=0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
