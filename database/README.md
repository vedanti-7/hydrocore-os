# database/

Documentation and discoverability layer for the database. NOT the source of schema truth
(that's backend/alembic/, which must live next to the models it migrates).

- `migrations/` — Mirrored view of backend/alembic for visibility from the repo root.
- `seeds/` — Sample plant profiles, demo data for local development.
- `schema-docs/` — ERD diagrams, kept in sync with the real schema.
