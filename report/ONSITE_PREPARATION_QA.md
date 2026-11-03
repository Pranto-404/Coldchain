# Pre-Hackathon Onsite Readiness — QA (2026-10-21)

**Source baseline:** ColdChain_Round1_Software_Ready_v6.zip; existing Round 1 simulation workflows retained.

## Automated verification

- Tests: **20 passed** using `python -m pytest -q` in container Linux environment: 13 original application tests + 4 Round 1 scenario tests + 3 additional hardware-configuration preparation tests.
- New tests cover unique generated firmware identities and HMAC keys, consistent backend/profile secrets, non-overwrite of existing private setup, invalid laptop IP rejection and detection of a mistyped Board B ID.
- JavaScript source check: `node --check web/app.js` passed after hardware/demo login mode separation.
- Offline configuration preflight file: `CHECK_HARDWARE_READY.py`; broker connectivity check offered but was not claimed validated with real Mosquitto.

## Not verified

- No Windows PowerShell/BAT execution was possible here. Test launcher on the actual Windows laptop in advance.
- Neither firmware build nor actual USB flashing / OLED / Dallas probe / door switch / relay / buzzer / LED / battery monitoring have been performed. Arduino CLI and ESP32 kit were not available.
- No real MQTT broker-to-ESP32 exchange, 30-minute hardware flash-buffer recovery, or internet alert delivery verified.
- Prediction model is trained/validated only on synthetic data. No real-device accuracy or medical suitability established.

## Security / operational limitations

The bundled onsite Mosquitto configuration accepts anonymous devices and listens on LAN port 1883: **trusted isolated hotspot demonstrations only**. Use authenticated broker + ACLs and TLS for any deployment beyond the local competition sandbox. Private passwords and signed-device keys are generated locally, not included in the public archive. Backend binds to loopback by default; QR checks on phones require deliberate network configuration.

**Grading:** No 100/100 or hardware-ready guarantee; prepare/test with organizer hardware and follow their requirements.
