"""Role rules live here so the UI and services can use the same rules."""

ROLES = ("Admin", "Researcher", "Viewer")


class PermissionDenied(Exception):
    pass


def require_role(role: str, allowed: tuple[str, ...]) -> None:
    if role not in allowed:
        raise PermissionDenied("Your account cannot perform this action.")


def may_run(role: str) -> bool:
    return role in ("Admin", "Researcher")


def may_manage_users(role: str) -> bool:
    return role == "Admin"
