# Two-Fridge Hardware Bill of Materials (No purchase/physical inspection claimed)

| Item | Qty | Reason |
|---|---:|---|
| ESP32 DevKit 3.3V | 2 | One per fridge; Wi-Fi/MQTT and local control |
| DS18B20 probes, preferably calibrated sealed probes | 2 | Refrigerator temperature |
| 4.7kΩ pull-up resistors | 2 | OneWire data pin |
| Reed magnetic door switches | 2 | Door opening and 60-second alarm |
| 0.96-inch SSD1306 OLED 128×64 I²C | 2 | Status/temp display |
| LED red + green + proper resistors | 4 | Alarm latch + safe operation |
| Buzzer with appropriate driver | 2 | Local door/sensor alarm |
| External optoisolated compressor control + **certified contactor** | 2 | Never connect high voltage directly to ESP32 |
| Power-failure button + wiring | 2 | Test mode power-loss simulation |
| Battery/power monitor, protected 3.3V ADC divider | 2 | Power status and calibrated battery percentage |
| Suitable protected backup power and 5V ESP32 supply | 2 | Actual continuity (not provided) |
| Optional battery-backed RTC (DS3231) | 2 | Preserve UTC time across offline reboot |
| Protected local router and MQTT broker | 1 each | Device transport; restrict network |

**Connections:** see the complete pin map in `firmware/ColdChain_ESP32/README.md`.

**Medical engineering requirement:** Food-grade/electronic hobby relays are not valid medical refrigerator motor controls. Use a professionally assessed safe, isolated interface and independent temperature protection. This project demonstrates decision logic; field use requires professional engineering and pharmacist/quality authority sign-off.
