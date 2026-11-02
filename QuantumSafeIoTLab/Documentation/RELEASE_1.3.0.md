QuantumSafe 1.3.0 — Professional ML Lab & Two-Role Access

Prerequisite: v1.2.1 installed.

ROLE POLICY
- Administrator (stored DB value Admin): all screens, ML training/import/AI, manage users.
- Security Operator (stored DB value Researcher): overview, gateway security and monitoring; NO ML/AI/account management.
- Legacy Viewer: login denied until Administrator changes role in Team Accounts. Historical database rows remain unchanged until edited; no destructive migration.
- Role changes are checked against SQL account record and cannot remove the last active admin. Existing signed-in sessions are checked on each Streamlit rerun.
- PC B standalone attack console remains a localhost testing participant, not an authenticated third business role.

ML LAB
- 4 practical tabs: train/compare, checkpoint library, AI improvement, deployment checks. Removed historical evidence / standalone LAN explanation tabs from the primary operator workflow; files remain intact.
- Offline guidance evaluates the most recent REAL training metrics, including FPR and per-fold spread. Optional remote LLM receives a metrics-only summary and administrator question, not the dataset, keys or model object.
- AI is advisory, no auto-training/deployment. Registry import stores untrusted model files WITHOUT loading them. Live ML inference requires actual feature acquisition matching TCP/MQTT schema.

NOT TESTED: actual Streamlit Windows GUI / SQL Server role migration / AI API external request. Back up the SQL database before deployment.
