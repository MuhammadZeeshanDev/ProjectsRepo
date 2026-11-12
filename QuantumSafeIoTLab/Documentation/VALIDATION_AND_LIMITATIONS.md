# Final build validation: 2026-11-02

## Automated checks performed on extracted source
- 65 selected current-version tests: PASS (virtual gateway, PC B, ML backend, model lifecycle, virtual IPS, v2.0 monitoring, SQL-outbox controls, acknowledgement, encrypted-device simulation).
- Python compilation: PASS.
- Verified `secure_device_message` queues only nonsecret crypto metadata; replay/tamper/disabled recipient rejected in mock-KEM control-flow tests.
- Final virtual crypto test uses a **mock KEM** because the build environment does not contain `pqcrypto`; it is NOT a real post-quantum cryptography verification.
- System checker output: SQL Server NOT VERIFIED (pyodbc not available), real ML-KEM-768 NOT VERIFIED (pqcrypto missing), native SWI-Prolog NOT DETECTED (Python fallback), ML algorithms RF/XGBoost/LightGBM installed in test environment.
- Complete historical test suite not all green: older API tests expect pre-v2 device methods/signatures and runtime-specific dependencies; the distributable includes current-version acceptance tests only.

## Verification required on user's Windows 10/11 PC
1. `INSTALL_WINDOWS.bat`, configure SQL instance, execute SQL scripts, first admin, then `VERIFY_FINAL_SYSTEM.bat`.
2. Confirm real `pqcrypto` ML-KEM shared-secret agreement PASS, actual source-to-recipient encrypted device test ALLOW, tamper/replay BLOCK.
3. Confirm SQL Server 2022 query for `RequestType='encrypted_mesh'` returns row(s), confirmed DB readback and populated crypto metadata.
4. Confirm `SWI-Prolog native` engine appears in app (not fallback) and runs incident and model rules.
5. Verify Windows siren, browser sound, two-user permissions and screenshot/render quality on actual display.
6. Verify independent CSV model training/validation on your actual dataset, restart/persistence and model import from trusted sources.

## Limits
- Virtual IoT endpoints only; localhost HTTP gateway with simulated secure mesh agents.
- ML-KEM is a KEM; payload encryption is AES-256-GCM using an HKDF-derived 256-bit key.
- SQL stores nonsecret event metadata/roles, while model artifacts/credentials are stored locally; it is not 100% SQL-only.
- Real router firewall, physical DHCP discovery, separated IoT device hardware clients, automatic ML packet enforcement and emergency-service calling are NOT implemented.
