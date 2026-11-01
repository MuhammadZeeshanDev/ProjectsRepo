from quantumsafe.virtual_network import VirtualGateway
from quantumsafe.permissions import may_run, may_manage_users

def test_device_registry():
    g=VirtualGateway()
    assert len(g.registered_devices)==3
    assert g.evaluate({'device':'unknown-99','nonce':'n','value':1,'token':g.token,'signature':'x'})['decision']=='BLOCK'

def test_trusted_device():
    g=VirtualGateway()
    p={'device':'virtual-cctv-01','nonce':'unique','value':22,'token':g.token}
    p['signature']=g.sign(p['device'],p['nonce'],p['value'])
    assert g.evaluate(p)['decision']=='ALLOW'

def test_role_boundaries():
    assert may_manage_users('Admin')
    assert not may_manage_users('Researcher')
    assert may_run('Researcher')
    assert not may_run('Viewer')
