# QuantumSafe — Beginner Team Explanation

**Why:** Connected sensors/cameras send network messages. We want a safe place to understand those messages and how a security system detects bad activity.

**What:** A local virtual IoT gateway, a secure communication demonstration (ML-KEM), a security event dashboard, a SQL Server history store, and a saved Random Forest classifier for compatible Edge-IIoTset CSV data.

**How:** Virtual client sends an HTTP telemetry request → gateway checks token, message integrity, replay nonce and rate limit → ALLOW/BLOCK → monitoring and optional SQL persistence. Separately, CSV → 10 expected features → saved preprocessor → RF → normal/attack predictions → summary/history.

**ML-KEM:** Encryption key establishment, NOT machine learning. 512/768/1024 are parameter set identifiers, NOT bit counts. ML-KEM establishes a shared secret, then symmetric encryption can protect data. A separate RF model predicts attack/normal.

**32 characters:** Number of text characters does not tell you secret strength. Check whether a field requires characters, bytes, or random entropy.

**Accounts:** Admin provisions accounts and roles. Researcher runs experiments. Viewer reviews outputs. No public signup.

**Limitations:** No real packet sniffing, no hardware integration, no ML-based blocking, no production firewall. Avoid presenting exploratory accuracy as independent real-world performance.
