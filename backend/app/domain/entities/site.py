"""Site — a physical farm/location. Top of the hierarchy."""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Site:
    name: str
    id: UUID = field(default_factory=uuid4)
    timezone: str = "UTC"
    created_at: datetime = field(default_factory=datetime.utcnow)
