"""Optional ACTUAL pqcrypto + localhost HTTP roundtrip; skips if not installed."""
import socket
import pytest
from quantumsafe import lan_client, lan_protocol as p
from quantumsafe.lan_gateway import GatewayController


def test_actual_mlkem_512_over_http_localhost_if_installed():
    pytest.importorskip('pqcrypto')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    c = GatewayController()
    secret = p.generate_secret()
    try:
        c.start(secret, port, False)
        for mode in ('normal', 'tamper', 'replay', 'unauthorized', 'key_swap'):
            result = lan_client.send_case('127.0.0.1', port, secret, 'ML-KEM-512', 26.5, mode)
            assert result['passed'], result
    finally:
        c.stop()
