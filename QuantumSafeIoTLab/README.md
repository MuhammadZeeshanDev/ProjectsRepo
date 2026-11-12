# QuantumSafe IoT Security Lab — v2.1.0 Final Virtual Prototype

**What this software does:** A locally hosted **virtual** IoT security management demo with Admin and Security Operator roles, SQL Server 2022 audit storage, device enrollment, localhost virtual gateway and simulated IPS, PC B security testing, CSV-trained Random Forest/XGBoost/LightGBM, SWI-Prolog evidence-based rules, analytics and an actual **ML-KEM-768 + HKDF-SHA256 + AES-256-GCM** encrypted virtual device-to-device exchange.

**What it does NOT do:** This does not intercept a physical Wi-Fi/LAN or act as a router firewall. Virtual devices and the two endpoint agents execute inside PC A's Python process. Physical endpoints need separately installed clients, secure key provisioning and real network routing. Training large CSVs is resource-bounded; a very large local file is scanned and a controlled sample is trained. There is no infinite-size or universal unlabeled CSV model training. Automatic model-based blocking of real traffic is not implemented.

## Windows 11 / Windows 10 setup
1. Install **Python 3.11 or 3.12** (with `py` launcher), SQL Server 2022 and Microsoft **ODBC Driver 18 for SQL Server**. Install **SWI-Prolog** to use native rule evaluation (optional; a clearly labeled Python fallback is available).
2. Run `INSTALL_WINDOWS.bat` in this extracted folder. It creates `.venv`, installs `pqcrypto==1.0.0`, Streamlit, scikit-learn, XGBoost, LightGBM and pyodbc. Do not run this from the parent project folder.
3. In **SQL Server Management Studio**, run `Database/01_create_database.sql` and then `Database/02_upgrade_v02.sql`. The application auto-initializes or upgrades gateway event tables on SQL connect. `Database/03_secure_device_audit.sql` is also provided for an explicit optional metadata migration/read-back.
4. Run `CONFIGURE_SQL_WINDOWS.ps1` (or launch through PowerShell) and specify your actual SQL Server instance name. Windows Authentication is required. For a trusted *development* server with a self-signed SQL TLS cert, explicitly opt into TrustServerCertificate. For real use, install a valid server certificate instead.
5. Run `BOOTSTRAP_ADMIN.bat` to register the first Admin in SQL Server.
6. Run `VERIFY_FINAL_SYSTEM.bat` and note the actual SQL, ML-KEM and SWI-Prolog results. **Only PASS means tested on your machine.**
7. Run `START_MAIN_APP.bat`. Login as Admin and open `Devices & Installation` → start gateway → `ML-KEM · Encrypted Device-to-Device Gateway`.
8. Run `START_PC_B.bat` or open Admin → `PC B Security Tests` for rejected-access demos.

### If you already have a QuantumSafe v2.x installation
- Shut down PC A and PC B. Back up **all** existing folders and SQL Server database before upgrading.
- The clean ZIP deliberately omits your existing `.env`, `Data` (device credentials, alert acknowledgement, SQL outbox), and `ML_Artifacts` (models/history). **To retain old accounts, devices, queued events, and saved models, migrate those local folders from your own backed-up project. Never share secrets or merge with public repos.**
- Re-use `.env` only on your own trusted machine. Set correct SQL Server 2022 instance name. Keep the old project as rollback until validation is complete.
- This ZIP is a **full application**, not a safe-updater overlay. Extract it to a **new directory**. Do not put this ZIP into `Updates/`.

## Operator / Administrator permissions
- Admin: monitoring, analytics, device installation/disable/rotation/quarantine, encrypted device test, ML CSV training and model review/import, PC B demo and accounts.
- Security Operator: monitoring and analytics only (read-only). Legacy DB role string is `Researcher` for compatibility with prior SQL records.
- Never give operators access to training, key material, PC B attack testing, or device modifications.

## ML-KEM demonstration
1. Ensure `VERIFY_FINAL_SYSTEM` shows real ML-KEM-768 cryptography PASS, and the virtual gateway is running.
2. Two devices are enrolled and active. In Devices & Installation open the **ML-KEM** expander.
3. Choose a source and recipient, send an ordinary message, observe ML-KEM ciphertext size, AES-GCM ciphertext size, SHA-256 and successful recipient authentication/decryption. Only the admin's local demo shows the recovered plaintext.
4. Change scenario to **Tamper**: receiver must reject the altered AES-GCM authentication tag. **Replay**: first delivery accepted, second rejected.
5. Observe secure-mesh events in the main monitoring dashboard and analytics. Use SQL Diagnostics to verify SQL read-back (not merely queued).
6. In SSMS run the query in `Database/03_secure_device_audit.sql` to see nonsecret cryptography audit fields. **Device secret/private keys, ML-KEM session secrets and plaintext are never written to gateway SQL logs.**

### Security design
ML-KEM is a **key-encapsulation mechanism**, not a message cipher. The endpoint encapsulates a secret for the recipient's fresh ML-KEM public key, derives a symmetric key with HKDF-SHA256, and encrypts the payload with AES-256-GCM. Source/destination IDs and a fresh nonce are authenticated as additional associated data. A gateway forwarding step handles ciphertext only. The demo checks enrolled/active endpoints and virtual quarantine. The in-memory agents are simulated, not separate hardware security boundaries; on actual devices implement authenticated public-key distribution, device attestation and client-side key custody.

### Persistence
- SQL Server: users/auth, audit tables, virtual device inventory and allowed/rejected gateway events including ML-KEM nonsecret audit metadata, **only after confirmed sync**.
- Host-local `Data`: device identity credentials, queued SQL events while SQL unavailable, acknowledgements, virtual quarantine state. Protect folder access and back up securely.
- Host-local `ML_Artifacts`: trained checkpoints, model metadata, Prolog recommendations and test history. Loading arbitrary `joblib` files is unsafe; only import models you trust.

## Verify
`PYTHONPATH=SourceCode python -m pytest -q Tests/test_final_crypto_mesh.py Tests/test_final_virtual_integration.py` can run a simulated control-path test. Those tests stub the KEM interface; **they do not prove actual native ML-KEM**. The **real** `VERIFY_FINAL_SYSTEM.bat` invokes the installed `pqcrypto` library. Native SQL and SWI-Prolog were not runnable in this build environment; local verification is essential.

Full docs: `Documentation/FINAL_RELEASE_GUIDE.md`.

---

## v2.2.0 portable Windows release (new recommended instructions)

Please read **`README_FIRST.txt`** or `Documentation/PORTABLE_INSTALLATION_v2.2.md`.
**First launch:** `INSTALL_AND_START.bat` (auto-dependency download, .env discovery, SQL schema + readback, temporary administrator). **Later launches:** `START_APP.bat`. Old installation instructions elsewhere in this README are superseded by these two entry points.
