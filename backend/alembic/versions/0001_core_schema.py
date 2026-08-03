"""Core schema: sites, greenhouses, devices, entities, state_changes

Revision ID: 0001
Revises:
Create Date: 2026-08-03
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "sites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("timezone", sa.String(64), server_default="UTC"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "greenhouses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("site_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("greenhouse_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("greenhouses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("device_type", sa.String(32), nullable=False),
        sa.Column("mqtt_client_id", sa.String(120), nullable=False, unique=True),
        sa.Column("status", sa.String(16), server_default="unknown"),
        sa.Column("firmware_version", sa.String(32), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_devices_greenhouse_id", "devices", ["greenhouse_id"])

    op.create_table(
        "entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(16), nullable=False),
        sa.Column("device_class", sa.String(32), nullable=False),
        sa.Column("unique_id", sa.String(160), nullable=False, unique=True),
        sa.Column("unit", sa.String(16), nullable=True),
        sa.Column("last_state", postgresql.JSONB, nullable=True),
        sa.Column("last_state_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attributes", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_entities_device_id", "entities", ["device_id"])

    op.create_table(
        "state_changes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", postgresql.JSONB, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_state_changes_entity_id_recorded_at", "state_changes", ["entity_id", "recorded_at"])


def downgrade() -> None:
    op.drop_table("state_changes")
    op.drop_table("entities")
    op.drop_table("devices")
    op.drop_table("greenhouses")
    op.drop_table("sites")
