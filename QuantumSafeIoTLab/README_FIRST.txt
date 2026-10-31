QUANTUMSAFE V2 SAFE UPDATE STARTER (v0.1)

1. Back up your entire QuantumSafeIoTLab folder and SQL Server database separately.
2. Copy UPDATE_APP.bat and UPDATE_APP.ps1 into the INNER QuantumSafeIoTLab folder (where requirements.txt and SourceCode are).
3. The updater creates Updates, Backups and UpdateLogs automatically.
4. Future update ZIPs go inside Updates. Keep exactly ONE ZIP there.
5. Close Streamlit before double-clicking UPDATE_APP.bat. Read version and confirm YES.

UPDATE ZIP FORMAT:
  update.json         {"product":"QuantumSafeIoTLab","version":"3.0.1"}
  payload/SourceCode/...  (modified app files)
  payload/Tests/...       (optional)
  payload/Documentation/... (optional)
  payload/Assets/...     (optional)

SECURITY/SCOPE:
- This is a cautious application-file updater, not a full V3 release.
- It DOES NOT install packages, execute SQL migrations, import CSVs, change .env, or modify SQL Server.
- It rejects scripts, executables and SQL from update ZIPs, and limits payload paths.
- Backups contain only overwritten files; new files are removed on in-process copy failure.
- A malicious or untrusted ZIP is NOT safe just because it passes these checks: only use updates you trust.
- App restart, tests, database backup, dependency updates, and SQL migrations remain manual until actual V2 source is reviewed.
- If a later app startup/test fails, use Backups to restore manually.
- ZIP file should not include a .venv folder or credentials.

YOUR EXISTING .venv OUTSIDE THE INNER FOLDER IS FINE. DO NOT MOVE IT.
