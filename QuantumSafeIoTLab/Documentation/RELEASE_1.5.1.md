# QuantumSafe 1.5.1 — training fix and persistence

* Fix confusing `Class count must be 2–20`: permit 2–100 categorical classes, provide clear error for >100, and add explicit normal-vs-attack binary mapping. For Edge-IIoTset, select a real target label. Do not select packet identifiers or timestamps as labels.
* Random Forest, XGBoost and LightGBM remain selectable **only when installed**. XGBoost and LightGBM libraries are not bundled; model weights are not bundled. Training uses a maximum 20,000 sampled rows from CSV (up to 3 GiB accepted).
* Every successful training run's metrics, fold results and metadata persist in `ML_Artifacts/training_history.sqlite3`. A trained model checkpoint is saved separately by clicking Save trained checkpoint. Models are **not automatically deployed to the live gateway**.
* LAN Lab is for virtual device enrollment and optional secure LAN messaging. PC B is a separate attacker console and is not needed to manage devices. Legacy LAN message protocol is not integrated with HTTP device credentials.
* No automatic training from unlabeled attack events. Administrator remains responsible for target labels, validation and model promotion.
* Existing device registry, alarm, Prolog, two roles and Pakistan timestamps unchanged.

## Test
1. Use a CSV with an actual attack-label column; check target values.
2. Train RF with 70/30, 3 folds; save checkpoint. Restart app, confirm saved training history and checkpoint.
3. Try binary mapping with the exact normal label; other labels become attack.
4. If XGBoost/LightGBM not shown, install the relevant package in the application's virtual environment.

Windows/SQL/SWI-Prolog and full 3GB data were not executed in this environment. Backup before updating.
