@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" CHECK_HARDWARE_READY.py --require-broker
) else if exist "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" (
  "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" CHECK_HARDWARE_READY.py --require-broker
) else (
  py -3 CHECK_HARDWARE_READY.py --require-broker
)
set "rc=%errorlevel%"
if not "%rc%"=="0" echo Check failed - see the details above.
pause
exit /b %rc%
