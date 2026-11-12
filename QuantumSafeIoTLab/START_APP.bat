@echo off
setlocal
cd /d "%~dp0"
title QuantumSafe - Start Application
if not exist ".venv\Scripts\python.exe" goto SETUP
if not exist ".env" goto SETUP
if not exist "Data\install_ready.marker" goto SETUP
goto RUN
:SETUP
 echo First run: downloading/checking requirements and preparing SQL Server...
 call "%~dp0INSTALL_AND_START.bat"
 exit /b %errorlevel%
:RUN
".venv\Scripts\python.exe" "SourceCode\preflight_start.py"
if errorlevel 1 (
 echo.
 echo Database is not ready. Use INSTALL_AND_START.bat to repair it.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run "SourceCode\app.py" --server.address 127.0.0.1 --server.port 8501 --server.headless false
if errorlevel 1 (
 echo.
 echo App could not start; run INSTALL_AND_START.bat or RUN_DIAGNOSTICS.bat to check setup.
 pause
)
