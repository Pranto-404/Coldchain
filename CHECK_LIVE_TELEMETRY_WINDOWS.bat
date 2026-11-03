@echo off
setlocal
cd /d "%~dp0"
set "PORT=8000"
if not "%~1"=="" set "PORT=%~1"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" CHECK_LIVE_TELEMETRY.py --port %PORT% --wait 90
) else if exist "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" (
  "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" CHECK_LIVE_TELEMETRY.py --port %PORT% --wait 90
) else (
  py -3 CHECK_LIVE_TELEMETRY.py --port %PORT% --wait 90
)
set "rc=%errorlevel%"
pause
exit /b %rc%
