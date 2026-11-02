# QuantumSafe IoT Lab — Major ML Research releases

## Installation
These are two independent sequential update ZIPs. Install **v1.0.0 first**, then **v1.1.0** with existing `Updates/UPDATE_APP.bat`. Stop the app before updating, keep ONE ZIP in Updates each time and preserve backups. Requires existing v0.9.0 installation.

## v1.0.0: Research evidence and model workbench
- Three algorithm families: Random Forest, XGBoost, LightGBM where each appears in recorded evidence.
- 70/30 and 80/20 split filters, **every recorded fold**, original/ROS balancing filters.
- Preserves v3 historical vs v4 group-aware experiments **separately**. Per-row provenance, source file SHA256, CSV exports.
- Includes authentic evidence CSVs from supplied research bundles, not fabricated or retrained results.
- Retains existing model registry where individual trusted exported checkpoint files can be stored, but **not auto-executed**.
- No new trained XGBoost/LightGBM checkpoint is included. One authentic v3 Random Forest 70/30 checkpoint is bundled as an **inert file** under Assets/ResearchEvidence/checkpoints, with SHA256. It is NOT executed or deployed automatically. XGBoost and LightGBM checkpoints were not supplied; research metrics are not checkpoints.

## v1.1.0: AI research advisor
- Evidence-grounded local deterministic recommendation, works offline (NOT a trained or generative AI model).
- Optional real OpenAI API call via admin entered key + internet + paid account; key is not saved by this page. Selected experiment rows and question are transmitted to the API. External API model access varies.
- Admin-only advisory UI; never auto-deploys models or controls alarm decisions.
- No live ML IDS for gateway HTTP telemetry: classifiers expect packet-level TCP/MQTT features; impossible to generate honestly from current HTTP event fields.

## Validate
Sign in Admin → ML Research Studio: choose v3, Random Forest, 70_30, Fold 1, Original. Then choose v4 and the same filters; values MUST remain separately sourced. Pick other models/folds/splits; download filtered rows. AI Research Advisor can explain selected evidence even offline; remote AI requires a valid API key.
End-to-end Windows/SQL/remote AI testing has not been performed in this build environment.
