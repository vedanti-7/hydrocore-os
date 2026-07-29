# infra/

Everything needed to run HydroCore OS as containers, on dev machines or on the Pi itself.

- `docker/mosquitto/` — mosquitto.conf, password file generation (auth required, no anonymous access).
- `docker/postgres/` — DB init scripts (extensions, first-run setup).
- `docker/nginx/` — Reverse proxy, future TLS termination.
- `environments/dev/` — docker-compose overrides for local development (hot reload, bind mounts).
- `environments/staging/` — Pre-production config.
- `environments/site-configs/` — ONE .env per physical greenhouse Pi. This is where
  multi-greenhouse scaling actually lives: greenhouse #2 is a new file here with a
  different SITE_ID, not a code change.
- `raspberry-pi/` — Pi OS provisioning scripts, systemd units, first-boot setup.
