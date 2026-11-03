COLDCHAIN V8 - COMPLETE PRE-HACKATHON PACKAGE
================================================

IMPORTANT: The firmware is intended for a classic ESP32 Dev Module + DS18B20.
If the organizers give a different ESP32 or sensor, pin mappings and firmware
must be adapted before upload. REAL hardware function cannot be tested in advance.

ONE MENU FOR ALL TASKS: 00_START_COLDCHAIN_WINDOWS.bat

BEFORE EVENT, WITH INTERNET:
1) Select 1: Launch demo, install Python libraries. Test login.
2) Select 2: Run backend automated tests.
3) Select 3: Download Arduino CLI + ESP32 core + libraries and official
   Mosquitto Windows installer. Install Mosquitto on your PC.
4) Select 4: Generate Fridge A/B profiles for your PERSONAL 2.4GHz hotspot,
   using the Windows laptop's LAN IPv4.
5) Select 6: Compile for classic ESP32 Dev Module (different board needs
   different FQBN and potentially different pins).
6) Select P: Check pre-event readiness, save report.

ON HACKATHON DAY:
1) Identify real board/sensor/relay/OLED model and pinouts.
2) If hotspot/IP changes, select 5. Do NOT rerun profile generation.
3) Select 7 to upload one board at a time; confirm COM port and board model.
4) Select 8 to run broker, 9 to start real hardware backend.
5) Select L to verify *real* telemetry from BOTH boards.
6) Test LED, sensor accuracy, switches, offline buffering, notifications.

PUBLIC SIMULATOR ACCOUNTS:
  admin       / ColdChainDemo_Admin2026!
  pharmacist  / ColdChainDemo_Pharmacist2026!
  inspector   / ColdChainDemo_Inspector2026!

REAL HARDWARE ACCOUNTS:
  admin, pharmacist, inspector with random passwords in
  ONSITE_PRIVATE_CREDENTIALS.txt (created when you select menu 4).

Do not connect mains power to hobby relay. Use low-voltage demonstrator only.
Take USB data cables and offline copies of Windows installers.
See docs\DO_THIS_BEFORE_HACKATHON.md for complete detailed workflow.
