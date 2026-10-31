"""NFR: local database connection uses encrypted, parameterized SQL Server."""
import pytest
from quantumsafe.config import sql_connection_string


def test_windows_sql_connection(monkeypatch):
    monkeypatch.setenv("SQL_SERVER", r"localhost\SQLEXPRESS")
    monkeypatch.setenv("SQL_AUTH", "windows")
    monkeypatch.setenv("SQL_TRUST_SERVER_CERTIFICATE", "true")
    result = sql_connection_string()
    assert "Trusted_Connection=yes" in result
    assert "Encrypt=yes" in result
    assert "SQL Server" in result


def test_sql_connection_injection_blocked(monkeypatch):
    monkeypatch.setenv("SQL_SERVER", "local;UID=bad")
    with pytest.raises(ValueError):
        sql_connection_string()
