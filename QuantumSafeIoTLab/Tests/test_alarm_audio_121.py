"""Regression checks for Windows winsound without SND_SYNC."""
import sys
import types
import unittest
from unittest.mock import patch
from quantumsafe.realtime_alarm import _windows_player, AlarmEngine, should_alarm

class AlarmAudioTests(unittest.TestCase):
    def test_missing_snd_sync_supported(self):
        calls=[]
        fake=types.SimpleNamespace(SND_ALIAS=0x10000, PlaySound=lambda name,flags: calls.append((name,flags)), Beep=lambda hz,ms: calls.append(('beep',hz)))
        with patch.object(sys,'platform','win32'), patch.dict(sys.modules,{'winsound':fake}):
            self.assertTrue(_windows_player({}))
        self.assertEqual(calls[0],('SystemExclamation',fake.SND_ALIAS))
        self.assertEqual(sum(1 for call in calls if call[0]=='beep'),3)

    def test_system_sound_failure_falls_back_to_beep(self):
        beeps=[]
        def fail(name,flags): raise RuntimeError('system alias disabled')
        fake=types.SimpleNamespace(SND_ALIAS=0x10000, PlaySound=fail, Beep=lambda hz,ms: beeps.append(hz))
        with patch.object(sys,'platform','win32'), patch.dict(sys.modules,{'winsound':fake}):
            self.assertTrue(_windows_player({}))
        self.assertEqual(len(beeps),3)

    def test_allow_event_never_alarms(self):
        self.assertFalse(should_alarm({'source':'LOCAL_HTTP','decision':'ALLOW','reason':'Invalid gateway token'}))

    def test_blocked_attack_deduplicated(self):
        engine=AlarmEngine(player=lambda e: True)
        event={'source':'LOCAL_HTTP','decision':'BLOCK','reason':'Invalid gateway token','event_id':'first-attack'}
        self.assertTrue(engine.notify(event))
        self.assertFalse(engine.notify(event))
        engine._queue.join()
        self.assertEqual(engine.played,1)

if __name__=='__main__': unittest.main()
