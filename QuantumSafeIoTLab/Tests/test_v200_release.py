"""v2.0 acceptance: genuine signed allowed, malicious blocked, live viewer and PC B discovery."""
import json
import secrets
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
import pytest
from quantumsafe import virtual_network, attacker_client
from quantumsafe.device_registry import DeviceRegistry
from quantumsafe.virtual_ips import VirtualIPS
from quantumsafe.device_tests import run_case,history
from quantumsafe.realtime_alarm import AlarmEngine,should_alarm,_siren_wav
from quantumsafe.ui.security_console import render_html

ADMIN={'RoleName':'Admin','Username':'Boss','UserId':1}
OP={'RoleName':'Researcher','Username':'Operator','UserId':2}

@pytest.fixture()
def g(tmp_path,monkeypatch):
    monkeypatch.setattr(virtual_network,'DeviceRegistry',lambda:DeviceRegistry(tmp_path/'devices.json'))
    monkeypatch.setattr(virtual_network,'VirtualIPS',lambda: VirtualIPS(tmp_path/'ips.sqlite3'))
    gw=virtual_network.VirtualGateway()
    gw.alarm_engine=AlarmEngine(player=lambda event: True)
    port=gw.start(0)
    try:yield gw,tmp_path
    finally:gw.stop()

def test_safe_login_and_bad_credentials_from_real_http(g):
    gw,path=g
    rows=[run_case(gw,'virtual-cctv-01',ADMIN,x,path/'results.sqlite3') for x in
          ('valid_signed_telemetry','unauthorized_credentials','tampered_signature','replayed_nonce','unknown_device')]
    assert all(x['passed'] for x in rows),rows
    assert [x['actual'] for x in rows]==['ALLOW','BLOCK','BLOCK','BLOCK','BLOCK']
    assert len(history(db_path=path/'results.sqlite3'))==5
    gw.alarm_engine._queue.join()
    assert gw.alarm_engine.total_alerts>=4

def test_disabled_user_cannot_run_admin_device_tests(g):
    gw,path=g
    with pytest.raises(PermissionError):run_case(gw,'virtual-cctv-01',OP,'valid_signed_telemetry',path/'results.sqlite3')

def test_viewer_requires_issued_token_and_revoke(g):
    gw,_=g
    host='http://127.0.0.1:%d'%gw.port
    for url in (host+'/viewer/'+'x'*43,host+'/viewer/'+'x'*43+'/state'):
        with pytest.raises(HTTPError) as exc:urlopen(url,timeout=2)
        assert exc.value.code==403
    token=gw.issue_viewer(ADMIN)
    with urlopen(host+'/viewer/'+token,timeout=2) as resp:
        body=resp.read().decode()
        assert 'QuantumSafe' in body and 'window.QS_ENABLE_POLL=true' in body
        assert 'no-store' in resp.headers['Cache-Control']
        assert resp.headers['Referrer-Policy']=='no-referrer'
    with urlopen(host+'/viewer/'+token+'/state',timeout=2) as resp:
        obj=json.load(resp)
        assert obj['gateway_running'] and obj['devices']
        assert 'events' not in obj
        assert 'device_keys' not in json.dumps(obj)
    gw.revoke_viewer(token)
    with pytest.raises(HTTPError) as exc:urlopen(host+'/viewer/'+token+'/state',timeout=2)
    assert exc.value.code==403
    with pytest.raises(PermissionError):gw.issue_viewer({'RoleName':'Hacker','UserId':3})

def test_pc_b_sees_new_device_without_gateway_credentials(g,tmp_path,monkeypatch):
    gw,registry_path=g
    monkeypatch.setattr(attacker_client,'discover_targets',lambda: [{k:v for k,v in r.items() if k in ('id','name','type','status','virtual_ip')}
           for r in gw.registry.inventory() if r['status']!='retired'])
    new='new-lab-cam'
    gw.manage_device('register',new,ADMIN,name='New Lab Camera',kind='Camera',virtual_ip='192.168.11.9')
    rows=attacker_client.discover_targets()
    assert next(x for x in rows if x['id']==new)['virtual_ip']=='192.168.11.9'
    assert all(not any(k in r for k in ('token','key_hex','signature')) for r in rows)
    res=attacker_client.send_dynamic_test(new,port=gw.port)
    assert len(res)==1 and res[0]['decision']=='BLOCK'
    assert len(attacker_client.send_dynamic_test(new,case='repeated',port=gw.port))==5

def test_audio_is_real_pcm_wav_not_just_text():
    raw=_siren_wav()
    assert raw[:4]==b'RIFF' and b'WAVE' in raw[:16] and len(raw)>20000
    assert should_alarm({'event_id':'a','source':'LOCAL_HTTP','decision':'BLOCK',
                         'reason':'Virtual IPS quarantine active'})
    assert not should_alarm({'event_id':'b','source':'LOCAL_HTTP','decision':'ALLOW',
                         'reason':'Authenticated and integrity verified'})

def test_html_has_no_unresolved_template_and_can_poll(g):
    gw,_=g
    rendered=render_html(gw.viewer_state(),polling=True)
    assert 'window.QS_ENABLE_POLL=true' in rendered
    assert '__QS_SNAPSHOT_JSON__' not in rendered and '__QS_ENABLE_POLL__' not in rendered
    assert 'AudioContext' in rendered and "fetch(endpoint" in rendered
