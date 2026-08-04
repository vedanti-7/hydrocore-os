"""
StateChange — append-only history of every Entity state transition.

This IS the historical graph data source and what the Automation Engine
queries for time-window conditions ("temp above X for 10 minutes").
Never updated, only inserted.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class StateChange:
    entity_id: UUID
    value: Any
    id: UUID = field(default_factory=uuid4)
    recorded_at: datetime = field(default_factory=datetime.utcnow)
