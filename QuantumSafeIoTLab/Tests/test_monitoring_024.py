"""Sanity checks for v0.2.4 live monitoring event format."""
from quantumsafe.virtual_network import VirtualGateway

def test_monitoring_event_snapshot():
    gateway = VirtualGateway()
    try:
        gateway.start()
        assert gateway.send('CCTV')['decision'] == 'ALLOW'
        assert gateway.send('Unauthorized access')['decision'] == 'BLOCK'
        with gateway.lock:
            events = list(gateway.events)
        assert len(events) == 2
        assert events[0]['decision'] == 'BLOCK'
        assert all('timestamp_utc' in item and 'device' in item and 'reason' in item for item in events)
    finally:
        gateway.stop()
