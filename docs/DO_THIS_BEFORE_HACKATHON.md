# COLDCHAIN V8 — PRE-HACKATHON CHECKLIST (Windows 10/11, 64 bit)

Use only on a trusted private LAN/hotspot. This is an educational demonstration, not a medical device. Do NOT wire ESP32 hobby relays directly to refrigerator mains/compressors.

## At home with working Internet (DO THESE NOW)

1. Extract the whole ZIP to a short writable directory such as `D:\ColdChain_V8`. Keep a second offline ZIP backup on a USB stick.
2. Double-click `00_START_COLDCHAIN_WINDOWS.bat`, choose **1**. The Python virtual environment and software dependencies will be prepared. Wait for dashboard and test Admin login. Close dashboard terminal afterwards.
3. Choose **2** to run Python tests, then **3** to download official Arduino CLI and install the Espressif board compiler/libraries. This *requires a substantial one-time download*. If Mosquitto is absent, the official Mosquitto installer is saved and you can choose to launch it before the event. After install check `START_BROKER_WINDOWS.bat`.
4. Decide on a personal **2.4 GHz Wi-Fi hotspot** that connects both boards and laptop. Know the **laptop's LAN IPv4** (Windows `ipconfig`). Choose **4** and enter hotspot SSID, password, laptop IPv4. It produces distinct `firmware\ColdChain_A` and `firmware\ColdChain_B` sketches and unique random device keys. Save `ONSITE_PRIVATE_CREDENTIALS.txt` safely on your laptop only.
5. Choose **6** to compile both sketches for *classic ESP32 Dev Module*. Compilation is only meaningful for that board type. Ask the organizers which exact model they will provide. For S3/C3/etc. adjust pin mapping and use the exact board FQBN.
6. Optional: create a Telegram bot with BotFather and get an authorized chat ID. Choose **T** to store details privately and send a test notification.
7. Choose **P** to create `report\MY_PC_PREFLIGHT.txt`. Anything listed as **PENDING** must be addressed or verified onsite. Do a dry run with the broker (option **8**) and MQTT local ping (option **M**).
8. Copy your current source, private config and offline installers to a *private* backup location. Never share `.env`, `ONSITE_PRIVATE_CREDENTIALS.txt` or firmware `secrets.h` with other teams.

## At hackathon, AFTER the organizers give you hardware

1. **First 5 minutes:** identify board model (classic ESP32 / S3 / C3), temperature sensor, OLED model/address, relay module polarity, wire voltage, USB-to-serial chip, power pins, and available 2.4 GHz network. Compare with `firmware/ColdChain_ESP32/README.md`.
2. If hotspot name, password or laptop IPv4 changed, choose **5**. It updates only those values; **device secrets and usernames remain unchanged**. Firmware must be **recompiled and reflashed** after this.
3. Wire low-voltage parts (temperature, switch, OLED, LEDs) safely. If there is any doubt, disconnect power and verify against manufacturer's pinout. *Never connect refrigerator mains to this prototype.*
4. Choose **7**, select **Fridge A**, matching **COM port**, and actual **board FQBN**. Read confirmation before upload. Verify the device at 115200 baud / OLED. Repeat option 7 for **Fridge B**. Do not flash the A sketch onto B.
5. On your private network start MQTT broker with option **8** and **KEEP THAT WINDOW OPEN**. If Windows Firewall blocks port 1883, approve access only on Private networks to LocalSubnet. Do NOT forward/expose port 1883 to the public Internet. Venue/public Wi-Fi may block local peer connections.
6. In a separate CMD window choose **M** to test broker locally, then choose **9** to start the **real hardware backend**, which disables simulation. Login credentials are in your private `ONSITE_PRIVATE_CREDENTIALS.txt` file. Keep broker and backend windows open.
7. In a third CMD window choose **L** and confirm both `FRIDGE_A` and `FRIDGE_B` have real fresh telemetry. This check cannot validate real temperature calibration or safe relay wiring.
8. Test: 5s MQTT; door changes; 60s door alert and actual Telegram receipt if configured; 7°C/3°C relay hysteresis and 60s off-time using a **low-voltage indicator**; 30-minute offline storage + in-order replay; heat-exposure; physical LED latch; three role permissions; integrity verification. Save evidence and times.
9. For the presentation, distinguish **synthetic Round 1 data** from **actual physical ESP32 observations**.

## If something goes wrong

| Problem | What to check first |
|---|---|
| Firmware fails to compile | Correct ESP32 board model, Arduino core, exact library versions, GPIO compatibility, compiler error output |
| Serial port missing | Data-capable USB cable, power, CP210x/CH340 USB driver, different USB port, Arduino CLI `board list` |
| ESP32 cannot join Wi-Fi | 2.4GHz SSID, hotspot password, client isolation, hotspot max-device setting |
| MQTT connection fails | Correct laptop LAN IPv4, broker running, Windows firewall Private profile/TCP 1883, hotspot peer isolation |
| No live readings despite MQTT | Clock NTP sync after boot, wrong HMAC secret, invalid data fields, broker topic, ArduinoJson v7 |
| Wi-Fi changes | Use menu **5**, then recompile and reflash both boards (don't rotate private keys) |
| Wrong Admin password | Open `ONSITE_PRIVATE_CREDENTIALS.txt`; do not use public simulator passwords in live mode |
| Door alert doesn't arrive | Telegram bot token, correct chat ID, Internet access, 60+ seconds continuous open-door state |
| Broker executable not found | Install saved official Mosquitto installer; reboot/confirm Program Files path if needed |
| No hardware supplied yet | Use software simulator with option 1; do not claim real sensor testing |

## Known limitations (read before promising results)

- The default firmware profile targets **classic ESP32 Dev Module** with **DS18B20**, SSD1306 I²C OLED, low-voltage active-LOW relay, and listed GPIOs. Other supplied components require changes. Firmware has **not been compiled and flashed to the actual event kit**.
- Firmware uses NTP for timestamps. Offline reboot before clock sync cannot create valid timestamped records; a battery-backed RTC would be needed for that case. `queue.jsonl` LittleFS storage has endurance/recovery limits.
- The battery ADC percentage uses an **illustrative** mapping, not a calibrated fuel gauge. No physical battery measurement has been verified.
- Built-in forecast uses a model validated on **synthetic trajectories**; it is not clinically validated on fridge hardware.
- The included broker configuration is anonymous and plaintext for use on an isolated personal hotspot only. HMAC verifies application telemetry but does not encrypt MQTT. **Do not use the broker on open/shared event Wi-Fi** or real medical operations.
- A port-open check, software tests and Arduino compilation are not equivalent to successful end-to-end physical tests.

## Official downloads for your laptop (use at home)

- Arduino CLI: https://docs.arduino.cc/arduino-cli/installation
- ESP32 board support package: https://github.com/espressif/arduino-esp32
- Eclipse Mosquitto: https://mosquitto.org/download/
- CP210x USB-UART drivers (when your board uses that chip): https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers

For event-day exact setup, consult `docs/ONSITE_DAY_GUIDE.md` and `firmware/ColdChain_ESP32/README.md`.
