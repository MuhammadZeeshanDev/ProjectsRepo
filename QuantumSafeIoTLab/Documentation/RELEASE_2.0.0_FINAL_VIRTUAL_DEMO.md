# QuantumSafe v2.0.0 — Final VIRTUAL IDS/IPS demo major release (4/4)

## Installation

Apply this update to the **existing QuantumSafeIoTLab application** using its existing safe updater. It is an application **overlay**, not a new standalone installation. Do **not** disable updater safety or copy protected system folders from another build.

1. Close Streamlit/PC B and backup the entire installation, especially `Data`, `ML_Artifacts`, `.env` and SQL Server independently.
2. Copy **only** `QuantumSafe_Update_2.0.0_Final_Virtual_Demo_Analytics.zip` into `<project>/Updates/` (remove or move prior ZIPs).
3. Launch `UPDATE_APP.bat`, type `YES`, and check `UpdateLogs` for errors.
4. Restart the app using the **existing** launcher and sign in as Admin. No database or secret files are replaced.
5. In `Devices & Installation`, start virtual gateway at `127.0.0.1:8765`; check Windows speaker output and browser sound settings.

## Admin demo — true ALLOW versus BLOCK

1. `Devices & Installation` → `Install new virtual device`: enter an ID, descriptive name/type, optional virtual IP/MAC. This does **not** provision a physical NIC.
2. Click `Start virtual gateway`, choose registered device, click `Send single test` → verify **ALLOW** and `Authenticated and integrity verified`.
3. In the `Device acceptance & safe-login demo`, run `valid_signed_telemetry`, `unauthorized_credentials`, `tampered_signature`, `replayed_nonce`, `unknown_device`.
4. Expected genuine localhost HTTP results: `ALLOW / BLOCK / BLOCK / BLOCK / BLOCK`. Both permitted and rejected requests are saved in available virtual gateway history. Persistent test outcomes in `Data/device_acceptance.sqlite3`.
5. `Actual SQL account login verification`: supply existing (not demo/backdoor) SQL account username/password. Legitimate active credentials return ALLOW, invalid credentials DENY. Passwords not persisted by this test.
6. PC B → `Start / Open PC B Test Station`: a **separate localhost Streamlit interface** at port 8502, inventory refreshes every 5 seconds from shared registry and includes newly enrolled devices. PC B **never** receives valid device credentials. Only deliberate invalid access tests are available.
7. `Live Security Monitoring` shows real local gateway events. Click **🔊 Sound on** inside browser viewer once to allow browser notification audio on new critical/high alerts. This is separate from Windows-host alarm (works without browser sound permission). The `TEST WINDOWS SECURITY SIREN` button queues a genuine local PCM WAV playback on Windows and logs failure diagnostics.
8. Open `Security Analytics & Charts`: observe timeline, allowed/rejected ratio, block reason rankings, per-device activity, actual authenticated telemetry values, saved ML metrics (where present). Start device readings and PC B requests to populate the graphs.

## Improvements vs v1.9.0

- More stable, reference-styled HTML dashboard: keep iframe mounted while local viewer polls; data diff updates preserve SVG and card DOM instead of tearing down device cards every 3 seconds; overlapping network polls are avoided.
- Two independently available alarm mechanisms: built-in Windows host `winsound` generated PCM WAV with diagnostic counter, and user-enabled Web Audio browser warnings.
- Device test station with real signed ALLOW, invalid credential BLOCK, signature-tampering BLOCK, replay BLOCK and unknown ID BLOCK, with persistent acceptance results and authorization checks.
- PC B dynamically lists IDs/names/types/configured virtual IPs from local device registry with no credential disclosure, works for new devices without restarting PC B.
- New **Security Analytics & Charts** read-only screen for Admin and Operator, six charts from genuine local virtual HTTP events and saved ML evaluations, professional semantic colors. Admin can export displayed evidence.
- Model/Prolog local evidence handling and controlled shadow evaluation retained from v1.9; Administrator still controls training/model import in application.

## Deliberate limitations — do not misrepresent in a demo

- The gateway accepts **localhost virtual telemetry** only. It is not a router, wireless access point, packet capture engine, Windows firewall, actual device IP allocator, or physical LAN IPS.
- Gateway virtual-IP settings and topology are identity labels for simulation. Actual observed source IP will be `127.0.0.1` on same-machine demos.
- SQL persistence requires properly configured external SQL Server and availability. Local gateway's ring-buffer history is capped; graphs represent available records, not guaranteed all traffic over 24h. Device-test records use persistent local SQLite.
- RF/XGBoost/LightGBM validation, checkpoint storage, Python/SWI-Prolog model ranking and shadow predictions remain separate from enforced IPS. Model routes are not automatically promoted to Windows/network-wide firewall rules.
- Audio is generated in code; we tested WAV shape, alarm enqueue and simulated player, **not real Windows speaker output**. Browser playback requires user click and a non-muted output.
- Imported `.joblib` is Python pickle based; only Administrator-supplied **trusted, compatible** files should be imported. Never load arbitrary files from unknown sources.
- Independent Windows UI smoothness, SQL Server integration, installed SWI-Prolog invocation and real multi-GB CSV training are **not verified** by container tests.

## Release smoke test

From project root where required dependencies are installed:

```powershell
& "..\.venv\Scripts\python.exe" -m pytest Tests/test_v200_release.py Tests/test_v200_analytics.py -q
```

For alarm playback verification open `Devices & Installation` as Admin and click `TEST WINDOWS SECURITY SIREN`; examine live `Audio failures` diagnostics.
