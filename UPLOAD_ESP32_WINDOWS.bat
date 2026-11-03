@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title ColdChain - Verify and Upload ESP32 A or B
set "CLI=%~dp0tools\arduino-cli\arduino-cli.exe"
if not exist "%CLI%" (
  where arduino-cli.exe >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] Arduino CLI not found. Run PREPARE_LAPTOP_WINDOWS.bat at home first.
    pause
    exit /b 1
  )
  set "CLI=arduino-cli.exe"
)
echo ====================================================
echo       COLDCHAIN - ESP32 FIRMWARE UPLOADER
 echo ====================================================
echo Plug ONE board at a time with a DATA USB cable.
echo 1. FRIDGE_A
 echo 2. FRIDGE_B
set /p "CHOICE=Choose board 1 or 2: "
if "%CHOICE%"=="1" (set "BOARD=A") else if "%CHOICE%"=="2" (set "BOARD=B") else (
 echo [ERROR] Choose 1 or 2.
 pause
 exit /b 1
)
set "SKETCH=%~dp0firmware\ColdChain_!BOARD!"
if not exist "!SKETCH!\secrets.h" (
 echo [ERROR] Board profile not generated. Run PREPARE_HARDWARE_WINDOWS.bat first.
 pause
 exit /b 1
)
echo.
echo Available serial ports:
"%CLI%" board list
echo.
set /p "COMPORT=Type the Windows COM port for FRIDGE_!BOARD! ^(e.g. COM5^): "
if "%COMPORT%"=="" (
 echo [ERROR] COM port is required.
 pause
 exit /b 1
)
set "FQBN=esp32:esp32:esp32"
echo Default board: ESP32 Dev Module ^(classic ESP32^)
echo DO NOT use default for ESP32-C3/S3 or an unsupported ESP32 board.
set /p "CUSTOM=Board FQBN [Enter=esp32:esp32:esp32]: "
if not "%CUSTOM%"=="" set "FQBN=%CUSTOM%"
echo.
echo Selected: FRIDGE_!BOARD! on !COMPORT! using !FQBN!
set /p "CONFIRM=Confirm this matches the PHYSICAL board? Type YES: "
if /i not "!CONFIRM!"=="YES" (
 echo Canceled without writing to hardware.
 pause
 exit /b 2
)
"%CLI%" compile --fqbn "!FQBN!" "!SKETCH!"
if errorlevel 1 goto fail
"%CLI%" upload --fqbn "!FQBN!" --port "!COMPORT!" "!SKETCH!"
if errorlevel 1 goto fail
echo.
echo [UPLOAD COMPLETED] FRIDGE_!BOARD! flashed by Arduino CLI.
echo Verify OLED, temperature and serial output at 115200 baud physically.
echo Use a different COM port for the other board.
pause
exit /b 0
:fail
echo.
echo [FAILED] See compiler/uploader error. Check board model, driver, USB cable and pin compatibility.
pause
exit /b 1
