# QuantumSafe 0.8.0 — Device identity hardening

Prerequisite: 0.7.7. This is a cumulative payload including earlier updates.

- Each enrolled virtual device receives its own random device token and HMAC signing key on gateway startup.
- Gateway validates device registration, shared gateway token, per-device token, message integrity, nonce uniqueness, and rate limits.
- A valid credential from one device cannot authenticate a different device.
- Administrator trusted test harness can send valid signed requests; PC B has no keys.
- BLOCK events remain eligible for a single incident alarm per UI session; normal traffic does not alarm.

Limitations: credentials live in process memory and reset on restart. No provisioning workflow, durable credential rotation, network isolation, or real ML-KEM authenticated session yet. PC B and PC A still run on the same localhost host. Do not use as production IoT authentication.

The following milestone will add ML-KEM session establishment only after authentication and supported crypto dependency checks.
