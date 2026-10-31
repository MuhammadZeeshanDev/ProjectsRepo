"""Local (software-only) sensor -> gateway encrypted message demonstration."""
import os
from hmac import compare_digest

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from . import crypto_engine


def _derive_key(shared_secret: bytes, salt: bytes, algorithm: str) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(), length=32, salt=salt,
        info=("QuantumSafeIoTLab/v1/" + algorithm).encode("ascii"),
    ).derive(shared_secret)


def send_reading(algorithm: str, temperature: float, tamper: bool = False) -> dict:
    """A trusted gateway public key is assumed; MITM defense is out of scope."""
    if not -50 <= temperature <= 150:
        raise ValueError("Enter a sensor temperature between -50 and 150°C.")
    # The public key and the secret key live only in this function's memory.
    public_key, secret_key = crypto_engine.make_keys(algorithm)
    kem_ciphertext, sender_secret = crypto_engine.encapsulate(algorithm, public_key)
    gateway_secret = crypto_engine.decapsulate(algorithm, secret_key, kem_ciphertext)
    if not compare_digest(sender_secret, gateway_secret):
        raise RuntimeError("The gateway could not establish the shared secret.")

    salt, nonce = os.urandom(16), os.urandom(12)
    aad = ("sensor->gateway|" + algorithm).encode("ascii")
    message = f"Temperature: {temperature:.1f} °C".encode("utf-8")
    encrypted = AESGCM(_derive_key(sender_secret, salt, algorithm)).encrypt(
        nonce, message, aad
    )
    delivered = bytearray(encrypted)
    if tamper:
        delivered[-1] ^= 1  # Change the AES-GCM tag: integrity check must fail.
    try:
        opened = AESGCM(_derive_key(gateway_secret, salt, algorithm)).decrypt(
            nonce, bytes(delivered), aad
        )
        success = not tamper and opened == message
    except InvalidTag:
        success = bool(tamper)  # Rejected a deliberately corrupted message.
        opened = None

    if not success:
        raise RuntimeError("Secure communication correctness test failed.")
    return {
        "algorithm": algorithm,
        "tampered": tamper,
        "passed": success,
        "message": opened.decode("utf-8") if opened is not None else None,
        "outcome": "Tampered data rejected" if tamper else "Secure data received",
        "ciphertext_bytes": len(encrypted),
    }
