@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run INSTALL_AND_START.bat first.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" SourceCode\bootstrap_sql.py
pause
