"""Small, explicit LAN protocol helpers. No private keys enter SQL or logs."""
import base64
import hashlib
import hmac
import json
import secrets

PROTOCOL = 'QuantumSafeLAN/2'
MAX_BODY_BYTES = 20_000


def generate_secret() -> str:
    """Random 256-bit secret shared *out of band* between both computers."""
    return secrets.token_urlsafe(32)


def check_secret(secret: str) -> None:
    if not isinstance(secret, str) or len(secret) < 32 or len(secret) > 200:
        raise ValueError('Shared lab secret must contain at least 32 characters.')


def encode(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')


def decode(value: str, max_size=5000) -> bytes:
    if not isinstance(value, str) or len(value) > 4 * max_size:
        raise ValueError('Invalid encoded data.')
    try:
        result = base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError('Invalid Base64 data.') from exc
    if len(result) > max_size:
        raise ValueError('Encoded data is too large.')
    return result


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True).encode('ascii')


def proof(secret: str, label: str, fields: dict) -> str:
    check_secret(secret)
    message = PROTOCOL.encode('ascii') + b'|' + label.encode('ascii') + b'|' + _canonical(fields)
    return hmac.new(secret.encode('utf-8'), message, hashlib.sha256).hexdigest()


def verify(secret: str, label: str, fields: dict, given: str) -> bool:
    if not isinstance(given, str) or len(given) != 64:
        return False
    return hmac.compare_digest(proof(secret, label, fields), given)


def gateway_fields(hello: dict) -> dict:
    return {key: hello[key] for key in ('id', 'algorithm', 'public_key', 'salt')}


def sender_fields(packet: dict) -> dict:
    # Data ciphertext is authenticated by AES-GCM, not by this PSK proof.
    # This allows the tamper test to reach the actual GCM integrity check.
    return {key: packet[key] for key in ('id', 'kem_ciphertext')}


def receipt_fields(result: dict) -> dict:
    return {key: result[key] for key in ('id', 'accepted', 'reason')}
