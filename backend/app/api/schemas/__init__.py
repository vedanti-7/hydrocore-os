"""
Pydantic request/response schemas — the API's wire contract.

Deliberately separate from app/domain/entities/: the domain dataclasses are
framework-free and may change shape for internal reasons, while these are a
published contract the frontend depends on. Read models set
from_attributes=True so they validate directly off a domain dataclass.
"""
