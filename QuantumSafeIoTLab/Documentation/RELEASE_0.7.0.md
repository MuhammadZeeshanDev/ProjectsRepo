# QuantumSafe v0.7.0 — Phase 2, independent virtual attacker

## What is implemented
- Separate Streamlit process for virtual PC B (`SourceCode/attacker_console.py`).
- Independent client has no defender token or signing key. It can only send bounded, predefined tests to loopback gateway.
- Defender gateway listens on `127.0.0.1:8765` when started in the dashboard; unauthorized attempts return BLOCK and are logged in existing event history and optional SQL event store.
- Source IP recorded in in-memory event; note: both processes use 127.0.0.1, not two distinct IPs. Existing SQL schema does not yet persist this new field.

## Windows demo
1. Apply this ZIP via `Updates/UPDATE_APP.bat` (only one ZIP in Updates folder).
2. Start main app and sign in; open Gateway & Alerts, click **Start local gateway**.
3. Open a second terminal in the project root and run:
   `..\.venv\Scripts\python.exe -m streamlit run SourceCode\attacker_console.py --server.address 127.0.0.1 --server.port 8502`
4. In the attacker console select **unauthorized** or **repeated_unauthorized**, click Run.
5. In defender dashboard inspect BLOCK events and SQL history (if configured).

## Honest limitations
- Virtual PC A/B are separate processes on one Windows PC, not isolated VMs or physical machines.
- Loopback only; no real network scanning, real IP reputation, actual IoT device, packet capture or network-wide blocking.
- Invalid-signature scenario cannot reach signature verification without a valid token; it is blocked at authentication first. A true authenticated tamper test remains available in defender's existing local scenarios.
- Browser autoplay alarm remains subject to browser permission; SQL availability depends on Windows configuration.
- Existing Random Forest ML, Prolog integration, model registry and automatic learning are not changed by this release.
- Gateway source identity is unverified client-supplied network context; loopback IP is not a unique attacker identity.
