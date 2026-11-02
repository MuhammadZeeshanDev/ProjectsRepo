import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import pytest
from threading import RLock
from quantumsafe import console_data
from quantumsafe.ui import security_console

class Registry:
    def __init__(self):
        self.rows=[
          {'id':'cam-01','name':'Camera 01','type':'Camera','status':'active','virtual_ip':'10.1.1.10'},
          {'id':'sensor-01','name':'Sensor <script>alert(1)</script>','type':'Sensor','status':'active','virtual_ip':'10.1.1.11'},
          {'id':'retired-01','name':'Gone','type':'Sensor','status':'retired'},
          {'id':'disabled-01','name':'Disabled device','type':'Camera','status':'disabled'},
        ]
    def inventory(self):return self.rows
class GW:
    def __init__(self, events, running=True):
        self.registry=Registry();self.events=events;self.lock=RLock();self.server=object() if running else None

def ev(now,device='cam-01',decision='ALLOW',reason='Authenticated and integrity verified',reading=22,source_ip='127.0.0.1'):
    return {'timestamp_utc':now.isoformat(timespec='seconds'),'device':device,'decision':decision,'reason':reason,
      'source_ip':source_ip,'source':'LOCAL_HTTP','reading':reading,'request_type':'telemetry'}

def test_registrations_and_observed_status():
    now=datetime.now(timezone.utc)
    gw=GW([ev(now),ev(now,decision='BLOCK',reason='Invalid per-device credential')])
    d=console_data.snapshot(gw,now=now)
    assert len(d['devices'])==3
    assert next(x for x in d['devices'] if x['id']=='cam-01')['status']=='attack'
    assert next(x for x in d['devices'] if x['id']=='sensor-01')['status']=='offline'
    assert next(x for x in d['devices'] if x['id']=='disabled-01')['status']=='quarantined'
    assert d['blocked_24h']==1
    assert d['traffic']['requests'][-1]==2
    assert d['traffic']['rejected_fraction'][-1]==.5
    assert d['alerts'][0]['severity']=='high'

def test_disabled_gateway_not_claim_live():
    now=datetime.now(timezone.utc)
    d=console_data.snapshot(GW([ev(now)],running=False),now=now)
    assert not d['gateway_running']
    assert next(x for x in d['devices'] if x['id']=='cam-01')['status']=='offline'
    assert 'No live traffic' in d['footer']

def test_multiple_simultaneous_events_not_collapsed():
    now=datetime.now(timezone.utc)
    a=ev(now,decision='BLOCK',reason='Replay nonce detected')
    b=ev(now,decision='BLOCK',reason='Replay nonce detected')
    assert len(console_data.merge_events([a,b]))==2
    assert len(console_data.merge_events([a,b],[a,b]))==2
    assert len(console_data.merge_events([a,b,b],[a,b]))==3
    assert len({v['console_uid'] for v in console_data.merge_events([a,b])})==2

def test_sql_and_local_merge_not_double_count():
    now=datetime.now(timezone.utc)
    a=ev(now,decision='BLOCK',reason='Message integrity check failed')
    sql=dict(a,event_id=100,timestamp_utc=now.isoformat(timespec='milliseconds').replace('+00:00','Z'))
    merged=console_data.merge_events([a],[sql])
    assert len(merged)==1

def test_ack_requires_admin_and_persists(tmp_path):
    uid='a'*24
    db=tmp_path/'db.sqlite3'
    with pytest.raises(PermissionError): console_data.acknowledge(uid,{'RoleName':'Researcher'},db)
    with pytest.raises(ValueError):console_data.acknowledge('bad',{'RoleName':'Admin'},db)
    console_data.acknowledge(uid,{'RoleName':'Admin','Username':'Alice'},db)
    assert uid in console_data.acked_uids(db)


def test_xss_escaped_in_embedded_json():
    now=datetime.now(timezone.utc)
    d=console_data.snapshot(GW([ev(now)]),now=now)
    html=security_console.render_html(d)
    assert 'Sensor <script>alert(1)</script>' not in html
    assert '\\u003cscript\\u003e' in html
    assert 'new WebSocket' not in html
    assert 'Sim.start' not in html
    assert 'source from local' not in html  # verify no fiction in template


def test_render_only_public_fields():
    now=datetime.now(timezone.utc)
    d=console_data.snapshot(GW([ev(now)]),now=now)
    d['events'].append({'secret':'token-must-not-appear'})
    html=security_console.render_html(d)
    assert 'token-must-not-appear' not in html
    assert '__QS_SNAPSHOT_JSON__' not in html


def test_stale_gateway_event_is_not_heartbeat():
    now=datetime.now(timezone.utc)
    d=console_data.snapshot(GW([ev(now-timedelta(minutes=2))]),now=now)
    assert next(x for x in d['devices'] if x['id']=='cam-01')['status']=='offline'
    assert sum(d['traffic']['requests'])==0


def test_alert_ack_changes_view_status():
    now=datetime.now(timezone.utc);a=ev(now,decision='BLOCK',reason='Invalid gateway token')
    uid=console_data.merge_events([a])[0]['console_uid']
    d=console_data.snapshot(GW([a]),now=now,acked={uid})
    assert d['alerts'][0]['acknowledged']


def test_nonfinite_telemetry_not_embedded():
    now=datetime.now(timezone.utc)
    a=ev(now,reading=float('nan'))
    d=console_data.snapshot(GW([a]),now=now)
    assert d['devices'][0]['value'] is None
    assert 'NaN' not in security_console.render_html(d)
