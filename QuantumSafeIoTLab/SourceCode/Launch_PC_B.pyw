"""Double-click to open PC B without PowerShell commands."""
import sys
from pathlib import Path
import ctypes
sys.path.insert(0, str(Path(__file__).resolve().parent))
from quantumsafe.pc_b_launcher import launch_console
try:
    launch_console()
except Exception as exc:
    if sys.platform == "win32":
        ctypes.windll.user32.MessageBoxW(None, str(exc), "QuantumSafe PC B could not start", 0x10)
    else:
        raise
