# QuantumSafe 0.7.1 — Device and Security Workflow

- Registered virtual CCTV, router, sensor; gateway rejects unregistered IDs.
- Gateway uses fixed loopback port 8765 so independent PC B can reach it.
- Admin-only security tests and per-device ML-KEM 512/768/1024 local self-check matrix.
- Security Operator (legacy DB role Researcher) sees monitoring but not test controls or ML training.
- Observer (legacy DB role Viewer) sees overview only.
- Admin (legacy DB role Admin) has full access. DB role names remain unchanged for safe migration.
- PC B test console describes what is sent and why gateway rejects it.

## Limitations

KEM tests are **local** pqcrypto key-agreement self-tests repeated for each virtual device identity; they do not establish independent device-to-gateway authenticated sessions. All devices are assumed KEM-capable in the virtual lab. No physical IoT, IP reputation, packet capture, new ML training, or remote firewall.

## Start

Install ZIP with UPDATE_APP.bat. Start defender gateway, then PC B with `python -m streamlit run SourceCode/attacker_console.py --server.port 8502`. SQL persistence depends on configured SQL Server.
