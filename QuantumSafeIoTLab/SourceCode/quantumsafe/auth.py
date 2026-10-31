"""Verify login credentials. The browser never decides its own permissions."""
from .users import by_username
from .passwords import verify
from . import db


def audit(user_id: int | None, action: str, ok: bool) -> None:
    # No passwords, ciphertext, secret material or sensitive errors in logs.
    db.execute(
        "INSERT INTO dbo.AuditLogs (UserId, ActionName, WasSuccessful) "
        "VALUES (?, ?, ?)", (user_id, action, int(ok))
    )


def sign_in(username: str, password: str):
    if not username or not password:
        return None
    found = by_username(username.strip())
    valid = bool(found and found["IsActive"]
                 and verify(found["PasswordHash"], password))
    audit(found["UserId"] if found else None, "LOGIN", valid)
    if not valid:
        return None
    return {k: found[k] for k in ("UserId", "Username", "RoleName")}
