@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Python environment missing. Read README.md and install requirements_peer.txt.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run SourceCode\peer_console.py --server.address 127.0.0.1 --server.port 8502
pause
