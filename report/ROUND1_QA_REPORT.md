# Round 1 Software Audit & QA — ColdChain

**Scope:** FastRoboX 1.0 Round 1, software simulation of challenge questions 2, 4 and 5. Not a physical hardware validation report.

## What was inspected

- Unpacked user-supplied `ColdChain_Perfect_UI_v5.zip` and reviewed backend, simulator, frontend, tests, docs, Windows launcher.
- Tested real FastAPI routes using isolated SQLite databases and FastAPI's `TestClient`.
- Browser-side smoke-tested frontend interactions with mock network responses and visually inspected rendered screens; browser access to local server was blocked by the execution environment, so this is **not** a full production browser/system test.
- Inspected, but did **not** execute, the Windows installer/BAT in Windows.

## Defects / presentation gaps addressed

1. Added one-click, **explicitly synthetic** historic heat-exposure scenes for Safe (100% left), At Risk (15% left) and Discard (0% left). Every scene writes an audit entry, without fabricating readings or touching real vaccine stock.
2. Added a simulated rising-temperature scene to generate a model forecast warning and eligible relocation candidates quickly enough for a three-minute video.
3. Seeded a small explicitly simulated baseline history on empty demo databases so temperature charts and indicative compressor health scores are available shortly after launch. Samples use the same signed telemetry ingestion as the rest of the simulator.
4. Fixed public QR generation to respect the current local server port instead of assuming `localhost:8000`. If `PUBLIC_BASE_URL` is configured, that explicit override is still honored.
5. Inventory now explicitly shows **weighted minutes used / 60** alongside remaining percentage, which helps the judges understand the budget.
6. Added a dedicated three-minute scene panel in Simulation Lab, presenter guide and release notes.

## Verified behaviour

- Existing backend test module: **13/13 passed** (authentication/RBAC, security, heat dose, integrity, relocation etc.).
- Added Round 1 backend tests: **4/4 passed** in isolated test runs. They cover demo-only scene permissions, 51/60 and 60/60 exposure arithmetic, predicted breach with suitable destination, pharmacist-only confirmation, and QR port selection.
- Direct API run: Admin, Pharmacist and Inspector login success; Safe/At Risk/Discard states correct; risk scenario generated warning; a Pharmacist confirmed a sample relocation; integrity check valid.
- JS syntax check: `node --check web/app.js` passes.
- Browser-side mock interaction test: no page errors; login screen, dashboard, inventory and simulation scene controls render and respond.

## Known limitations (do not hide from judges)

- ESP32 firmware is provided but hardware flashing, physical sensors, OLED, relay, buzzer, power-failure and persistent offline buffering were **not** verified.
- External SMS/Telegram/email delivery is not part of the ready-to-run local simulation.
- Trained forecasting model is evaluated on **synthetic** trajectories, not real clinical fridge measurements.
- The scene presets stage illustrative historical dose values; they are not sensor-derived historical observations.
- Pharmacist confirmation updates software inventory assignment; staff would need to physically move and verify stock in a real facility.
- Local QR links point to the PC's localhost port; scanning from another device requires networking and a configured accessible base URL.
- The one-click Windows BAT is inspected but not executed in the tool's Linux environment; users should perform a real Windows smoke test before submission.
- The organizers' email requests at least 3 questions and a <=3 minute video. Whether software-only simulation is acceptable for Round 1 remains unconfirmed by the provided instructions.

## Recommended final on-device validation

1. Extract final ZIP to a new folder; click `START_DEMO_WINDOWS.bat` and verify first-run Python/dependency setup.
2. Check login using all three roles; Inspector must not access simulation controls or write actions.
3. Q2: stage At Risk and Discard, read weighted minutes in Inventory and check public QR.
4. Q5: stage rising risk, show forecast & health score, then confirm relocation as Pharmacist.
5. Check Security > Verify Integrity; export CSV; check phone-sized browser layout.
6. Record the complete 3-minute screen demonstration and verify viewing access from a private browser session.
