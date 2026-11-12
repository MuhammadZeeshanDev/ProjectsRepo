# QuantumSafe IoT Security Lab v2.2.0 — portable Windows setup

## One-click install

Extract the full folder (Desktop, Downloads, USB copy, any writable path). On Windows 10/11, double-click **`INSTALL_AND_START.bat`** once with internet access. Dependencies are downloaded on this PC, inside its `.venv`, not shipped as Windows executables inside the archive. The script uses Microsoft `winget` for Python 3.12, Microsoft ODBC Driver 18 for SQL Server, optional SQL Server 2022 Express, and SWI-Prolog. It uses `pip` for application Python packages.

**No manual `.env` creation**: Setup discovers a running local SQL Server instance using registry plus local fallback names, connects with Windows Integrated Authentication, creates or upgrades database tables without dropping existing data, and writes `.env`. If necessary, choose an instance at the prompt. For existing SQL installations, the running Windows account must have permissions to create or alter the app's tables. For a fresh SQL installation it must have `CREATE DATABASE` rights. No remote SQL server is accepted with an unverified self-signed certificate. The local self-signed TLS exception is limited to localhost variants.

Setup inserts a dedicated `INSTALL_HEALTH_CHECK` into SQL `dbo.AuditLogs` and immediately reads it back. Only then is installation marked ready. **A successful local queue does not mean SQL synchronization succeeded.** After launch, use **Devices & Installation → SQL Server 2022 → Write and read back a real ALLOW event** to prove real gateway writes.

If SQL Server is absent, setup explicitly asks permission to install Microsoft SQL Server 2022 Express. This can require elevation, licensing agreement, service configuration, and an OS reboot. It will NOT hide errors or pretend the server is running.

## Login and recovery

New installations provision `Zeeshan` as Administrator using the requested temporary demo password. The first login immediately requires choosing a new private password (12–128 characters). The database stores Argon2id password hashes, not plaintext. Existing `Zeeshan` records are not reset automatically. Authorized local SQL Server **sysadmin** owners may run `RECOVER_ADMIN.bat`, confirm the action, and reset only `Zeeshan` to the temporary credential, again requiring immediate password change. Other accounts are preserved.

Do not expose Streamlit TCP port 8501 to the public Internet. The app is localhost-only by default. Never use the requested demo password outside the test machine.

## Run

Double-click `START_APP.bat`, which checks dependencies and SQL connectivity and launches the Streamlit dashboard locally. `START_PC_B.bat` launches the attack test console locally. `RUN_DIAGNOSTICS.bat` checks SQL, ML-KEM, local Prolog detection and ML packages.

When copying the folder to another PC, **do not transfer** `.venv`, `.env`, device keys, or any private user data unless explicitly performing an authorized migration. Run installer again on the destination. A database on the previous PC does not move automatically.

## SQL Server evidence

- SQL login/users, experiments and login audit: SQL Server 2022 `dbo.Users`, `dbo.AuditLogs`, etc.
- Virtual gateway ALLOW/BLOCK incidents and crypto audit metadata: `dbo.VirtualGatewayEvents`.
- Virtual device enrollment status and configured virtual IP: `dbo.VirtualDeviceInventory`.
- Durable offline queue before SQL write success: `Data/sql_sync_outbox.sqlite3`. Queue is not the SQL database.
- Trained ML checkpoints remain in local `ML_Artifacts` (not copied into SQL). Model key material and message plaintext are not mirrored.

For real SQL verification, open SQL Server Management Studio and query:

```sql
USE QuantumSafeIoTLab;
SELECT TOP 20 * FROM dbo.AuditLogs ORDER BY AuditId DESC;
SELECT TOP 20 * FROM dbo.VirtualGatewayEvents ORDER BY EventId DESC;
SELECT TOP 20 * FROM dbo.VirtualDeviceInventory ORDER BY UpdatedAtUtc DESC;
```

## Scope and honesty

The program implements a **virtual localhost security lab**. ML-KEM + AES-GCM simulated device-to-device gateway cryptography requires a compatible native library and is verified independently by `RUN_DIAGNOSTICS.bat`. SWI-Prolog is a local rules engine with Python fallback if unavailable. Neither is a claim of physical network-wide packet capture, transparent router configuration, or certified production IPS. Actual Windows installer/ODBC/SQL-Prolog behavior **must be tested on the target PC**; this archive was built and statically checked in a Linux environment.
