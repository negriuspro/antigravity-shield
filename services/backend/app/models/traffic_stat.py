import uuid
from datetime import datetime
from sqlalchemy import Integer, BigInteger, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class TrafficStat(Base):
    __tablename__ = "traffic_stats"
    __table_args__ = (UniqueConstraint("device_id", "hour"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    hour: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_queries: Mapped[int] = mapped_column(Integer, default=0)
    blocked_queries: Mapped[int] = mapped_column(Integer, default=0)
    allowed_queries: Mapped[int] = mapped_column(Integer, default=0)
    bytes_saved: Mapped[int] = mapped_column(BigInteger, default=0)
    unique_domains: Mapped[int] = mapped_column(Integer, default=0)
