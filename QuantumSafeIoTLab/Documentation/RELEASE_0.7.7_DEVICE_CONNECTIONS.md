# QuantumSafe v0.7.7 — Virtual Device Connection Observations

## New
- Device-wise ACTIVE (observed) / IDLE / NOT OBSERVED from actual successful gateway events.
- Last trusted activity time and ALLOW/BLOCK counters.
- Separate table for requests claiming unregistered device IDs.
- Clear connection interpretation: this is not physical-device connectivity, a persistent TCP session, or IP reputation verification.
- Alarm logic from v0.7.6 retained unchanged.

## How to test
1. Start gateway as Admin; run Camera: trusted telemetry. Camera should show ACTIVE (observed).
2. Wait >30 seconds without valid camera telemetry: camera becomes IDLE.
3. Send unauthorized PC B request: blocked attempt increments; it does not mark device connected.
4. Test Sensor trusted reading: sensor becomes ACTIVE (observed).
5. Verify alerts and SQL history independently if SQL Server is configured.

## Next planned
- Independent per-device enrollment credentials and real virtual secure-session lifecycle.
- Authenticated ML-KEM device ↔ gateway session (not self-test only).
- Dedicated per-device security tests and validated alert delivery.

## Limitations
- Current gateway shares one token and HMAC key among trusted test requests. Device-specific credentials are NOT yet implemented.
- Loopback-only HTTP simulation. No real IoT devices or network-wide monitoring.
- No live ML inference from gateway HTTP events.
