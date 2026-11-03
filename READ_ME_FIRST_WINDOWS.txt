COLDCHAIN - COMPLETE EXTRACT & RUN EDITION (V3)
================================================

NO PATCHES. NO FILE COPYING. THIS IS THE FULL PROJECT.

1. Right-click the downloaded ZIP and choose Extract All.
2. Inside the extracted folder, double-click START_DEMO_WINDOWS.bat.
3. Allow time for the first run to install Python 3.11 (if needed) and dependencies.
   Internet access is required the first time if Python/packages are not installed.
4. Wait for the green COLDCHAIN IS READY! message.
5. The browser should open automatically. If not: http://127.0.0.1:8000
   (If port 8000 is busy, the displayed URL might be 8001, 8002, etc.)
6. Demo logins (all are pre-created and ready):
   Admin      -> admin / ColdChainDemo_Admin2026!
   Pharmacist -> pharmacist / ColdChainDemo_Pharmacist2026!
   Inspector  -> inspector / ColdChainDemo_Inspector2026!

To close the demo, close the black command window.
To restart it, double-click START_DEMO_WINDOWS.bat again.
To run automatic tests, double-click RUN_TESTS_WINDOWS.bat.
If anything fails, send logs\Windows_Setup.log and a screenshot.

BOTH previous launcher issues have been addressed:
* No hard-stop if Python 3.11 is missing (auto-install Python 3.11 user-only).
* No inline Python -c import/version commands (PowerShell quote-stripping bug).

This archive includes application backend, frontend, simulator, ESP32 source,
model, documentation, six-page PDF report, and QA report.
The software mode runs without Docker, MQTT broker or physical devices.
Real ESP32 validation and delivery of real-world alerts need separate setup.
This is NOT validated medical monitoring equipment.
