# QuantumSafe v1.7.0 — administrator ML backend + SWI-Prolog + monitoring-only frontend

**Phase 1 of four releases:** v1.7 engine → v1.8 virtual/LAN device gateway → v1.9 compatible live IDS/IPS → v2.0 verified final application.

This ZIP is a **safe updater-compatible incremental overlay** (`update.json` + `payload/SourceCode`, `payload/Tests`, `payload/Documentation`). It does not overwrite credentials, original datasets, current SQL Server tables, locally saved model files, the virtual gateway logic, the alarm implementation or earlier research files. It **replaces `SourceCode/app.py`** to enforce the requested monitoring-only operator experience. Administrators retain a separate Gateway & Devices page and Team Accounts management. If a prior LAN Lab page exists, it remains accessible to the Administrator. The user's connected SQL Server is only used to display existing gateway-event history, not for training. New model metadata is recorded separately in local SQLite.

## What is working

- CSV → 3 locally trained algorithms: Random Forest, XGBoost and LightGBM (`manage_ml.py train`, `train-all`). The admin can select original input feature columns, normal label, binary/multiclass target, 70/30 or 80/20 held-out split and 3/5 stratified folds. IoT feature candidates are automatically screened, including exclusion of common IDs/IPs, other labels and `mqtt.protoname` (a known Edge-IIoTset label-shortcut issue). Admin can override selected features with explicit `--features`, but compromised feature sets are excluded from automatic routing for Edge-IIoTset.
- CSV input is a **local file path**, not a browser upload. **No fixed byte-size limit** is enforced for this backend path; the entire CSV is streamed in bounded chunks. RAM/CPU, file encoding, storage and parsing still impose real limits. Training runs on an explicitly reported *bounded sampled subset* of the file: 30,000 rows by default; user-configurable 200–500,000 rows. Therefore *accepting an arbitrarily large CSV is NOT the same as full-dataset training.* A streaming uniform-priority sample with per-class minimum selection is used; validation is on the sampled data, not independently collected live network traffic.
- Class counts are diagnosed rather than the earlier confusing 2–20 error. Supports 2–40 classes in the actual training engine. If too many categories, inspect the target or use `--binary --normal-label ...`. The raw column must be a real labeled attack target; unlabeled data cannot directly train supervised classifiers. Class imbalance and group/time leakage can still affect results.
- Every successful training run creates **immutable** checkpoint bytes, SHA-256 checksum, class/feature schema, source dataset SHA-256, model metrics, per-threat precision/recall/FPR, CV folds, parent version and timestamp in `ML_Artifacts/IDS_Engine/` (SQLite `ids_models.sqlite3`). The original large CSV stays where it is; source path+hash is recorded. Protect and back up both. The ML metadata database is **not the same database as SQL Server user accounts and gateway events**.
- `retrain --model-id N --csv ...` performs **clean model refitting with original algorithm and features**, stores a *new* immutable model version, and keeps the older model. This is not online `partial_fit` of original weights, because Random Forest/XGBoost/LightGBM do not share a safe, universal incremental training contract. `import-and-retrain` supports local, administrator-verified `.joblib/.pkl` model families RF/XGBoost/LGBM as a starting **algorithm/schema** (new weights trained afresh). Importing untrusted pickle/joblib can execute code; importing requires explicit `--i-trust-local-pickle`. A new estimator family can be added only by manually reviewing/adding its constructor to trusted `SourceCode/quantumsafe/ml_engine/custom_estimators.py`, never via a public upload form.
- `rank` and automatic post-training ranking use saved per-threat facts, model integrity and a fixed rule file `quantumsafe/rules/ids_model_selector.pl` to select the best compatible **shadow-only** model. Uses native SWI-Prolog if installed (`QUANTUMSAFE_SWIPL` or `--swipl`), or a clearly labeled equivalent Python rule fallback. Independent Python/Prolog output disagreement aborts routing. Only models trained from the SAME source CSV hash are directly compared by default; without `--dataset-sha`, the most recently trained dataset is used. Thresholds are conservative demo defaults, not calibrated production policy. Selected candidates are not deployed to a firewall.
- `predict --model-id N --csv FILE` processes local CSV in bounded batches with exact required feature schema, writes all predictions to output CSV, stores representative anomaly records in SQLite. `auto-shadow-jsonl` accepts true feature dictionaries from an **external collector** through stdin; generates advisory `REVIEW` results and no network change. There is no live TCP/MQTT adapter in this update. The virtual HTTP gateway produces different fields and is NOT silently fed to these trained classifiers.
- `quantumsafe/rules/ids_incident_policy.pl` evaluates actual SQL gateway incident counts for repeated replay/crypto/unknown/rate-limit events. Alerts are READ-ONLY recommendations (medium/high/critical). **It does not automatically rotate keys, quarantine physical devices, contact police, or disable network interfaces.**
- The regular frontend is read-only, autorefreshed every ~4 seconds. Security Operator sees only Security Monitoring. Administrator sees Monitoring, Gateway & Devices, Team Accounts. ML training, CSV uploads and Prolog command execution are **not** on any public-facing Streamlit page. Only a local administrator with OS permission to run `manage_ml.py` can initiate training. Apply Windows ACLs to restrict the project/venv and model data.

## Update installer (Windows)

1. Stop application/PC B consoles. Back up your project and **Data, ML_Artifacts, SQL Server database**. The updater backs up overwritten application files, *not* runtime data.
2. Place **only** `QuantumSafe_Update_1.7.0_Backend_ML_Prolog_Monitoring.zip` in `QuantumSafeIoTLab/Updates`.
3. Run existing `QuantumSafeIoTLab/UPDATE_APP.bat`, confirm `YES`. Restart the app with your current launcher.
4. From **QuantumSafeIoTLab** project directory, check your Python environment:

```powershell
& "..\.venv\Scripts\python.exe" SourceCode\manage_ml.py list-algorithms
```

If XGBoost/LightGBM missing, install in the **same** environment:

```powershell
& "..\.venv\Scripts\python.exe" -m pip install -r SourceCode\requirements_ids_v170.txt
```

5. To activate native SWI-Prolog if not on PATH, use the path to your installed `swipl.exe`:

```powershell
$env:QUANTUMSAFE_SWIPL = 'C:\Program Files\swipl\bin\swipl.exe'
& $env:QUANTUMSAFE_SWIPL --version
```

6. **Train all three on labeled IoT CSV:**

```powershell
& "..\.venv\Scripts\python.exe" SourceCode\manage_ml.py train-all --csv "D:\Datasets\iot_train.csv" --label Attack_label --normal-label 0 --max-rows 30000 --folds 3 --test-fraction 0.3
```

The backend automatically ranks eligible models after training and saves the shadow routes. If the target is textual `Attack_type` with normal category `Normal`, use:

```powershell
& "..\.venv\Scripts\python.exe" SourceCode\manage_ml.py train-all --csv "D:\Datasets\iot_train.csv" --label Attack_type --normal-label Normal --binary --max-rows 50000
```

7. **Inspect, clean-retrain, compare, predict:**

```powershell
& "..\.venv\Scripts\python.exe" SourceCode\manage_ml.py models
& "..\.venv\Scripts\python.exe" SourceCode\manage_ml.py retrain --model-id 1 --csv "D:\Datasets\new_iot.csv" --max-rows 50000
& "..\.venv\Scripts\python.exe" SourceCode\manage_ml.py rank
& "..\.venv\Scripts\python.exe" SourceCode\manage_ml.py predict --model-id 1 --csv "D:\Datasets\iot_test.csv" --output "D:\Datasets\predictions.csv"
```

8. **Use your own trusted pretrained RF/XGBoost/LightGBM checkpoint:**

```powershell
& "..\.venv\Scripts\python.exe" SourceCode\manage_ml.py import-and-retrain --checkpoint "D:\Models\my_rf.joblib" --csv "D:\Datasets\new_iot.csv" --label Attack_label --normal-label 0 --i-trust-local-pickle
```

The input `.joblib` must contain a supported estimator with an original `features` list, or explicitly include `--features feature1 feature2 ...`. It is **not** an unsafe automatic execution path exposed to users. The current implementation extracts algorithm/feature schema and trains a new version: it does not continue old coefficients or trees. For fully novel model families, review and add a constructor to `custom_estimators.py` on the admin PC; its estimator must expose `fit`, `predict` and `get_params`.

9. To feed **real feature dictionaries** externally (one JSON object per line, exact original column keys):

```powershell
Get-Content "D:\Datasets\feature_events.jsonl" | & "..\.venv\Scripts\python.exe" SourceCode\manage_ml.py auto-shadow-jsonl
```

This is an **interface for an external collector**, not a built-in real network sniffer or IPS; output is shadow-only.

## Acceptance / limitations

- Verify training with a real labeled dataset and compare expected label counts. Wrong labels or severe imbalance produce explicit actionable errors instead of fabricated success.
- Verify saved checkpoint persists after restarting the application; train version N+1 with `retrain`. Verify `rank` engine says **SWI-Prolog native** on your Windows installation. Test `predict` with a CSV that includes **exact trained feature names**. Deliberately remove a field and confirm prediction refuses it rather than fabricating values.
- On this build environment, **12 automated tests passed** and a full three-model CLI training+ranking+500-row inference smoke test passed on synthetic labeled data. Syntax and packaging checks pass. The synthetic dataset is deliberately separable: its perfect accuracy is NOT real IDS effectiveness.
- **Not verified here:** Windows Streamlit GUI launch, SQL Server runtime, SWI-Prolog Windows executable, 3GiB+ CSV end-to-end run, private LAN discovery, real TCP/MQTT feature collection, network-wide gateway enforcement, real physical IoT device provisioning, emergency siren/audio. They must be verified on your deployment machine.
- Do not rely on any security claim until end-to-end validation on the target network. User monitoring should not expose or run admin training. Physical network-wide monitoring requires real packet/flow routing or a mirror/collector—Wi-Fi association alone does not supply every packet.
- SWI-Prolog is a **rule engine**, not a generative AI model. There is no OpenAI/cloud key. Model-selection policy uses only persisted evidence. Application does **not** automatically contact police/emergency services.

## Next three planned updates

- **v1.8.0:** Virtual network discovery/configured device IPs, enrollment, IP/device identity, validated feature collector adapter and cross-component lifecycle.
- **v1.9.0:** Live compatible ML inference pipeline, supervised shadow-to-enforcement policy, device isolation interfaces and alarms, with fail-safe modes.
- **v2.0.0:** End-to-end Windows integration tests, backup/recovery, rollbacks, usable dashboards, installer and final verified demo.
