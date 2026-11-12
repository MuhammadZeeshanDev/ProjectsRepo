"""Final virtual gateway KEM/AEAD + SQL event staging behavior.
KEM stub exercises control flow. Native pqcrypto tests require actual Windows environment.
"""
import os,sys,hashlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'SourceCode'))
from quantumsafe import virtual_network, device_registry, secure_mesh

ADMIN={'RoleName':'Admin','Username':'Test Admin','UserId':1}

class FakeOutbox:
    def __init__(self):self.events=[];self.devices=[]
    def enqueue_event(self,e):self.events.append(dict(e))
    def stage_device(self,x):self.devices.append(dict(x))
    def stage_inventory(self,items):self.devices+=list(items)
    def start(self):pass
    def stop(self):pass


def _k():
    seed=os.urandom(32)
    return seed,seed

def _e(pk):
    c=os.urandom(32)
    return c,hashlib.sha256(pk+c).digest()

def _d(sk,c):
    return hashlib.sha256(sk+c).digest()


def test_crypto_events_are_logged_without_plaintext_or_private_keys(tmp_path,monkeypatch):
    monkeypatch.setattr(virtual_network,'DeviceRegistry',lambda:device_registry.DeviceRegistry(tmp_path/'devices.json'))
    monkeypatch.setattr(virtual_network,'SqlSync',FakeOutbox)
    monkeypatch.setattr(secure_mesh.crypto_engine,'make_keys',lambda _: _k())
    monkeypatch.setattr(secure_mesh.crypto_engine,'encapsulate',lambda _,pub:_e(pub))
    monkeypatch.setattr(secure_mesh.crypto_engine,'decapsulate',lambda _,sk,ct:_d(sk,ct))
    g=virtual_network.VirtualGateway()
    g.start(port=0)
    try:
        r=g.secure_device_message('virtual-cctv-01','virtual-sensor-01','TEST-SECRET-123',scenario='normal')
        assert r['decision']=='ALLOW' and r['delivered_text']=='TEST-SECRET-123'
        assert r['kem_ciphertext_bytes']>0 and r['ciphertext_bytes']>0
        stored=g.sql_sync.events[-1]
        assert stored['request_type']=='encrypted_mesh' and stored['crypto_verified']
        assert stored['crypto_algorithm']=='ML-KEM-768'
        assert 'TEST-SECRET-123' not in repr(stored)
        assert 'secret_key' not in repr(stored)
        assert 'kem_ciphertext' not in stored
        tampered=g.secure_device_message('virtual-cctv-01','virtual-sensor-01','TEST-SECRET-123',scenario='tamper')
        assert tampered['decision']=='BLOCK' and not tampered['receiver_opened']
        replayed=g.secure_device_message('virtual-cctv-01','virtual-sensor-01','TEST-SECRET-123',scenario='replay')
        assert replayed['decision']=='BLOCK' and replayed['first_delivery']
        g.manage_device('disable','virtual-sensor-01',ADMIN)
        assert 'virtual-sensor-01' not in g.secure_mesh._agents
        denied=g.secure_device_message('virtual-cctv-01','virtual-sensor-01','TEST-SECRET-123')
        assert denied['decision']=='BLOCK'
    finally:
        g.stop()
