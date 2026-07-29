# frontend/

React + Tailwind dashboard.

- `src/components/` — Reusable UI (cards, charts, forms).
- `src/pages/` — Dashboard, Devices, Automation, Reports.
- `src/hooks/` — useEntity, useWebSocket, etc.
- `src/api/` — REST/WebSocket client, ideally generated from backend's OpenAPI schema.
- `src/store/` — App state management.
- `src/types/` — Shared TS types mirroring backend schemas.

Talks to backend/ only via REST (reads/writes) and WebSocket (live state pushes).
