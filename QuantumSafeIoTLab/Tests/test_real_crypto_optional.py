"""Actual native-library check; will SKIP until pqcrypto is installed."""
import pytest
from quantumsafe import crypto_engine


def test_real_mlkem_all_three():
    pytest.importorskip("pqcrypto")
    for name in crypto_engine.ALGORITHMS:
        answer = crypto_engine.self_test(name)
        assert answer["passed"], f"Real key agreement failed for {name}"
