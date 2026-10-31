from datetime import datetime
from quantumsafe import gateway_event_store as store

def test_sql_event_store_surface():
    assert callable(store.initialize)
    assert callable(store.is_initialized)
    assert callable(store.insert_event)
    assert callable(store.recent_events)
    assert callable(store.counts)

def test_datetime_parsing():
    stamp = datetime.fromisoformat('2026-10-31T12:00:00+00:00')
    assert stamp.utcoffset().total_seconds() == 0
