# Technical Architecture and Data Contracts

```text
ESP32 A (DS18B20, door, relay, LEDs, OLED, LittleFS offline buffer)
      | signed HMAC JSON; 5s interval + door-change
      v
      +-------> MQTT broker coldchain/telemetry/FRIDGE_A ---+
ESP32 B ------> MQTT broker coldchain/telemetry/FRIDGE_B ---+--> MQTT bridge
                                                              | validate HMAC,
                                                              | current send time,
                                                              | unique nonce and seq
                                                              v
                    +-------------------------------------- FastAPI ingest
                    |                                       |       |
                    v                                       v       v
            SQLite WAL data                          audit hash   alert outbox
               |          |                               chain      Telegram/email
               |          +--> 60-min weighted exposure budget
               |                      |
               v                      +--> discard latch command (signed)
          RandomForest predictor
          cooling health heuristic --> relocation suggestions
                    |
                    v
      Authenticated HTML dashboard + roles + public token QR pages
```

## Auth and access
`POST /api/auth/login` accepts username/password and issues 6-hour JWT using HS256. Passwords are bcrypt hash with cost 12, checked with constant-time compare. JWT alone never authorizes a role: on each protected request the backend reads current enabled user/role from SQLite. `require()` rejects forbidden operations on server.

## Device message JSON

```json
{
  "device_id": "FRIDGE_A",
  "seq": 12001,
  "observed_at": 1792600000,
  "temp_c_100": 445,
  "door_open": false,
  "mains_ok": true,
  "compressor_on": false,
  "battery_pct": 100,
  "sent_at": 1792600002,
  "nonce": "f3b90fe313f7ab1b",
  "signature": "<64 hexadecimal characters: HMAC-SHA256>"
}
```

`observed_at` and `sent_at` are Unix UTC seconds. The `signature` is HMAC-SHA256 over the UTF-8 canonical string formed by joining these ten fields with vertical bars, in the exact order listed above, encoding booleans as `1` or `0`, and temperature as an integer (100ths of a Celsius degree). `signature` itself is excluded. The backend enforces `abs(now - sent_at) <= 120 s` and `observed_at` no older than one day relative to `sent_at`. On re-transmission generate a fresh signed `sent_at`/`nonce`, retaining the original `seq`, measurement and `observed_at`.

A queue message is removed only after **server ACK** `coldchain/ack/<device>`, signed HMAC over `device_id|seq|sent_at|nonce`. A 5.5-second timeout initiates re-sign/retry; repeated identical sequence is idempotently acknowledged. A duplicate nonce or changed content under the same sequence is rejected and security-logged. High-water sequence reservations in NVS avoid identity collisions after unexpected reboot.

The backend also publishes **signed commands** to `coldchain/cmd/<device>`, HMAC over `device_id|discard_latch_as_0_or_1|sent_at|nonce`. ESP32 checks signature and recency before changing the NVS-persisted red latch.

## Temperature budget

For two successive valid measurements `i`, `i+1`, with time delta `d` seconds, and `0 < d <= 90`:

`dose_increment = 0` when `T_i <= 8°C`; `dose_increment = d` when `8 < T_i <= 12°C`; `dose_increment = 2*d` when `T_i > 12°C`.

`exposure_seconds = min(3600, exposure_seconds + dose_increment)`, tracked **per batch**. The last-measurement temperature is used across the interval (zero-order hold). If the telemetry gap is greater than 90 seconds, it is explicitly audit-logged and **no safe exposure assumption is made**. A batch's exposure is not cleared when moved to another fridge. `remaining_pct < 20` => At Risk. `remaining_pct == 0` => Discard. Backend and physical LED latch require an Admin action; resetting the software state does **not** permit using spoiled doses.

## Hash chain
`digest_i = SHA256(prev_digest + '|' + ISO_UTC_time + '|' + actor + '|' + action + '|' + canonical_json_details)`; genesis prev hash is `GENESIS`. `Verify Integrity` recomputes each digest, validates linked prev hashes, **and compares every reading event to its stored readings row**. Editing a sensor row, deleting a row, or modifying a chained event yields failure. An attacker with unrestricted DB access could recompute the entire chain; production requires an independently signed, off-site anchor.

## Prediction
The shipped model is a pre-trained RandomForestRegressor using eight features extracted from the latest 61 samples (~5 minutes of data at five-second cadence): temp, trend °C/min, mean, variability, door, mains, compressor, and compressor duty fraction. Training sources 220 deterministic **synthetic** fridge-physics scenarios. Target is temperature at time +30 minutes. When the serialized model is absent or cannot load, the application uses an explicitly labeled engineering-rule fallback and does **not** claim an ML prediction.

Compressor health shows an indicative 0-100 score based on median cooling slope while the compressor is on, mains available, and door closed. It requires at least five valid cooling intervals. Its reference expected cooling rate of 0.18°C/min is **synthetic** and must be calibrated to an actual refrigeration unit before meaningful interpretation.

## Data contracts and performance
- Backend: FastAPI, SQLite3 in WAL mode, PyJWT HS256, bcrypt; optional paho-mqtt client.
- Frontend: same-origin API, no external JS/CSS CDN, responsive pure HTML/CSS/JavaScript.
- Metadata: source=`simulator` vs source=`device` for every reading; simulated flag on refrigerator.
- Public pages contain only name, batch/lot, status, percentage, expiry, check timestamp. Opaque 128-bit token avoids guessable IDs.
- MQTT local demo listens on 1883 without auth. This is **never safe for internet-facing deployment**; put broker on a private LAN and enable TLS, authentication and ACLs for production.
