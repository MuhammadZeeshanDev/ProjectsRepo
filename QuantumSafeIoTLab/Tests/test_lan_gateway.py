"""Genuine HTTP localhost requests with deterministic fake ML-KEM adapter.

These test protocol logic and network flow but NOT real ML-KEM math. The
existing test_real_crypto_optional.py uses actual pqcrypto if installed.
"""
import socket
import pytest
from quantumsafe import crypto_engine, lan_client, lan_protocol as p
from quantumsafe.lan_gateway_core import Gateway, SESSION_TTL_SEC
from quantumsafe.lan_gateway import GatewayController


@pytest.fixture
def fake_kem(monkeypatch):
    monkeypatch.setattr(crypto_engine, 'make_keys', lambda algorithm: (b'public-key', b'private-key'))
    monkeypatch.setattr(crypto_engine, 'encapsulate', lambda algorithm, pk: (b'kem-ct', b'S' * 32))
    monkeypatch.setattr(crypto_engine, 'decapsulate', lambda algorithm, sk, ct: b'S' * 32)


@pytest.fixture
def listener(fake_kem):
    secret = p.generate_secret()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    c = GatewayController()
    c.start(secret, port=port, allow_lan=False)
    yield '127.0.0.1', port, secret, c
    c.stop()


def test_local_network_health_and_valid_delivery(listener):
    host, port, secret, controller = listener
    assert lan_client.check_gateway(host, port)
    result = lan_client.send_case(host, port, secret, 'ML-KEM-512', 26, 'normal')
    assert result['passed'], result
    assert controller.gateway.snapshot()['counts']['MESSAGE_ACCEPTED'] == 1


@pytest.mark.parametrize('scenario,event', [
    ('tamper', 'TAMPER_OR_INVALID'),
    ('replay', 'REPLAY_BLOCKED'),
    ('unauthorized', 'UNAUTHORIZED'),
])
def test_attack_scenarios_are_rejected(listener, scenario, event):
    host, port, secret, controller = listener
    result = lan_client.send_case(host, port, secret, 'ML-KEM-768', 23, scenario)
    assert result['passed'], result
    assert controller.gateway.snapshot()['counts'][event] == 1


def test_key_substitution_detected_before_network_send(listener):
    host, port, secret, controller = listener
    result = lan_client.send_case(host, port, secret, 'ML-KEM-1024', 23, 'key_swap')
    assert result['passed'], result
    assert controller.gateway.snapshot()['counts'].get('MESSAGE_ACCEPTED', 0) == 0


def test_wrong_secret_is_rejected_by_sender(listener):
    host, port, secret, _ = listener
    result = lan_client.send_case(host, port, p.generate_secret(), 'ML-KEM-512', 20)
    assert not result['passed']
    assert 'Untrusted' in result['details']


def test_gateway_rejects_unknown_algorithm(fake_kem):
    gateway = Gateway(p.generate_secret())
    status, _ = gateway.hello('RSA-unsafe')
    assert status == 400


def test_handshake_expires(fake_kem):
    clock = [10.0]
    gateway = Gateway(p.generate_secret(), clock=lambda: clock[0])
    status, hello = gateway.hello('ML-KEM-512')
    assert status == 200
    clock[0] += SESSION_TTL_SEC + 1
    assert gateway.deliver({'id': hello['id']})[0] == 404


def test_start_stop_is_explicit(listener):
    host, port, secret, controller = listener
    assert controller.running
    controller.stop()
    assert not controller.running
    with pytest.raises(lan_client.PeerError):
        lan_client.check_gateway(host, port)
