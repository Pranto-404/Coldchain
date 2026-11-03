#pragma once
// CLASSIC ESP32 Dev Module reference pinout only.
// For ESP32-C3/S3 and other components, consult board datasheets before changing.
// NO MAINS CONNECTIONS. GPIO pins drive low-voltage demo indicators only.
constexpr int PIN_TEMP = 4;           // DS18B20 DATA (4.7k pull-up to 3.3V)
constexpr int PIN_DOOR = 18;          // Door switch to GND, internal pull-up
constexpr int PIN_RELAY = 19;         // Isolated LOW-VOLTAGE relay module signal
constexpr int PIN_RED = 25;           // Red LED with current limiting resistor
constexpr int PIN_GREEN = 26;         // Green LED with current limiting resistor
constexpr int PIN_BUZZER = 27;        // Active buzzer via driver if needed
constexpr int PIN_POWER_BUTTON = 32;  // Simulated mains-fail button
constexpr int PIN_BATTERY = 34;       // ADC only; calibrated divider REQUIRED
constexpr int PIN_OLED_SDA = 21;
constexpr int PIN_OLED_SCL = 22;
constexpr uint8_t OLED_I2C_ADDRESS = 0x3C; // Many SSD1306 units also use 0x3D
constexpr bool RELAY_ACTIVE_LOW = true;
constexpr bool DOOR_OPEN_WHEN_LOW = true;
constexpr bool POWER_OK_WHEN_HIGH = true;
constexpr bool POWER_BUTTON_TOGGLES = true; // true: momentary button toggles mains-fail; false: switch level
