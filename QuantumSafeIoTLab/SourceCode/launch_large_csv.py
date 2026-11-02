"""Launch QuantumSafe with a 3GiB Streamlit upload limit. Use from project root."""
import subprocess
import sys
from pathlib import Path
app = Path(__file__).resolve().parent / 'app.py'
raise SystemExit(subprocess.call([sys.executable, '-m', 'streamlit', 'run', str(app), '--server.address', '127.0.0.1', '--server.maxUploadSize', '3072', '--server.maxMessageSize', '3072']))
