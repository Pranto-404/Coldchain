# ColdChain — Actual Hardware Test Record (blank template)

**Date/time (timezone):** ________   **Team:** ________   **Engineer:** ________

**Actual hardware received:**

- Board A exact variant / USB chip / COM port: ________________________
- Board B exact variant / USB chip / COM port: ________________________
- Sensor/accuracy and supply: ________________________
- OLED model, I²C address, relay interface polarity: ________________________
- Wi-Fi local SSID (never record password): ________________________
- Backend version / commit / archive hash: ________________________

| Test ID | Procedure | Expected observation | Actual observation | Pass / Fail / Blocked |
| --- | --- | --- | --- | --- |
| H1 | Boot board A | OLED + unique FRIDGE_A ID | | |
| H2 | Boot board B | OLED + unique FRIDGE_B ID | | |
| H3 | MQTT 5s readings | New seq from each about every 5 sec | | |
| H4 | Toggle door switch | Immediate telemetry event | | |
| H5 | Control thresholds | Low-voltage relay ON at 7°C, OFF at 3°C | | |
| H6 | Anti-short-cycle | No restart during 60s min off | | |
| H7 | Above-8°C interval | Correct heat budget decrement | | |
| H8 | Above-12°C interval | Double-weighted exposure | | |
| H9 | Discard & red latch | Discard latch remains red | | |
| H10 | Door >60s | Buzzer and configured external alert received | | |
| H11 | Power fail button | Mains false and battery indicator updated | | |
| H12 | Wi-Fi offline 30+ min | Ordered sync, no duplicates, no loss | | |
| H13 | Signature/nonce | Invalid/replayed messages rejected/logged | | |
| H14 | Audit Verify Integrity | Integrity valid / edited records detectable | | |
| H15 | AI forecast & relocation | Synthetic-model warning, qualified move confirmation | | |
| H16 | Admin/Pharmacist/Inspector RBAC | Server rejects unauthorized writes | | |

**Evidence filenames (no secrets):**

- Screenshots / photos: ________________________
- Serial logs: ________________________
- MQTT log snippets: ________________________
- Backend/pytest results: ________________________
- Alert delivery evidence (redact tokens and private data): ________________________

**Unresolved issues:** ________________________

**Truthful limitations:** Hardware test results are pending until completed; AI model currently trained on synthetic trajectories and is not clinically validated.
