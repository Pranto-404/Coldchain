@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ColdChain - Configure Telegram Door Alerts
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" CONFIGURE_TELEGRAM.py
) else if exist "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" (
  "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" CONFIGURE_TELEGRAM.py
) else (
  py -3 CONFIGURE_TELEGRAM.py
)
echo.
echo If Internet is unavailable at event, Telegram cannot deliver notifications.
pause
