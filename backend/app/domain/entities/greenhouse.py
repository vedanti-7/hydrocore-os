"""Greenhouse — a growing area within a Site."""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Greenhouse:
    site_id: UUID
    name: str
    id: UUID = field(default_factory=uuid4)
    description: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
