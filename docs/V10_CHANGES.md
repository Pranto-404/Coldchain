# ColdChain V10 — audit fixes and upgrades

V10 builds on V9. Same start-up (`START_DEMO_WINDOWS.bat` or `python run_demo.py`), same deploy kit (Render backend + Vercel frontend).

## Bugs found and fixed

| # | Bug (V9) | Impact | Fix (V10) |
|---|----------|--------|-----------|
| 1 | Sidebar stretched to full page height with `space-between`, pushing navigation ~900 px down once data loaded | Judges could not see the menu | Sticky full-height sidebar |
| 2 | Compressor health compared simulator cooling (~2.9 °C/min) to a fixed 0.18 °C/min reference, so the score was always 100 | "Degraded compressor" demo never showed weakening (Task 5) | Health now uses complete cooling runs vs the fridge's best run / reference; weak compressor scores ~28–34 |
| 3 | Simulator idle warming (0.78 °C/min) was outside the model's training envelope | AI forecast raised false breach warnings during normal thermostat cycling | Physics retuned: 0 false warnings in 2 h of normal cycling; power cut flagged 32 min before the breach |
| 4 | Login lockout keyed only by client IP; behind Render/Vercel every user shares the proxy IP | 10 wrong passwords from anyone locked everyone out for 10 min | Throttle keyed by `X-Forwarded-For` client + username |
| 5 | Recent events feed was flooded by a `reading` row every 5 s per fridge | Activity panel useless | Feed excludes raw readings (still in audit + chain) |
| 6 | Door alerts (`alert_outbox`) and rejected-packet log returned by the API but never shown | Task 3/4 evidence invisible in the UI | Notification center, critical banner, rejected-messages table |
| 7 | Below 2 °C shown only as "Warning" in the UI while firmware OLED says BREACH | Inconsistent Safe/Warning/Breach | UI status mirrors firmware logic exactly |
| 8 | Batch move allowed into a stale/offline or <2 °C fridge | Unsafe relocation | Destination must be online (≤60 s), 2–8 °C, mains, door closed |
| 9 | Static files cached 60 s | Old JS after redeploy | `no-cache` + ETag revalidation, versioned asset URLs |
| 10 | Lists re-rendered every 5 s under the mouse | Clicks on "Move"/toggles could be lost | Live lists pause updates while hovered/focused |
| 11 | Mobile: horizontal overflow (page 766 px wide on a 375 px phone) | Broken phone layout | Fixed grid/flex min-width; two-row mobile nav |
| 12 | Firmware rewrote the whole queue file on every ACK (O(n²) flash writes) and re-read it every 800 ms for the OLED count | 30-min backlog synced slowly, flash wear | Read offset + cached count; occasional compaction |
| 13 | Firmware power-fail input was level-only (button had to be held) and a power change waited for the next 5 s tick | Awkward demo, late report | Debounced toggle button (`POWER_BUTTON_TOGGLES`), immediate sample on power change |
| 14 | Print-QR popup used inline `onload` (blocked by CSP) | Label never printed | Print triggered from the app |

## New features

- **Digital-twin fridge cards:** OLED mock-up with the same text as the ESP32, red/green LEDs, buzzer, animated compressor fan and door, battery bar, offline-buffer counter.
- **Interactive chart:** 2–8 °C band, door-open shading, AI +30 min forecast drawn as a dashed projection, hover tooltip, 10 min / 30 min / 2 h range.
- **Notification center + critical banner:** breach, cold, door > 60 s, power, forecast, weak compressor, at-risk/discard/expired batches; optional sound alert.
- **One-click role login**, keyboard shortcuts (`1`–`6`, `/`, `R`), deep links (`#inventory`, `#ai` …).
- **Inventory:** search, status/fridge filters with counts, sortable columns, batch details + QR + printable label, edit, dispose with reason (audited), guarded admin latch reset.
- **AI insights page:** now → predicted, trend, model method, compressor health ring with latest-vs-baseline rate bars, grouped relocation advice with **Confirm all**, and the full **model report** (dataset, features with importance, MAE/RMSE/precision/recall/F1, confusion matrix, validation plot, limitations).
- **Security page:** live hash-chain visual; **Tamper a reading (demo)** → Verify shows the exact broken record → Undo; **attack buttons** (forged signature, replay, stale, unknown device) pushed through the real ingest path and logged.
- **Users page (Admin):** list, create, change role, enable/disable (server-enforced, audited) and a permission matrix.
- **Simulation lab:** one-click scenarios per task (door, power cut, Wi-Fi outage, weak compressor, rising risk, exposure budget), live node state (compressor, 60 s min-off countdown, battery, buffered count), reset to normal.
- **Public QR page:** phone-first verdict card ("Safe to use" / "At risk" / "Do not use" / "Expired"), heat-budget bar, expiry countdown, storage location, auto-refresh.

## Verification

- `pytest`: 36 passed (26 original + 10 new in `tests/test_v10_features.py`).
- Offline model check on the new simulator physics: normal cycling 0/230 false warnings; power cut warned at cut, breach 32 min later; weak compressor health 34.
- Browser walkthrough as Admin, Pharmacist and Inspector at desktop and 375 px phone width (details in the hand-off summary).
- **Not verified:** firmware was not compiled (Arduino CLI not installed on the test PC) and no physical ESP32 test was possible. Run `CHECK_ESP32_COMPILE_WINDOWS.bat` before the event.

## Suggested 3-minute demo path

1. Sign in as **Pharmacist** (one click). Overview: two live twins, all safe.
2. Lab → **Cut power** → bell + battery card; Lab → **Weaken compressor** → health drops within about a minute.
3. Lab → **Stage rising risk** → Overview chart shows the AI projection above 8 °C → **Confirm all** relocation.
4. Inventory → **QR** → open the public page on a phone.
5. Sign in as **Admin** → Security → **Replay attack** (blocked) → **Tamper a reading** → **Verify integrity** (fails at the exact record) → **Undo**.
6. AI insights → scroll to the model report (dataset, features, results).
