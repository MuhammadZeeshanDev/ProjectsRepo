"""Regression test for monitoring on stale gateway objects; no public viewer fallback."""
from quantumsafe.ui.security_monitor import _viewer_session

ADMIN = {'RoleName':'Admin', 'UserId':1, 'Username':'Admin'}

class Legacy:
    server = object()
    port = 8765
    # Intentionally lacks issue_viewer().

class Modern:
    def __init__(self):
        self.tokens=set()
    def issue_viewer(self, actor):
        assert actor['UserId'] == 1
        self.tokens.add('t'*45)
        return 't'*45
    def valid_viewer(self, token): return token in self.tokens
    def viewer_state(self): return {}

def test_old_gateway_returns_no_viewer_and_does_not_bypass_auth():
    state={}
    assert _viewer_session(Legacy(), ADMIN, state, clock=lambda:100.0) is None
    assert 'qs_monitor_viewer' not in state

def test_new_gateway_issues_and_reuses_token():
    gateway=Modern(); state={}
    first=_viewer_session(gateway,ADMIN,state,clock=lambda:100.0)
    assert first['token']=='t'*45
    assert _viewer_session(gateway,ADMIN,state,clock=lambda:101.0) is first
    gateway.tokens.clear()
    assert _viewer_session(gateway,ADMIN,state,clock=lambda:102.0)['token']=='t'*45
