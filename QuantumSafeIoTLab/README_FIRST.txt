QUANTUMSAFE IoT SECURITY LAB v2.2 — WINDOWS ONE-CLICK PACKAGE
=============================================================
1. Extract the ENTIRE QuantumSafeIoTLab folder anywhere on a Windows PC.
   Don't run files from inside the ZIP. Avoid extracting inside Program Files.
2. DOUBLE-CLICK INSTALL_AND_START.bat (first time). Internet needed to
   download Python, ODBC, SWI-Prolog if missing, and Python libraries.
3. Installer detects your existing SQL Server 2022 instance and uses Windows
   authentication. It creates/updates the QuantumSafeIoTLab database safely.
   If SQL Server is missing, installer offers SQL Server 2022 Express (requires
   your consent and Windows administrator permission). An inaccessible SQL
   instance is a blocking error, not a fake success.
4. Installer creates Zeeshan Administrator if missing; temporary password is
   the one you requested (123456789012). You MUST change it on first login.
5. For subsequent launches just double-click START_APP.bat.
6. For the independent attack simulator use START_PC_B.bat.
7. If needed: RUN_DIAGNOSTICS.bat or RECOVER_ADMIN.bat (authorized SQL owner only).

Do NOT copy a .env file from another PC. Installer creates a fresh local .env
from detected SQL details. The .env never stores an SQL password.

IMPORTANT: The app is a virtual localhost IDS/IPS prototype, not a real
network-wide router firewall. SQL persistence is verified by an INSERT and
readback during setup; live gateway events are queued then synchronized to SQL.
