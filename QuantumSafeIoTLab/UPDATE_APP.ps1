param([string]$ProjectRoot = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = (Resolve-Path $ProjectRoot).Path
$updates = Join-Path $root 'Updates'
$backupRoot = Join-Path $root 'Backups'
$logs = Join-Path $root 'UpdateLogs'
New-Item -ItemType Directory -Force -Path $updates,$backupRoot,$logs | Out-Null
$log = Join-Path $logs ("update_" + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
Start-Transcript -Path $log | Out-Null
$temp = $null
try {
  Write-Host 'QuantumSafe safe updater - application files only' -ForegroundColor Cyan
  if (!(Test-Path (Join-Path $root 'SourceCode\app.py'))) { throw 'Run UPDATE_APP.bat from the QuantumSafeIoTLab project folder (SourceCode/app.py missing).' }
  $packages = @(Get-ChildItem $updates -Filter '*.zip' -File | Sort-Object LastWriteTime -Descending)
  if ($packages.Count -ne 1) { throw "Expected exactly ONE update ZIP in $updates; found $($packages.Count)." }
  $zip = $packages[0]
  $temp = Join-Path ([IO.Path]::GetTempPath()) ('quantumsafe_update_' + [guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $temp | Out-Null
  Expand-Archive -LiteralPath $zip.FullName -DestinationPath $temp
  $manifestPath = Join-Path $temp 'update.json'
  if (!(Test-Path $manifestPath)) { throw 'Update ZIP must contain update.json at its root.' }
  $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
  if ($manifest.product -ne 'QuantumSafeIoTLab' -or !$manifest.version) { throw 'Invalid product/version in update.json.' }
  $payload = Join-Path $temp 'payload'
  if (!(Test-Path $payload)) { throw 'Missing payload directory.' }
  $files = @(Get-ChildItem $payload -File -Recurse)
  if ($files.Count -eq 0) { throw 'Empty update payload.' }
  $allowed = @('SourceCode/','Tests/','Documentation/','Assets/')
  foreach ($f in $files) {
    $relative = $f.FullName.Substring($payload.Length).TrimStart('\','/').Replace('\','/')
    if (!(@($allowed | Where-Object { $relative.StartsWith($_, [StringComparison]::OrdinalIgnoreCase) }).Count -gt 0)) { throw "Forbidden update path: $relative" }
    if ($relative -match '(^|/)(\.env|\.venv|__pycache__)(/|$)' -or $relative -match '\.(ps1|bat|cmd|exe|dll|pyd|sql)$') { throw "Blocked sensitive/executable update file: $relative" }
  }
  Write-Host "Package: $($zip.Name); Version: $($manifest.version); Files: $($files.Count)"
  $answer = Read-Host 'Stop the running app first. Apply update now? Type YES'
  if ($answer -cne 'YES') { throw 'Cancelled by user.' }
  $backup = Join-Path $backupRoot ('app_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
  New-Item -ItemType Directory -Path $backup | Out-Null
  $newPaths = New-Object System.Collections.Generic.List[string]
  foreach ($f in $files) {
    $relative = $f.FullName.Substring($payload.Length).TrimStart('\','/')
    $destination = Join-Path $root $relative
    if (Test-Path $destination) {
      $oldCopy = Join-Path $backup $relative
      New-Item -ItemType Directory -Force -Path (Split-Path $oldCopy) | Out-Null
      Copy-Item -LiteralPath $destination -Destination $oldCopy
    } else { $newPaths.Add($relative) }
  }
  try {
    foreach ($f in $files) {
      $relative = $f.FullName.Substring($payload.Length).TrimStart('\','/')
      $destination = Join-Path $root $relative
      New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
      Copy-Item -LiteralPath $f.FullName -Destination $destination -Force
    }
    Write-Host 'Application files updated. Database and dependencies were NOT changed.' -ForegroundColor Green
    Write-Host "Backup: $backup"
    Write-Host 'Restart app and run tests. If a test fails, restore from the backup.'
  } catch {
    foreach ($f in @(Get-ChildItem $backup -Recurse -File)) {
      $relative = $f.FullName.Substring($backup.Length).TrimStart('\','/')
      $destination = Join-Path $root $relative
      Copy-Item -LiteralPath $f.FullName -Destination $destination -Force
    }
    foreach ($relative in $newPaths) { $p = Join-Path $root $relative; if (Test-Path $p) { Remove-Item -LiteralPath $p -Force } }
    throw
  }
} catch { Write-Host "UPDATE STOPPED: $($_.Exception.Message)" -ForegroundColor Red; exit 1 }
finally { if ($temp -and (Test-Path $temp)) { Remove-Item $temp -Recurse -Force }; Stop-Transcript | Out-Null }
