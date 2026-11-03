@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title COLDCHAIN - HACKATHON CONTROL CENTER
:menu
cls
echo ==============================================================
echo   COLDCHAIN - FASTROBOX HACKATHON CONTROL CENTER ^(V8^)
echo ==============================================================
echo.
echo  BEFORE EVENT - RUN AT HOME WITH INTERNET
 echo  [1] Start SOFTWARE simulator dashboard
 echo  [2] Run Python software tests / setup
 echo  [3] Prepare Arduino ESP32 tools and download MQTT installer
 echo  [4] Create private FRIDGE_A / FRIDGE_B firmware profiles
 echo  [5] Update Wi-Fi/hotspot WITHOUT changing device secrets
 echo  [6] Compile both ESP32 sketches for classic ESP32 Dev Module
 echo.
echo  HACKATHON DAY - AFTER HARDWARE IS GIVEN
 echo  [7] Upload ESP32 firmware A or B ^(choose COM + board^)
 echo  [8] Start local MQTT broker ^(keep window open^)
 echo  [9] Start REAL hardware dashboard ^(keep window open^)
 echo  [L] Verify LIVE hardware readings ^(both boards^)
 echo  [M] Run MQTT broker ping test
 echo  [T] Configure and test Telegram alert
 echo  [P] Produce local preflight report
 echo  [Q] Exit
 echo.
set /p "CHOICE=Select an option: "
if /i "%CHOICE%"=="1" call "%~dp0START_DEMO_WINDOWS.bat"
if /i "%CHOICE%"=="2" call "%~dp0RUN_TESTS_WINDOWS.bat"
if /i "%CHOICE%"=="3" call "%~dp0PREPARE_LAPTOP_WINDOWS.bat"
if /i "%CHOICE%"=="4" call "%~dp0PREPARE_HARDWARE_WINDOWS.bat"
if /i "%CHOICE%"=="5" call "%~dp0UPDATE_NETWORK_WINDOWS.bat"
if /i "%CHOICE%"=="6" call "%~dp0CHECK_ESP32_COMPILE_WINDOWS.bat"
if /i "%CHOICE%"=="7" call "%~dp0UPLOAD_ESP32_WINDOWS.bat"
if /i "%CHOICE%"=="8" call "%~dp0START_BROKER_WINDOWS.bat"
if /i "%CHOICE%"=="9" call "%~dp0START_HARDWARE_WINDOWS.bat"
if /i "%CHOICE%"=="L" (
 set "LIVE_PORT=8000"
 set /p "LIVE_PORT=Hardware dashboard port [8000]: "
 if "!LIVE_PORT!"=="" set "LIVE_PORT=8000"
 call "%~dp0CHECK_LIVE_TELEMETRY_WINDOWS.bat" !LIVE_PORT!
)
if /i "%CHOICE%"=="M" call "%~dp0MQTT_SMOKE_TEST_WINDOWS.bat"
if /i "%CHOICE%"=="T" call "%~dp0CONFIGURE_TELEGRAM_WINDOWS.bat"
if /i "%CHOICE%"=="P" call "%~dp0PRE_HACKATHON_CHECK_WINDOWS.bat"
if /i "%CHOICE%"=="Q" exit /b 0
goto menu
