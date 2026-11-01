import pathlib

def test_release_version():
    from quantumsafe.version import APP_VERSION
    assert APP_VERSION == '0.5.0'

def test_permissions():
    from quantumsafe.permissions import may_run, may_manage_users
    assert may_run('Researcher') and not may_run('Viewer')
    assert may_manage_users('Admin') and not may_manage_users('Researcher')
