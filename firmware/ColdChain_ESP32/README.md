# ESP32 ColdChain Node — Two-Board Deployment

Flash the same sketch on TWO ESP32 DevKit boards, using distinct `secrets.h` files:
- board 1: `DEVICE_ID="FRIDGE_A"`, `DEVICE_SECRET` matches `DEVICE_FRIDGE_A_SECRET`
- board 2: `DEVICE_ID="FRIDGE_B"`, `DEVICE_SECRET` matches `DEVICE_FRIDGE_B_SECRET`

**V8 pin profile:** all GPIOs, door/power switch polarity, relay signal polarity and OLED I2C address are in `hardware_pins.h`. The hardware wizard copies it into the private folders for A and B. If your actual component wiring differs, edit each board's own `hardware_pins.h`, then compile/upload again. Do not apply a classic ESP32 pin assignment unchanged to C3/S3.

## Required Arduino libraries
Install `ESP32 by Espressif Systems`, `ArduinoJson` v7, `PubSubClient`, `DallasTemperature`, `OneWire`, `Adafruit SSD1306`, and `Adafruit GFX` in Arduino IDE 2.x.

## Wiring (3.3V-safe logic / isolated drivers only)
| Part | ESP32 pin | Notes |
|---|---:|---|
| DS18B20 temperature (DATA) | GPIO4 | 4.7kΩ pullup from DATA to 3.3V |
| Reed door switch | GPIO18 | other terminal GND; LOW means open in this example; invert if hardware differs |
| Isolated compressor relay signal | GPIO19 | Active LOW is default; separate rated contactor/industrial safety interlocks required |
| Red LED | GPIO25 | current-limit resistor |
| Green LED | GPIO26 | current-limit resistor |
| Active buzzer drive | GPIO27 | use transistor driver if required |
| Power failure DEMO button | GPIO32 | wire to GND, internal pullup |
| Battery indication (ADC) | GPIO34 | calibrated divider required; do NOT feed battery voltage directly |
| OLED SSD1306 I2C | SDA21 / SCL22 | 0x3C, 128x64 |

**Safety:** Never directly control mains-voltage vaccine refrigeration with a breadboard relay. Physical compressor protection, anti-short-cycle rating, thermostat override, fail-safe thermal alarms, NIST-traceable calibration, validated refrigeration, and professional electrical inspection are needed for real medicines. Do not use this sample for clinical storage as-is.

## Operation
- Samples every **5 seconds** and immediately on door state changes.
- Local hysteresis: ON at **≥7°C**, OFF at **≤3°C**, with **≥60 seconds** since switch-off before any re-enable.
- OLED displays temperature and `SAFE`, `WARNING`, or `BREACH`.
- Local buzzer activates after the door has been continuously open **more than 60 seconds** or for sensor/queue fault.
- Signed telemetry is delivered to MQTT topic `coldchain/telemetry/FRIDGE_A` or `FRIDGE_B`.
- Client subscribes to app-level authenticated acknowledgement topic `coldchain/ack/<id>`; a flash-buffered sample is removed only after verified ACK. Ordered sequence numbers and server de-duplication support exactly-once DB insertion over at-least-once retry.
- Default flash queue supports ≥900 records, more than **30 minutes at 5-second intervals**.
- Retained signed server command `coldchain/cmd/<id>` maintains red discard latch until admin reset. Local NVS latch survives reboot.
- Timestamps are epoch UTC; synchronize NTP before a Wi-Fi outage. For accurate timestamps across complete power loss/offline boot, add a battery-backed RTC (e.g., DS3231) and integrate it before clinical deployment.

## Engineering limitations
- LittleFS append-and-compact is readable reference code. At 5-second intervals over months, write amplification and flash endurance warrant a circular buffer, industrial FRAM, or SD wear-leveling.
- For production use TLS client connectivity + Mosquitto per-device ACLs + broker credentials; the included broker config is explicitly local-demo-only.
- Battery ADC is an illustrative mapping and requires physical calibration; 100% under mains is merely the demo convention.
- Compressor must use certified independent thermal/freeze protection. The logic never replaces a validated medical refrigerator controller.
- Offline queue is durable in LittleFS; delivery assumes MQTT connectivity returns and current clock is valid.
