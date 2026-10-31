"""Real SQL Server smoke test; opt-in with QUANTUMSAFE_TEST_DB=1."""
import os
import pytest
from quantumsafe import db


def test_sql_server_available_if_requested():
    if os.environ.get("QUANTUMSAFE_TEST_DB") != "1":
        pytest.skip("Requires local SQL Server, ODBC Driver 18 and .env")
    assert db.database_ready()
    assert db.one("SELECT COUNT(*) AS CountUsers FROM dbo.Users") is not None
