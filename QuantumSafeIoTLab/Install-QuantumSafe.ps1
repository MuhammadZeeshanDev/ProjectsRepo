# QuantumSafe portable bootstrap. Supports running from any extracted folder.
# Downloads trusted package dependencies using Microsoft Windows Package Manager.
# Existing SQL databases and data are preserved; no credentials printed.
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

function Header($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function HasWinget() { return [bool](Get-Command winget -ErrorAction SilentlyContinue) }
function Install-WingetPackage([string] $packageId) {
    if (-not (HasWinget)) {
        throw "Windows Package Manager (winget) not found. Install App Installer from Microsoft Store and rerun setup."
    }
    Write-Host "Downloading and installing $packageId via Windows Package Manager..."
    & winget install --id $packageId --exact --accept-package-agreements --accept-source-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) { throw "winget install of $packageId failed (exit $LASTEXITCODE). Review elevation or network access." }
}
function Find-Python {
    $candidates = @()
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        foreach ($ver in @('3.12','3.11')) {
            try {
                $candidate = & py "-$ver" -c "import sys; print(sys.executable if sys.maxsize>2**32 else '')" 2>$null
                if ($LASTEXITCODE -eq 0 -and $candidate) { $candidates += $candidate.Trim() }
            } catch {}
        }
    }
    $candidates += @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe"
    )
    foreach ($candidate in $candidates) {
        if (-not $candidate -or -not (Test-Path -LiteralPath $candidate)) { continue }
        $ok = & $candidate -c "import sys;print(int(sys.version_info[:2] in ((3,11),(3,12)) and sys.maxsize>2**32))" 2>$null
        if ($LASTEXITCODE -eq 0 -and "$ok".Trim() -eq '1') { return $candidate }
    }
    return $null
}
function OdbcInstalled {
    $reg = 'HKLM:\SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers'
    if (-not (Test-Path $reg)) { return $false }
    $props = Get-ItemProperty -Path $reg
    return ($props.'ODBC Driver 18 for SQL Server' -eq 'Installed' -or $props.'ODBC Driver 17 for SQL Server' -eq 'Installed')
}
function Find-Prolog {
    if (Get-Command swipl -ErrorAction SilentlyContinue) { return $true }
    $locations = @('C:\Program Files\swipl\bin\swipl.exe','C:\Program Files\SWI-Prolog\bin\swipl.exe')
    foreach ($f in $locations) { if (Test-Path -LiteralPath $f) { return $true } }
    return $false
}

Header 'Step 1 / 4 — Python 3.11 or 3.12 (64-bit)'
$python = Find-Python
if (-not $python) {
    Install-WingetPackage 'Python.Python.3.12'
    $python = Find-Python
    if (-not $python) { throw 'Python installed but not located. Open a fresh PowerShell window and rerun INSTALL_AND_START.bat.' }
}
Write-Host "Python: $python" -ForegroundColor Green
$venvPy = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPy)) {
    & $python -m venv (Join-Path $Root '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Python virtual environment.' }
}
if (-not (Test-Path -LiteralPath $venvPy)) { throw 'Missing .venv Python interpreter.' }

Header 'Step 2 / 4 — Python packages (internet required on first install)'
& $venvPy -m pip install --disable-pip-version-check --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip initialization failed.' }
& $venvPy -m pip install --disable-pip-version-check -r (Join-Path $Root 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check internet, Python architecture and requirements.txt.' }

Header 'Step 3 / 4 — SQL Server 2022 and ODBC'
if (-not (OdbcInstalled)) { Install-WingetPackage 'Microsoft.msodbcsql.18' }
# SQL Engine installation is offered only after an actual failed connection probe.
# Admin privileges and Microsoft SQL Server licensing prompts may be required.
& $venvPy (Join-Path $Root 'SourceCode\bootstrap_sql.py')
$sqlResult = $LASTEXITCODE
if ($sqlResult -ne 0) {
    Write-Warning 'Could not reach existing SQL Server or initialize database.'
    $reply = Read-Host 'Install Microsoft SQL Server 2022 Express (requires admin permission and Microsoft license)? [y/N]'
    if ($reply -match '^[Yy]$') {
        Install-WingetPackage 'Microsoft.SQLServer.2022.Express'
        Start-Sleep -Seconds 5
    }
    $manual = Read-Host 'SQL instance name (ENTER to auto-detect; example: localhost\SQLEXPRESS)'
    if ([string]::IsNullOrWhiteSpace($manual)) {
        & $venvPy (Join-Path $Root 'SourceCode\bootstrap_sql.py')
    } else {
        & $venvPy (Join-Path $Root 'SourceCode\bootstrap_sql.py') --server $manual
    }
    if ($LASTEXITCODE -ne 0) {
        throw 'SQL setup not verified. Check SQL service, ODBC, Windows account permission, and server instance; rerun INSTALL_AND_START.bat.'
    }
}

Header 'Step 4 / 4 — SWI-Prolog and final checks'
if (-not (Find-Prolog)) {
    Write-Host 'SWI-Prolog not detected. Installing local rule engine...'
    try { Install-WingetPackage 'SWI-Prolog.SWI-Prolog' }
    catch { Write-Warning "SWI-Prolog install not completed: $_. Rules may use Python fallback until installed." }
}
& $venvPy (Join-Path $Root 'SourceCode\final_system_check.py')
if ($LASTEXITCODE -ne 0) { Write-Warning 'Some optional system checks did not pass; review diagnostics.' }
# Mark only after SQL connection, schema and write/read-back confirmed.
$marker = Join-Path $Root 'Data\install_ready.marker'
New-Item -ItemType Directory -Path (Split-Path $marker) -Force | Out-Null
Set-Content -Path $marker -Value 'SQL schema, account and audit readback confirmed; local install finished.' -Encoding ASCII
Write-Host "`n[READY] QuantumSafe installed in $Root" -ForegroundColor Green
Write-Host 'Launch with START_APP.bat. PC B console: START_PC_B.bat.'
