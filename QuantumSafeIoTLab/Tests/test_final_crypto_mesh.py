"""Control-plane tests. Fake KEM validates wiring; REAL pqcrypto is additionally tested on Windows."""
import hashlib
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'SourceCode'))
from quantumsafe import secure_mesh, device_registry

class Registry:
    def __init__(self):
        self.data={'camera':b'a'*32,'sensor':b'b'*32,'router':b'c'*32}
    def inventory(self):
        return [{'id':d,'name':d,'status':'active'} for d in self.data]

class IPS:
    def __init__(self):self.disabled=set()
    def active(self,d):return d in self.disabled

class Gateway:
    def __init__(self):
        self.server=object();self.registry=Registry();self.device_keys=self.registry.data
        self.registered_devices={k:k for k in self.device_keys};self.ips=IPS()


def fake_keys(_):
    v=os.urandom(32)
    return v,v

def fake_encaps(_, pk):
    ct=os.urandom(16)
    return ct, hashlib.sha256(pk+ct).digest()

def fake_decaps(_,sk,ct):
    return hashlib.sha256(sk+ct).digest()


def test_two_virtual_devices_delivery_tamper_replay_and_revocation(monkeypatch):
    monkeypatch.setattr(secure_mesh.crypto_engine,'make_keys',fake_keys)
    monkeypatch.setattr(secure_mesh.crypto_engine,'encapsulate',fake_encaps)
    monkeypatch.setattr(secure_mesh.crypto_engine,'decapsulate',fake_decaps)
    gw=Gateway();mesh=secure_mesh.SecureMesh(gw)
    ok=mesh.exchange('camera','sensor','reading=25')
    assert ok['receiver_opened'] and ok['delivered_text']=='reading=25'
    assert ok['ciphertext_bytes']>len('reading=25')
    assert ok['kem_ciphertext_bytes']>0
    failed=mesh.exchange('camera','sensor','reading=25',scenario='tamper')
    assert failed['decision']=='BLOCK' if 'decision' in failed else not failed['receiver_opened']
    assert not failed['receiver_opened'] and failed['delivered_text'] is None
    replay=mesh.exchange('camera','sensor','reading=25',scenario='replay')
    assert replay['first_delivery'] and not replay['receiver_opened']
    gw.ips.disabled.add('sensor')
    blocked=mesh.exchange('camera','sensor','x')
    assert not blocked['receiver_opened']
    gw.ips.disabled.clear()
    old=mesh._agents['sensor']
    gw.device_keys['sensor']=b'd'*32
    mesh.exchange('camera','sensor','new identity')
    assert mesh._agents['sensor'] is not old


def test_crypto_label_and_sql_insert_contract():
    import inspect
    from quantumsafe import gateway_event_store as g
    src=inspect.getsource(g.insert_event)
    assert 'CryptoKEMCiphertextBytes' in src
    assert 'CryptoCiphertextSha256' in src
    assert 'RequestType' in src and 'CryptoAlgorithm' in src


def test_prolog_policy_rules_loaded():
    from quantumsafe.ml_engine import incidents
    ev=[{'decision':'BLOCK','device':'a','reason':'Encrypted packet replay blocked'} for _ in range(3)]
    out=incidents.audit(ev,swipl='')
    assert out['devices']['a']['severity']=='critical'
    assert 'quarantine_review' in out['devices']['a']['recommendations']


def test_encrypted_threats_trigger_existing_windows_and_browser_alarm_rules():
    from quantumsafe.realtime_alarm import should_alarm
    from quantumsafe.security_alerts import alarm_eligible
    for reason in ('Encrypted packet authentication failed (tampering or invalid key)',
                   'Encrypted packet replay blocked'):
        item=dict(event_id='a'*32,decision='BLOCK',source='VIRTUAL_MESH',reason=reason)
        assert should_alarm(item)
        assert alarm_eligible(item)
    assert not should_alarm(dict(event_id='b'*32,decision='ALLOW',source='VIRTUAL_MESH',reason='ok'))
