import importlib.util
import pathlib
import threading
import time

spec = importlib.util.spec_from_file_location('realtime_alarm', pathlib.Path(__file__).resolve().parents[1] / 'SourceCode' / 'quantumsafe' / 'realtime_alarm.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def ev(i, reason='Invalid per-device credential', decision='BLOCK'):
    return {'event_id': str(i), 'reason': reason, 'decision': decision, 'source': 'LOCAL_HTTP'}


def test_threat_first_event_and_unique_events():
    hit = []
    a = m.AlarmEngine(player=lambda e: hit.append(e))
    assert a.notify(ev(1))
    assert not a.notify(ev(1))
    assert a.notify(ev(2, 'Replay nonce detected'))
    a._queue.join()
    assert len(hit) == 2
    assert a.total_alerts == 2 and a.played == 2


def test_normal_and_review_no_audio():
    a = m.AlarmEngine(player=lambda e: None)
    assert not a.notify(ev(1, decision='ALLOW'))
    assert not a.notify(ev(2, reason='Invalid telemetry'))
    assert not a.notify({'event_id':'3', 'reason':'Unknown link', 'decision':'REVIEW', 'source':'MANUAL_CONTENT_RULES'})
    assert a.total_alerts == 0


def test_unregistered_attempt_is_security_event():
    assert m.should_alarm(ev(3, reason='Device is not registered'))


def test_error_not_swallowed():
    def fail(_): raise RuntimeError('no speakers')
    a = m.AlarmEngine(player=fail)
    assert a.notify(ev(5))
    a._queue.join()
    assert a.failures == 1 and 'no speakers' in a.last_error


def test_manual_speaker_test_is_not_incident():
    seen = []
    a = m.AlarmEngine(player=lambda e: seen.append(e))
    assert a.test_sound()
    a._queue.join()
    assert a.total_alerts == 0 and seen == [{'_test': True}]
