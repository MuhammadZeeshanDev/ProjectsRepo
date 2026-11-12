@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Python environment missing. Run INSTALL_AND_START.bat first.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" "SourceCode\final_system_check.py"
pause
