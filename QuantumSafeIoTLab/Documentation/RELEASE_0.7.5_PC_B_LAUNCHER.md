# QuantumSafe v0.7.5 — PC B one-click launch

## Included
- On the Defender > Gateway & Alerts screen, **Administrator** can click **Open PC B Test Station**.
- Windows users can double-click `SourceCode/Launch_PC_B.pyw` to open PC B without typing PowerShell commands (requires Python `.pyw` file association).
- Launcher uses the **same Python interpreter** as the main Streamlit process and starts PC B at `http://127.0.0.1:8502`.
- Launcher checks whether port 8502 is already listening before starting a new instance. It does not verify the identity of an existing process on that port; use a dedicated lab PC.
- PC B remains a separate credential-free interface. Defender gateway must still be started on port 8765.

## Quick test
1. Start QuantumSafe and sign in as Administrator.
2. Open **Gateway & Alerts**; click **Start local gateway**.
3. Click **Open PC B Test Station** (or double-click `SourceCode/Launch_PC_B.pyw`).
4. Choose a virtual device and run a controlled test; check Defender alerts and SQL history.

## Scope
This is a launcher and usability release, not a true second VM or a new cryptographic session. It does not add ML-KEM authenticated IoT connections, Prolog reasoning or new ML models. The Streamlit app and SQL Server must be configured as before.
