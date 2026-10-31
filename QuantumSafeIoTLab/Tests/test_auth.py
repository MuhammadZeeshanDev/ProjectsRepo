"""FR-01: test login without connecting to an actual local database."""
from quantumsafe import auth


def test_login_success(monkeypatch):
    monkeypatch.setattr(auth, "by_username", lambda name: {
        "UserId": 1, "Username": "student", "RoleName": "Researcher",
        "PasswordHash": "hashed", "IsActive": True
    })
    monkeypatch.setattr(auth, "verify", lambda saved, password: password == "correct")
    events = []
    monkeypatch.setattr(auth, "audit", lambda *args: events.append(args))
    result = auth.sign_in("student", "correct")
    assert result["RoleName"] == "Researcher"
    assert events == [(1, "LOGIN", True)]


def test_disabled_user_denied(monkeypatch):
    monkeypatch.setattr(auth, "by_username", lambda name: {
        "UserId": 2, "Username": "disabled", "RoleName": "Viewer",
        "PasswordHash": "hash", "IsActive": False
    })
    events = []
    monkeypatch.setattr(auth, "audit", lambda *args: events.append(args))
    assert auth.sign_in("disabled", "correct") is None
    assert events == [(2, "LOGIN", False)]
