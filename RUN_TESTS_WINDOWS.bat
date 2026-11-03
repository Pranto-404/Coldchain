@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ColdChain - Automatic Setup and Tests
echo.
echo =========================================
echo  COLDCHAIN - AUTO INSTALL AND TESTS
echo =========================================
echo.
if not exist "%~dp0BOOTSTRAP_WINDOWS.ps1" (
  echo [ERROR] Extract the complete ZIP before running tests.
  pause
  exit /b 1
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0BOOTSTRAP_WINDOWS.ps1" -RunTests
set "code=%errorlevel%"
echo.
if "%code%"=="0" (echo All ColdChain tests completed successfully.) else (echo One or more ColdChain tests failed.)
pause
exit /b %code%
