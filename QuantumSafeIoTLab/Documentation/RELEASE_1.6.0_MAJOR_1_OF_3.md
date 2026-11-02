# QuantumSafe v1.6.0 — Major update 1 / 3 (Train → Validate → Save → Local AI review)

## What actually works in this update

- One Administrator-only ML Lab workflow for Random Forest, XGBoost and LightGBM (if their libraries are installed).
- Optional **experiment grid**: one or all installed algorithms × one or both 70/30 and 80/20 splits × 3-fold or 5-fold cross-validation. Every trained model/run is saved separately; each fold's metrics remain separate.
- Dataset variant tags: Original, ROS, Custom; feature-selection tags: Manual, SA-HFS v3/v4, Other. These tags DOCUMENT the selected method; selecting SA-HFS does NOT run the underlying SA-HFS algorithm.
- Correct FPR class orientation for normal/attack labels (the previous code incorrectly assumed the first class is always normal).
- Local trained checkpoint registry: hash-checked model files in `ML_Artifacts/trained_checkpoints/` and persistent SQLite metadata in `ML_Artifacts/validated_models.sqlite3`.
- Streamed **offline** CSV evaluation against any locally trained model (RF/XGB/LGBM), up to 3 GiB local CSV. CSV prediction output and evaluation history saved under `ML_Artifacts/`.
- Administrator review for an OFFLINE candidate with note; retirement disables further CSV evaluation. Neither review nor retirement changes gateway traffic policy.
- SWI-Prolog / optional local Ollama advisor can read the saved model catalog across restarts. New Prolog recommendations address offline candidates and models with weak observed metrics.
- Existing device registry, two-role permissions, PC B launcher, alarm logic, Islamabad time, and SQL event storage unchanged.

## Important operational limits

1. HTTP virtual gateway events are NOT TCP/MQTT feature vectors. No trained ML model is attached to live gateway blocking in v1.6.
2. Training accepts a *CSV file up to 3 GiB* but trains on a representative sample **up to 20,000 rows**, NOT all 3 GiB rows. Streaming inference processes all rows of a compatible local CSV, without holding the whole CSV in RAM.
3. Dataset files are not copied automatically. Dataset name, source size/row count/sampling provenance, SHA256 of the sampled CSV and model weights are saved. The sample digest is NOT the full 3 GiB input file hash.
4. Checkpoint files are serialized with joblib and must stay on the trusted host. Imported `.pkl/.joblib` are intentionally NOT loaded by the new evaluator. Loading untrusted pickles can execute arbitrary code. Installed sklearn/xgboost/lightgbm versions must match checkpoint compatibility requirements.
5. Binary mapped models require labeled evaluation CSV to contain the same `normal`/`attack` labels already mapped; raw multiclass source labels are not silently recoded by the evaluator. Predictions still run without labels.
6. Prolog rules are deterministic. Ollama is an OPTIONAL local conversational model. Neither autonomously retrains or deploys models. `swipl.exe` and Ollama availability must be checked on the Windows machine.
7. Offline candidate approval is NOT production deployment; network feature source + validation and guarded policy remain phases 2 and 3.
8. For real-time performance, full-packet capture, Windows sound output and SQL Server end-to-end behavior are NOT tested in this execution environment.

## Installation

Pre-requisite: v1.5.1 installed. Backup application folder and SQL Server. Stop main app and PC B. Place **only this ZIP** in `QuantumSafeIoTLab\Updates\`. Run `UPDATE_APP.bat` and restart. This patch updates only `SourceCode/`, `Tests/`, `Documentation/` and the Prolog rule file. No `.env`, existing credentials, historical checkpoints or SQL tables are deleted.

## Test v1.6.0 in the Windows UI

1. Administrator → ML Lab & AI → Train & compare. Choose your actual CSV and **label** column (not an ID). Select Original or ROS and the genuine feature-selection protocol used when CSV was made.
2. Choose either one algorithm or all installed algorithms. Select both splits and optionally both fold settings. Start with one algorithm / one split for resource usage.
3. After training, check per-model metrics, each fold, and `Save trained checkpoint` / auto-save. Check `Saved models & approval`; restart and verify runs persist.
4. Select a saved model under `Test CSV`; enter an independent compatible CSV path. Compare prediction counts, actual test metrics (when matching labels exist), and the persisted evaluation history.
5. Use `Local AI + Prolog` with `swipl.exe`. Review its findings, especially false positives and unstable folds. It must NOT claim live ML predictions based on HTTP gateway incidents.
6. Optional: review a model as an **offline candidate**. Gateway blocking should stay unchanged.

## Three-release completion plan

- **1/3 v1.6.0 (delivered):** Clean ML training, all saved algorithms/splits/folds, local CSV testing, persistent model history, offline AI/Prolog evidence, admin candidate review.
- **2/3 v1.7.0 (planned, NOT implemented here):** Authenticated feature ingestion for actual supported network schemas, passive/shadow ML inference, feature/schema compatibility, evidence retention and drift checks. Existing rule gateway remains authoritative.
- **3/3 v2.0.0 (planned, NOT implemented here):** Administrator-gated deployment and rollback, verified alarm integration, lifecycle checks/diagnostics, repeatable Windows/SQL/SWI-Prolog test report, deployment documentation. Production approval contingent on device/network capture and independent validation.

A Windows virtual-device demo is possible; physical IoT packet monitoring requires compatible capture/telemetry adapters and permissions. Do not mistake localhost testing for Internet-scale security coverage.
