@echo off
setlocal
cd /d "%~dp0"
title QuantumSafe Setup - installs dependencies and starts app
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-QuantumSafe.ps1"
if errorlevel 1 (
 echo.
 echo SETUP DID NOT COMPLETE. Read the message above; your existing SQL data is preserved.
 pause
 exit /b 1
)
echo.
echo Starting QuantumSafe...
call "%~dp0START_APP.bat"
