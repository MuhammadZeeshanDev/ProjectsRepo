import unittest
from datetime import datetime, timezone
from quantumsafe.pakistan_time import display
from quantumsafe.realtime_alarm import should_alarm, AlarmEngine
from quantumsafe.virtual_network import VirtualGateway

class Major090(unittest.TestCase):
    def test_pkt(self):
        self.assertEqual(display('2026-11-02T00:00:00Z'), '02-11-2026 05:00:00')
    def test_utc_aware(self):
        self.assertEqual(display(datetime(2026,11,2,0,0,tzinfo=timezone.utc)), '02-11-2026 05:00:00')
    def test_normal_no_alarm(self):
        self.assertFalse(should_alarm(dict(source='LOCAL_HTTP', decision='ALLOW',reason='Authenticated and integrity verified')))
    def test_unknown_only_no_alarm(self):
        self.assertFalse(should_alarm(dict(source='LOCAL_HTTP',decision='BLOCK',reason='Device is not registered')))
    def test_first_attack_and_dedupe(self):
        played=[]
        engine=AlarmEngine(player=lambda event: played.append(event['event_id']))
        e=dict(event_id='first',source='LOCAL_HTTP',decision='BLOCK',reason='Invalid gateway token')
        self.assertTrue(engine.notify(e))
        self.assertFalse(engine.notify(e))
        engine._queue.join()
        self.assertEqual(played,['first'])
    def test_ten_normal_zero_one_attack_one(self):
        played=[]
        engine=AlarmEngine(player=lambda event: played.append(event['event_id']))
        for i in range(10):
            self.assertFalse(engine.notify(dict(event_id=str(i),source='LOCAL_HTTP',decision='ALLOW',reason='Authenticated and integrity verified')))
        self.assertTrue(engine.notify(dict(event_id='attack',source='LOCAL_HTTP',decision='BLOCK',reason='Message integrity check failed')))
        engine._queue.join()
        self.assertEqual(played,['attack'])
    def test_real_gateway_first_block(self):
        gateway=VirtualGateway()
        seen=[]
        gateway.alarm_engine.player=lambda e:seen.append(e['event_id'])
        event=gateway.evaluate({'device':'virtual-cctv-01','nonce':'n','value':42,'token':'invalid'},source_ip='127.0.0.1')
        gateway.alarm_engine._queue.join()
        self.assertEqual(event['decision'],'BLOCK')
        self.assertEqual(len(seen),1)
    def test_impersonation_alarm(self):
        self.assertTrue(should_alarm(dict(source='LOCAL_HTTP',decision='BLOCK',reason='Invalid per-device credential')))
    def test_replay_alarm(self):
        self.assertTrue(should_alarm(dict(source='LOCAL_HTTP',decision='BLOCK',reason='Replay nonce detected')))

if __name__=='__main__': unittest.main()
