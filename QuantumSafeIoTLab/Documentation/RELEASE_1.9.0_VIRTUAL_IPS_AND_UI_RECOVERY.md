# QuantumSafe v1.9.0 — local virtual IDS/IPS response + UI updater repair

## IMPORTANT — Fix for blocked v1.8.1 updater

The previously supplied v1.8.1 ZIP contained `Tests/__pycache__/test_v181_dashboard.cpython-313-pytest-9.0.2.pyc` and `.pytest_cache`. The existing safe PowerShell updater CORRECTLY rejects cache and executable bytecode. **Do not modify/disable that safety check.**

**v1.9.0 is cumulative relative to v1.8.0**: it includes the clean v1.8.1 reference dashboard assets, scripts and tests, then the new 1.9.0 functionality. You do NOT need to apply the rejected v1.8.1 ZIP first. Keep 1.8.0 installed, replace the old ZIP in the project's `Updates` folder with this 1.9.0 ZIP, run UPDATE_APP.bat, type YES. Existing `Data`, `ML_Artifacts` and SQL Server data are untouched. Preserve a backup. Keep exactly ONE ZIP in Updates. The update must be applied with the app stopped.

## What's genuinely implemented

1. Existing QuantumIoTLab-inspired professional theme and live virtual monitoring dashboard are restored through the earlier clean v1.8.1 sources, with no public unauthenticated FastAPI/WebSocket control endpoint.
2. Existing admin `Devices & Installation`, `ML & AI Control`, independent PC B attacker console and Team Accounts panels remain present; Security Operator gets monitoring-only navigation.
3. **New: Local virtual IPS policy engine** in `quantumsafe/virtual_ips.py`, persisting settings, time-bounded device quarantines and administrator audit history in `Data/virtual_ips.sqlite3`.
4. **Manual quarantine/release UI** in Devices & Installation; enrolled devices only, Administrator only, requires typing matching device ID. Every change creates an audit entry. Quarantine expires automatically; survives application restart until expiry.
5. **Optional auto-containment** explicitly OFF by default. When Administrator enables, after 3 integrity/replay/rate-limit failures within 60 seconds from a sender with **correct gateway token + valid per-device credential**, quarantine that registered device for 120 seconds. Spoofed IDs, unknown devices and invalid credentials do **not** quarantine anyone. This is virtual-gateway containment, not network/firewall isolation. False positives are possible; this is a controllable demo policy.
6. **Gateway enforcement:** quarantined devices with otherwise valid credentials are rejected immediately with reason `Virtual IPS quarantine active`; invalid gateway and device tokens are validated BEFORE revealing containment status. Existing HMAC/replay/rate-limit logic and Windows alarm remain in place. Virtual IPS reason is a critical alert.
7. **New: nonblocking shadow ML worker.** On valid signed **numeric** HTTP readings, it asynchronously checks the already-selected saved model routes against **actually observed fields only** (`device`, `source_ip`, `reading`, `value`, `request_type`, `identity_verified`). Missing TCP/UDP/MQTT/DNS model fields are reported incompatible, NOT invented. No ML-driven blocking. The dashboard reports shadow activity and model compatibility.
8. Persistent records: app's existing SQL Server event store is unchanged, and new IPS state has its separate locally persisted SQLite database. No automatic police/emergency dispatch.

## Important architecture limits

- This is a **localhost virtual gateway**. It cannot assign physical IPs, discover external Wi-Fi clients, capture arbitrary router packets, operate Windows firewall, quarantine an actual camera, or call emergency services.
- Pre-trained classifiers requiring Edge-IIoTset TCP/MQTT/DNS features cannot run on plain HTTP virtual readings. A real packet/flow collector and secure real gateway provisioning are necessary for meaningful physical-network ML IDS/IPS; that is a separate verified integration.
- Only signed, authenticated numeric telemetry enters the new best-effort shadow ML queue. When no compatible pre-approved models exist, existing rule-based protection continues; the dashboard does NOT fabricate ML detections.
- SWI-Prolog rules/ranking, backend training, RF/XGBoost/LightGBM pipeline and model checkpoints from v1.7/1.8 are preserved; the update does not falsely imply that model ranking automatically replaces a network firewall policy.
- Automatic quarantine has denial-of-service tradeoffs even with signed identities (e.g., a compromised sender with stolen valid credentials). Keep it OFF for safety tests until understood.

## Windows test plan

1. Start with v1.8.0 working, shut down application and PC B. Remove rejected v1.8.1 update from Updates folder. Apply v1.9.0 ZIP using UPDATE_APP.bat and type YES. No `__pycache__` block should appear.
2. Login Admin. Confirm Monitoring shows the new reference-style dashboard; switch light/dark theme; check PC B tab and ML & AI Control are still present.
3. In Devices & Installation, start virtual gateway, send a valid telemetry, and check dashboard heartbeat and observed localhost IP.
4. Use PC B to send invalid device credential and replay/tamper requests. Verify BLOCK events and audible alarm on Windows host.
5. Device & Installation -> Virtual IPS, quarantine an active virtual camera manually; valid telemetry for that camera should get 403 / BLOCK. Release, then check it accepts telemetry.
6. Turn ON auto policy with Admin acknowledgement, produce 3 **credential-valid** integrity-failed requests within 60 sec, verify 120-second quarantine. Invalid-credential spoof attempts alone must never quarantine that camera. Turn auto policy OFF after test.
7. Check audit history, restart app and verify quarantine persistence (until expiration); verify operator role cannot access device/IPs settings.
8. Check ML & AI Control algorithms and saved models. If selected model features are actual HTTP telemetry fields, shadow predictions can run; otherwise dashboard should show incompatibility and *not* report fake classification.
9. Test SQL Server, installed native SWI-Prolog and actual Windows audio; those native integrations were **not** executed in the Linux test environment.

## Automated validation

- New tests: 9 passed (IPS auth, lifecycle, policy limits, security checks, shadow observation).
- Existing targeted regression tests: 27 passed for v1.7/1.8 models, virtual gateway and device identity; 15 passed for v1.8.1 dashboard and alarm reliability. No Windows/SQL/native Prolog tests claimed.
- Safe ZIP scan: packages only application code, docs and Python source tests; no `__pycache__`, `.pytest_cache`, `.pyc` or forbidden executable update files.
