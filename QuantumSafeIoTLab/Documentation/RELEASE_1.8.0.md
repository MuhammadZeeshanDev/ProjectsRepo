# QuantumSafe v1.8.0 — Administrator UI restoration + virtual device installation + PC B

**Required baseline:** QuantumSafe v1.7.0 installed over your existing base application. Apply this **overlay ZIP** with `UPDATE_APP.bat` from `QuantumSafeIoTLab`, after backups. The archive updates source code only; it does not replace SQL Server, trained models, `Data/` or `.env` files.

## What changed

### Four admin operating functions, one operator monitoring screen

Administrator sidebar:

- **Live Security Monitoring** — virtual gateway status, registered virtual devices, synthetic live readings, observed source IP, current incidents, saved IDS models, SWI-Prolog-selected shadow routes.
- **Devices & Installation** — start/stop local HTTP gateway, register virtual IoT device ID/display name/type/virtual IP/virtual MAC, start/stop live reading generator, test trusted telemetry, disable/enable/rotate/revoke/retire device credentials. Old `Data/device_registry.json` credentials are migrated automatically to new `Data/virtual_devices.json` on first use, WITHOUT deleting the old file.
- **ML & AI Control** — admin-only CSV training, in-UI RF/XGBoost/LightGBM selection, 70/30 or 80/20 holdout, 3 or 5 validation folds, scheduled background jobs, persistent model checkpoints, offline CSV predictions, clean retraining, importing trusted `.joblib` and Prolog model selection.
- **PC B Security Tests** — restore dedicated PC B launcher and existing independent attack console at `http://127.0.0.1:8502`. Support testing arbitrary newly enrolled IDs (unauthorized attempt); PC B never gets trusted device keys.
- **Team Accounts** — existing administrator account controls.

Security Operator sidebar: **Live Security Monitoring** only. All device management, training, imports, PC B launch and team administration are hidden AND device management permissions are checked server-side.

### ML backend behavior

1. Admin selects **CSV local path** or **Upload CSV**. For huge CSV, enter a local path in the UI; this uses a bounded-memory streaming scan. **The browser uploader limits to 256 MiB in this panel to avoid out-of-memory crashes.** File size is not capped for local path; CPU, RAM, disk space, parser and reasonable execution time remain hard constraints.
2. Admin chooses attack-label, normal class, safe features, RF/XGB/LGBM (depending on installed packages), sampling size (2,000–500,000), split and folds. A CSV requires labeled benign/attack records; no system can honestly auto-train a supervised detector on completely unlabeled data.
3. Job runs in a **single backend worker**. The UI remains available to monitor while it runs. Persistent job log: `ML_Artifacts/IDS_Engine/admin_jobs.sqlite3`. If server restarts mid-job, jobs are marked interrupted; no phantom successes.
4. Every completed model is saved immutably under `ML_Artifacts/IDS_Engine/models` with a SHA-256 integrity check; metadata, folds, features and per-class metrics are saved to `ids_models.sqlite3`.
5. Prolog uses held-out per-class recall/precision/FPR, sample support, prediction latency and integrity facts to choose **SHADOW-only** routes, never unverified automatic physical IPS blocking. Native SWI-Prolog uses installed `swipl.exe` when detectable, otherwise Python fallback is labeled. A Prolog rule excludes known Edge-IIoTset mqtt.protoname data-shortcut risk.
6. Import via Admin UI:
   - **Compatible bundle**: includes `pipeline`, `classes`, `schema` (numeric/categorical/features), `label`, `normal_label`. Imported model starts **unverified_import** quarantine; Admin validates with a separate labeled CSV. It cannot auto-route based solely on an import.
   - **Pretrained RF/XGBoost/LightGBM estimator**: detect its estimator class and **clean retrain a NEW version** on an Admin-provided labeled CSV. The original saved weights are NOT incrementally trained or automatically deployed. To use novel algorithms beyond these, a reviewed custom estimator plugin is still necessary; arbitrary uploaded Python code is not run.

**Security warning:** `.joblib` is Python pickle serialization and can execute arbitrary code when loaded. ONLY trusted Admin-created checkpoints should be uploaded. Never import files from unknown senders. Training upload files and credentials are stored locally; secure file-system access to `Data` and `ML_Artifacts`.

### Virtual device installation and 2-PC distinction

This version implements virtual-device installation, not physical IoT auto-discovery. The Admin enters a **simulated virtual IP and optional MAC** for inventory; the real HTTP source IP is independently shown as **127.0.0.1** because this is a localhost virtual gateway. These are **not** proof of a physical device or a DHCP-assigned address. New virtual device sends recurring synthetic telemetry after the Admin presses **Start live readings**. It shows active only after recent authenticated telemetry (last 30s). Stop/retire => no further trusted telemetry.

PC A = Defender/main Streamlit app + gateway; PC B = independent attacker Streamlit app. By default BOTH run on the same PC, different localhost ports (8501/8502) with a simulated connection to gateway port 8765. **They do not need a two-PC network link for virtual tests.** A later physical LAN collector, authenticated remote enrollment, TLS/session negotiation and network-wide routing/firewall changes are separate development stages.

## Windows installation

1. Back up whole `QuantumSafeIoTLab` app, SQL Server, `Data/` and `ML_Artifacts/`. Stop gateway and Streamlit UI.
2. Ensure v1.7.0 already installed. Put **only** `QuantumSafe_Update_1.8.0_Admin_UI_PC_B_Devices_ML.zip` in `QuantumSafeIoTLab/Updates/`.
3. Run `UPDATE_APP.bat` (in project root), enter `YES` on confirmation.
4. Use existing Windows venv, e.g. from `QuantumSafeIoTLab` folder:

   ```powershell
   & "..\.venv\Scripts\python.exe" SourceCode\launch_large_csv.py
   ```

5. Admin login -> **Devices & Installation** -> Start gateway -> register `virtual-camera-02` with optional simulated IP `192.168.50.12` -> Start live readings -> Monitoring must show it active and source IP 127.0.0.1.
6. Admin -> **PC B Security Tests** -> Start PC B -> test `virtual-camera-02` as an unauthorized identity -> expect BLOCK and logged incident.
7. Admin -> **ML & AI Control** -> choose local labeled CSV -> check Attack_label and normal class (often `0`) -> train RF then other installed models -> jobs history -> saved models -> Prolog shadow rankings.
8. Log in with Security Operator account -> only Monitoring sidebar available. Administrator can see all management panels.

Optional dependencies, install only inside the app's existing venv if missing:

   ```powershell
   & "..\.venv\Scripts\python.exe" -m pip install scikit-learn pandas numpy joblib xgboost lightgbm
   ```

## Verification performed in this environment

- Python syntax compilation of updated source: PASS
- v1.8 + prior v1.7 pytest suite: **25 PASS** on Linux, covering device persistence, admin authorization, virtual HTTP gateway allow/deny, custom PC B unauthorized tests, credential revocation, SQL-independent model persistence, RF/XGB/LightGBM training, job status, .joblib quarantine and independent validation, Prolog ranking, size-bounded samples, import-template recognition.
- Python training uses small synthetic IoT CSV. **NOT** a test of IDS accuracy in the real world.
- Actual Windows Streamlit UI **not tested** (Streamlit package unavailable in this isolated Linux environment), Windows SQL Server **not tested**, Windows SWI-Prolog **not tested**, Windows speaker **not tested**, real 3-GiB CSV **not tested**, full physical LAN **not implemented**.
- No automatic physical firewall, network scanning, quantum-safe end-to-end authentication or remote police contact is claimed. Existing gateway block and Windows alarm paths remain available for HTTP virtual rule violations.

## Roadmap after v1.8.0

- **v1.9.0**: compatible live TCP/MQTT feature adapter, cautious anomaly shadow validation, IPS policy gate, audit/alarms — do not invent model input features.
- **v2.0.0**: admin-approved deployment, rollback, secure remote device provisioning design, Windows/SQL/Prolog end-to-end UAT, stable installer and final operator dashboard.
