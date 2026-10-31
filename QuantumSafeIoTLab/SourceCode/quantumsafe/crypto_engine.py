"""Thin wrapper around *real* NIST ML-KEM; never reimplement crypto maths."""
from importlib import import_module
from hmac import compare_digest

ALGORITHMS = {
    "ML-KEM-512": "pqcrypto.kem.ml_kem_512",
    "ML-KEM-768": "pqcrypto.kem.ml_kem_768",
    "ML-KEM-1024": "pqcrypto.kem.ml_kem_1024",
}


class CryptoUnavailable(RuntimeError):
    pass


def _engine(algorithm: str):
    if algorithm not in ALGORITHMS:
        raise ValueError("Unsupported ML-KEM algorithm.")
    try:
        mod = import_module(ALGORITHMS[algorithm])
        if not all(callable(getattr(mod, n, None)) for n in
                   ("keygen", "encaps", "decaps")):
            raise CryptoUnavailable("Unexpected pqcrypto interface; use version 1.0.0.")
        return mod
    except ImportError as exc:
        raise CryptoUnavailable(
            "Real ML-KEM engine is missing. Install requirements.txt (pqcrypto==1.0.0)."
        ) from exc


def make_keys(algorithm: str):
    return _engine(algorithm).keygen()


def encapsulate(algorithm: str, public_key):
    return _engine(algorithm).encaps(public_key)


def decapsulate(algorithm: str, secret_key, ciphertext):
    return _engine(algorithm).decaps(secret_key, ciphertext)


def self_test(algorithm: str) -> dict:
    """Actual shared-secret agreement, with no private material returned."""
    mod = _engine(algorithm)
    public_key, secret_key = mod.keygen()
    ciphertext, sent = mod.encaps(public_key)
    received = mod.decaps(secret_key, ciphertext)
    sizes = {name: int(getattr(mod, name)) for name in (
        "PUBLIC_KEY_SIZE", "SECRET_KEY_SIZE", "CIPHERTEXT_SIZE", "SHARED_SECRET_SIZE"
    )}
    success = compare_digest(sent, received)
    if not success:
        raise RuntimeError("ML-KEM key agreement failed.")
    return {"algorithm": algorithm, "passed": success,
            "sizes": sizes, "implementation": "pqcrypto 1.0.0"}
