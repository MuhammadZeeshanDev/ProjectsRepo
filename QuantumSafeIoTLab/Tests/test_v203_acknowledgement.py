"""Regressions for durable alert acknowledge and protected live viewer."""
from collections import deque
from datetime import datetime, timezone
from threading import RLock
import uuid
from unittest.mock import patch

import pytest
from quantumsafe import console_data
from quantumsafe.virtual_network import VirtualGateway


class Registry:
    def inventory(self):
        return [{'id':'cam-01','name':'Camera','type':'Camera','status':'active','virtual_ip':'10.0.0.2'}]


class DummyGateway:
    def __init__(self, events):
        self.server=object()
        self.events=deque(events)
        self.registry=Registry()
        self.lock=RLock()


def block(uid=None):
    return {'event_id':uid or uuid.uuid4().hex,
            'timestamp_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'device':'cam-01', 'decision':'BLOCK', 'reason':'Invalid gateway token',
            'request_type':'telemetry','source_ip':'127.0.0.1'}


def test_acknowledge_stays_visible_in_gateway_viewer(tmp_path, monkeypatch):
    alert = block()
    gw = DummyGateway([alert])
    db=tmp_path/'ack.sqlite3'
    monkeypatch.setattr(console_data, 'ACK_DB', db)
    from quantumsafe import gateway_event_store
    monkeypatch.setattr(gateway_event_store, 'is_initialized', lambda:False)
    uid=console_data.snapshot(gw)['alerts'][0]['id']
    assert not VirtualGateway.viewer_state(gw)['alerts'][0]['acknowledged']
    console_data.acknowledge(uid,{'RoleName':'Admin','Username':'Tester'})
    # The exact live /viewer/.../state pathway used to pass an empty ack set.
    assert VirtualGateway.viewer_state(gw)['alerts'][0]['acknowledged']
    # Cached or restarted gateway processes must still read durable status.
    fresh=DummyGateway([alert])
    assert VirtualGateway.viewer_state(fresh)['alerts'][0]['acknowledged']


def test_ack_id_is_stable_when_mirrored_into_sql(tmp_path):
    alert=block()
    local_id=console_data.merge_events([alert])[0]['console_uid']
    sql=dict(alert,timestamp_utc=alert['timestamp_utc'].replace('+00:00','Z'),sql_event_id=300)
    merged=console_data.merge_events([alert],[sql])
    assert len(merged)==1
    assert merged[0]['console_uid']==local_id
    db=tmp_path/'ack.sqlite3'
    console_data.acknowledge(local_id,{'RoleName':'Admin','Username':'Tester'},db)
    assert console_data.snapshot(DummyGateway([]),[sql],console_data.acked_uids(db))['alerts'][0]['acknowledged']


def test_two_events_same_second_receive_unique_ids(tmp_path):
    a,b=block(),block()
    assert console_data.identity(a)==console_data.identity(b)
    uids={x['console_uid'] for x in console_data.merge_events([a,b])}
    assert len(uids)==2
    # Even if one more is SQL mirrored, old event IDs must not shift.
    mirror=dict(a,sql_event_id=123)
    uids_mirrored={x['console_uid'] for x in console_data.merge_events([a,b],[mirror])}
    assert uids_mirrored==uids


def test_legacy_ack_uid_still_accepted():
    event=block();gw=DummyGateway([event])
    item=console_data.merge_events([event])[0]
    assert item['console_uid']!=item['legacy_console_uid']
    assert console_data.snapshot(gw,acked={item['legacy_console_uid']})['alerts'][0]['acknowledged']


def test_operator_cannot_ack(tmp_path):
    with pytest.raises(PermissionError):
        console_data.acknowledge('a'*24,{'RoleName':'Researcher'},tmp_path/'a.sqlite3')


def test_live_viewer_with_sql_failure_keeps_ack(tmp_path, monkeypatch):
    alert=block();gw=DummyGateway([alert]);db=tmp_path/'ack.sqlite3'
    monkeypatch.setattr(console_data, 'ACK_DB', db)
    uid=console_data.merge_events([alert])[0]['console_uid']
    console_data.acknowledge(uid,{'RoleName':'Admin','Username':'Tester'})
    from quantumsafe import gateway_event_store
    def fail():raise RuntimeError('SQL temporarily unavailable')
    monkeypatch.setattr(gateway_event_store,'is_initialized',fail)
    assert VirtualGateway.viewer_state(gw)['alerts'][0]['acknowledged']


def test_sql_sync_does_not_reidentify_events_when_order_changes():
    older=block();newer=block()
    local=[newer,older]  # gateway deque: newest first
    sql=[dict(older,sql_event_id=91)]  # async SQL writer saved oldest first
    original={x['console_uid'] for x in console_data.merge_events(local)}
    after={x['console_uid'] for x in console_data.merge_events(local,sql)}
    assert original==after
    assert len(after)==2
