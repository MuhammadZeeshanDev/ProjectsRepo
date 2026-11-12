@echo off
cd /d "%~dp0"
set "QSPY=.venv\Scripts\python.exe"
if not exist "%QSPY%" set "QSPY=..\.venv\Scripts\python.exe"
"%QSPY%" SourceCode\final_system_check.py
pause
