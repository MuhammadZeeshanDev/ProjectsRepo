"""Regression tests for analytics list crash and SQL Server durable mirroring."""
import importlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest
from quantumsafe import analytics_data, gateway_event_store
from quantumsafe.sql_sync import SqlSync
from quantumsafe.virtual_network import VirtualGateway


def _event(uid='evt123', decision='ALLOW', reading=42.0):
    return {'event_id':uid,'timestamp_utc':'2026-11-02T14:00:00Z',
            'device':'virtual-sensor-01','decision':decision,'reason':'Authenticated',
            'source':'LOCAL_HTTP','request_type':'telemetry','source_ip':'127.0.0.1',
            'reading':reading,'identity_verified':decision=='ALLOW'}


def test_analytics_iterable_regression():
    rows=[dict(time_utc=i) for i in range(250)]
    rev=analytics_data.newest_rows({'rows':rows}, 200)
    assert [r['time_utc'] for r in rev] == list(range(249,49,-1))
    assert len(rows)==250
    assert analytics_data.newest_rows({'rows':[]}) == []
    assert analytics_data.newest_rows({'rows':rows},0)==[]


def test_sql_queue_saves_and_reopens(tmp_path):
    events=[];devices=[]
    p=tmp_path/'outbox.sqlite3'
    q=SqlSync(p,event_writer=lambda e: events.append(e) or True,
              device_writer=lambda d: devices.append(d) or True)
    q.enqueue_event(_event())
    q.stage_device({'id':'virtual-sensor-01','name':'Device','type':'Sensor','status':'active',
                    'virtual_ip':'192.168.10.4','key_hex':'SECRET','token':'PRIVATE'})
    assert q.pending_counts()=={'events':1,'devices':1}
    reopened=SqlSync(p,event_writer=lambda e: events.append(e) or True,
                     device_writer=lambda d: devices.append(d) or True)
    assert reopened.flush_once() == 2
    assert reopened.pending_counts()=={'events':0,'devices':0}
    assert events[0]['reading']==42.0
    assert 'key_hex' not in devices[0] and 'token' not in devices[0]


def test_transient_sql_failure_preserves_durable_queue(tmp_path):
    p=tmp_path/'outbox.sqlite3'
    def fail(_):raise ConnectionError('SQL Server offline')
    q=SqlSync(p,event_writer=fail,device_writer=lambda _:True)
    q.enqueue_event(_event())
    assert q.flush_once()==0
    assert q.pending_counts()['events']==1
    assert 'SQL Server offline' in q.last_error
    captured=[]
    fixed=SqlSync(p,event_writer=lambda e: captured.append(e) or True,
                  device_writer=lambda _:True)
    assert fixed.flush_once()==1
    assert fixed.pending_counts()['events']==0
    assert captured[0]['event_id']=='evt123'


def test_device_update_replaces_pending_before_sync(tmp_path):
    items=[]
    q=SqlSync(tmp_path/'queue.db',device_writer=lambda d:items.append(d) or True)
    q.stage_device({'id':'dev-x','name':'X','type':'Sensor','status':'active'})
    q.stage_device({'id':'dev-x','name':'X','type':'Sensor','status':'disabled'})
    assert q.pending_counts()['devices']==1
    assert q.flush_once()==1
    assert items[0]['status']=='disabled'


def test_sql_event_writer_payload_and_duplicate_uid(monkeypatch):
    calls=[]
    class Cursor:
        def execute(self, sql, *args):
            calls.append((sql,args))
            return self
    class Conn:
        def cursor(self):return Cursor()
    from contextlib import contextmanager
    @contextmanager
    def fake_connection():yield Conn()
    monkeypatch.setattr(gateway_event_store,'initialize',lambda:True)
    monkeypatch.setattr(gateway_event_store,'connection',fake_connection)
    assert gateway_event_store.insert_event(_event('a123',reading=18.5))
    query, args=calls[0]
    assert query.count('?')==16
    assert args.count('a123')==3
    assert 18.5 in args
    assert isinstance(args[0],datetime) and args[0].tzinfo is None


def test_gateway_autowires_local_outbox_not_blocking_sql(monkeypatch,tmp_path):
    from quantumsafe import virtual_network
    queued=[]
    class FakeQueue:
        def __init__(self):pass
        def enqueue_event(self,item):queued.append(item)
        def stage_inventory(self,items):pass
        def stage_device(self,item):pass
        def start(self):pass
    monkeypatch.setattr(virtual_network,'SqlSync',FakeQueue)
    g=VirtualGateway()
    try:
        g.start(port=0)
        assert g.send('Sensor')['decision']=='ALLOW'
        assert queued and queued[0]['decision']=='ALLOW'
        assert g.send('Unauthorized access')['decision']=='BLOCK'
        assert queued[-1]['decision']=='BLOCK'
    finally:g.stop()


def test_schema_does_not_embed_device_secrets():
    src=(Path(__file__).resolve().parents[1]/'SourceCode'/'quantumsafe'/'gateway_event_store.py').read_text()
    assert 'VirtualDeviceInventory' in src
    assert 'GatewayEventUid' in src
    assert 'key_hex' not in src
    assert 'device_token' not in src
