# Security, Operational Risks and Mitigations

| Threat | Prototype mitigation | Production next step |
|---|---|---|
| Unauthorized pharmacist/admin actions | Per-request JWT authorization and current server-side DB roles | MFA, session revocation, anomaly alerting |
| Weak/reversible password storage | bcrypt cost 12 (Python module; on offline Linux host libxcrypt bcrypt fallback) | Dedicated auth service and password rotation policy |
| ESP32 telemetry spoofing | Per-device HMAC over all critical fields | Key rotation, secure element, device certificates |
| Telemetry replay / duplicates | Fresh `sent_at`, random nonce, per-device sequence and SQLite uniqueness | MQTT TLS + authenticated broker, signed firmware, anti-rollback |
| Sending old readings after outage | Send new signed transport timestamp but preserve observed time and seq | RTC clock integrity and traceable synchronization |
| Lost Wi-Fi causes missing audit history | Persistent ESP32 LittleFS queue, one-in-flight ACK and ordered replay | Industrial FRAM ring buffer, physical burn-in tests, network quality alerts |
| Tampered temperature readings / audit events | Linked SHA-256 digest per audit event, verifies reading table against digest | External WORM/signed digest anchors, independent DB permissions |
| Misleading breach prediction | 30-min model is explicitly labeled synthetic | Test on real independent refrigerators; monitor missed-breach rate |
| Unsafe relocation | Server checks logged destination status + freshness, blocks discard/expiry, requires staff action | Check capacity, quarantine/custody, cold-room constraints, barcode scanning |
| Unsafe compressor control | Local hysteresis and min-off timer, sensor fault halts relay | Certified controller, compressor interlocks, electrician, calibration |
| Access to device credentials | `.gitignore` for `secrets.h` and `.env`; separate A/B secret | Secret vault, per-device ACL, TLS and hardware key protection |
| Insecure local MQTT broker | Local-only demo documentation | Never deploy `allow_anonymous true` to public internet |
| Clinical misuse | Report warnings and explicit quarantine notices | Validate under local national regulations; clinical SOP and documentation |

**Design principle:** Never let an ML suggestion alone move real medicine or override a physical safety relay. Firmware decisions and human release processes are independent of model forecasts.
