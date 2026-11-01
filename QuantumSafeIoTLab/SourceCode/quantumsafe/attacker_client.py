"""Credential-free, localhost-only security test client. Not a general attack tool."""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

PORT = 8765
TESTS = {
    'unauthorized': 'Unknown client without trusted token',
    'invalid_signature': 'Invalid integrity signature without device secret',
    'repeated_unauthorized': 'Five unauthorized attempts (bounded)',
}

def send_test(test, port=PORT):
    if test not in TESTS:
        raise ValueError('Unsupported lab test')
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('Invalid port')
    attempts = 5 if test == 'repeated_unauthorized' else 1
    results = []
    for i in range(attempts):
        payload = {
            'device': 'virtual-cctv-01',
            'nonce': f'attacker-attempt-{i}',
            'value': 42,
            'token': 'not-a-trusted-token',
            'signature': '0' * 64,
        }
        if test == 'invalid_signature':
            payload['signature'] = 'bad-signature'
        request = Request(f'http://127.0.0.1:{port}/telemetry',
                          data=json.dumps(payload).encode('utf-8'),
                          headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urlopen(request, timeout=3) as response:
                results.append(json.loads(response.read()))
        except HTTPError as exc:
            if exc.code != 403:
                raise
            results.append(json.loads(exc.read()))
        except URLError as exc:
            raise ConnectionError('Start the defender gateway on port 8765 first') from exc
    return results
