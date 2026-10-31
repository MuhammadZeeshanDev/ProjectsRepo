"""Passwords are stored as Argon2id hashes, never readable text."""
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


def validate_password(password: str) -> None:
    if len(password) < 12 or len(password) > 128:
        raise ValueError("Password must contain 12 to 128 characters.")


def make_hash(password: str) -> str:
    validate_password(password)
    return _hasher.hash(password)


def verify(password_hash: str, password: str) -> bool:
    try:
        return bool(_hasher.verify(password_hash, password))
    except (VerificationError, ValueError, TypeError):
        return False
