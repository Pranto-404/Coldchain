# Quality Assurance and Evidence

## Executed tests

Command: `PYTHONPATH=. python -m pytest -q` in project root (PowerShell: `python -m pytest -q`).

**Observed result: 13 passed.** Tests run against isolated temporary SQLite databases through the FastAPI test client. The suite verifies:

1. JWT auth and Admin / Pharmacist / Inspector server authorization; authenticated versus public endpoints.
2. No-account QR image and public lot/expiry/status page.
3. Valid signed device telemetry, repeated nonce replay rejection, identical-sequence idempotent retransmit.
4. Changed payload with the same sequence rejected and recorded as suspicious.
5. Invalid HMAC and stale send timestamp rejected; logs preserve rejection reasons.
6. 13°C for 30 real minutes of readings consumes a 60-minute weighted heat budget.
7. 8.0°C exactly does not consume heat exposure; `<20%` remaining is At Risk.
8. Discarded batch transfer is blocked, Admin-only reset works, Pharmacist reset denied.
9. Normal relocation confirmation preserves heat-dose ledger and rejects stale recommendation.
10. Edited audit entry is detected by hash-chain verification.
11. Edited sensor reading table row is detected by audit cross-check.
12. Door-open for over 60 seconds generates an alert record; missing credentials show **not_configured**, never success.
13. Signed simulated telemetry, mains-loss status, Wi-Fi-off buffer replay in ascending order, no duplicate DB rows.

## Verified additional artifacts
- `python -m compileall -q coldchain` — syntax compile pass.
- `node --check web/app.js` — JavaScript syntax check pass.
- `python train_model.py` — model trained and metrics exported; results in `report/model_metrics.json` and validation PNG.
- Local server HTTP health and authenticated `/api/dashboard` smoke-tested. Two synthetic fridges produced real ingested rows after a simulator battery-boundary bug was found and fixed.

## Not tested / do not misrepresent
- Arduino code was not compiled with its vendor libraries; two ESP32 boards were not flashed or physically connected to a refrigerator.
- Relay, OLED, battery ADC, flash endurance, and retained red LED latch were not observed electrically.
- Browser QA (rendering/cross-device/accessibility) was not completed in a normal unrestricted browser. The layout code exists; manual visual QA remains.
- External Telegram/SMTP message delivery needs working credentials and an actual recipient and was not tested.
- MQTT broker, signed hardware ACK and low-level ESP32 reconnection were not bench-tested end to end.
- Real refrigerator sensor calibration, model field accuracy, and clinical safety decisions remain unvalidated.

## Recommended judge-side final checklist
- [ ] Open login screen, use all three roles, verify buttons respect access.
- [ ] With a real browser, view desktop (1440px), laptop (1024px), tablet, and 390px mobile screen; test QR popup and form interactions.
- [ ] Start local simulator and observe 2 fresh fridges and time plots.
- [ ] Simulate a door-open event for >60 seconds and see alert outcome.
- [ ] Simulate power loss and reconnect Wi-Fi after buffering, compare source order in CSV.
- [ ] Show forecast prediction and safe relocation, and confirm as Pharmacist.
- [ ] Corrupt a copy of the database and run Verify Integrity to demonstrate detection (do not corrupt submission DB).
- [ ] If hardware is available, flash separate IDs/secrets and check threshold timing with a probe simulator.
- [ ] Configure Telegram or SMTP privately and prove an actual alert delivery before claiming the feature fully deployed.
