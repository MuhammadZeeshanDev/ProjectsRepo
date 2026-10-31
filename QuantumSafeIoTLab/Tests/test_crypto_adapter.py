"""FR-04: adapter API test. Replaces external library ONLY inside this unit test."""
import pytest
from quantumsafe import crypto_engine


class DummyKemForAdapterTest:
    PUBLIC_KEY_SIZE = 800
    SECRET_KEY_SIZE = 1632
    CIPHERTEXT_SIZE = 768
    SHARED_SECRET_SIZE = 32
    def keygen(self):
        return b"public", b"private"
    def encaps(self, public_key):
        assert public_key == b"public"
        return b"cipher", b"x" * 32
    def decaps(self, secret_key, ciphertext):
        assert secret_key == b"private" and ciphertext == b"cipher"
        return b"x" * 32


def test_unknown_algorithm_rejected():
    with pytest.raises(ValueError):
        crypto_engine._engine("ML-KEM-999")


def test_adapter_with_test_double(monkeypatch):
    monkeypatch.setattr(crypto_engine, "_engine", lambda _alg: DummyKemForAdapterTest())
    info = crypto_engine.self_test("ML-KEM-512")
    assert info["passed"] is True
    assert info["sizes"]["PUBLIC_KEY_SIZE"] == 800
