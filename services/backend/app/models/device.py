import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Enum as PgEnum, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, INET, MACADDR
from app.database import Base
import enum


class DeviceStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    unknown = "unknown"


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mac: Mapped[str] = mapped_column(MACADDR, unique=True, nullable=False)
    ip: Mapped[str] = mapped_column(INET, nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[DeviceStatus] = mapped_column(PgEnum(DeviceStatus, name="device_status"), default=DeviceStatus.unknown)
    group_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
