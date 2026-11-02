"""User records; all admin actions check authorization against the database."""
from . import db
from .passwords import make_hash
from .permissions import ROLES, require_role


def by_username(username: str):
    return db.one(
        "SELECT UserId, Username, PasswordHash, RoleName, IsActive "
        "FROM dbo.Users WHERE Username = ?", (username,)
    )


def by_id(user_id: int):
    return db.one(
        "SELECT UserId, Username, RoleName, IsActive "
        "FROM dbo.Users WHERE UserId = ?", (user_id,)
    )


def active_actor(user_id: int) -> dict:
    user = by_id(user_id)
    if not user or not user["IsActive"]:
        raise PermissionError("Account is disabled or no longer exists.")
    if user["RoleName"] not in ROLES:
        raise PermissionError("Legacy Observer account: ask Administrator to switch your role to Security Operator or disable it.")
    return user


def list_users(actor_id: int) -> list[dict]:
    require_role(active_actor(actor_id)["RoleName"], ("Admin",))
    return db.rows(
        "SELECT UserId, Username, RoleName, IsActive, CreatedAtUtc "
        "FROM dbo.Users ORDER BY UserId DESC"
    )


def create_user(actor_id: int | None, username: str, password: str,
                role: str, initial_admin: bool = False) -> None:
    username = username.strip()
    if not 3 <= len(username) <= 50 or not all(
        c.isalnum() or c in ("_", "-", ".") for c in username
    ):
        raise ValueError("Username must be 3–50 letters, digits, dots, dashes or underscores.")
    if role not in ROLES:
        raise ValueError("Please choose a valid role.")
    # First account is created only by setup_admin.py on an empty database.
    if initial_admin:
        if role != "Admin" or db.one("SELECT TOP 1 UserId FROM dbo.Users"):
            raise ValueError("Initial admin may be created only in an empty database.")
    else:
        if actor_id is None:
            raise PermissionError("Administrator sign-in is required.")
        require_role(active_actor(actor_id)["RoleName"], ("Admin",))
    db.execute(
        "INSERT INTO dbo.Users (Username, PasswordHash, RoleName) VALUES (?, ?, ?)",
        (username, make_hash(password), role)
    )


def set_active(actor_id: int, target_id: int, active: bool) -> None:
    actor = active_actor(actor_id)
    require_role(actor["RoleName"], ("Admin",))
    target = by_id(target_id)
    if not target:
        raise ValueError("Account not found.")
    if target_id == actor_id and not active:
        raise ValueError("You cannot disable your own logged-in account.")
    if target["RoleName"] == "Admin" and not active:
        count = db.one("SELECT COUNT(*) AS AdminCount FROM dbo.Users "
                       "WHERE RoleName = 'Admin' AND IsActive = 1")["AdminCount"]
        if count <= 1:
            raise ValueError("At least one active administrator must remain.")
    db.execute("UPDATE dbo.Users SET IsActive = ? WHERE UserId = ?",
               (int(active), target_id))


def set_role(actor_id: int, target_id: int, role: str) -> None:
    """Only an active administrator may change roles. Never remove the final active admin."""
    actor = active_actor(actor_id)
    require_role(actor["RoleName"], ("Admin",))
    if role not in ROLES:
        raise ValueError("Choose Administrator or Security Operator.")
    target = by_id(target_id)
    if not target:
        raise ValueError("Account not found.")
    if int(target_id) == int(actor_id) and role != "Admin":
        raise ValueError("You cannot remove your own Administrator access.")
    if target["RoleName"] == "Admin" and role != "Admin" and target["IsActive"]:
        count = db.one("SELECT COUNT(*) AS AdminCount FROM dbo.Users WHERE RoleName = 'Admin' AND IsActive = 1")["AdminCount"]
        if count <= 1:
            raise ValueError("At least one active Administrator must remain.")
    db.execute("UPDATE dbo.Users SET RoleName = ? WHERE UserId = ?", (role, target_id))
