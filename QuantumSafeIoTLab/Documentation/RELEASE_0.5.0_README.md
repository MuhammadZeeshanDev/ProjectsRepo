# QuantumSafe v0.5.0 — Lab Guide and Demo Reliability

## Actual changes
- Central version 0.5.0, including the virtual gateway heading.
- New **Lab Guide** page: beginner walkthrough, ML-KEM explanation, roles, network data, and honest architecture boundary.
- Virtual gateway explains why each scenario is allowed/blocked.
- No changes to model checkpoint, SQL schema, authentication backend, or upload limit.

## Security/role behavior (already implemented in earlier project)
- Admin creates users and chooses Admin / Researcher / Viewer; no public signup.
- Admin can disable accounts. Viewer sees results; Admin/Researcher run lab tests.
- First admin is bootstrapped through local setup script, not public registration.
- Existing roles are enforced by server-side permission functions, not only menu visibility.

## Important ML integration limitation
The current local HTTP gateway uses a JSON `device`, `nonce`, `value`, `token`, `signature` schema.
The saved Edge-IIoTset RF requires ten TCP/MQTT features. HTTP telemetry does not include them. Do NOT fabricate values or claim the model classifies gateway requests. A compatible, consent-based capture/feature-extraction adapter must be implemented and validated first. Current ML predictions are offline CSV-based.

## Install
1. Stop app. Place only this ZIP in `QuantumSafeIoTLab/Updates`.
2. Run `UPDATE_APP.bat`, type `YES`.
3. Launch with the existing large-upload launcher: `& "..\.venv\Scripts\python.exe" SourceCode\launch_large_csv.py`.
4. Check title v0.5.0 and Lab Guide page. Test gateway + SQL + ML as separate flows.

## GitHub safety
Do not commit `.env`, `.venv`, `Backups`, `Updates`, private CSVs, prediction outputs, local DB files, credentials or API tokens. Audit all tracked files before push. Use example config, document setup and dependency versions. This update does not perform repository cleanup automatically.

## Tests
Python syntax checked in packaging environment. No Windows SQL Server or end-to-end runtime test was possible here.
