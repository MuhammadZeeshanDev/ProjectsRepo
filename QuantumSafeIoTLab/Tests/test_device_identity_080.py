import unittest
from quantumsafe.virtual_network import VirtualGateway

class DeviceIdentityTests(unittest.TestCase):
    def setUp(self): self.g = VirtualGateway()
    def payload(self, device='virtual-cctv-01'):
        p={'device':device,'nonce':'unique-123','value':42,'token':self.g.token,'device_token':self.g.device_tokens[device]}
        p['signature']=self.g.sign(device,p['nonce'],p['value'])
        return p
    def test_valid_device(self): self.assertEqual(self.g.evaluate(self.payload())['decision'],'ALLOW')
    def test_missing_device_credential(self):
        p=self.payload();p.pop('device_token');self.assertEqual(self.g.evaluate(p)['reason'],'Invalid per-device credential')
    def test_cross_device_credential(self):
        p=self.payload();p['device_token']=self.g.device_tokens['virtual-router-01'];self.assertEqual(self.g.evaluate(p)['decision'],'BLOCK')
    def test_cross_device_signature(self):
        p=self.payload();p['signature']=self.g.sign('virtual-router-01',p['nonce'],p['value']);self.assertEqual(self.g.evaluate(p)['decision'],'BLOCK')
    def test_replay(self):
        p=self.payload();self.assertEqual(self.g.evaluate(p)['decision'],'ALLOW');self.assertEqual(self.g.evaluate(p)['reason'],'Replay nonce detected')
    def test_unknown(self):
        p=self.payload();p['device']='unknown';self.assertEqual(self.g.evaluate(p)['reason'],'Device is not registered')
    def test_normal_does_not_alarm(self):
        from quantumsafe.security_alerts import alarm_eligible
        self.assertFalse(alarm_eligible(self.g.evaluate(self.payload())))
    def test_block_does_alarm(self):
        from quantumsafe.security_alerts import alarm_eligible
        p=self.payload();p['device_token']='wrong';self.assertTrue(alarm_eligible(self.g.evaluate(p)))

if __name__=='__main__': unittest.main()
