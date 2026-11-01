# QuantumSafe IoT Lab — Phase 1 Foundation Audit (v0.6.1)

## Verified from the uploaded project
- Installed version: 0.6.0; main Streamlit app, SQL Server access layer, gateway, ML-KEM demo, offline Edge-IIoTset RF inference and role-based accounts are present.
- Roles in current database/code: **Admin, Researcher, Viewer**. Proposed Admin/Security Operator split is **not yet implemented**. Changing it needs an explicit SQL migration and service-level permission audit.
- Existing `UPDATE_APP.bat` / `.ps1` accepts exactly one ZIP in `Updates`, copies whitelisted source/tests/docs/assets, backs up replaced files, and does not apply database changes or dependency updates. It is **not signed** and does **not perform automatic post-install rollback**.
- The uploaded archive contains `.env`, local SQL/ML artifact state, updater logs and backups. **Do not publish this archive to GitHub**. Rotate credentials if this archive was shared outside your trusted environment.
- Existing RF checkpoint is fixed-schema, offline inference only; do not claim it processes live HTTP gateway events. ML-KEM is key establishment, not intrusion detection. Prolog and automated retraining are not implemented.

## Design decision: three update lanes
1. **App patch ZIP** — compatible source/tests/docs/assets through existing updater. Stop app; keep backups; manual smoke test.
2. **Admin ML Studio** — future separate dataset/model/algorithm registry. Validate feature schema, provenance, evaluation, and model safety; never automatically deserialize arbitrary uploaded pickle/joblib.
3. **Security intelligence** — future signed policy/Prolog rule bundles, with staged validation and rollback.

## Versioned boundaries
`module_contracts.py` documents component inputs, outputs, and *current status*. A static catalog does not imply the planned components exist. Future adapters must implement explicit schemas and authorization boundaries; no dynamic plugin execution yet.

## Next phase (not in this update)
- Isolated virtual IoT device, defender gateway, independent attacker console, distinct participant credentials.
- Observe actual source endpoints; unknown IP alone does not establish maliciousness.
- Enforce protected access at gateway, alert and persist decision; keep ML inference distinct until genuine compatible features exist.
- Only then add Prolog reasoning, admin-only ML Studio and controlled adaptive learning.

## Safe install
1. Close Streamlit and any gateway processes.
2. **Remove the older v0.6.0 ZIP from `Updates`** (store it elsewhere); the existing installer refuses more than one ZIP.
3. Copy the v0.6.1 ZIP into `Updates` and run `UPDATE_APP.bat`, then type `YES`.
4. Run `python -m pytest Tests/test_foundation_061.py -q` in the project's configured virtual environment.
5. Restart the application. Database schema, existing model, datasets, `.env`, and passwords are untouched.

## Security note
The included preflight checks ZIP structure and destination paths **only**. It does not establish publisher authenticity or make arbitrary source updates safe. Signed packages, migration runner and automatic rollback remain future work.
