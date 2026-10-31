"""Gateway handshake, message integrity, replay and event state."""
from collections import Counter, deque
from datetime import datetime, timezone
import json
import secrets
import threading
import time
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from . import crypto_engine, lan_protocol as p
from .sensor_demo import _derive_key

SESSION_TTL_SEC = 120
MAX_SESSIONS = 200


class Gateway:
    """RAM-only sessions (expire after 120 seconds)."""

    def __init__(self, shared_secret, event_sink=None, clock=None):
        p.check_secret(shared_secret)
        self._secret = shared_secret
        self._sessions = {}
        self._lock = threading.RLock()
        self._clock = clock or time.monotonic
        self._events = deque(maxlen=100)
        self._counts = Counter()
        self._sink = event_sink

    def _event(self, event, outcome, source_ip, algorithm=None):
        item = {'event': event, 'outcome': outcome, 'source_ip': source_ip[:64],
                'algorithm': algorithm, 'timestamp_utc': datetime.now(timezone.utc).isoformat()}
        with self._lock:
            self._counts[event] += 1
            self._events.appendleft(item)
        if self._sink:
            try:
                self._sink(item)  # DB logging failure never breaks packet integrity checks.
            except Exception:
                pass

    def snapshot(self):
        with self._lock:
            return {'counts': dict(self._counts), 'events': list(self._events),
                    'open_handshakes': sum(not s['used'] for s in self._sessions.values())}

    def _cleanup(self):
        now = self._clock()
        expired = [key for key, session in self._sessions.items()
                   if now - session['created'] > SESSION_TTL_SEC]
        for key in expired:
            del self._sessions[key]

    def hello(self, algorithm, source_ip='local'):
        if algorithm not in crypto_engine.ALGORITHMS:
            return 400, {'error': 'Unsupported ML-KEM algorithm.'}
        with self._lock:
            self._cleanup()
            if len(self._sessions) >= MAX_SESSIONS:
                return 429, {'error': 'Too many outstanding lab sessions.'}
            public_key, private_key = crypto_engine.make_keys(algorithm)
            session_id, salt = secrets.token_hex(16), secrets.token_bytes(16)
            self._sessions[session_id] = {
                'algorithm': algorithm, 'private_key': private_key,
                'salt': salt, 'created': self._clock(), 'used': False
            }
        response = {'id': session_id, 'algorithm': algorithm,
                    'public_key': p.encode(public_key), 'salt': p.encode(salt)}
        response['gateway_proof'] = p.proof(self._secret, 'gateway', p.gateway_fields(response))
        self._event('HANDSHAKE', 'Accepted', source_ip, algorithm)
        return 200, response

    def deliver(self, packet, source_ip='local'):
        if not isinstance(packet, dict) or not isinstance(packet.get('id'), str):
            return 400, {'error': 'Malformed request.'}
        session_id = packet['id']
        with self._lock:
            self._cleanup()
            session = self._sessions.get(session_id)
            if session is None:
                return 404, {'error': 'Session unknown or expired.'}
            algorithm = session['algorithm']
            if session['used']:
                self._event('REPLAY_BLOCKED', 'Rejected', source_ip, algorithm)
                return self._receipt(session_id, False, 'Replay blocked', 409)
            try:
                fields = p.sender_fields(packet)
                auth_ok = p.verify(self._secret, 'sender', fields, packet.get('sender_proof'))
            except (KeyError, ValueError, TypeError):
                auth_ok = False
            if not auth_ok:
                self._event('UNAUTHORIZED', 'Rejected', source_ip, algorithm)
                return self._receipt(session_id, False, 'Sender authentication failed', 403)
            # Consume this one-time handshake BEFORE decoding or decrypting data.
            session['used'] = True
            private_key, salt = session['private_key'], session['salt']
            session['private_key'] = None  # Release private material immediately.
        try:
            kem_ct = p.decode(packet['kem_ciphertext'])
            nonce = p.decode(packet['nonce'], 12)
            ciphertext = p.decode(packet['encrypted'], 1024)
            if len(nonce) != 12 or len(ciphertext) < 16:
                raise ValueError('Invalid AEAD message.')
            secret = crypto_engine.decapsulate(algorithm, private_key, kem_ct)
            aad = (p.PROTOCOL + '|' + session_id + '|' + algorithm).encode('ascii')
            opened = AESGCM(_derive_key(secret, salt, algorithm)).decrypt(nonce, ciphertext, aad)
            message = json.loads(opened.decode('utf-8'))
            if (not isinstance(message, dict) or message.get('type') != 'temperature'
                    or type(message.get('celsius')) not in (int, float)
                    or not -50 <= message['celsius'] <= 150):
                raise ValueError('Invalid sensor data.')
        except (InvalidTag, ValueError, TypeError, KeyError, UnicodeError, RuntimeError):
            self._event('TAMPER_OR_INVALID', 'Rejected', source_ip, algorithm)
            return self._receipt(session_id, False, 'Invalid encrypted message', 422)
        self._event('MESSAGE_ACCEPTED', 'Accepted', source_ip, algorithm)
        # No raw sensor value is saved to SQL. The response is authenticated.
        return self._receipt(session_id, True, 'Secure reading accepted', 200)

    def _receipt(self, session_id, accepted, reason, status):
        receipt = {'id': session_id, 'accepted': accepted, 'reason': reason}
        receipt['gateway_proof'] = p.proof(self._secret, 'receipt', p.receipt_fields(receipt))
        return status, receipt

