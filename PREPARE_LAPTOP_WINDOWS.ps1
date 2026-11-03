# Prepare Windows toolchain BEFORE the event while Internet is available.
# Downloads official Arduino CLI Windows build, installs ESP32 core and libraries.
# Mosquitto installer is saved from the publisher; installation needs user confirmation.
param([switch]$SkipMosquittoDownload, [switch]$SkipCoreInstall)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$ToolsDir=Join-Path $Root 'tools\arduino-cli'
$Downloads=Join-Path $Root 'tools\installers'
$Exe=Join-Path $ToolsDir 'arduino-cli.exe'
$ZipFile=Join-Path $Downloads 'arduino-cli_Windows_64bit.zip'
$ESP='https://espressif.github.io/arduino-esp32/package_esp32_index.json'
function Step([string]$msg){Write-Host "`n[PREP] $msg" -ForegroundColor Cyan}
function Check([int]$code,[string]$msg){if($code -ne 0){throw $msg}}
New-Item -ItemType Directory -Force -Path $ToolsDir,$Downloads | Out-Null
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }
try {
  if(-not (Test-Path $Exe)){
    Step 'Fetching the official Arduino CLI (requires Internet)'
    $source='https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Windows_64bit.zip'
    if(-not (Test-Path $ZipFile)) {Invoke-WebRequest -Uri $source -OutFile $ZipFile -UseBasicParsing -TimeoutSec 1200}
    Expand-Archive -LiteralPath $ZipFile -DestinationPath $ToolsDir -Force
    if(-not (Test-Path $Exe)){throw 'Arduino CLI missing in extracted official archive.'}
  }
  Step 'Verifying Arduino CLI'
  & $Exe version
  Check $LASTEXITCODE 'Arduino CLI did not run correctly.'
  if(-not $SkipCoreInstall){
    Step 'Refreshing ESP32 board core index (may need time / Internet)'
    & $Exe core update-index --additional-urls $ESP
    Check $LASTEXITCODE 'ESP32 board index update failed. Check Internet/proxy.'
    Step 'Installing Espressif ESP32 board core / compiler'
    & $Exe core install esp32:esp32 --additional-urls $ESP
    Check $LASTEXITCODE 'ESP32 core installation failed.'
    Step 'Installing firmware libraries and dependencies'
    foreach($lib in @('OneWire','DallasTemperature','ArduinoJson','PubSubClient','Adafruit GFX Library','Adafruit SSD1306')){
      Write-Host "  Installing $lib"
      & $Exe lib install $lib
      Check $LASTEXITCODE "Library install failed: $lib"
    }
  }
  Step 'Installed ESP32 cores'
  & $Exe core list
  Step 'Installed firmware libraries'
  & $Exe lib list
  if(-not $SkipMosquittoDownload){
    $MosInstaller=Join-Path $Downloads 'mosquitto-2.1.2-install-windows-x64.exe'
    if(-not (Test-Path $MosInstaller)){
      Step 'Downloading Eclipse Mosquitto Windows installer from official publisher'
      Invoke-WebRequest -Uri 'https://mosquitto.org/files/binary/win64/mosquitto-2.1.2-install-windows-x64.exe' -OutFile $MosInstaller -UseBasicParsing -TimeoutSec 1200
    }
    Step 'Mosquitto setup saved for offline use'
    Write-Host "  Installer: $MosInstaller"
    Write-Host '  Install it on your PC before the event; you may be prompted for admin permissions.' -ForegroundColor Yellow
    $found=(Get-Command mosquitto.exe -ErrorAction SilentlyContinue)
    if(-not $found -and -not (Test-Path "$env:ProgramFiles\mosquitto\mosquitto.exe")){
      $ans=Read-Host 'Run the official Mosquitto installer now? Y/N'
      if($ans -match '^y$'){
        $p=Start-Process -FilePath $MosInstaller -Wait -PassThru
        Write-Host "Installer exit code: $($p.ExitCode). Confirm successful installation before event."
      }
    }
  }
  Write-Host "`n[OK] Arduino CLI installation and requested tool preparation completed." -ForegroundColor Green
  Write-Host 'Next: PREPARE_HARDWARE_WINDOWS.bat, then CHECK_ESP32_COMPILE_WINDOWS.bat.'
} catch {
  Write-Host "`n[FAILED] $($_.Exception.Message)" -ForegroundColor Red
  Write-Host 'Fix Internet/access issue, then run PREPARE_LAPTOP_WINDOWS.bat again. Already downloaded files are kept.'
  exit 1
}
