# QuantumSafe 2.0.1 — Gateway/Monitoring compatibility hotfix

## Reported error
`AttributeError: 'VirtualGateway' object has no attribute 'issue_viewer'` inside `security_monitor.show()`.

## Root cause
The v2.0.0 dashboard expects `VirtualGateway.issue_viewer`, while the actual **running** gateway object lacks the method. `issue_viewer` exists in the v2.0.0 package's `virtual_network.py`, so this is consistent with an incomplete or mixed source update, or a stale Streamlit Python process holding an old gateway instance. We cannot determine which occurred on the user's Windows machine from the traceback alone.

## Remediation
1. Close every QuantumSafe **PC A** and **PC B** browser/app launcher and terminate their running Streamlit Python processes (Ctrl+C in the windows that launched them). Make a project backup (including Data, ML_Artifacts and SQL Server backup separately).
2. Put this **only** `QuantumSafe_Update_2.0.1_Gateway_Viewer_Hotfix.zip` into `<QuantumSafeIoTLab>/Updates`, run `UPDATE_APP.bat`, type `YES`, verify "Application files updated".
3. Start the app **in a new Python process**, not through Streamlit's hot-reload. Sign in as Administrator and open **Live Security Monitoring**. Start gateway if needed from Devices & Installation.
4. Verify that `SourceCode/quantumsafe/virtual_network.py` includes `def issue_viewer(self, actor, *, lifetime=1200):`.
5. New dashboard issues authenticated short-lived viewer tokens. If the runtime is still old, monitoring degrades gracefully to an **authenticated read-only snapshot**, instead of crashing. Do not expose an unauthenticated viewer or weaken gateway token security.

## Included
- Reinstalls matching v2.0 `virtual_network.py` (device credentials, viewer authorization, virtual IPS, alarm, shadow ML).
- Updates monitoring to tolerate legacy running gateways, missing IPS/ML/alarm diagnostics and stale viewer sessions.
- Updates visible app version to `2.0.1`. No database/configuration/secret files or updater scripts are changed.

## Verification limits
Source code syntax and targeted behavioral tests pass in a Linux test container. User's actual Windows installed files, running Streamlit process, SQL Server and speaker cannot be remotely confirmed.
