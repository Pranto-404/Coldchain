#pragma once
// Create secrets.h from this file. Use UNIQUE DEVICE_ID and DEVICE_SECRET per board.
#define DEVICE_ID "FRIDGE_A"  // change to FRIDGE_B on the second ESP32
#define DEVICE_SECRET "SimulatedOnly_FRIDGE_A_Key2026" // match DEVICE_FRIDGE_A_SECRET in .env
#define WIFI_SSID "YOUR_WIFI_NAME"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define MQTT_BROKER_IP "192.168.1.100" // computer's LAN IP, not localhost
#define MQTT_BROKER_PORT 1883
// Demo broker on trusted local LAN only. Use TLS and authenticated MQTT in deployment.
