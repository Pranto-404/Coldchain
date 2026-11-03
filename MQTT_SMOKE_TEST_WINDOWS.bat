@echo off
setlocal
cd /d "%~dp0"
title ColdChain - Check Local MQTT Broker
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" MQTT_SMOKE_TEST.py
) else (
  py -3 MQTT_SMOKE_TEST.py
)
pause
