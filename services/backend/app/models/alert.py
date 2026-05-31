import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Text, DateTime, Enum as PgEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, BIGINT
from app.database import Base
import enum


class AlertChannel(str, enum.Enum):
    email = "email"
    telegram = "telegram"
    discord = "discord"
    webhook = "webhook"


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[AlertChannel] = mapped_column(PgEnum(AlertChannel, name="alert_channel"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(PgEnum(AlertSeverity, name="alert_severity"), default=AlertSeverity.info)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
