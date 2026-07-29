# backend/

FastAPI application. Clean-architecture layering — no layer skips another.

- `app/api/` — HTTP + WebSocket routes only. No business logic here.
- `app/domain/entities/` — Core model: Site, Greenhouse, Device, Entity, StateChange. Framework-free.
- `app/domain/interfaces/` — Abstract contracts implemented by infrastructure.
- `app/domain/services/` — Business logic: Automation Engine, Sensor Manager, Actuator Manager.
- `app/infrastructure/database/` — SQLAlchemy models + repositories, implements domain interfaces.
- `app/infrastructure/mqtt/` — Broker client, topic parsing, publish/subscribe logic.
- `app/infrastructure/external/` — Email, notifications, future cloud sync.
- `app/core/` — Config, logging, DI wiring.
- `alembic/` — Database migrations. The ONLY source of schema truth.

Rule: domain/ never imports from infrastructure/ or api/. Dependencies point inward.
