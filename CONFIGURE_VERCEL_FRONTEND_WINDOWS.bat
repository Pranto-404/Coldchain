@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (py -3.12 CONFIGURE_VERCEL_FRONTEND.py & if not errorlevel 1 exit /b 0)
if exist ".venv\Scripts\python.exe" (".venv\Scripts\python.exe" CONFIGURE_VERCEL_FRONTEND.py & pause & exit /b %errorlevel%)
where python >nul 2>nul
if not errorlevel 1 (python CONFIGURE_VERCEL_FRONTEND.py & pause & exit /b %errorlevel%)
echo Python not found. Use the Python from the ColdChain START_DEMO_WINDOWS.bat setup.
pause
exit /b 1
