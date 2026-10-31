"""Measure real ML-KEM operations on the host computer (NOT on an ESP32)."""
from hmac import compare_digest
from time import perf_counter_ns
import platform
import statistics
from importlib.metadata import version
from . import crypto_engine


def validate_trials(trials: int) -> None:
    if type(trials) is not int or not 1 <= trials <= 1000:
        raise ValueError("Select between 1 and 1,000 test iterations.")


def run_trials(algorithm: str, trials: int, progress=None) -> list[dict]:
    validate_trials(trials)
    # The algorithm's allowlist is enforced before measurement.
    crypto_engine._engine(algorithm)
    measurements = []
    for number in range(1, trials + 1):
        start = perf_counter_ns()
        pk, sk = crypto_engine.make_keys(algorithm)
        key_ns = perf_counter_ns() - start

        start = perf_counter_ns()
        ct, secret1 = crypto_engine.encapsulate(algorithm, pk)
        encaps_ns = perf_counter_ns() - start

        start = perf_counter_ns()
        secret2 = crypto_engine.decapsulate(algorithm, sk, ct)
        decaps_ns = perf_counter_ns() - start

        if not compare_digest(secret1, secret2):
            raise RuntimeError(f"Key agreement failed on trial {number}.")
        for operation, ns in (("KeyGen", key_ns), ("Encaps", encaps_ns),
                              ("Decaps", decaps_ns)):
            measurements.append({"trial": number, "operation": operation,
                                 "duration_ns": int(ns)})
        if progress:
            progress(number, trials)
    return measurements


def summarize(measurements: list[dict]) -> list[dict]:
    result = []
    for operation in ("KeyGen", "Encaps", "Decaps"):
        values = [m["duration_ns"] / 1e6 for m in measurements
                  if m["operation"] == operation]
        if not values:
            continue
        result.append({"Operation": operation,
                       "Median (ms)": statistics.median(values),
                       "Mean (ms)": statistics.mean(values),
                       "Trials": len(values)})
    return result


def environment() -> dict:
    return {"host_os": platform.platform(), "cpu": platform.processor(),
            "python": platform.python_version(), "pqcrypto": version("pqcrypto"),
            "unit": "perf_counter_ns wall-clock on host PC",
            "hardware_device": False}
