@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ColdChain - Check Laptop Readiness
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" PRE_HACKATHON_CHECK.py --save
) else if exist "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" (
  "%LOCALAPPDATA%\Programs\ColdChainPython311\python.exe" PRE_HACKATHON_CHECK.py --save
) else (
  py -3 PRE_HACKATHON_CHECK.py --save
)
echo.
echo [INFO] PENDING means not yet proven. It does not mean the project failed.
pause
