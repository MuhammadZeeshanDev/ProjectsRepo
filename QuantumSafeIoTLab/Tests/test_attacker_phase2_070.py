"""Controlled local integration checks; no SQL Server required."""
import pytest
from quantumsafe.virtual_network import VirtualGateway
from quantumsafe.attacker_client import send_test

def test_independent_client_rejected_and_logged():
    gateway = VirtualGateway()
    gateway.start(port=0)
    try:
        event = send_test('unauthorized', port=gateway.port)[0]
        assert event['decision'] == 'BLOCK'
        assert event['reason'] == 'Invalid device token'
        assert gateway.events[0]['source_ip'] == '127.0.0.1'
    finally:
        gateway.stop()

def test_repeated_unauthorized_is_bounded():
    gateway = VirtualGateway()
    gateway.start(port=0)
    try:
        result = send_test('repeated_unauthorized', port=gateway.port)
        assert len(result) == 5
        assert all(e['decision'] == 'BLOCK' for e in result)
    finally:
        gateway.stop()

def test_client_rejects_unknown_scenarios():
    with pytest.raises(ValueError):
        send_test('arbitrary_request')
