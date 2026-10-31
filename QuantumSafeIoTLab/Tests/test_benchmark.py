"""FR-07: correct iteration count, separate timings, and boundaries."""
import pytest
from quantumsafe import benchmark


def test_limits():
    for invalid in (0, -1, 1001, 3.5, True):
        with pytest.raises(ValueError):
            benchmark.validate_trials(invalid)


def test_three_measurements_per_iteration(monkeypatch):
    monkeypatch.setattr(benchmark.crypto_engine, "_engine", lambda alg: object())
    monkeypatch.setattr(benchmark.crypto_engine, "make_keys", lambda alg: (b"p", b"s"))
    monkeypatch.setattr(benchmark.crypto_engine, "encapsulate",
                        lambda alg, public: (b"c", b"s" * 32))
    monkeypatch.setattr(benchmark.crypto_engine, "decapsulate",
                        lambda alg, secret, ciphertext: b"s" * 32)
    samples = benchmark.run_trials("ML-KEM-512", 3)
    assert len(samples) == 9
    assert {s["operation"] for s in samples} == {"KeyGen", "Encaps", "Decaps"}
    assert len(benchmark.summarize(samples)) == 3
