# ColdChain Competition Pitch — 10-Minute Live Demonstration

**0:00–0:45 · Opening** — “Vaccines and insulin can lose effectiveness in the wrong temperature window. ColdChain gives pharmacists a verifiable history of every degree, every batch, and every response.” State clearly that this demonstration uses synthetic fridge twins unless physical devices are actually connected.

**0:45–2:00 · Monitoring** — Show Fridge Alpha and Beta, 5-second telemetry, DS18B20 + door + compressor + battery fields, OLED firmware implementation, and the 2–8°C operating target. Explain the local 7°C ON / 3°C OFF hysteresis and 60-second off-time, which does not depend on the server.

**2:00–3:15 · Batch safety** — Open Inventory. Show each lot's 60-minute heat budget, 2x time above 12°C, status At Risk below 20% and Discard at zero; demonstrate the public QR viewer and expiry without login. Explain that transferring a batch does not wipe exposure history.

**3:15–4:30 · Failures** — Switch mains off and back on in Simulation lab, then Wi-Fi off for several seconds and back on; show ordered data replay and anti-duplicate sequence behavior. Note simulator buffering is RAM while hardware LittleFS queue supports over 30 minutes.

**4:30–5:30 · Door response** — Keep Alpha door open for over 60 seconds. Show audit event and local buzzer implementation. If external credentials are not available, say that Telegram/email is integrated but delivery was not tested; display `not_configured` instead of making a false claim.

**5:30–7:00 · Prediction** — Drive an overheating scenario using Simulation lab heat spike / reduced cooling. Show temperature forecast at +30 minutes and health score; open `report/forecast_validation.png` and explain the 220 synthetic trajectories, group holdout and the actual synthetic MAE/recall. Avoid claiming clinical validation.

**7:00–8:15 · Relocation** — On a threatened fridge, show eligible batches suggested for an in-range destination and confirm one as Pharmacist. State actual physical relocation remains human verified.

**8:15–9:20 · Security / accountability** — Use Inspector login to show read-only status. Explain signed HMAC device messages, timestamp + nonce, JWT/bcrypt/roles, public QR privacy, hash-chain verification, replay rejection. Press Verify Integrity. Offer CLI demo `python -m pytest -q` showing 13 passing automated checks.

**9:20–10:00 · Close** — “ColdChain converts temperature streams into auditable actions: prevent spoilage, recognize exposure, and tell the right person what to move and why.” Mention the physical hardware and real-world model validation still needed before clinical deployment.
