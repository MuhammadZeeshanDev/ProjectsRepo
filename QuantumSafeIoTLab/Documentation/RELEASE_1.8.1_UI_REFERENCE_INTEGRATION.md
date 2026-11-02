# QuantumSafe v1.8.1 — Reference UI integration and feature audit

**Prerequisite:** QuantumSafe v1.8.0 applied, app kept closed during update.

## What changed

The visual dashboard was adapted from the user-supplied `QuantumIoTLab.zip`, specifically its `static/index.html`. The core visual language is preserved: responsive light/dark cards, security posture banner, KPIs, logical topology canvas, alert feed, gateway activity chart, device cards, status filters, alert indicator and theme switch.

The existing **authenticated Streamlit** application stays the control plane. A restrained shared light/dark visual theme also styles the Admin panels (sidebar, typography, KPI cards, tables and buttons), while their original functionality is preserved:
- Administrator: `📊 Live Security Monitoring`, `🌐 Devices & Installation`, `🧠 ML & AI Control`, `🧪 PC B Security Tests`, `👥 Team Accounts` (unchanged from v1.8.0).
- Security Operator: read-only monitoring, no ML import/training or device modification.
- UI requests device inventory and event history through existing Python services (no untrusted public endpoints).
- Alert acknowledgements are **Administrator-only**, persisted locally in `Data/console_alerts.sqlite3` (separate from existing SQL Server incident records). Event export is Administrator-only.
- Virtual gateway responses, device enrollment and stored ML evidence remain unchanged. No new network-blocking logic is implied.

## Reference features audited

| Reference feature | Decision | Explanation |
|---|---|---|
| Network topology diagram | Integrated visually | Shows enrolled *virtual* device identities and their logical relation to localhost HTTP gateway; not observed physical packet paths. |
| Sensor/device cards and readings | Integrated | Values are from authenticated local virtual telemetry, not made-up readings or reference demo fixtures. |
| Responsive light/dark layout, filters, alert indicator | Integrated | Client-only interactions inside isolated Streamlit HTML component. |
| Alert feed and severity | Integrated | Derived from existing rejected gateway events; no invented email notifications. |
| Acknowledgement | Integrated safely outside iframe | Admin-only Streamlit action, locally persisted. |
| Traffic + anomaly chart | Adapted | Charts actual logged virtual HTTP request counts and rejected-request fraction over 90 s, **not** packet/s or ML anomaly score. |
| FastAPI WebSocket simulate/IPS commands | **Not adopted** | Reference backend accepts unauthenticated control messages; unsafe to expose as-is. Existing Admin PC B and Devices controls retained. |
| IsolationForest unsupervised ML | **Not merged** | Reference model trains on synthetic traffic; unrelated to user's labeled RF/XGBoost/LightGBM checkpoints and real network data. |
| Auto-block, quarantine, timed release | **Not adopted** | Reference applies to its own simulated SQLite pipeline, not Windows firewall / router. Existing gateway already refuses invalid telemetry. |
| SMTP notifications | **Not copied** | Requires configured credentials and security review. Existing first-attack local alarm remains unaffected. |
| SQLite demo database and seed 10 devices | **Not adopted** | Would conflict with user accounts, SQL Server history and true registered virtual-device inventory. |

## Security properties and limitations

1. Uploaded HTML is used as a **local read-only component**, with payload JSON made safe against HTML/script injection. No reference demo WebSocket, public control API, or automatic simulated attacks execute.
2. Monitoring embeds only sanitized/limited event data; per-device credentials/ML model files are never passed to browser HTML.
3. No claim of **real network traffic scanning, gateway DHCP/DNS assignment, ML packet-level IPS or physical-device quarantine**. These remain later phases.
4. The console topology is logical. A configured virtual IP is inventory metadata, not a real host IP; observed `127.0.0.1` comes from signed localhost requests.
5. The 'Rejected requests' metric covers the visible event sample in the preceding 24 h (up to 600 recent SQL events + local 200). It is not an exhaustive lifetime or whole-network count.
6. Alarm policies, model selection, stored model versions, device credential changes, and PC B controls are unchanged from v1.8.0.
7. Default event viewer refreshes via Streamlit every 5 seconds. If SQL Server is unavailable, local in-memory gateway events are still shown; no database data is silently fabricated.
8. Does not bundle fonts, trained models, credentials or reference application's independent Python FastAPI backend.

## Install

1. Back up the entire QuantumSafeIoTLab folder, especially `Data`, `ML_Artifacts` and SQL Server database.
2. Close app and PC B station.
3. Put exactly one ZIP (`QuantumSafe_Update_1.8.1_UI_Reference_Integration.zip`) into the app's `Updates` folder.
4. Run existing `UPDATE_APP.bat` and type **YES**.
5. Launch application as before, sign in. Use sidebar `📊 Live Security Monitoring` for new reference-style console; Admin actions remain on other panels.

## Test on Windows

1. In Admin `Devices & Installation`, start the virtual gateway; enroll a device, send signed test telemetry; new UI must show it as recently reporting with its virtual inventory address.
2. In Admin `PC B Security Tests`, send an unauthorized request. UI should show rejected activity, correct device and observed source IP; the gateway must reject it.
3. In Admin monitoring below the visual, acknowledge the event; refresh and verify persistent acknowledgement after restart.
4. Disable a device in Devices panel: new UI marks it *Disabled*, not online, and future requests fail.
5. Check `ML & AI Control`: your RF/XGBoost/LightGBM dataset/training/import and Prolog route tools should still appear unchanged.
6. Sign in as Security Operator: verify only monitoring visible, no Admin actions.
7. Switch dark/light, filter devices, inspect traffic and alert counts, export evidence as Admin.

## Validation

- 10 new dashboard-adapter tests pass (event dedupe, roles, acknowledgement persistence, freshness, escaping, output data boundaries).
- 13 v1.8 regression tests pass, including synthetic RF, XGBoost and LightGBM training, device enrollment/credential revocation, PC B rejection and job importer.
- JavaScript syntax check passed using Node.js.
- Chromium rendered the standalone UI preview without page errors, with four devices and one alert. The preview uses **illustrative synthetic readings only**; the installed app reads real existing virtual-gateway observations.
- **Not verified here:** Windows/Streamlit integration, SQL Server, native Prolog, PC B full GUI, real LAN hardware or actual multi-GB CSV training.
