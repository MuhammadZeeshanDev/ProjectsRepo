"""FR-02: service permission guard works even without the UI."""
import pytest
from quantumsafe import users
from quantumsafe.permissions import PermissionDenied


def test_researcher_cannot_create_user(monkeypatch):
    monkeypatch.setattr(users, "active_actor", lambda uid: {"RoleName": "Researcher"})
    with pytest.raises(PermissionDenied):
        users.create_user(7, "tester", "A good long password!", "Viewer")


def test_invalid_role_rejected():
    with pytest.raises(ValueError):
        users.create_user(None, "tester", "A good long password!", "SuperAdmin")


def test_admin_prevents_self_disabling(monkeypatch):
    monkeypatch.setattr(users, "active_actor", lambda uid: {"RoleName": "Admin"})
    monkeypatch.setattr(users, "by_id", lambda uid: {"RoleName": "Admin"})
    with pytest.raises(ValueError, match="your own"):
        users.set_active(3, 3, False)
