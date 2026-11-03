# ColdChain Windows one-click bootstrapper; Windows PowerShell 5.1+, Windows 10/11 64-bit.
# Installs official Python 3.11 per-user only if a suitable Python is not present.
# Everything runs from the extracted project directory. No admin account needed.
# Version 3: no inline python -c commands; launch is PowerShell 5.1 friendly.
param([switch]$RunTests, [switch]$HardwareMode)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root
$VenvDir = Join-Path $Root '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
$ManagedDir = Join-Path $env:LOCALAPPDATA 'Programs\ColdChainPython311'
$ManagedPython = Join-Path $ManagedDir 'python.exe'
$PythonVersion = '3.11.9'
$OfficialInstallerUrl = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe'
$Requirements = Join-Path $Root 'requirements.txt'
$RuntimeProbe = Join-Path $Root 'PYTHON_RUNTIME_CHECK.py'
$TranscriptStarted = $false
$ServerProcess = $null

function Step([string]$message) { Write-Host "`n[ColdChain] $message" -ForegroundColor Cyan }
function Fail([string]$message) { throw $message }

function CompatiblePython([string]$exe) {
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { return $false }
    if (-not (Test-Path -LiteralPath $RuntimeProbe -PathType Leaf)) { return $false }
    try {
        # Run a real .py file rather than Python -c to avoid PS 5.1 quote stripping.
        $versionText = & $exe $RuntimeProbe --check 2>$null
        return (($LASTEXITCODE -eq 0) -and ("$versionText" -match '^3\.(11|12)\.64$'))
    } catch { return $false }
}

function DetectPython {
    # A working project virtual environment takes precedence and avoids downloads.
    if (CompatiblePython $VenvPython) { return $VenvPython }

    $known = @(
        $ManagedPython,
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe')
    )
    foreach ($candidate in $known) {
        if (CompatiblePython $candidate) { return $candidate }
    }

    # Other Python installations may be registered even if py.exe isn't on PATH.
    foreach ($key in @(
        'HKCU:\Software\Python\PythonCore\3.11\InstallPath',
        'HKLM:\Software\Python\PythonCore\3.11\InstallPath',
        'HKCU:\Software\Python\PythonCore\3.12\InstallPath',
        'HKLM:\Software\Python\PythonCore\3.12\InstallPath'
    )) {
        try {
            if (Test-Path $key) {
                $installation = (Get-Item $key).GetValue('')
                if ($installation) {
                    $candidate = Join-Path $installation 'python.exe'
                    if (CompatiblePython $candidate) { return $candidate }
                }
            }
        } catch { }
    }

    if (Get-Command 'py.exe' -ErrorAction SilentlyContinue) {
        foreach ($version in @('3.11','3.12')) {
            try {
                $found = & py "-$version" $RuntimeProbe --path 2>$null
                if ($LASTEXITCODE -eq 0 -and $found) {
                    $candidate = "$(($found | Select-Object -Last 1))".Trim()
                    if (CompatiblePython $candidate) { return $candidate }
                }
            } catch { }
        }
    }
    $commands = @(Get-Command 'python.exe' -All -ErrorAction SilentlyContinue)
    foreach ($command in $commands) {
        if ($command.Source -and (CompatiblePython $command.Source)) { return $command.Source }
    }
    return $null
}

function InstallPython {
    if (-not [Environment]::Is64BitOperatingSystem) {
        Fail 'The bundled installer needs 64-bit Windows 10/11.'
    }
    Step "Python 3.11/3.12 not found. Downloading official Python $PythonVersion installer..."
    Write-Host "Source: $OfficialInstallerUrl"
    Write-Host 'Installation: current Windows user only; administrator access is NOT required.'
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }
    $tempDir = Join-Path $env:TEMP 'ColdChainPythonSetup'
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    $installer = Join-Path $tempDir "python-$PythonVersion-amd64.exe"
    if (-not (Test-Path -LiteralPath $installer)) {
        try {
            Invoke-WebRequest -Uri $OfficialInstallerUrl -OutFile $installer -UseBasicParsing -TimeoutSec 900
        } catch {
            Fail ('Cannot download Python from python.org. Connect to the internet, then run this BAT again. Details: ' + $_.Exception.Message)
        }
    }
    Write-Host 'Validating the official installer digital signature...'
    $signature = Get-AuthenticodeSignature -FilePath $installer
    if (($signature.Status -ne 'Valid') -or (-not $signature.SignerCertificate) -or
        ($signature.SignerCertificate.Subject -notmatch 'Python Software Foundation')) {
        Remove-Item -LiteralPath $installer -Force -ErrorAction SilentlyContinue
        Fail 'Installer signature is missing/invalid. Nothing was installed. Retry with an unrestricted, trusted connection.'
    }

    New-Item -ItemType Directory -Path $ManagedDir -Force | Out-Null
    Step 'Installing Python silently. This may take a few minutes...'
    $installerArgs = @('/quiet', 'InstallAllUsers=0', "TargetDir=`"$ManagedDir`"", 'PrependPath=0',
        'Include_launcher=0', 'Include_pip=1', 'Include_test=0', 'Shortcuts=0',
        'Include_doc=0', 'AssociateFiles=0')
    $install = Start-Process -FilePath $installer -ArgumentList $installerArgs -Wait -PassThru
    if ($install.ExitCode -notin @(0,3010)) {
        Fail "Python installer ended with code $($install.ExitCode). Check Windows permissions/security settings."
    }
    if (-not (CompatiblePython $ManagedPython)) {
        Fail "Python installation finished, but $ManagedPython is not usable. Check security/antivirus settings."
    }
    Write-Host 'Python successfully installed.' -ForegroundColor Green
    return $ManagedPython
}

function EnsureEnvironment([string]$basePython) {
    if (CompatiblePython $VenvPython) {
        Write-Host 'Existing project Python environment found.' -ForegroundColor Green
        return
    }
    if (Test-Path -LiteralPath $VenvDir) {
        $backupName = '.venv_backup_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
        Step "Existing environment is unusable; preserving it as $backupName"
        Rename-Item -LiteralPath $VenvDir -NewName $backupName
    }
    Step 'Creating an isolated project environment...'
    & $basePython -m venv $VenvDir
    if ($LASTEXITCODE -ne 0 -or -not (CompatiblePython $VenvPython)) {
        Fail 'Could not create the project environment (.venv). Ensure the extracted folder is writable.'
    }
}

function InstallDependencies {
    if (-not (Test-Path -LiteralPath $Requirements)) { Fail 'requirements.txt not found. Please extract the FULL ZIP first.' }
    $verifier = Join-Path $Root 'VERIFY_DEPENDENCIES.py'
    if (-not (Test-Path -LiteralPath $verifier)) { Fail 'VERIFY_DEPENDENCIES.py is missing. Extract the COMPLETE updated ZIP.' }
    $marker = Join-Path $VenvDir '.coldchain_requirements_sha256.txt'
    $desiredHash = (Get-FileHash -LiteralPath $Requirements -Algorithm SHA256).Hash

    # This check is independent of the previous failed setup marker. If pip finished
    # successfully before the old launcher crashed, reuse all installed packages.
    # Run a Python FILE instead of Windows PowerShell -c with embedded quotes,
    # which PowerShell 5.1 can misinterpret when passing native process arguments.
    $healthy = $false
    try {
        & $VenvPython $verifier --quiet *> $null
        if ($LASTEXITCODE -eq 0) {
            & $VenvPython -m pip check *> $null
            if ($LASTEXITCODE -eq 0) { $healthy = $true }
        }
    } catch { $healthy = $false }

    if ($healthy) {
        Set-Content -LiteralPath $marker -Value $desiredHash -Encoding ASCII
        Write-Host 'All required Python packages are already installed and verified. No reinstall needed.' -ForegroundColor Green
        return
    }

    Step 'Installing/repairing required Python libraries (first launch may take a few minutes)...'
    Write-Host 'Packages: FastAPI, Uvicorn, security libraries, machine learning, QR, tests, etc.'
    & $VenvPython -m pip --version
    if ($LASTEXITCODE -ne 0) {
        & $VenvPython -m ensurepip --upgrade
        if ($LASTEXITCODE -ne 0) { Fail 'Could not prepare pip.' }
    }
    & $VenvPython -m pip install --disable-pip-version-check --prefer-binary --timeout 60 --retries 3 -r $Requirements
    if ($LASTEXITCODE -ne 0) {
        Fail 'Package installation failed. Make sure you have internet access, then run the BAT again.'
    }
    & $VenvPython -m pip check
    if ($LASTEXITCODE -ne 0) { Fail 'Python dependency check failed. See error above.' }
    & $VenvPython $verifier
    if ($LASTEXITCODE -ne 0) { Fail 'One or more application packages could not be imported. See details above.' }
    Set-Content -LiteralPath $marker -Value $desiredHash -Encoding ASCII
    Write-Host 'All Python packages installed successfully.' -ForegroundColor Green
}

function PortFree([int]$port) {
    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        if ($null -ne $listener) { try { $listener.Stop() } catch { } }
    }
}

function RunApp {
    $port = 8000
    while ($port -le 8020 -and -not (PortFree $port)) { $port++ }
    if ($port -gt 8020) { Fail 'Ports 8000-8020 are busy. Close other demo servers and retry.' }
    $env:PORT = "$port"
    if ($HardwareMode) {
        $env:DEMO_MODE = '0'
        $env:MQTT_ENABLED = '1'
        $env:BIND_HOST = '127.0.0.1'
        Write-Host 'HARDWARE MODE - Simulation disabled; MQTT live ingestion enabled.' -ForegroundColor Yellow
    } else {
        $env:DEMO_MODE = '1'
        $env:MQTT_ENABLED = '0'
        $env:BIND_HOST = '127.0.0.1'
    }
    $url = "http://127.0.0.1:$port"
    Step "Starting ColdChain dashboard on $url"
    Write-Host 'Dashboard will open automatically when the server is ready.'
    $script:ServerProcess = Start-Process -FilePath $VenvPython -ArgumentList 'run_demo.py' -WorkingDirectory $Root -NoNewWindow -PassThru
    $ready = $false
    for ($n = 0; $n -lt 70; $n++) {
        $ServerProcess.Refresh()
        if ($ServerProcess.HasExited) {
            Fail "ColdChain server stopped unexpectedly (exit code $($ServerProcess.ExitCode)). Review the Python error above."
        }
        try {
            $status = Invoke-RestMethod -Uri "$url/health" -TimeoutSec 2 -ErrorAction Stop
            if ($status.ok -eq $true) { $ready = $true; break }
        } catch { }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) { Fail 'ColdChain did not become ready within 70 seconds. See server output above.' }

    Write-Host "`n=======================================" -ForegroundColor Green
    Write-Host ' COLDCHAIN IS READY!' -ForegroundColor Green
    Write-Host " URL: $url"
    if ($HardwareMode) {
        Write-Host ' Login: admin / pharmacist / inspector'
        Write-Host ' Passwords: open ONSITE_PRIVATE_CREDENTIALS.txt on THIS PC only.' -ForegroundColor Yellow
    } else {
        Write-Host ' Admin username: admin'
        Write-Host ' Admin password: ColdChainDemo_Admin2026!'
        Write-Host ' Pharmacist: pharmacist / ColdChainDemo_Pharmacist2026!'
        Write-Host ' Inspector: inspector / ColdChainDemo_Inspector2026!'
    }
    Write-Host '=======================================' -ForegroundColor Green
    Write-Host 'Close this window (or press Ctrl+C) to stop the local server.'
    try { Start-Process $url | Out-Null }
    catch { Write-Host "Could not automatically open your browser. Manually visit $url" -ForegroundColor Yellow }
    Wait-Process -Id $ServerProcess.Id
}

try {
    if (-not (Test-Path -LiteralPath $RuntimeProbe)) { Fail 'PYTHON_RUNTIME_CHECK.py is missing. Extract the complete ZIP.' }
    if (-not (Test-Path -LiteralPath (Join-Path $Root 'run_demo.py'))) {
        Fail 'run_demo.py was not found. Extract the entire ZIP before running START_DEMO_WINDOWS.bat.'
    }
    foreach ($requiredFile in @('requirements.txt', 'VERIFY_DEPENDENCIES.py', 'coldchain\app.py', 'web\index.html', 'web\app.js', 'models\forecast.joblib')) {
        if (-not (Test-Path -LiteralPath (Join-Path $Root $requiredFile) -PathType Leaf)) {
            Fail "Missing application file: $requiredFile. Extract the entire ZIP first."
        }
    }
    try {
        $logDir = Join-Path $Root 'logs'
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Start-Transcript -Path (Join-Path $logDir 'Windows_Setup.log') -Append -ErrorAction Stop | Out-Null
        $TranscriptStarted = $true
    } catch {
        Write-Host 'Note: setup log could not be opened; continuing without logging.' -ForegroundColor Yellow
    }
    Write-Host '=========================================' -ForegroundColor Cyan
    Write-Host '  COLDCHAIN - ONE CLICK AUTO SETUP' -ForegroundColor Cyan
    Write-Host '=========================================' -ForegroundColor Cyan
    Write-Host "Project: $Root"
    if ($HardwareMode) { Write-Host 'Hardware mode: Mosquitto must already be running on a trusted LAN.' }
    else { Write-Host 'Software demo: no Docker, Arduino IDE, or MQTT broker required.' }

    Step 'Looking for an existing Python 3.11/3.12 (64-bit)...'
    $basePython = DetectPython
    if (-not $basePython) { $basePython = InstallPython }
    Write-Host "Using: $basePython" -ForegroundColor Green
    EnsureEnvironment $basePython
    InstallDependencies
    if ($HardwareMode) {
        Step 'Checking live hardware configuration and local MQTT broker...'
        & $VenvPython (Join-Path $Root 'CHECK_HARDWARE_READY.py') --require-broker
        if ($LASTEXITCODE -ne 0) { Fail 'Hardware preflight failed. See docs/ONSITE_DAY_GUIDE.md.' }
    }
    if ($RunTests) {
        Step 'Executing ColdChain automated tests...'
        & $VenvPython (Join-Path $Root 'RUN_TESTS_SPLIT.py')
        if ($LASTEXITCODE -ne 0) { Fail 'One or more test suites did not pass; see report\LOCAL_TEST_RUN.txt.' }
        Write-Host 'All automated tests passed.' -ForegroundColor Green
    } else {
        RunApp
    }
} catch {
    Write-Host "`n[SETUP/START ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Log file: $(Join-Path $Root 'logs\Windows_Setup.log')" -ForegroundColor Yellow
    Write-Host 'Fix the problem above, then retry the chosen START_*_WINDOWS.bat.' -ForegroundColor Yellow
    exit 1
} finally {
    if ($null -ne $ServerProcess) {
        try {
            $ServerProcess.Refresh()
            if (-not $ServerProcess.HasExited) { Stop-Process -Id $ServerProcess.Id -Force -ErrorAction SilentlyContinue }
        } catch { }
    }
    if ($TranscriptStarted) { try { Stop-Transcript | Out-Null } catch { } }
}
