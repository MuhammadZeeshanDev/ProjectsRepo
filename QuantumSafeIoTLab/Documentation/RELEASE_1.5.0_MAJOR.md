# QuantumSafe v1.5.0 — Professional LAN Lab, local AI/Prolog, 3-GiB CSV

**Prerequisite:** Install the earlier updates through v1.4.0; apply this ZIP using existing `UPDATE_APP.bat`. The ZIP is an overlay, **not** a full installer. Back up your app, SQL Server data, and `Data` folder first.

## Working additions

1. **LAN Lab & Devices** in the sidebar, visible to Administrator and Security Operator. Local virtual device inventory, active/disabled/retired counts, CSV export without credentials, and existing optional private-LAN ML-KEM listener in its own tab.
2. **Administrator-only device lifecycle:** register a new virtual device (fresh unique HMAC key and device credential); disable/enable; rotate keys; permanently retire. All changes are reflected immediately in the current HTTP gateway. Disabled and retired device IDs cannot authenticate. Old credentials are rejected after rotation. Registry persists across restarts in `Data/device_registry.json` (created automatically on first start). Audit trail in `Data/device_audit.jsonl`. Retired IDs cannot be reused; SQL historical gateway events remain intact.
3. **Defender test of any enrolled device** plus **PC B custom-target unauthorized test**, without giving PC B trusted keys.
4. **Local Prolog integration**: search for SWI-Prolog `swipl` on PATH and common Windows installation paths; allow Administrator to enter exact local `swipl.exe` path. Fixed, allowlisted Prolog rules analyze training metrics, up to 5,000 gateway / optional SQL history events, current device status counts and local model-registry metadata. Fallback is explicitly labeled *Python rules*, never misrepresented as native Prolog.
5. **Optional conversational AI (100% local)**: use locally installed Ollama on `127.0.0.1:11434` and locally downloaded model. No hosted API or key. AI sees summarized evidence, no device tokens or raw dataset rows; it recommends, but does not automatically change models, roles, or security decisions. With no Ollama, deterministic Prolog is still usable. **No LLM model weights are included** in this update.
6. **3 GiB CSV acceptance and offline ML workflow:** normal launch scripts set Streamlit upload limit to 3072 MiB; local file path is preferred for large CSVs to avoid browser memory pressure. Training scans the whole CSV in bounded 20k-row chunks and chooses a deterministic, uniform random-priority **sample up to 20,000 rows**, then performs existing separate CV folds, 70/30 or 80/20 holdout, RF/XGBoost/LightGBM where installed. **3 GiB acceptance is NOT 3 GiB full-data training**. The bundled verified RF checkpoint can also predict a local CSV up to 3 GiB in chunks; results are written to a local file. A small file on disk was tested; a real 3 GiB CSV was **not** tested in this environment.

## Where to find changes

- Sidebar: **🌐 LAN Lab & Devices → Device inventory** for device registration, disable, retire, rotate. Operations require Administrator role.
- Sidebar: **🌐 LAN Lab & Devices → Private LAN connection** for older (separate) secure message gateway tests, if configured. This is a standalone protocol and does **not** automatically enroll or authenticate against the virtual HTTP device allowlist.
- Sidebar: **🛡️ Device Security & Tests → Send authenticated test telemetry** (supports newly enrolled virtual IDs).
- One-click **PC B**: bottom section "Test a newly registered virtual device" uses a supplied ID; sends an unauthenticated local test.
- Sidebar: **🤖 ML Lab & AI → Train & compare / Test CSV / Local AI + Prolog**.

## Run locally

Use your installed Windows virtualenv and SQL Server configuration:

```powershell
& "..\.venv\Scripts\python.exe" SourceCode\launch_large_csv.py
```

PC B launches by the existing `SourceCode\Launch_PC_B.pyw` double click or main dashboard button. Ensure only one update ZIP resides in `Updates/` when applying.

## SWI-Prolog and local LLM

- For native Prolog, enter your existing executable path in ML Lab, e.g. `C:\Program Files\swipl\bin\swipl.exe`, if not auto-detected. Check command via `& 'C:\Program Files\swipl\bin\swipl.exe' --version`. Do **not** point at arbitrary executables. The app executes fixed rules, not user Prolog code.
- For a conversational local AI, install Ollama separately and download a model once; model execution then stays on the local PC. A model on disk plus its local Ollama service must be running. This ZIP does not bundle model weights, install Ollama, access external APIs, or automatically download from the internet.
- If the local LLM is unavailable, explanations still work via SWI-Prolog/Python rules without any API key.

## Windows acceptance checks

1. Record current virtual device list. Register `virtual-camera-02` in LAN Lab, refresh, then send trusted test telemetry from Defender: expect **ALLOW**.
2. From PC B, enter `virtual-camera-02` as a custom target; unauthorized test must **BLOCK** and show a new attack incident. Windows host alarm should queue once; verify physically via **Test Windows speaker**. This Linux build environment cannot verify speaker hardware.
3. Disable `virtual-camera-02`, then retry; expect **BLOCK**. Enable and trusted test should **ALLOW** again. Rotate credentials, verify an old saved token is refused, and restart app to verify persistent registration.
4. Confirm Security Operator can view inventory but has no device-management controls.
5. In ML Lab, select a real CSV ≤3 GiB, choose features, algorithm, 70/30 or 80/20 and 3/5 folds; compare per-fold and held-out metrics. For a large file, use **Local file path** rather than browser upload.
6. Enter `swipl.exe` path and run AI & Prolog; check engine says **SWI-Prolog (local)**, not fallback. Select optional SQL evidence (200/1000/5000 rows) to analyze stored gateway events; if SQL is unavailable, current in-memory evidence still works.
7. Start Ollama with a locally installed model if desired; confirm installed model appears in the dropdown and can answer based on current bounded evidence. No API key.

## Important security/operational boundaries

- Device registry stores secret material on disk in plain JSON under `Data/` (local host ACL protection required). Restrict permissions, include it in backup, do not send it to contractors or source control. This update does **not** implement encrypted secret storage, secure device provisioning, or TPM-backed keys.
- `Data` and `ML_Artifacts` are created by the runtime and are not included in this ZIP; update does not overwrite existing application data.
- The **virtual HTTP gateway** still listens on loopback `127.0.0.1` and is not a real-world IDS or firewall. PC A/B virtual HTTP tests use the same host. The separate legacy private LAN secure-message listener uses a shared secret and is **not** integrated with device inventory.
- Your 10-feature Edge-IIoTset RF model requires matching TCP/MQTT features; current virtual HTTP events are NOT valid model inputs. No live ML automatic blocking is claimed. XGBoost/LightGBM checkpoints are not bundled unless independently supplied.
- Training on a 20k random sample can be unreliable for minority attacks or time/device leakage. Validation on independently collected live-representative data is still necessary. The 3-GiB file limit is an acceptance/storage constraint, not a guarantee of browser RAM/disk capacity.
- The optional Ollama LLM can produce inaccurate advice; native Prolog rules are deterministic but not autonomous learning. Deployment always requires Admin review.
- We did NOT run the Windows Streamlit UI, SQL Server, SWI-Prolog binary, real 3-GiB upload, or speakers in this environment because the required runtime/services were unavailable. Python modules, HTTP behavior and bounded-size CSV tests were exercised on Linux; see `Documentation/VALIDATION_1.5.0.txt`.

## Competitor cross-check (official documentation, reviewed Nov 2026)

| Capability | ThingsBoard | Wazuh | QuantumSafe v1.5.0 |
|---|---|---|---|
| Device enrollment / credentials | Yes: device provisioning, access tokens and certificate options | Agent enrollment and RBAC | **Virtual-only** local registry with per-device keys, disable/retire/rotate |
| Event collection / incident analysis | Telemetry and alarm workflows | Rules, alerts, endpoint monitoring, real-time log analysis | HTTP gateway and optionally SQL logs; Prolog rules; **no network-wide IDS** |
| Deployment / access controls | Mature platform roles and monitoring | Mature security roles/rules | Two app roles; local security tool, still a prototype |
| Native AI | Not asserted here | Not asserted here | SWI-Prolog explanations + optional local Ollama summaries (not autonomous) |

Sources: https://thingsboard.io/docs/user-guide/provisioning/ ; https://documentation.wazuh.com/current/user-manual/ruleset/ ; https://github.com/wazuh/wazuh-documentation/blob/main/source/getting-started/components/wazuh-dashboard.rst . This is a feature-level comparison, not a claim of production equivalence.
