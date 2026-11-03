# Hackathon kit guide (on-site hardware and Windows tools)

> Moved from the old README. The project overview now lives in the root `README.md`.

# COLDCHAIN — FASTROBOX ONSITE READY PACKAGE V8

**This is the complete extracted-project package** containing the original Round-1 web/AI simulator, the real-ESP32 hardware backend, two board-profile generator, firmware, a Windows control-menu, and preparation/diagnostic tools. The official question tasks are covered in software/reference code, but real ESP32 compatibility is **unverified until the organizer kit is available**. The model was evaluated on synthetic data; it is not a clinical device.

**START HERE (Windows 10/11):** double-click **`00_START_COLDCHAIN_WINDOWS.bat`**. Read **`00_READ_ME_FIRST_BANGLA.txt`** and **`docs/DO_THIS_BEFORE_HACKATHON.md`**.

Before event, select menu option 1 to initialize Python, 2 for tests, 3 to download ESP32 compiler/libraries and official Mosquitto installer, 4 to create private A/B profiles, 6 to compile for classic ESP32, and P to save a hardware-readiness report. Onsite, select 5 if Wi-Fi changes (no secret rotation), 7 to compile and flash A or B after confirming actual COM port and board model, 8 to start the broker, 9 to start hardware backend, and L to verify live readings. Physical wiring, OLED, power failure, relay, buzzer and offline testing must be performed with the organizer kit.

**Important:** a fresh download does not contain official Arduino/Mosquitto Windows executables or your private credentials. First-time setup must be completed at home with Internet. A board supplied as ESP32-C3/S3, a different temperature probe, or different pinouts will require adaptation. Do not wire mains compressors to the reference circuit.

---

# HARDWARE-READY ONSITE KIT — READ THIS FIRST

**Preparation permission confirmed:** The user reported the event permits bringing previously written software/firmware. This package extends the Round 1 V6 project with an onsite workflow for the two *actual* ESP32 nodes, without claiming any physical test has occurred.

**Two independent launch paths:**

- **Round 1 software simulation:** `START_DEMO_WINDOWS.bat` — uses clearly labeled synthetic sensor data and demo accounts.
- **Hackathon physical prototype:** `PREPARE_HARDWARE_WINDOWS.bat` (once to generate private credentials and two board sketches), then `START_BROKER_WINDOWS.bat`, `CHECK_HARDWARE_WINDOWS.bat`, and `START_HARDWARE_WINDOWS.bat`. Verify both boards with `CHECK_LIVE_TELEMETRY_WINDOWS.bat`. Optional compile: `CHECK_ESP32_COMPILE_WINDOWS.bat` after Arduino CLI + packages are installed.

**Read `ONSITE_START_HERE.txt` and `docs/ONSITE_DAY_GUIDE.md`.** The hardware steps require a trusted LAN, actual kit parts, the Arduino toolchain and locally installed Mosquitto; they are **not** fully automatic or physically verified. Generated `.env`, `firmware/ColdChain_A/secrets.h`, `firmware/ColdChain_B/secrets.h` and `ONSITE_PRIVATE_CREDENTIALS.txt` must stay private. Never use a hobby relay to switch mains/refrigeration power, or claim this prototype is fit for clinical vaccine storage.

**Testing:** the existing 17 Round 1/backend tests plus 3 new offline setup tests passed locally (20/20). Windows BAT execution, firmware compilation and actual two-device MQTT/OLED/relay tests remain **pending** until hardware and a Windows test machine are available.

---

# COLDCHAIN — Vaccine & Medicine Storage Monitor

**FastRoboX Round 1 software-only demo edition:** start with `ROUND1_START_HERE.txt` and `docs/ROUND1_VIDEO_3MIN_GUIDE.md`. The Simulation Lab contains one-click **synthetic** exposure and forecast scenes for a video covering Questions 2, 4, and 5. All figures must be described as simulated, not clinical measurements.

**Round 1 · IoT + security + predictive analytics · 100-point task coverage**

A runnable **two-fridge cold-chain system** with a carefully styled responsive web dashboard, FastAPI backend, SQLite evidence trail, authenticated MQTT ingestion, independently operating ESP32 firmware, inventory/QR workflows, thermal-budget engine, compressor health score, and model-backed 30-minute breach forecasts. A clearly labeled **synthetic twin** allows full software demonstrations without pretending physical boards were operated.

> **Scope and safety:** This is a competition prototype, **not a certified vaccine storage product**. ESP32 boards, actual refrigeration equipment, battery status calibration, internet-delivered alerts, and clinical decisions must be verified independently. A 100/100 grade cannot be promised; see `docs/REQUIREMENTS_MATRIX.md` and `docs/VALIDATION.md` for what is verified vs pending.

## 1. Windows ONE-CLICK START (no manual Python installation)

**Full ready-to-run v3 (2026-10-21):** unzip the contents, double-click `START_DEMO_WINDOWS.bat`. No separate patch or file copying is necessary. If Python 3.11/3.12 is missing, the launcher downloads the official signed user-level installer, creates `.venv`, installs the listed packages, verifies them from a standalone Python file (avoids PowerShell argument-quoting pitfalls), starts the local server, probes `/health`, and opens your browser. First setup requires Internet. Keep the command window open while you use the application. This is a software simulation, not validated clinical equipment.

**Launcher hotfix (21 October 2026):** Fixed a Windows PowerShell 5.1 quoting bug which incorrectly stripped quotation marks from the Python dependency-check command and triggered `SyntaxError: ( was never closed` after dependencies installed. Dependency verification now runs from `VERIFY_DEPENDENCIES.py`. Existing valid `.venv` packages are detected and reused (no repeated download).

1. **Extract the entire ZIP** into a normal writable folder. Do not run `.bat` directly inside a ZIP archive.
2. **Double-click `START_DEMO_WINDOWS.bat`.** Keep the black terminal window open.
3. The launcher automatically **finds Python 3.11/3.12 (64-bit)** or downloads the official digitally signed **Python 3.11.9** installer from `python.org`, installs Python for the current Windows user (no admin rights), creates `.venv`, installs all packages from `requirements.txt`, verifies dependencies and starts the backend.
4. Once the server passes the health check, the BAT **opens your browser automatically** at the local dashboard (usually **http://127.0.0.1:8000**; an alternative port is selected when needed).
5. Sign in as `admin` / `ColdChainDemo_Admin2026!` to explore two virtual fridges, readings, heat budgets, batches, forecasting, QR codes and audit verification. Close the console / press `Ctrl+C` to stop the demo.

**Important:** Internet is required for the **first launch when Python or pip packages need installation**; further launches reuse the local environment and typically need no download. Windows 10/11 (64-bit) is recommended, with sufficient storage and access to `python.org` and PyPI. If Windows security policy blocks downloading/installing programs, the BAT reports the error rather than claiming success. Installation and application output are kept in `logs/Windows_Setup.log` to aid diagnosis. The installer validates the official Python download's Windows Authenticode signature before running it. No admin rights or Docker/Mosquitto/Arduino installation is required for the simulated web demo. **Do not run this demonstration against real medical refrigerators.**

To automatically install dependencies and run the tests without opening the dashboard, double-click **`RUN_TESTS_WINDOWS.bat`**.

### Optional command-line start (if Python is already installed)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe run_demo.py
```

**Local demo accounts:**

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `ColdChainDemo_Admin2026!` |
| Pharmacist | `pharmacist` | `ColdChainDemo_Pharmacist2026!` |
| Inspector | `inspector` | `ColdChainDemo_Inspector2026!` |

These are deliberately public DEMO credentials. **Do not expose this instance to the internet** or put real medical data into it. For any non-demo deployment, disable demo mode and replace all defaults in a private `.env` file.

## 2. Explore the web application

**Overview:** live two-device cards (temperature, door, mains, compressor, battery), interactive temperature trace, 30-minute forecasts, cooling-health indicators, latest events, and relocation suggestions. Refresh every five seconds.

**Inventory:** add batches, view lot number, remaining heat budget, expiration, status, and public QR; move eligible stock between units with server-side validation. Heat exposure is **never reset by moving** the batch.

**Security & audit:** inspect the linked SHA-256 audit trail, verify hash integrity against stored sensor records, and export reading history as CSV. Device telemetry requires a valid HMAC, fresh sending time, nonce, and authorized device ID; identical retransmissions are deduplicated.

**Simulation lab:** Admin/Pharmacist only. Toggle door open, power loss, artificially degraded compressor, Wi-Fi loss/recovery, and thermal load. Lab controls operate only when `DEMO_MODE=1`, never against physical devices.

**Inspector role:** read-only access to operational dashboard, stock list, and verification; cannot add/move/reset products, manage users, or operate simulations. Server rejects forbidden write attempts.

## 3. Ten-minute demonstration

1. Sign in as Admin. Open Overview: **two distinct synthetic ESP32 twins** and their temperature history appear.
2. Open Inventory and show lot/expiry/exposure; click `QR` and open the public page in another tab **without login**.
3. In Simulation lab, hold door open **over 60 seconds**. Observe local-demo event/alert record. Actual Telegram/email delivery requires channel settings below.
4. Toggle main power off for Fridge Alpha. Its telemetry continues reporting `mains_ok=false` and simulated battery level. Re-enable mains.
5. Toggle Wi-Fi off on Alpha; observe its last-update becoming stale. Toggle Wi-Fi back on: queued samples are signed and imported in sequence (the **firmware** queue uses persistent LittleFS; **simulation** queue lives in RAM).
6. Toggle heat spike and degraded compressor on Alpha. Observe temperature, forecast warnings, and relocation suggestions when Beta is below 6.5°C and healthy. As Pharmacist, confirm one recommended move; the server records the action.
7. Visit Security & audit; press **Verify integrity** to validate the SHA-256 chain, then export temperature readings.
8. Run `python -m pytest -q` and show the actual passing tests; open `report/model_metrics.json` and `report/forecast_validation.png`, explicitly declaring all training/test trajectories **synthetic**.

See the timed presenter script in `docs/DEMO_SCRIPT.md`.

## 4. Hardware route (two real ESP32s)

1. Create `firmware/ColdChain_ESP32/secrets.h` from `secrets.example.h`.
2. Build two physical nodes using the wiring checklist in `firmware/ColdChain_ESP32/README.md`.
3. Flash one with `FRIDGE_A` / secret A, and the other with `FRIDGE_B` / secret B, using Arduino IDE 2.x and the listed libraries.
4. Provide a dedicated Mosquitto broker (Docker example included). Point both ESP32 sketches to the broker's LAN IP.
5. Start backend with `MQTT_ENABLED=1`, `DEMO_MODE=0`, and matching secrets. The backend subscribes to `coldchain/telemetry/+` and publishes signed ACKs and discard commands.
6. Test 7°C / 3°C hysteresis, 60-second minimum compressor off-time, door alarm, 30+ minutes network loss, ordered replay, battery sensing, and physical red-latch reset **on hardware**. These steps were not verified by this package creation.

Do **not** connect refrigerator mains or use a non-isolated relay without qualified electrical supervision. For clinical use, enforce certified independent thermostat/freeze protection, calibrated probes, device auth + TLS + broker ACLs, protected power supply, and audited procedures.

## 5. SMS / Telegram / email integration

In private `.env` set `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` **or** configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `ALERT_EMAIL_TO`. When a device door remains open **strictly more than 60 seconds**, the backend attempts a Telegram message or email. Each delivery outcome is stored in `alert_outbox` as `delivered`, `failed`, or `not_configured` — a missing external credential is never reported as success.

## 6. Run tests and retrain

```powershell
python -m pytest -q
python train_model.py
```

Tests include auth roles, signed telemetry, replay refusal, ID/sequence deduplication, modified payload rejection, 2x >12°C exposure, 8°C boundary, At Risk/Discard status, reset restriction, relocation, public QR, log tampering, simulation recovery, and 60-second door alert. Refer to `docs/VALIDATION.md` for results and limitations.

The RandomForest model is trained with seed **20261021** using **220 independently seeded synthetic refrigeration trajectories**, split **by entire trajectory** into 171 train / 49 test trajectories (not random overlapping samples). It predicts the temperature **30 minutes ahead** using eight features. The reproducible metrics are in `report/model_metrics.json`. This is **not performance proven on any actual medical refrigerator**.

## 7. Repository map

```text
coldchain/             FastAPI app, database, security, alerting, exposure engine, predictor, MQTT bridge, demo twin
web/                   Responsive HTML, CSS, and dependency-free JavaScript
firmware/ColdChain_ESP32/
                       Dual-node Arduino firmware + wiring + config template
models/                Pretrained synthetic RandomForest model
train_model.py         Deterministic synthetic dataset creation, training, holdout evaluation
report/                Model data and validation graphics + PDF competition report
assets/                Optional screenshots / supporting evidence
features & tests:      tests/ (pytest suite)
docs/                  Scoring matrix, architecture, deployment, QA, demonstration
Dockerfile, docker-compose.yml, mosquitto.conf
                       Demo-only MQTT broker and API container wiring
```

## 8. Technical rules and safety assumptions

- **Fridge control (node):** compressor ON when `T>=7°C` and minimum-off counter permits, OFF at `T<=3°C`; independent of cloud response.
- **Status:** safe within normal 2–8°C envelope, warning for approaching upper limit, open door, or power off, breach for outside 2–8°C / latch / sensor fault.
- **Budget:** first observed interval above 8°C is weighted 1x; above 12°C is weighted 2x; stops counting after 60 weighted minutes; `<20%` remaining gives At Risk, `0%` is irreversible discard latch unless admin uses the restricted software reset.
- **Missing sensor data:** gaps over 90 seconds are flagged and **not silently filled as safe or assumed heat exposure**. Missing interval clinical stability requires independent assessment.
- **Tamper detection:** chained event hashes also cross-check `readings` table values; production hardening should anchor signed daily head hashes outside the writable database.
- **Relocation:** model/threshold recommendation uses source danger and a current, powered, closed, sufficiently cool destination. It cannot verify physical capacity, compatibility, or handling procedure. A user's confirmation updates the inventory ledger, not the physical batch.
- **Model and compressor health:** predictive output and health index are **advisory**, not validated medical risk metrics.

## 9. Production security checklist

- Set unique 32+ character device secrets and JWT secret, never commit `.env` or `secrets.h`.
- Switch `DEMO_MODE=0`, enable HTTPS reverse proxy and MQTT TLS on a private network.
- Replace demo MQTT `allow_anonymous true` with per-device username/cert and ACLs before any public deployment.
- Restrict public QR to opaque token only; don't include recipient data or patient information.
- Protect databases/backups and use externally anchored audit hashes for adversarial tamper resistance.
- Retest firmware on two actual devices and calibrate probe and battery divider.
- Provide alert service credentials; test real delivery to a subscribed recipient.
- Confirm expiry, stability rules, beyond-use decisions and quarantine with a licensed pharmacist.

**Authoring integrity:** No real-world test evidence, photographed hardware, credentialed email delivery, or clinical model validation is claimed. The deliverable is a runnable, inspectable software implementation plus firmware source ready for hardware integration.

## 10. Easy Windows launch and broker hardening

You can double-click **`START_DEMO_WINDOWS.bat`** even if Python is not installed; it automatically installs a verified user-level runtime and dependencies with internet access, reuses them on subsequent runs, and opens the browser when ready. **`RUN_TESTS_WINDOWS.bat`** also performs automatic setup before running automated tests. Source-controlled launchers contain no user passwords except the deliberately public local-demo sample credential.

For production broker hardening, compare `mosquitto.production.example.conf` and `mosquitto.acl.example`. Provision private TLS certificates, password file, and unique authentication credentials per device; never use the included anonymous local-demo broker on the open internet.

The included pretrained model was generated with **scikit-learn 1.8.0**; that version is pinned in requirements to avoid loading a pickle with incompatible library versions. Do not load any untrusted `.joblib` model file.
