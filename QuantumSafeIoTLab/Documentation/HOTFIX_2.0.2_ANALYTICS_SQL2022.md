# QuantumSafe v2.0.2 — Analytics Crash + SQL Server 2022 Persistence Fix

## What broke

1. `analytics_panel.py` attempted `reversed(list)[:200]` — Python's reverse iterator cannot be sliced. The analytics evidence table now takes the latest 200 rows, then reverses their order.
2. The v2.0.1 gateway defaulted to `event_sink=None`. The visible **Devices & Installation** page only enabled SQL persistence **if the SQL gateway table was already present**. Fresh SQL installations quietly kept virtual HTTP events in memory only; on process restart those events disappeared. The old, hidden virtual lab offered manual schema initialization but this path was not shown in the new Admin panel.

## v2.0.2 design

- New `SqlSync` durable local SQLite outbox at `Data/sql_sync_outbox.sqlite3`. Events and device inventory metadata are queued first and then mirrored to SQL Server **asynchronously**. Gateway HTTP decision is not delayed by a disconnected SQL Server.
- SQL Server schema `dbo.VirtualGatewayEvents`: timestamps, device IDs, decisions, rejection reasons, attack metadata, source IP, numeric reading when available, identity verification and IPS action. New `GatewayEventUid` is unique for idempotent retries; columns are added to existing tables without dropping history.
- SQL Server schema `dbo.VirtualDeviceInventory`: non-secret device metadata and current lifecycle status. **Device keys and tokens stay in the local secured registry**, not the SQL mirror.
- Auto-initialize SQL schema on first queued write; auto-retry after transient SQL connection failures.
- Administrator **Devices & Installation → SQL Server 2022 · Persistence & Diagnostics** shows pending SQL queue counts, last confirmed SQL save, failures, connection/init/sync test, and a **real authenticated HTTP request that must be read back by event UID from SQL Server** to show PASS.
- Security console and analytics read available SQL events and show queue/offline status, not fabricated data.

## What is stored where

| Data | Storage |
| --- | --- |
| Account login and role tables | Existing SQL Server |
| Virtual gateway ALLOW/BLOCK audit history and numeric readings | SQL Server `dbo.VirtualGatewayEvents` once sync is confirmed |
| Virtual device name, IP label, type, state | SQL Server `dbo.VirtualDeviceInventory` once sync is confirmed |
| Pending writes during SQL outage | Local `Data/sql_sync_outbox.sqlite3` (durable, NOT SQL) |
| Sensitive per-device keys, gateway credentials | Local `Data/virtual_devices.json` and process memory; not SQL |
| Trained ML models, evaluation metadata | Local `ML_Artifacts/IDS_Engine/ids_models.sqlite3` and joblib files, NOT SQL |
| Alert acknowledgement state | Local SQLite, NOT SQL |

**Not retroactive:** virtual events already lost from memory before applying this update cannot be recovered. Events previously written to SQL remain untouched.

## Install and verify on Windows / SQL Server 2022

1. Close PC A/PC B Streamlit applications and stop both Python processes. Back up project `Data`, `ML_Artifacts`, and the SQL database.
2. Place **only this update ZIP** in the project's `Updates` folder. Run existing `UPDATE_APP.bat`, confirm and restart the app. Do **not** disable updater validation.
3. Log in as Administrator, open **Devices & Installation**, start virtual gateway.
4. Expand **SQL Server 2022 · Persistence & Diagnostics** and click **Check SQL connection, initialize and sync**. The screen reports actual SQL server/database, row count or the exact error.
5. Click **Write and read back a real ALLOW event**. Only a successful SQL SELECT by event UID produces a PASS.
6. In SQL Server Management Studio (SSMS), select the database configured in the project `.env` (default `QuantumSafeIoTLab`); run:

```sql
SELECT TOP (20) EventId,EventTimeUtc,DeviceId,Decision,Reason,SourceIp,Reading,GatewayEventUid
FROM dbo.VirtualGatewayEvents ORDER BY EventId DESC;
SELECT TOP (20) DeviceId,DeviceName,DeviceType,EnrollmentStatus,VirtualIp,UpdatedAtUtc
FROM dbo.VirtualDeviceInventory ORDER BY UpdatedAtUtc DESC;
```

7. If SQL is unreachable, queued event/device counts increase locally. Diagnose SQL connectivity, then click sync again. **Queued is not equivalent to saved in SQL.**

### Typical SQL issues

- `Login timeout expired` / `server not found`: Check `.env` **SQL_SERVER** (e.g. `localhost\\SQLEXPRESS` only if that instance exists), service, TCP/SQL Browser as appropriate.
- `Cannot open database`: Check **SQL_DATABASE** and Windows Authentication permissions.
- `SSL Provider / certificate chain`: ODBC Driver 18 defaults to encrypted connection. Configure a trusted cert; for strictly local development with self-signed certificate only, `SQL_TRUST_SERVER_CERTIFICATE=true` may be used after understanding the trust implications.
- `CREATE TABLE permission denied`: the SQL login must have schema creation/migration rights to initialize tables (or the DBA must run an equivalent approved schema migration).
- `No module named pyodbc` / ODBC driver missing: Install requirements into the *same* active app virtual environment and install Microsoft's ODBC Driver 18 for SQL Server.

## Validation limits

- The local unit tests use isolated temporary SQLite and simulated SQL writer/reader objects. They do not confirm connectivity to the user's Windows SQL Server 2022 instance.
- This patch does not introduce physical network sniffing/firewalling, and it does not move ML model checkpoints to SQL Server.
- Original virtual device and PC B functions are preserved.
