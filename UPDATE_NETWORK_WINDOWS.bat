@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ColdChain - Change WiFi / Host IP ONLY
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" UPDATE_NETWORK.py
) else if exist "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" (
  "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" UPDATE_NETWORK.py
) else (
  py -3 UPDATE_NETWORK.py
)
set "rc=%errorlevel%"
echo.
if not "%rc%"=="0" echo [ERROR] Network update failed - see above.
if "%rc%"=="0" echo REFLASH BOTH ESP32 BOARDS after this change.
pause
exit /b %rc%
