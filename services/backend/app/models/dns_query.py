import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, INET
from app.database import Base


class DnsQuery(Base):
    __tablename__ = "dns_queries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    client_ip: Mapped[str] = mapped_column(INET, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    query_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    upstream: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    queried_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
