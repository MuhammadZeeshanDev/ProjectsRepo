"""Tests for authentication and input bounds; no network required."""
import pytest
from quantumsafe import lan_protocol as p, lan_client


def test_generated_secret_has_enough_entropy():
    a, b = p.generate_secret(), p.generate_secret()
    assert a != b
    p.check_secret(a)
    with pytest.raises(ValueError):
        p.check_secret('short')


def test_hmac_covers_critical_key_fields():
    secret = p.generate_secret()
    fields = {'id': 'a', 'algorithm': 'ML-KEM-512', 'public_key': 'abc', 'salt': 'def'}
    mac = p.proof(secret, 'gateway', fields)
    assert p.verify(secret, 'gateway', fields, mac)
    assert not p.verify(secret, 'gateway', dict(fields, public_key='changed'), mac)
    assert not p.verify(secret, 'sender', fields, mac)


def test_input_validation_rejects_oversize_or_bad_base64():
    with pytest.raises(ValueError):
        p.decode('not base64 !!!')
    with pytest.raises(ValueError):
        p.decode(p.encode(b'A' * 30), max_size=20)


@pytest.mark.parametrize('name', ['http://evil.com', '127.0.0.1:80',
                                  'localhost/path', '', 'abc..def'])
def test_only_ip_or_simple_hostnames(name):
    with pytest.raises(ValueError):
        lan_client.server_url(name, 8765)
