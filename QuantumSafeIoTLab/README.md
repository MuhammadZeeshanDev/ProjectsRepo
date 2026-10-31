# QuantumSafe IoT Lab — v0.2 (Python + SQL Server 2022)

**ONE working software project for TWO university CCPs:** Cybersecurity and Software Engineering. **This is not an IDS** (no unknown-attack detection, sniffing or ML attack classifier). v0.2 adds GUI buttons for local crypto tests, real private-LAN communication between two computers, controlled integrity/replay/authentication tests, benchmark comparisons, a built-in test runner and an SQL security-event history. It is a **virtual IoT simulation**, not a physical ESP32 or battery/power experiment.

## ⭐ IMPORTANT: If you already used v0.1 (Admin user exists)

Your existing SQL Server is `ZEESHAN\SQLEXPRESS` and your database should already exist. **DO NOT delete the old database or recreate the Admin.**

1. Extract this v0.2 ZIP to a **new folder** in VS Code.
2. From your existing v0.1 folder, **COPY your working `.env` file** into the new v0.2 `QuantumSafeIoTLab` root. The example `.env.example` is not the actual config. The ZIP intentionally does **not** contain your secret `.env` or your admin password.
3. In **SSMS → New Query**, open and run **only** `Database/02_upgrade_v02.sql` against `ZEESHAN\SQLEXPRESS`. It adds the `SecurityEvents` table; the five old tables and records are preserved. Check `SELECT name FROM QuantumSafeIoTLab.sys.tables WHERE name='SecurityEvents';`.
4. Open VS Code terminal in this v0.2 project folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python SourceCode/check_system.py
python -m pytest -q Tests
python -m streamlit run SourceCode/app.py --server.address 127.0.0.1
```

5. Open `http://localhost:8501` and **log in with your EXISTING admin `zeeshan` and existing password**. Do **not** run `setup_admin.py` a second time.
6. Alternatively after the virtual environment is ready, double-click `START_MAIN_APP.bat`. Keep its window open while the application is used.

**If starting completely fresh:** First run `Database/01_create_database.sql` in SSMS, then `Database/02_upgrade_v02.sql`, create `.env` from `.env.example`, install requirements and run `python SourceCode/setup_admin.py` once.

## 📱 Every important feature has a frontend button

| App screen | Frontend buttons and what they do |
|---|---|
| 🏠 Dashboard | Quick links to local demo, LAN Lab, benchmark, Test Center, results |
| 🔒 Secure Demo | **Send Encrypted Reading**, **Test Modified Ciphertext**; saves outcomes to `SecureDemoTests` |
| 🌐 LAN Lab → Gateway | **Generate Strong Secret**, **Start Gateway**, **Stop Gateway**, **Refresh**, **Show My Computer IP**; choose port and optional LAN access; see in-memory event counts |
| 🌐 LAN Lab → Send / attack tests | **Check Gateway Connection**, **Normal**, **Tamper**, **Replay**, **Unauthorized Sender**, **Substituted Public Key**, **Run ALL 5**, **Run ALL 15 (3 algorithms × 5 tests)**, **Export CSV** |
| 🌐 LAN Lab → Security events | **Refresh Saved Events**, **Export Events CSV**; reads SQL `SecurityEvents` |
| ⚡ Run Benchmark | **Benchmark Selected Algorithm**, **Benchmark ALL 3 Algorithms**, **Download Summary CSV**; stores raw timing samples to SQL |
| 🧪 Test Center | **Test SQL Connection**, **Check Database Tables**, each **ML-KEM self-test**, **ALL 3 tests**, **Normal Local Demo**, **Tampered Local Demo**, **Run Automated Tests Now** |
| 📊 Results | **Compare latest three algorithms**, select saved experiments; see charts, download measured CSV |
| 👥 Users (Admin only) | Create users, enable/disable accounts, change account access |

**Permissions:** Admin = all controls, Researcher = permitted demo, network send, benchmarks and checks, Viewer = saved results only. Only Admin can start/stop the network listener and run pytest from the UI.

## 🌐 TWO REAL COMPUTERS: how to demo safely

You need two Windows computers (A and B) connected to the **same private/trusted LAN or personal hotspot**. They run Python code on their **respective devices**. The IoT sensor and gateway are still *software-based*, not real microcontrollers.

### Computer A = Gateway / Receiver

1. Run the **main app** from the steps above, sign in as Admin.
2. Open **🌐 LAN Lab → Gateway controls**.
3. Press **Generate strong shared secret**. This produces a fresh random 256-bit secret. Do not use a simple password. Copy it securely to Computer B (not a public chat). It is only kept in the app's memory and is never sent to the gateway over HTTP.
4. Choose port **8765** (or any free port 1024–65535). For an actual second computer, tick **Allow another computer on my private LAN**. This binds the gateway to `0.0.0.0` (all interfaces). If unticked, only this computer can connect on `127.0.0.1`.
5. Click **Start Gateway**. **Keep the main Streamlit app running**. You can press **Stop Gateway** whenever finished.
6. Get A's **private IPv4** using the UI **Show My Computer Name / Private IP**. If it does not return the right Wi-Fi address, on Windows use `Settings → Network & internet → Wi-Fi / Ethernet → Properties → IPv4 address`, or `ipconfig`. Common private addresses are `192.168.x.x` or `10.x.x.x`; do **not** use the Streamlit Network URL as a gateway address.
7. If Computer B cannot connect, Windows Defender Firewall on Computer A may block port 8765. Create an **inbound TCP rule for 8765 on PRIVATE networks only**, scoped to Computer B's private IP if possible. Do not disable the firewall or allow Public networks. No port forwarding.

### Computer B = Real Peer / Sender, WITHOUT SQL Server

1. Copy the **entire v0.2 ZIP** to B and extract it. **Do not copy the `.env` or database credentials**. B does not need SSMS, SQL Server or admin setup.
2. Open the folder in VS Code; install Python 3.12 and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements_peer.txt
python -m streamlit run SourceCode/peer_console.py --server.address 127.0.0.1 --server.port 8502
```

3. Or after installation, double-click `START_PEER_CONSOLE.bat`. Open `http://localhost:8502` **on Computer B**.
4. Enter **Computer A's private IPv4**, port **8765**, the **same strong secret**, choose ML-KEM-512/768/1024 and a temperature.
5. Press **Check Gateway Connection** (reachability only) and **Normal Encrypted Reading**. Then click the four other security test buttons, or **Run ALL 5 Security Tests**. The code makes real HTTP requests **from B to A**. A handles genuine ML-KEM key establishment and AES-GCM protection, not a recorded or fake output.
6. On **A**, click **Refresh Gateway Status** to see events, and **Security events → Refresh Saved Events** to see what SQL Server stored. Export CSV for your CCP evidence. When done, **Stop Gateway** and remove the temporary Windows firewall rule.

### What the security scenarios actually prove

| Button | What happens | Expected result |
|---|---|---|
| Normal | ML-KEM encapsulation + HKDF + AES-GCM encrypted sensor reading | **Accepted** |
| Tampered | Change one encrypted byte, attempt to decrypt at gateway | **AES-GCM rejects**, event logged |
| Replay | Deliver the EXACT same authenticated ciphertext packet twice | First **accepted**, second **rejected** |
| Unauthorized | Sender's PSK-based HMAC is deliberately wrong | **Authentication rejected** |
| Substituted public key | Simulate replacement of public key after obtaining gateway's proof | Client **rejects before sending**, local-only control (no packet delivered) |

**Technical scope and trust assumptions:** This *educational* PSK-authenticated handshake uses HMAC-SHA256 for proof of gateway key and sender, actual ML-KEM from `pqcrypto`, HKDF-SHA256 and AES-256-GCM. The shared secret must be obtained through a trustworthy separate channel and must remain secret; it is not a PKI, not full TLS, not tested against comprehensive MITM/DoS attacks, and does not authenticate physical sensors. The HTTP transport exposes **metadata**, though temperature data is encrypted. Run **only on your own controlled private LAN**. The protocol has not undergone an external security audit. **Do not expose the gateway to the public internet.** The UI is also intentionally bound to localhost. An attacker without the secret may still overload/interrupt this educational service; this is not a hardened network service.

## 🗄️ SQL Server database and testing evidence

Your old tables remain: `Users`, `Experiments`, `Measurements`, `SecureDemoTests`, `AuditLogs`.
New table: `SecurityEvents`, containing only the **event name, accepted/rejected outcome, source IP, algorithm and UTC date/time**; it never stores sensor values, passwords, private keys, shared secret or ciphertext. While gateway runs, recent event counts also live temporarily in RAM. Restarting app clears RAM events but *saved* SQL records remain. If SQL is unavailable during a network packet, gateway can still process it; check the SQL Events tab for persistence status.

For SSMS verification:

```sql
USE QuantumSafeIoTLab;
GO
SELECT TOP 20 EventId, EventName, Outcome, SourceIp, Algorithm, CreatedAtUtc
FROM dbo.SecurityEvents ORDER BY EventId DESC;
```

The **Test Center** executes code tests from the UI, with live SQL test enabled. In a terminal you can run `python -m pytest -q Tests`. Tests for protocol logic use a mocked ML-KEM adapter to isolate networking; an additional test uses **actual installed pqcrypto** when available. No test count is claimed before running on your Windows machine. Real LAN success must be verified using two machines and is NOT proven by localhost tests.

## 🧩 Small source-code files

| Location | Responsibility |
|---|---|
| `SourceCode/app.py` | Login/session and screen navigation |
| `SourceCode/peer_console.py` | Standalone GUI for second computer (no SQL) |
| `quantumsafe/crypto_engine.py` | Actual ML-KEM wrapper |
| `quantumsafe/sensor_demo.py` | Local AES-GCM demonstration; HKDF helper |
| `quantumsafe/lan_protocol.py` | Packets, Base64 and HMAC proofs |
| `quantumsafe/lan_gateway_core.py` | Gateway key exchange, decrypt, replay and event logic |
| `quantumsafe/lan_gateway_server.py` | HTTP request parsing for gateway |
| `quantumsafe/lan_gateway.py` | Start/Stop gateway listener on UI click |
| `quantumsafe/lan_client.py` | Peer networking, ML-KEM, normal/security scenario logic |
| `quantumsafe/security_events.py` | SQL Server security event records |
| `quantumsafe/ui/lan_page.py` | Three-tab LAN Lab frontend |
| `quantumsafe/ui/peer_page.py` | Five big network-test buttons frontend |
| `quantumsafe/ui/test_center.py` | Built-in manual and pytest UI controls |
| `quantumsafe/ui/*` | Other small UI screens |
| `Database/01_create_database.sql` | Base tables (existing v0.1) |
| `Database/02_upgrade_v02.sql` | **Non-destructive v0.2 update** |
| `Tests/` | Unit, protocol and localhost network tests |

## Research honesty and deliverables

- **Cybersecurity CCP:** compare three actual ML-KEM parameter sets, key establishment, AES-GCM encryption, integrity failure, replay & unauthenticated sender rejection on a virtual IoT peer and private LAN. Measurements are wall-clock **host-PC** timings only, not battery/microcontroller results. No IDS claims.
- **Software Engineering CCP:** same project code and SQL Server; document SRS, database ERD, permissions, UML, UI, requirements traceability, Git history, real tests and screenshots.
- Final DOCX/PDF academic reports are **not included at this development stage**, per the plan to compile them when implementation is complete.
- This build was tested **offline in the packaging environment** with synthetic (mocked) ML-KEM for network tests, without a live SQL Server or a second Windows machine; user's successful v0.1 native ML-KEM test does not prove every new v0.2 workflow. Validate on your two devices before treating it as final evidence.
