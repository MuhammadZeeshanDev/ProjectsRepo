"""Client for a separate laptop: actual LAN requests, ML-KEM and AEAD."""
import json
import os
from urllib import error, request

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from . import crypto_engine, lan_protocol as p
from .sensor_demo import _derive_key


class PeerError(RuntimeError):
    pass


def server_url(host, port) -> str:
    # Allow IP addresses or simple LAN DNS names; reject URLs and injection.
    if not isinstance(host, str) or not 1 <= len(host) <= 253 or any(
        ch not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-'
        for ch in host
    ) or '..' in host or host.startswith('-') or host.endswith('-'):
        raise ValueError('Enter an IP address or computer name, not a URL.')
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError('Port must be 1024–65535.')
    return f'http://{host}:{port}'


def _json_request(url, path, payload=None):
    if payload is None:
        req = request.Request(url + path)
    else:
        body = json.dumps(payload).encode('utf-8')
        req = request.Request(url + path, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read(20_000))
    except error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read(20_000))
        except (ValueError, UnicodeDecodeError):
            raise PeerError(f'Gateway sent HTTP {exc.code}.') from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        raise PeerError('Cannot reach gateway. Check its IP, LAN switch, port and private Windows firewall.') from exc


def check_gateway(host, port):
    status, info = _json_request(server_url(host, port), '/health')
    return status == 200 and info.get('service') == p.PROTOCOL


def _prepare(host, port, secret, algorithm, temperature, scenario):
    p.check_secret(secret)
    if algorithm not in crypto_engine.ALGORITHMS:
        raise ValueError('Unsupported algorithm.')
    if not -50 <= temperature <= 150:
        raise ValueError('Temperature must be between -50 and 150°C.')
    url = server_url(host, port)
    status, hello = _json_request(url, '/hello', {'algorithm': algorithm})
    if status != 200:
        raise PeerError(hello.get('error', 'Gateway refused the handshake.'))
    fields = p.gateway_fields(hello)
    if scenario == 'key_swap':
        # Controlled simulation of an attacker replacing gateway's public key.
        fields['public_key'] = p.encode(os.urandom(len(p.decode(fields['public_key']))))
    if not p.verify(secret, 'gateway', fields, hello.get('gateway_proof')):
        return None, url, 'BLOCKED: Untrusted or substituted gateway key.'
    public_key = p.decode(fields['public_key'])
    salt = p.decode(hello['salt'], 16)
    kem_ct, shared = crypto_engine.encapsulate(algorithm, public_key)
    nonce = os.urandom(12)
    aad = (p.PROTOCOL + '|' + hello['id'] + '|' + algorithm).encode('ascii')
    message = json.dumps({'type': 'temperature', 'celsius': float(temperature)}).encode('utf-8')
    encrypted = AESGCM(_derive_key(shared, salt, algorithm)).encrypt(nonce, message, aad)
    if scenario == 'tamper':
        altered = bytearray(encrypted)
        altered[-1] ^= 1
        encrypted = bytes(altered)
    packet = {'id': hello['id'], 'kem_ciphertext': p.encode(kem_ct),
              'nonce': p.encode(nonce), 'encrypted': p.encode(encrypted)}
    proof_secret = ('incorrect-secret-' + secret) if scenario == 'unauthorized' else secret
    packet['sender_proof'] = p.proof(proof_secret, 'sender', p.sender_fields(packet))
    return packet, url, None


def send_case(host, port, secret, algorithm, temperature, scenario='normal'):
    """Runs ONE chosen UI scenario and checks the expected security result."""
    if scenario not in ('normal', 'tamper', 'replay', 'unauthorized', 'key_swap'):
        raise ValueError('Invalid test scenario.')
    packet, url, block = _prepare(host, port, secret, algorithm, temperature, scenario)
    if block:
        return {'scenario': scenario, 'passed': scenario == 'key_swap', 'details': block,
                'http_status': None}
    status, receipt = _json_request(url, '/deliver', packet)
    if not p.verify(secret, 'receipt', p.receipt_fields(receipt), receipt.get('gateway_proof')):
        raise PeerError('Gateway receipt was not authenticated. Do not trust the response.')
    if scenario == 'replay':
        # Send the *exact same* encrypted packet twice.
        second_status, second = _json_request(url, '/deliver', packet)
        if not p.verify(secret, 'receipt', p.receipt_fields(second), second.get('gateway_proof')):
            raise PeerError('Replay response was not authenticated.')
        passed = (status == 200 and receipt['accepted'] and
                  second_status == 409 and not second['accepted'])
        detail = f"First delivery: {receipt['reason']}; second delivery: {second['reason']}"
        return {'scenario': scenario, 'passed': bool(passed), 'details': detail,
                'http_status': second_status}
    expected = {'normal': (200, True), 'tamper': (422, False),
                'unauthorized': (403, False)}[scenario]
    passed = (status, receipt['accepted']) == expected
    return {'scenario': scenario, 'passed': passed, 'details': receipt['reason'],
            'http_status': status}
