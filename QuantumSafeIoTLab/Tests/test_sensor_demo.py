"""FR-05/06: real AES-GCM tamper rejection; only the KEM is replaced in test."""
import pytest
from quantumsafe import sensor_demo


def setup_test_kem(monkeypatch):
    monkeypatch.setattr(sensor_demo.crypto_engine, "make_keys",
                        lambda alg: (b"public", b"private"))
    monkeypatch.setattr(sensor_demo.crypto_engine, "encapsulate",
                        lambda alg, public: (b"kem_cipher", b"z" * 32))
    monkeypatch.setattr(sensor_demo.crypto_engine, "decapsulate",
                        lambda alg, secret, ciphertext: b"z" * 32)


def test_secure_message_success(monkeypatch):
    setup_test_kem(monkeypatch)
    result = sensor_demo.send_reading("ML-KEM-512", 27.5)
    assert result["passed"] and "27.5" in result["message"]


def test_modified_message_rejected(monkeypatch):
    setup_test_kem(monkeypatch)
    result = sensor_demo.send_reading("ML-KEM-512", 27.5, tamper=True)
    assert result["passed"] and result["message"] is None
    assert result["outcome"] == "Tampered data rejected"


def test_invalid_temperature(monkeypatch):
    with pytest.raises(ValueError):
        sensor_demo.send_reading("ML-KEM-512", -51)
