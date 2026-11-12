# Optional: manually select a SQL instance and rerun automatic, additive setup.
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $py)) { throw 'Run INSTALL_AND_START.bat before configuring SQL.' }
$server = Read-Host 'SQL Server instance name (example localhost\SQLEXPRESS)'
if ([string]::IsNullOrWhiteSpace($server)) { & $py (Join-Path $Root 'SourceCode\bootstrap_sql.py') }
else { & $py (Join-Path $Root 'SourceCode\bootstrap_sql.py') --server $server }
if ($LASTEXITCODE -ne 0) { throw 'SQL configuration failed. Verify Windows SQL account permissions.' }
