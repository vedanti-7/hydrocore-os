# ai/

Plant health AI. Scaffolded now, built in Phase 2 (after the core sense-decide-act loop is solid).

- `models/` — Trained weights. NOT committed to git — .gitignore'd, distributed as release artifacts.
- `training/` — Training scripts, dataset prep.
- `inference-service/` — Standalone deployable service, called by backend/ over an internal API.
- `notebooks/` — Exploration only, never production code.

Deliberately kept as a separate service, not baked into backend/ — plant health inference
is compute-heavy and must never be able to crash or block the control-loop backend.
