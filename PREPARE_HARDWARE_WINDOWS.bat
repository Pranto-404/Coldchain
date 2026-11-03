@echo off
setlocal
cd /d "%~dp0"
title ColdChain - Prepare Onsite Hardware
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" PREPARE_HARDWARE.py
) else if exist "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" (
  "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" PREPARE_HARDWARE.py
) else (
  py -3 PREPARE_HARDWARE.py
)
set "rc=%errorlevel%"
echo.
if not "%rc%"=="0" echo Setup did not finish - read the message above.
echo Press any key to exit.
pause >nul
exit /b %rc%
