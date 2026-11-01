"""Launch the isolated PC B training console with one click (Windows-friendly)."""
from pathlib import Path
import socket
import subprocess
import sys
import time
import webbrowser

HOST = "127.0.0.1"
PORT = 8502

def console_is_running(host=HOST, port=PORT):
    try:
        with socket.create_connection((host, port), timeout=0.35):
            return True
    except OSError:
        return False

def launch_console(open_browser=True):
    url = f"http://{HOST}:{PORT}"
    if not console_is_running():
        source_dir = Path(__file__).resolve().parents[1]
        app = source_dir / "attacker_console.py"
        if not app.is_file():
            raise FileNotFoundError(f"Attacker console not found: {app}")
        command = [sys.executable, "-m", "streamlit", "run", str(app),
                   "--server.address", HOST, "--server.port", str(PORT),
                   "--server.headless", "true", "--browser.gatherUsageStats", "false"]
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        # Child process is intentionally separate; never passes defender credentials.
        subprocess.Popen(command, cwd=str(source_dir.parent),
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=creationflags)
        for _ in range(35):
            if console_is_running():
                break
            time.sleep(0.2)
        if not console_is_running():
            raise RuntimeError("PC B console did not start. Check Streamlit installation and port 8502.")
    if open_browser:
        webbrowser.open(url)
    return url

if __name__ == "__main__":
    try:
        print("Starting QuantumSafe PC B Security Test Station...")
        print(launch_console())
    except Exception as error:
        print(f"Could not start PC B: {error}", file=sys.stderr)
        raise SystemExit(1)
