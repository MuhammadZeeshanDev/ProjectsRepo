"""FR-01/FR-02: user roles must be enforced by service code."""
import pytest
from quantumsafe.permissions import require_role, PermissionDenied, may_run


def test_admin_and_researcher_can_run():
    for role in ("Admin", "Researcher"):
        require_role(role, ("Admin", "Researcher"))
        assert may_run(role)


def test_viewer_cannot_run():
    with pytest.raises(PermissionDenied):
        require_role("Viewer", ("Admin", "Researcher"))
    assert not may_run("Viewer")
