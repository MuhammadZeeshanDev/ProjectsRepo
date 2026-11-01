from datetime import datetime, timedelta, timezone
from quantumsafe.device_connections import connection_rows, unknown_attempts

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
DEV = {'camera': 'Camera', 'sensor': 'Sensor'}
def evt(device, decision, seconds=0, source='LOCAL_HTTP'):
    return {'device':device, 'decision':decision, 'source':source,
            'timestamp_utc':(NOW-timedelta(seconds=seconds)).isoformat()}

def test_only_authenticated_allow_counts_as_active():
    rows=connection_rows([evt('camera','BLOCK'),evt('sensor','ALLOW')],DEV,now=NOW)
    assert rows[0]['Connection observation']=='NOT OBSERVED'
    assert rows[1]['Connection observation']=='ACTIVE (observed)'

def test_idle_and_never_observed():
    rows=connection_rows([evt('camera','ALLOW',90)],DEV,now=NOW)
    assert rows[0]['Connection observation']=='IDLE (last seen)'
    assert rows[1]['Connection observation']=='NOT OBSERVED'

def test_unknown_device_is_not_registered():
    events=[evt('intruder','BLOCK'),evt('camera','ALLOW')]
    assert len(unknown_attempts(events,DEV))==1

def test_malformed_timestamp_does_not_crash():
    e=evt('camera','ALLOW');e['timestamp_utc']='not-a-date'
    assert connection_rows([e],DEV,now=NOW)[0]['Connection observation']=='NOT OBSERVED'

def test_non_http_events_do_not_fake_connection():
    assert connection_rows([evt('camera','ALLOW',source='MANUAL_CONTENT_RULES')],DEV,now=NOW)[0]['Connection observation']=='NOT OBSERVED'
