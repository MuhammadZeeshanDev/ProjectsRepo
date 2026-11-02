import json
import time
from pathlib import Path
import pytest
from quantumsafe.virtual_ips import VirtualIPS
from quantumsafe import virtual_network
from quantumsafe.device_registry import DeviceRegistry

ADMIN={'RoleName':'Admin','Username':'A'}
OPERATOR={'RoleName':'Researcher','Username':'O'}


def policy(tmp_path):
    fake_time=[1000.0]
    return VirtualIPS(tmp_path/'ips.sqlite3',clock=lambda:fake_time[0]),fake_time


def test_policy_defaults_off_and_permission(tmp_path):
    ips,t=policy(tmp_path)
    assert not ips.settings()['auto_quarantine']
    with pytest.raises(PermissionError):ips.set_auto(True,OPERATOR)
    with pytest.raises(PermissionError):ips.quarantine('camera-01',OPERATOR)
    with pytest.raises(PermissionError):ips.release('camera-01',OPERATOR)
    assert ips.audit()==[]


def test_manual_persistence_expiry_release(tmp_path):
    ips,t=policy(tmp_path)
    ips.quarantine('camera-01',ADMIN,seconds=60)
    assert ips.active('camera-01')
    ips2=VirtualIPS(tmp_path/'ips.sqlite3',clock=lambda:t[0])
    assert ips2.active('camera-01')
    t[0]+=61
    assert not ips2.active('camera-01')
    ips2.quarantine('camera-01',ADMIN,seconds=60)
    ips2.release('camera-01',ADMIN)
    assert not ips2.active('camera-01')
    assert [x['action'] for x in ips2.audit()][:2]==['release','quarantine']


def test_default_never_auto_quarantines(tmp_path):
    ips,t=policy(tmp_path)
    ev={'device':'camera-01','reason':'Message integrity check failed'}
    assert not any(ips.observe(ev,trusted_identity=True,enrolled=True) for _ in range(3))
    assert not ips.active('camera-01')


def test_auto_only_valid_identity_and_threshold(tmp_path):
    ips,t=policy(tmp_path)
    ips.set_auto(True,ADMIN)
    ev={'device':'camera-01','reason':'Message integrity check failed'}
    for _ in range(10):
        assert not ips.observe(ev,trusted_identity=False,enrolled=True)
    assert not ips.active('camera-01')
    for _ in range(2):
        assert not ips.observe(ev,trusted_identity=True,enrolled=True)
    assert ips.observe(ev,trusted_identity=True,enrolled=True)
    assert ips.active('camera-01')
    t[0]+=121
    assert not ips.active('camera-01')


def test_unknown_and_untrusted_never_quarantine(tmp_path):
    ips,t=policy(tmp_path);ips.set_auto(True,ADMIN)
    for _ in range(10):
        assert not ips.observe({'device':'camera-01','reason':'Invalid per-device credential'},trusted_identity=False,enrolled=True)
        assert not ips.observe({'device':'unknown','reason':'Replay nonce detected'},trusted_identity=True,enrolled=False)
    assert not ips.active('camera-01') and not ips.active('unknown')


def test_gateway_ipc_intercepts_signed_telemetry_and_releases(tmp_path,monkeypatch):
    monkeypatch.setattr(virtual_network,'DeviceRegistry',lambda:DeviceRegistry(tmp_path/'devices.json'))
    monkeypatch.setattr(virtual_network,'VirtualIPS',lambda: VirtualIPS(tmp_path/'ips.sqlite3'))
    gateway=virtual_network.VirtualGateway()
    did='virtual-cctv-01'
    gw_token=gateway.token
    token=gateway.device_tokens[did]
    def make(n,v=45,tkn=token):
        return {'device':did,'nonce':n,'value':v,'token':gw_token,'device_token':tkn,
                'signature':gateway.sign(did,n,v)}
    assert gateway.evaluate(make('a'))['decision']=='ALLOW'
    gateway.ips.quarantine(did,ADMIN)
    event=gateway.evaluate(make('b'))
    assert event['decision']=='BLOCK' and event['reason']=='Virtual IPS quarantine active'
    gateway.ips.release(did,ADMIN)
    assert gateway.evaluate(make('c'))['decision']=='ALLOW'
    assert gateway.evaluate(make('d',tkn='wrong'))['reason']=='Invalid per-device credential'
    assert not gateway.ips.active(did)


def test_gateway_authenticated_integrity_can_trigger_auto(tmp_path,monkeypatch):
    monkeypatch.setattr(virtual_network,'DeviceRegistry',lambda:DeviceRegistry(tmp_path/'devices.json'))
    monkeypatch.setattr(virtual_network,'VirtualIPS',lambda: VirtualIPS(tmp_path/'ips.sqlite3'))
    gw=virtual_network.VirtualGateway(); gw.ips.set_auto(True,ADMIN)
    did='virtual-cctv-01'
    def send(n,tamper=False):
        msg={'device':did,'nonce':n,'value':22,'token':gw.token,'device_token':gw.device_tokens[did],
            'signature':gw.sign(did,n,22)}
        if tamper:msg['value']=999
        return gw.evaluate(msg)
    assert send('a',True)['decision']=='BLOCK'
    assert send('b',True)['decision']=='BLOCK'
    third=send('c',True)
    assert third['decision']=='BLOCK'
    assert 'ips_action' in third
    assert gw.ips.active(did)
    assert send('d')['reason']=='Virtual IPS quarantine active'
