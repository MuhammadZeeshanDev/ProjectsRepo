"""Read local configuration; this file never stores real passwords."""
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    # Local unit tests can import pure business logic without optional .env support.
    def load_dotenv(*_args, **_kwargs):
        return False

# Locate .env at the project root, even when Streamlit changes its working folder.
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def _safe_setting(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    if not value or any(ch in value for ch in (";", "{", "}")):
        raise ValueError(f"Invalid setting: {name}")
    return value


def sql_connection_string() -> str:
    """Use Windows sign-in to access the user's local SQL Server by default."""
    server = _safe_setting("SQL_SERVER", r"localhost\SQLEXPRESS")
    database = _safe_setting("SQL_DATABASE", "QuantumSafeIoTLab")
    driver = _safe_setting("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    auth = _safe_setting("SQL_AUTH", "windows").lower()
    trust = _safe_setting("SQL_TRUST_SERVER_CERTIFICATE", "false").lower()
    if auth != "windows":
        raise ValueError("This beginner release supports Windows Authentication only.")
    if trust not in ("true", "false"):
        raise ValueError("SQL_TRUST_SERVER_CERTIFICATE must be true or false.")
    return (
        f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
        "Trusted_Connection=yes;Encrypt=yes;"
        f"TrustServerCertificate={'yes' if trust == 'true' else 'no'};"
        "Connection Timeout=5;"
    )
