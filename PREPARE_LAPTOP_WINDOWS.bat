@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ColdChain - Preinstall ESP32 toolchain and Broker
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0PREPARE_LAPTOP_WINDOWS.ps1"
set "rc=%errorlevel%"
echo.
if not "%rc%"=="0" echo [ERROR] Preparation incomplete. Retry BEFORE the hackathon with Internet.
pause
exit /b %rc%
