@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Please install with INSTALL_AND_START.bat first.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run "SourceCode\attacker_console.py" --server.address 127.0.0.1 --server.port 8502 --server.headless false
pause
