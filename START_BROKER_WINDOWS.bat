@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ColdChain - Mosquitto Onsite Broker
set "MOSQUITTO_EXE="
if exist "%~dp0tools\mosquitto\mosquitto.exe" set "MOSQUITTO_EXE=%~dp0tools\mosquitto\mosquitto.exe"
for %%E in (mosquitto.exe) do if not defined MOSQUITTO_EXE for /f "delims=" %%P in ('where %%E 2^>nul') do if not defined MOSQUITTO_EXE set "MOSQUITTO_EXE=%%P"
if not defined MOSQUITTO_EXE if exist "%ProgramFiles%\mosquitto\mosquitto.exe" set "MOSQUITTO_EXE=%ProgramFiles%\mosquitto\mosquitto.exe"
if not defined MOSQUITTO_EXE if exist "%ProgramFiles(x86)%\mosquitto\mosquitto.exe" set "MOSQUITTO_EXE=%ProgramFiles(x86)%\mosquitto\mosquitto.exe"
if not defined MOSQUITTO_EXE (
 echo [ERROR] mosquitto.exe not found. Install Eclipse Mosquitto first.
 echo Official site: https://mosquitto.org/download/
 echo After installation, run this BAT again.
 pause
 exit /b 1
)
echo ===============================================================
echo   ColdChain LAN MQTT broker - isolated competition network ONLY
echo ===============================================================
echo WARNING: This local demo broker allows anonymous MQTT clients.
echo Keep PC on a TRUSTED LOCAL HOTSPOT. Never forward port 1883.
echo Do not use this with patient data or real refrigerators.
echo.
echo Press Ctrl+C to stop the broker.
"%MOSQUITTO_EXE%" -c "%~dp0mosquitto.onsite.conf" -v
set "rc=%errorlevel%"
echo.
echo Broker has stopped. Exit code: %rc%
pause
exit /b %rc%
