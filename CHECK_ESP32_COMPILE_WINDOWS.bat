@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ColdChain - Compile Both ESP32 Sketches
if not exist "firmware\ColdChain_A\secrets.h" (
  echo [ERROR] Run PREPARE_HARDWARE_WINDOWS.bat first.
  pause
  exit /b 1
)
set "ARDUINO_CLI=%~dp0tools\arduino-cli\arduino-cli.exe"
if not exist "%ARDUINO_CLI%" (
  where arduino-cli.exe >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] Arduino CLI missing. Run PREPARE_LAPTOP_WINDOWS.bat first.
    pause
    exit /b 1
  )
  set "ARDUINO_CLI=arduino-cli.exe"
)
echo Using the standard ESP32 Dev Module target as a starting point.
echo If the organizer supplies ESP32-S3/C3/etc. you MUST choose its exact FQBN.
echo This checks compilation only, NOT electronics or physical function.
echo.
"%ARDUINO_CLI%" compile --fqbn esp32:esp32:esp32 "firmware\ColdChain_A"
if errorlevel 1 goto buildfail
"%ARDUINO_CLI%" compile --fqbn esp32:esp32:esp32 "firmware\ColdChain_B"
if errorlevel 1 goto buildfail
echo.
echo [PASS] Both ESP32 profiles compiled for esp32:esp32:esp32.
pause
exit /b 0
:buildfail
echo [FAIL] Compile failed. Check ESP32 core and libraries in docs\ONSITE_DAY_GUIDE.md.
pause
exit /b 1
