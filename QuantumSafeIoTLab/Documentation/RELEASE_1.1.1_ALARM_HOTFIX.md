# QuantumSafe v1.1.1 — Alarm reliability hotfix

Requires v1.1.0 (or v0.9.0 plus later updates). Install alone using UPDATE_APP.bat. Existing ML Studio, AI Advisor, columns, PKT formatting and PC B launcher are not modified.

## Fixes
- First security BLOCK event queues Windows sound immediately, independent of Streamlit rerun.
- Adds missing **unregistered device access attempts** to the alarm policy.
- Adds PC A Windows speaker test and visible queue / played / failure counters. Previously the alarm worker silently discarded all audio failures.
- Restores browser audio fallback for freshly observed incidents. Browser autoplay still requires an enabled audio context and will not be reliable on all browsers.
- Deduplicates by event ID; ordinary ALLOW, REVIEW and invalid-format events do not ring.

## Troubleshooting
1. Use **Gateway & Alerts → Test Windows speaker (PC A)**; inspect Played / failures and error text after a refresh.
2. Verify Windows sound output, Volume Mixer, audio service, and that the gateway runs on the PC where the speaker is attached.
3. If the test shows played but no audible sound, Windows sound settings or output routing can still be silent; the software cannot prove acoustic playback.
4. Run PC B unauthorized test; the first BLOCK should queue 1 alarm. Refreshing the dashboard should not enqueue the same incident.

Only gateway-owned security decisions trigger alarms. Does not classify arbitrary URLs or turn unknown IP alone into malware. Windows speaker integration requires actual Windows device test.
