"""
Database configuration and connection handling.

Every panel imports get_conn() from here instead of opening its own
connection string, so the server name only has to be changed in one
place.
"""

from tkinter import messagebox
import pyodbc

# Change SERVER to match your own SQL Server instance name.
# Examples: "localhost", "DESKTOP-ABC123\\SQLEXPRESS", ".\\SQLEXPRESS"
SERVER = "ZEESHAN\SQLEXPRESS"
DATABASE = "ClothMarketDB"
DRIVER = "ODBC Driver 17 for SQL Server"

CONN_STR = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"Trusted_Connection=yes;"
)


def get_conn():
    """Opens a fresh connection to SQL Server, or None if it fails."""
    try:
        return pyodbc.connect(CONN_STR)
    except Exception as e:
        messagebox.showerror(
            "Database Connection Failed",
            "Could not connect to SQL Server.\n\n"
            "Please check:\n"
            "  1. SQL Server 2022 is running\n"
            "  2. The SERVER name in app/config.py is correct\n"
            "  3. The ClothMarketDB database has been created\n"
            "     (run database/cloth_market.sql in SSMS first)\n\n"
            f"Details: {e}",
        )
        return None
