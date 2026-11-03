@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ColdChain - Automatic Setup and Dashboard
echo.
echo =========================================
echo    COLDCHAIN - AUTO INSTALL AND LAUNCH
echo =========================================
echo.
echo First run needs internet to download Python / packages if missing.
echo This program only installs Python for your Windows user; no admin rights needed.
echo.
if not exist "%~dp0BOOTSTRAP_WINDOWS.ps1" (
  echo [ERROR] BOOTSTRAP_WINDOWS.ps1 is missing.
  echo Please extract the COMPLETE ZIP into a folder before running.
  pause
  exit /b 1
)
where powershell.exe >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Windows PowerShell is required.
  pause
  exit /b 1
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0BOOTSTRAP_WINDOWS.ps1"
set "code=%errorlevel%"
echo.
if not "%code%"=="0" (
  echo [ERROR] ColdChain setup or application failed, exit code %code%.
) else (
  echo ColdChain was stopped. You can run this BAT again anytime.
)
echo Press any key to close this window.
pause >nul
exit /b %code%
