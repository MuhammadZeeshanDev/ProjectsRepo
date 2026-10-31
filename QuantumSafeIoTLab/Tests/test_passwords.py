"""FR-01: never store readable passwords; test bad-input boundary."""
import pytest
from quantumsafe.passwords import make_hash, verify


def test_password_hash_and_check():
    secret = "correct horse battery staple"
    encoded = make_hash(secret)
    assert secret not in encoded
    assert verify(encoded, secret)
    assert not verify(encoded, "wrong password")


def test_short_password_rejected():
    with pytest.raises(ValueError):
        make_hash("password")
