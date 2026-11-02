# QuantumSafe v1.2.0 — Unified ML Lab & AI

Install AFTER v1.1.1. This update consolidates ML Research Studio, registry, limited local training, AI advisor and live inference readiness into ONE administrator screen. Existing evidence files and existing registry data remain untouched.

## Available training now
- Upload a CSV <=60MB, first 20,000 rows; select explicit label, <=30 features, RF or installed XGBoost/LightGBM.
- 70/30 or 80/20 stratified held-out split; 3 or 5 separate stratified folds on TRAINING partition; missing value handling and categorical encoding fit within folds.
- Evaluate held-out once. Locally save joblib checkpoint and SHA256 metadata (saved, not deployed). Never load untrusted uploaded pickle.
- Existing historical evidence remains separately filterable by model, split, fold and balancing.
- AI assistant is embedded in ML Lab, with offline evidence-based advice or opt-in external API; does NOT self-train or automatically integrate models.
- LAN Lab was a legacy two-machine shared-secret connection tester; its separate navigation was removed, with honest explanation in ML Lab. Files remain for backwards compatibility.

## Critical boundaries
Actual full-size dataset training, fully automated multi-model pipeline, all imported trained model checkpoints, and LIVE gateway TCP/MQTT inference remain NOT implemented. Only RF original checkpoint is known available from prior release. SQL and Windows end-to-end testing remain necessary.

To install: put only this ZIP in Updates, run UPDATE_APP.bat, restart the app. Backup first.
