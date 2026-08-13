from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    group: Mapped[str] = mapped_column(String(60), nullable=False)

    events: Mapped[list[EventRecord]] = relationship(back_populates="device")


class EventRecord(Base):
    __tablename__ = "event_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.device_id"), nullable=False)
    group: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    battery_level: Mapped[int] = mapped_column(Integer, nullable=False)
    signal_level: Mapped[int] = mapped_column(Integer, nullable=False)
    health_score: Mapped[int] = mapped_column(Integer, nullable=False)
    loaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    device: Mapped[Device] = relationship(back_populates="events")
