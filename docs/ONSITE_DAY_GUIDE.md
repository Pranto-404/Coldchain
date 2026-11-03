> **V8 event-day shortcuts:** Start at `00_START_COLDCHAIN_WINDOWS.bat` and follow `docs/DO_THIS_BEFORE_HACKATHON.md`. For *network changes only*, run `UPDATE_NETWORK_WINDOWS.bat` and reflash both boards; this preserves HMAC device secrets and backend account passwords. The pinout/polarity/OLED address settings are now isolated in each board's `hardware_pins.h` file. The USB uploader prompts for A/B, COM port and board FQBN and requires explicit confirmation. `PREPARE_LAPTOP_WINDOWS.bat` retrieves the official Arduino CLI, ESP32 core/libraries, and saves the official Mosquitto installer for pre-event installation. The generated `report/MY_PC_PREFLIGHT.txt` is a readiness check, not physical hardware evidence.

# ColdChain — Hardware Integration Day Guide (ESP32 × 2)

**Status:** advance preparation only. Firmware compilation, physical wiring, communications and real-alert delivery are **not** verified until you test with the actual organizer-supplied kit. No use with real vaccine storage or live mains compressor circuitry.

## Ground rules before the event

- You confirmed the organizer permits bringing prewritten software/code. Retain this confirmation and still follow any device/Internet restrictions stated onsite.
- Organizer email names **13–14 November 2026**, whereas your later message names 14–15 November. Confirm the event date and the IoT kit distribution slot.
- The question paper describes **two ESP32 nodes**. Organizer did not yet provide exact ESP32 variant, sensor/relay models, wiring, allowed network or electrical safety rules; verify this once you receive the actual kit.
- The Round 1 video remains its own submission (maximum 3 minutes, at least 3 questions, deadline 5 November 2026). Do not confuse its simulation evidence with real hardware results.

## BEFORE THE EVENT — prepare laptop software

1. Extract the complete ZIP into a regular writable local folder on your Windows laptop, e.g. `D:\ColdChain_Onsite`.
2. Run `START_DEMO_WINDOWS.bat` once at home with Internet to install Python dependencies, then close it. `RUN_TESTS_WINDOWS.bat` runs the software tests.
3. Install **Arduino IDE 2.x** and the **Espressif ESP32** board package; library manager libraries: `OneWire`, `DallasTemperature`, `ArduinoJson` v7, `PubSubClient`, `Adafruit GFX Library`, `Adafruit SSD1306` (and its dependencies). Verify both sketches compile once profiles exist. For Arduino CLI users, `CHECK_ESP32_COMPILE_WINDOWS.bat` attempts compilation for the *generic ESP32 Dev Module* target only. For S3/C3 boards select the actual model and amend pin assignments.
4. Install **Eclipse Mosquitto** locally on Windows, from its official publisher. `START_BROKER_WINDOWS.bat` finds `mosquitto.exe` if installed in PATH or typical `Program Files\mosquitto`. No Docker is required for this route.
5. Optional: download drivers for CP2102/CP210x and CH340 USB-serial chips from their manufacturers. Bring **data-capable USB cables**, a working charger/power bank and an offline copy of installers and your ZIP.
6. Keep demo video/software and onsite mode separate. Never copy old `coldchain.db` into the real-ESP32 setup.

## ONE-TIME LOCAL PRIVATE CONFIGURATION

Use the actual hotspot/router for the event, or an equivalent private practice hotspot:

1. Connect the **Windows laptop and both ESP32 boards to the same 2.4 GHz Wi‑Fi network**. ESP32 classic models generally require 2.4 GHz; many phone hotspots default to 5 GHz. Some managed guest networks isolate clients and will prevent connectivity.
2. In Windows Command Prompt run `ipconfig`. Find the **IPv4 address of the laptop's Wi‑Fi/hotspot adapter** (for example `192.168.137.1`). Do **not** use `127.0.0.1` as the ESP32 broker address.
3. Double-click `PREPARE_HARDWARE_WINDOWS.bat` and enter: Wi-Fi SSID, its password, and **laptop IPv4**.
4. Wizard generates **private** `.env`, a file `ONSITE_PRIVATE_CREDENTIALS.txt` containing randomized Admin/Pharmacist/Inspector passwords, and two separate Arduino sketches:

   ```text
   firmware/ColdChain_A/ColdChain_A.ino
   firmware/ColdChain_A/secrets.h        (FRIDGE_A-specific device key)
   firmware/ColdChain_B/ColdChain_B.ino
   firmware/ColdChain_B/secrets.h        (FRIDGE_B-specific device key)
   ```

5. The backend and firmware passwords are generated on your PC; **never upload `.env`, `secrets.h`, or the credentials file to GitHub or a public form.** The original public ZIP does **not** contain those secrets. The wizard does not overwrite them without `--force`.
6. If laptop IP/SSID/hotspot password changes, regenerate configuration and **reflash both boards** because the C++ headers are compiled into the firmware. Regenerating `--force` rotates JWT/device secrets, making previously flashed devices unable to authenticate. Back up first.

## ONSITE 0–90 MINUTES — connect hardware, not mains

| Stage | Action | Proof to save |
| --- | --- | --- |
| A. Inspect (5–10 min) | Identify actual ESP32 variant, OLED address, DS18B20 or substituted sensor, switch polarity, pin-safe relay module, USB serial chip | Kit inventory + annotated pinout |
| B. Board A (15–20 min) | Open `firmware/ColdChain_A/ColdChain_A.ino`, select exact board/COM port, Compile then Upload. Check serial at 115200 and OLED temperature. | Compile log + serial/OLED photo |
| C. Board B (10–15 min) | Repeat with `firmware/ColdChain_B/ColdChain_B.ino`. **Never flash A's sketch to B**, or their IDs/keys collide. | Second device photo/log |
| D. MQTT (5–10 min) | Start `START_BROKER_WINDOWS.bat`. Use a trusted **isolated hotspot**, approve inbound Windows firewall for **private networks only** if permitted. | Broker console showing two connections |
| E. Backend (5–10 min) | Run `CHECK_HARDWARE_WINDOWS.bat`, then `START_HARDWARE_WINDOWS.bat`. This disables simulator and uses a separate `coldchain_onsite.db`. | `/health` with `demo:false` |
| F. Live telemetry (5–10 min) | Run `CHECK_LIVE_TELEMETRY_WINDOWS.bat`, passing the actual backend port as an argument if it isn't 8000. Both must show fresh `simulated=False` readings. | Screenshot of both units reporting |
| G. Safety tests (time permitting) | Verify threshold logic with SAFE test setup (no medicines or mains). Exercise switches, disconnected Wi-Fi, signed/replayed payloads, alarms. | Timestamped screenshots, logs, measurement notes |

**Note:** You may need several hours on unfamiliar hardware or in restricted Wi‑Fi environments. These durations are **targets, not guaranteed completion times**.

## Default wiring reference (only if exact components match)

| Device / interface | Default pin | Important note |
| --- | --- | --- |
| DS18B20 data | GPIO4 | DATA → 3.3V with 4.7 kΩ pullup |
| Door reed switch | GPIO18 | INPUT_PULLUP; LOW = open in firmware (check actual wiring) |
| Isolated low-voltage relay indicator | GPIO19 | Default active-LOW; **never wire fridge compressor/mains to breadboard** |
| Red LED | GPIO25 | Current-limiting resistor required |
| Green LED | GPIO26 | Current-limiting resistor required |
| Buzzer | GPIO27 | Active buzzer; driver/transistor if current requires |
| Power-fail demo button | GPIO32 | Connect to ground through button (pullup active) |
| Battery ADC | GPIO34 | Use voltage divider, do not apply battery voltage directly; battery mapping must be calibrated |
| SSD1306 128×64 OLED | GPIO21 SDA, GPIO22 SCL | I²C 0x3C by default; actual board may use 0x3D |

### Fallback when organizer provides different hardware

- **ESP32-S3/C3 or other MCU:** GPIO list is not automatically portable. Check board pinout and replace constants in each `.ino`, select exact board type before compiling.
- **DHT11/DHT22 or another temperature sensor:** reference sketch supports DS18B20 **only**. Requires explicit code adaptation and accuracy check. Do not present simulated readings as measured output.
- **No OLED / relay / battery input in kit:** note partial fulfillment and test remaining features honestly. Ask if substitution is allowed.
- **Internet blocked:** local MQTT and dashboard work with a trusted local router/hotspot (once dependencies are installed), but Wi-Fi NTP and Telegram/email may not. Clock sync must be available for signed-message timestamps; confirm device time before disconnecting Wi‑Fi.

## End-to-end demonstration and evidence

1. Inspect OLED temperature against a second thermometric reference if supplied; record **observed calibration uncertainty**.
2. Show new hardware reading every approximately 5 seconds; open/close the magnetic switch and verify immediate extra publish.
3. With low-voltage load only, test compressor control at **≥7°C ON**, **≤3°C OFF**, with minimum **60s OFF time**. Record actual switching times; sensor accuracy and power-failure protections need real validation.
4. Verify **above 8°C heat-exposure accumulation**, double weight **above 12°C**, and Safe → At Risk → Discard states with audit evidence. Offline gaps are **not silently treated as safe**.
5. Keep the door open **over 60 seconds**; verify buzzer and delivered Telegram/email message if credentials configured. Missing credentials should be reported as not configured, never successful delivery.
6. Disconnect Wi-Fi for **at least 30 minutes**, verify persistent backlog and ordered, deduplicated replay; physically power cycling during a buffering test needs independent RTC for accurate offline timestamps. Save before/after sequence IDs and DB count.
7. Demonstrate HMAC invalid signatures and replay rejection, audit Verify Integrity and role-restricted actions. Never reveal private keys in recordings.
8. Confirm AI forecasts are trained on **synthetic historical trajectories**; no real refrigerator model validation has yet been performed.

## Failure checklist

| Symptom | First checks |
| --- | --- |
| `mosquitto.exe not found` | Install Mosquitto from publisher; confirm path and start broker BAT before hardware BAT |
| MQTT broker bind failure / port 1883 busy | Windows service/another Mosquitto already listening: stop duplicate and use existing trusted broker; don't start two listeners |
| Hardware preflight failed | Check `.env`, missing private headers, mismatch in device keys; check Mosquitto is actually running |
| Device has Wi‑Fi but no MQTT | PC IPv4 wrong, guest/client isolation, Windows Firewall inbound TCP 1883, wrong 2.4GHz SSID, broker not listening |
| Only one fridge visible | Board B may have been flashed with A ID or key; check private header for board B and reflash |
| `no fresh telemetry` after reset | NTP sync/invalid clock, signature mismatch, different broker IP, payload JSON too long; inspect Serial Monitor and backend audit |
| OLED blank | Check SDA/SCL, 3.3V, I²C address 0x3C/0x3D, installed OLED libraries |
| Bad/unchanging battery percentage | ADC calibration pending; current mapping is illustrative, not metrology |
| QR code opens localhost on a phone | Backend binds to 127.0.0.1 by default; use QR on same PC. **Only on trusted LAN** consider `BIND_HOST=0.0.0.0` and `PUBLIC_BASE_URL=http://<laptop-ip>:<port>` after checking access permissions/firewall |
| Door alert says not configured | Configure Telegram Bot + Chat ID or authorized SMTP credentials; check actual receipt, not only event existence |

## Last-minute checklist

- Two uniquely named `.ino` sketches compile for **actual board hardware**, not only default ESP32 Dev Module.
- Verified USB ports/cables and ability to reflash offline.
- Mosquitto installer and Arduino libraries cached locally.
- `.env` / secrets generated on private PC; never submitted publicly.
- `START_DEMO_WINDOWS.bat` still serves Round-1 *synthetic* presentation mode.
- `START_HARDWARE_WINDOWS.bat` uses **live** MQTT; it fails early if broker isn't running.
- Keep read-only backups of ZIP, README, current code, test outputs and demo video separately.
- Clearly label which evidence came from simulator vs physical hardware.
