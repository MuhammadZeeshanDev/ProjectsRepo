# QuantumSafe IoT Lab — User Manual (v0.6.0)

## Why this lab exists
A virtual learning environment to demonstrate IoT network requests, rule-based gateway security, basic phishing-style message alerts, ML-KEM key establishment, and offline ML attack classification. **Not** a browser protection extension, production firewall, or live ML IDS.

## Roles
Admin creates accounts and assigns Admin / Researcher / Viewer roles. Users do not self-register. Researchers run lab tests; Viewers see the overview. Admin can manage users.

## Start
Install the ZIP using `UPDATE_APP.bat` (keep only one update ZIP in `Updates`). Restart the app using your existing large-file launcher: `& "..\.venv\Scripts\python.exe" SourceCode\launch_large_csv.py`.

## Demonstration A — suspicious text and alarm
1. Sign in as Admin or Researcher.
2. Open **Gateway & Alerts**.
3. Enter `Urgent bank verification: send your password` and click **Check & test alert**.
4. Expect **BLOCK** and an audio control with a short beep. If sound does not autoplay, press Play.
5. Enter `Temperature sensor reading: 23` and click again. Expect **ALLOW (no configured pattern matched)**. This is **not** proof that content is safe.
6. Check live monitoring. If SQL event table is initialized, review saved events below.

## Demonstration B — HTTP gateway
1. Click **Start local gateway**.
2. Select **CCTV**, click **Send request**; expect ALLOW.
3. Select **Unauthorized access**, click **Send request**; expect BLOCK.
4. Try **Tampered message**, **Replay attack**, **Rate limit**; explain each rule.
5. Click **Stop local gateway**.

## Demonstration C — offline ML
Open **ML Detection**, select a compatible Edge-IIoTset CSV and run the saved SA-HFS v3 Random Forest. Ten original TCP/MQTT features are preprocessed to eleven inputs. Results are exploratory; model does not currently classify gateway HTTP requests.

## Demonstration D — ML-KEM
Open **ML-KEM Secure Demo**. Compare ML-KEM-512, -768 and -1024. They are parameter sets for establishing shared secrets, **not** ML classifiers or direct encryption of application data.

## What remains before public release
- Verify end-to-end Windows and SQL Server operation.
- Add true TCP/MQTT feature extraction and validate against saved RF preprocessing before any gateway ML classification.
- Add full permission and audit tests; review secure defaults and credential handling.
- GitHub security scan, remove secrets, backups, virtualenv and private datasets.
- Real malicious-link reputation or browser-wide blocking would need a separate trusted service/extension; not provided by this lab.
