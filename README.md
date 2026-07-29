# HydroCore OS

A Raspberry Pi based Industrial IoT Operating System for Hydroponics, Greenhouse
Automation, and Controlled Environment Agriculture (CEA).

Open-source, production-grade, built with the same seriousness as Mycodo, Home
Assistant, and OctoPrint.

---

## Architecture in one paragraph

Each greenhouse runs its own Raspberry Pi 5, hosting the full stack locally
(FastAPI backend, PostgreSQL, Mosquitto MQTT broker) — this is an **edge-first,
federated** topology, not a single central cloud brain. Control loops (fans,
pumps, valves) must keep working even if the internet drops, which only works
if the decision-making lives on-site. ESP32-S3 nodes (environment monitoring,
environment control, water monitoring, water control) talk to the local
Mosquitto broker over MQTT. The backend consumes telemetry, persists state to
Postgres, evaluates automation rules, and pushes live updates to the React
frontend over WebSocket. Multi-greenhouse support is a **configuration
discipline**, not a rewrite: `Site`/`Greenhouse` sit at the top of the domain
model from day one, and `infra/environments/site-configs/` is where a second
greenhouse becomes a new config file, not new code.

## Folder guide

| Folder | Purpose |
|---|---|
| `backend/` | FastAPI app — clean architecture (api / domain / infrastructure / core) |
| `frontend/` | React + Tailwind dashboard |
| `firmware/` | ESP32-S3 node code, one folder per node type + shared lib |
| `ai/` | Plant health inference — separate deployable service (Phase 2) |
| `infra/` | Docker configs, Mosquitto/Postgres/Nginx setup, per-site environments, Pi provisioning |
| `database/` | Schema docs, ERDs, seed data (schema truth itself lives in `backend/alembic/`) |
| `hardware/` | Wiring diagrams, BOM, pinout maps — the contract between hardware and firmware |
| `docs/` | MkDocs site, Architecture Decision Records, API docs, user guide |
| `scripts/` | Setup, deploy, and dev automation |
| `tests/` | Cross-service end-to-end tests |

Every folder above also has its own `README.md` explaining its subfolders in detail.

## Communication flow

```
firmware/ (ESP32 nodes)
   --> MQTT publish/subscribe -->
infra/docker/mosquitto/ (broker, auth required, no anonymous access)
   --> consumed by -->
backend/app/infrastructure/mqtt/
   --> persists via -->
backend/app/infrastructure/database/  -->  database/ (Postgres)
   --> pushes live state via WebSocket, serves REST -->
frontend/
   --> (Phase 2) camera frames sent to -->
ai/inference-service/  -->  results returned to backend/
```

`hardware/` and `docs/` don't participate at runtime — they're the contracts
and knowledge base that keep `firmware/` and `backend/` honest as the team
grows. `infra/` doesn't run application logic either — it's the environment
definition that makes the same `docker-compose.yml` behave identically on a
dev laptop and on the real Pi.

---

## Roadmap (4 months, ~2-week sprints)

| Sprint | Focus | Key output |
|---|---|---|
| 0 (now) | Foundation | Repo skeleton + Docker stack running on the Pi |
| 1 | Device & Entity Manager | Core domain model + Postgres schema (Site -> Greenhouse -> Device -> Entity) |
| 2 | MQTT Manager + firmware skeleton | Topic schema, `firmware/shared/` MQTT lib, env-monitor-node publishing real data |
| 3 | Sensor Manager + live data | Backend ingests telemetry, WebSocket pushes to frontend, first real dashboard |
| 4 | Actuator Manager + env-control-node | Relay control from UI, command round-trip proven end-to-end |
| 5 | Auth & RBAC | Login, roles, protects control endpoints before more actuators are added |
| 6 | Automation Engine | Trigger/condition/action rules, first real automation |
| 7 | Water Monitoring + Water Control nodes | pH/EC/DO ingestion, pump/valve control |
| 8 | Plant Profiles + Growth Stage Manager + Scheduler | Ties automation to a real crop cycle |

Camera/AI, Recipe Engine, Notifications, and Reports land in Phase 2, after the
core sense -> decide -> act -> display loop is solid.

---

## Day 1 Actions (do these now, on the physical Pi)

1. **Provision the Raspberry Pi 5** — flash 64-bit Raspberry Pi OS Lite (or
   Ubuntu Server 24.04 arm64), enable SSH, set a static IP or stable hostname
   on your LAN.
2. **Install Docker + Compose on the Pi**
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   # log out/in, then verify:
   docker run hello-world
   ```
3. **Create the GitHub repo** (`hydrocore-os`), push this exact folder
   structure as the first commit. Pick a license (MIT or Apache-2.0 are
   standard for this category of project).
4. **This skeleton is your commit** — every folder here already has a
   `README.md` explaining its purpose. Commit it before any real code lands,
   so the structure itself is reviewable and locked in.
5. **Add the Module 0 files** (docker-compose.yml, backend skeleton,
   Mosquitto config, Postgres init) into their now-correct folders.
6. **Clone the repo onto the Pi itself**, run `docker compose up --build`,
   and confirm the full stack comes up **on the actual Pi**, not just a dev
   laptop — arm64-specific issues show up here, better caught today than in
   week 6.
7. **Tag it**: `git tag v0.0.1-skeleton` — this is the real, working "day one"
   milestone.

Once this is done, come back and we'll design Sprint 1 (Device & Entity
Manager) properly — architecture, schema, and folder placement — before
writing any code.
