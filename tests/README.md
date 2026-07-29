# tests/

Cross-service tests that don't belong to a single component.

- `e2e/` — Playwright end-to-end tests hitting real running containers
  (full stack: frontend -> backend -> Postgres/MQTT).

Unit and integration tests for individual services live inside their own folders
(backend/tests/, frontend uses its own test setup).
