# firmware/

ESP32-S3 node code. Each *-node/ folder is a self-contained PlatformIO project.

- `shared/` — Common lib: WiFi provisioning, MQTT client wrapper, OTA updater.
  Written ONCE, reused by all four node types — this logic is identical across nodes;
  only sensor/actuator drivers differ.
- `env-monitor-node/` — Temp, humidity, CO2, O2, PAR, light intensity.
- `env-control-node/` — Humidifier, grow lights, AC, ventilation/exhaust fans.
- `water-monitor-node/` — pH, EC, DO, water temp, water level.
- `water-control-node/` — Peristaltic pumps, water pump, drain/fill valves, mixing pump.
- `camera-node/` — Future: dual Raspberry Pi camera integration.

Nodes publish telemetry to and subscribe to commands from infra/docker/mosquitto/.
Pin assignments come from hardware/pinout-maps/ — never hardcode a GPIO without checking there first.
