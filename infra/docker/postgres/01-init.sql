-- Runs once on first container start (empty data volume only).
-- Extensions we know we'll need across future modules.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
