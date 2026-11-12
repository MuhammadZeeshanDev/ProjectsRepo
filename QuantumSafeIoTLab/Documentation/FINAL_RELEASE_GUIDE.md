# QuantumSafe Final Virtual Prototype — Feature and Verification Report

## Architecture (what is implemented)

```text
                    PC A: Streamlit app on localhost:8501
                   ├── SQL Server 2022 identity/login (Windows auth)
                   ├── Admin: Devices & Installation, ML & AI, PC B, Accounts
                   ├── Security Operator: Monitoring + Analytics (read-only)
                   ├── Virtual Gateway: localhost:8765 (signed telemetry + virtual IPS)
                   ├── In-process virtual endpoint A
                   │   ML-KEM encapsulation + HKDF + AES-256-GCM encrypt
                   ├── Gateway secure mesh: ciphertext-only routing/registry checks
                   ├── In-process virtual endpoint B
                   │   ML-KEM decapsulation + AES-256-GCM authenticated decrypt
                   ├── SQL outbox (durable local SQLite → SQL Server 2022)
                   └── ML: RF / XGB / LightGBM → saved model evidence → SWI-Prolog review
                     PC B: separate localhost:8502 attacker/test console
```

**The virtual peer agents are in the same PC A process.** This test proves wiring and real cryptographic operations when `pqcrypto` is installed; it is not independent real hardware cryptographic protection.

## UI simplification
- Only six top-level panels (two operator-visible): Live Security Monitoring, Analytics, Devices & Installation, ML & AI Control, PC B Tests, Team Accounts.
- ML-KEM test and SQL diagnostics are integrated *inside* Devices & Installation rather than separate research pages.
- No extra operator training or key-management controls. Removed backup directories, runtime data, cached tests and old release notes from distributable.

## Real crypto sequence
1. Admin starts virtual gateway and registers two devices; registry has unique credentials. Disabled/retired/quarantined devices cannot send or receive.
2. Recipient virtual agent creates ML-KEM-768 public/private keypair. Sender encapsulates shared secret to recipient's public key.
3. Sender derives 32-byte AES key using HKDF-SHA256 with nonce + sender/recipient context.
4. Sender authenticates metadata (sender, recipient, ML-KEM algorithm, nonce) via AES-GCM AAD and encrypts text.
5. Gateway relay handles ciphertext, KEM ciphertext, nonce, and source/recipient IDs. It does NOT receive the session key or plaintext argument.
6. Recipient decapsulates and decrypts. Authentication failure or repeated nonce blocks the message. Credential rotation invalidates cached virtual device agents.
7. Nonsecret operation metadata/decision enters local SQL outbox and is mirrored to dbo.VirtualGatewayEvents; Admin UI and SQL Management Studio can independently observe SQL confirmation. A pending local outbox is NOT an SQL persistence pass.

## SWI-Prolog
- `ml_engine/selector.py` loads fixed `rules/ids_model_selector.pl`. Uses bounded recorded, independently evaluated model metrics; compares class recall, precision, false positive rate, inference latency, sample support, checkpoint integrity. Saves approved **shadow routes**, not automatic full network-block actions.
- `ml_engine/incidents.py` uses `rules/ids_incident_policy.pl` for event severity/risk and recommendations. Output is checked against independent Python rules. The UI displays **SWI-Prolog native** only if the installed `swipl` binary actually runs. Else clearly labeled Python fallback.
- To force path, set `QUANTUMSAFE_SWIPL=C:\\Program Files\\swipl\\bin\\swipl.exe` in the project's own environment.

## SQL Server 2022
- Run `01_create_database.sql`, then `02_upgrade_v02.sql` in SSMS, ensuring `dbo.Users` and audit tables exist.
- `gateway_event_store.initialize()` creates or upgrades virtual gateway event/inventory tables on first SQL write. `03_secure_device_audit.sql` is an optional explicit migration and audit query.
- `SourceCode/final_system_check.py` tests live SQL, initializes gateway tables and reports only confirmed server-side counts. A SQL-connection failure must not be shown as successful. Device data queues locally until connection is restored.
- ML checkpoints and device secrets are deliberately **not stored in SQL**. Local SQLite/JSON data must be protected and backed up.

## Threat audio
- Virtual gateway's existing `realtime_alarm.AlarmEngine` handles blocked-event notifications on PC A Windows sound output.
- The new secure mesh calls the same alarm engine only on rejected encrypted deliveries. Browser sound may also require a user gesture.
- If PC A has no audio output available, incident still appears in dashboard and SQL queue; sound output must be tested on actual Windows machine.

## Verification scope
- Python compilation and focused pytest tests verify control flow, SQL outbox formatting, security-event metadata and prior v2.x compatibility.
- In this build environment `pqcrypto`, Windows ODBC, native SWI-Prolog, Windows speaker and Streamlit are absent. Native ML-KEM, SQL Server write/read-back, SWI-Prolog and GUI are **NOT verified here**.
- The included `VERIFY_FINAL_SYSTEM.bat` verifies these dependencies directly on the actual Windows PC; Admin UI then offers functional encrypted link and read-back tests.
- Legacy old version tests may fail due to deprecated APIs; current targeted release tests are reported separately. No blanket claim of a fully green historical suite.

## Recommended final demo
1. Admin logs in → SQL connected status.
2. Gateway starts → three simulated devices visible with distinct configured vs observed IPs.
3. Add a fourth device, start synthetic telemetry. PC B discovery shows it without any credentials.
4. Signed telemetry ALLOW; PC B unauthorized access BLOCK → sound + incident.
5. Two virtual devices exchange a real cryptographically encrypted payload (KEM+AES) → green allow; tampering/replay → red block + risk.
6. View SQL Diagnostics → write/read-back PASS and SQL metadata query.
7. SWI-Prolog incident evaluation → engine shown; Admin ML trains labeled IoT CSV; model saved and reviewed.
8. Operator logs in → only monitoring/analytics, no admin controls.

## Production gap
Full physical router gateway, DHCP/mDNS discovery, device-side client provisioning, network traffic capture, real packet-level IPS/firewall and unattended ML-based packet enforcement are not included in the virtual prototype. Hardware deployment requires extra engineering/security review.
