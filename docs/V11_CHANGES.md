# ColdChain V11 — hardware view, new interface, live deployment

**Live demo:** https://coldchain-monitor-30qu.onrender.com  (Render free plan, Singapore)
**Source:** https://github.com/Pranto-404/Coldchain — pushes to `main` redeploy automatically.

The free plan sleeps after 15 minutes without visitors; the first request then takes ~50 s to wake
it, and the demo database starts fresh (30 minutes of simulated history is seeded on boot). Open the
link a minute before presenting.

## Hardware page (new)

An interactive drawing of one ESP32 node, driven by the same telemetry as the dashboard:

- Glass-door fridge with one vial per stored batch (colour = Safe / At risk / Discard), DS18B20 probe,
  reed switch and magnet, compressor with spinning fan and heat exhaust, frost while cooling.
- ESP32 DevKit with the real pin numbers from `hardware_pins.h`, SSD1306 OLED showing the firmware's
  text, relay module whose contact closes when the compressor runs, red/green LEDs, buzzer, mains-fail
  button, 18650 battery level.
- Signals animate along the wires; each MQTT packet travels ESP32 → broker → API → database and an ACK
  returns. With Wi-Fi down, packets drop into the flash-queue box and replay in order on reconnect.
- **Click the door, the mains-fail button or the antenna** to change the simulated node. Like the real
  firmware, a change is published immediately instead of waiting for the next 5 s sample.
- Thermostat state machine (Idle → Cooling at ≥ 7 °C after 60 s off → Min-off at ≤ 3 °C) with a
  hysteresis bar, live pin map, and a serial monitor printing the firmware's diagnostic lines.

## Interface redesign

Instrument-panel styling instead of the generic dashboard look: paper background, ink type, one cold
accent colour, IBM Plex Sans/Mono, hairline rules, SVG icons (no emoji). Motion is tied to state:
dial and health rings sweep to new values, numbers count to new readings, the chart draws in once,
LEDs glow, the bell rings on a new critical alert. Animations respect "reduce motion".

## Fixes found while testing V11

- Entry animations replayed on every 5 s refresh, making the page flicker → first render only.
- Chart drew a straight line (and door shading) across periods with no data → gaps shown as "no data".
- Inventory table pushed the page wider than the screen at ~960 px → table scrolls in its panel.
- Thermostat dial labels overlapped the reading → simplified dial.
- Demo mode used a JWT secret written in the public source → random secret per server start.

## Tests

`pytest`: 38 passed (adds immediate-publish and hardware-asset/CSP tests).
