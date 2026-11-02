"""Portable app launcher. Run using the Python interpreter from the venv."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[1]
raise SystemExit(subprocess.call([sys.executable,'-m','streamlit','run',str(root/'SourceCode'/'app.py'), '--server.address','127.0.0.1','--server.port','8501','--server.maxUploadSize','3072','--server.maxMessageSize','3072'],cwd=root))
