"""The only module that talks directly to SQL Server 2022."""
from contextlib import contextmanager
from .config import sql_connection_string


@contextmanager
def connection():
    import pyodbc
    con = pyodbc.connect(sql_connection_string(), timeout=5, autocommit=False)
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def rows(sql: str, args=()) -> list[dict]:
    """Read SQL query results as simple Python dictionaries."""
    with connection() as con:
        cur = con.cursor()
        cur.execute(sql, *args)
        names = [column[0] for column in cur.description]
        return [dict(zip(names, record)) for record in cur.fetchall()]


def one(sql: str, args=()):
    items = rows(sql, args)
    return items[0] if items else None


def execute(sql: str, args=()) -> int:
    with connection() as con:
        cur = con.cursor()
        cur.execute(sql, *args)
        return int(cur.rowcount)


def database_ready() -> bool:
    try:
        return one("SELECT 1 AS IsReady")["IsReady"] == 1
    except Exception:
        return False
