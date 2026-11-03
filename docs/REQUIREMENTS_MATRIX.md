# ColdChain 100-Point Requirements Coverage Matrix

Source: user-supplied **1st round question .pdf**, two-page ColdChain brief. No section-wise mark distribution was specified in the PDF; **do not infer point allocation**. Coverage is functional/source-file evidence; points cannot be guaranteed without evaluation.

| PDF requirement | Implementation evidence | Status / proof |
|---|---|---|
| 2 ESP32 nodes, temperature, door, relay, LED | `firmware/ColdChain_ESP32/ColdChain_ESP32.ino`, `secrets.example.h`, hardware README | Firmware source included; two physical boards not tested |
| OLED temperature and Safe / Warning / Breach | `displayTick()` in sketch | Implemented, requires real OLED bench test |
| MQTT every five seconds + door-change events | `loop()`, `appendSample()`, `networkTick()`; `coldchain/mqttbridge.py` | Coded; broker/hardware not bench tested |
| Compressor ON at 7C, OFF at 3C, min OFF 60s | `regulate()`, `relaySet()` | Implemented locally; physical compressor safety certification pending |
| Every batch 60 min above 8C | `core.py` `ingest()`, `batch_view()` | API tests pass |
| Over 12C exposure counts double | `core.py` weighted sample intervals | Automated test: 13C for 30m => Discard |
| Under 20% At Risk / zero Discard / admin red reset | `batch_status`, `admin_reset`, signed MQTT command, persistent firmware latch | API and RBAC tests pass; physical LED pending |
| Simulated power failure + battery report | Firmware button GPIO32 / battery ADC, simulation controls | Software test pass; actual battery calibration pending |
| Offline at least 30m, ordered deduped synchronization | Firmware LittleFS 900-sample queue, verified ACK, SQLite UNIQUE(seq) and nonce checks | Simulation recovery test pass; hardware flash durability and Wi-Fi test pending |
| Door >60s buzzer + external message | Firmware buzzer GPIO27, backend `alerts.py` | Door threshold test pass; actual delivery requires Telegram/SMTP credentials |
| JWT + bcrypt; 3 roles; server permission | `security.py`, `app.py` dependencies, user SQL | Tested inspector/pharmacist/admin authorization |
| Live dashboard with styled UI | `web/index.html`, `web/styles.css`, `web/app.js` | Built; full browser visual/device QA still required |
| Manage batches and move between fridges | `/api/batches`, `/api/relocations/confirm` | API tests pass |
| Public QR status & expiry without login | `/api/public/batch`, `/api/public/qr/*.png`, `/check/{token}` | API test pass |
| Device HMAC-SHA256 timestamp nonce reject/log replays | `core.py`, `security.py`, firmware HMAC | Tests pass for valid/replayed/invalid/duplicate/changed payload |
| Tamper-evident hash chain Verify Integrity | `db.py append_audit`, `core.py verified_integrity`, security UI | Hash tampering and reading-table tampering tests pass |
| Forecast 30 minutes ahead, warn >8C | `train_model.py`, `ml.py`, `models/forecast.joblib` | Synthetic trajectory-level held-out results documented |
| Compressor weakening 0-100 | `ml.py compressor_health` | Coded using observed active-cooling gradient; bench/reference calibration pending |
| Which batches to move and to which safe fridge | `core.py relocation_suggestions` | End-to-end API relocation test passes |
| Pharmacist one-click confirm relocation | dashboard button, `/api/relocations/confirm` | API test passes and RBAC enforced |
| Short dataset/features/results report | `report/ColdChain_Competition_Report.pdf` + metrics JSON/chart | Included; contains limitations and no fabricated field results |

## Important limitations
- The hardware sketch has not been compiled with Arduino IDE or flashed onto two boards in this environment.
- The browser layout has not been visually verified in a normal browser here. Functional API tests are stronger than visual QA in this package.
- No SMS/email/Telegram account was linked, so actual alert delivery is unverified.
- The forecast test data is synthetic. **Do not represent these model metrics as real clinical deployment accuracy.**
- The competition PDF does not provide grading weights; completing checkboxes does not promise 100/100.
