# hardware/

The handoff point between the physical build and the firmware code. Even though the
hydroponics hardware build itself isn't the software team's job, firmware/ is useless
without an agreed pin/wiring contract — that contract lives here.

- `wiring-diagrams/` — Per node type.
- `bom/` — Bill of materials.
- `pinout-maps/` — GPIO/ADC pin assignments per node. Firmware code must match this exactly.
- `datasheets/` — Sensor/actuator datasheets for reference.
