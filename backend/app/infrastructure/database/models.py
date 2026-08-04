"""
SQLAlchemy ORM models — the persistence representation of the domain.

These are intentionally separate from app/domain/entities/. Business logic
never imports from this file directly; only repositories do.
"""
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SiteModel(Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    greenhouses: Mapped[list["GreenhouseModel"]] = relationship(back_populates="site")


class GreenhouseModel(Base):
    __tablename__ = "greenhouses"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    site: Mapped["SiteModel"] = relationship(back_populates="greenhouses")
    devices: Mapped[list["DeviceModel"]] = relationship(back_populates="greenhouse")


class DeviceModel(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    greenhouse_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("greenhouses.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    device_type: Mapped[str] = mapped_column(String(32), nullable=False)
    mqtt_client_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="unknown")
    firmware_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_seen_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    greenhouse: Mapped["GreenhouseModel"] = relationship(back_populates="devices")
    entities: Mapped[list["EntityModel"]] = relationship(back_populates="device")

    __table_args__ = (Index("ix_devices_greenhouse_id", "greenhouse_id"),)


class EntityModel(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(16), nullable=False)
    device_class: Mapped[str] = mapped_column(String(32), nullable=False)
    unique_id: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_state_changed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    device: Mapped["DeviceModel"] = relationship(back_populates="entities")

    __table_args__ = (Index("ix_entities_device_id", "device_id"),)


class StateChangeModel(Base):
    __tablename__ = "state_changes"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    recorded_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_state_changes_entity_id_recorded_at", "entity_id", "recorded_at"),
    )
