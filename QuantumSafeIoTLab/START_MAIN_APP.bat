@echo off
cd /d "%~dp0"

if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" -m streamlit run SourceCode\app.py --server.address 127.0.0.1 --server.port 8501
) else (
    echo Python environment not found.
    pause
    exit /b 1
)

pause