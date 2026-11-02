# QuantumSafe v0.9.0 — major alarm/time update

## Install
Install on top of v0.8.0 using the existing Updates/UPDATE_APP.bat. Keep only this ZIP in Updates. Back up the project and database first. Existing files in this package are cumulative from v0.7.4 to v0.8.0.

## Implemented
- Gateway-side alarm is queued immediately on the **first** confirmed blocked security request, independent of Streamlit fragment polling. Windows `winsound.Beep` plays on the **Windows computer running the gateway process**, not a remote browser.
- Alarm triggers for invalid gateway token, invalid per-device credential, tampering, replay and rate-limit rejection. Unknown/unregistered identity alone does not prove malice and does not trigger sound. Normal activity never triggers sound.
- Event IDs are deduplicated; audio playback happens on a background worker and does not delay HTTP requests.
- Islamabad/Pakistan PKT (+05:00) columns added in device monitoring and incident views. Existing UTC columns retained and SQL timestamps remain UTC.
- Device identities, one-click PC B launcher, device monitoring, SQL incident logging and other v0.8.0 features retained.

## Honest limitations
- Windows toast notifications are not implemented. The on-screen Streamlit incident list remains available.
- No authenticated end-to-end ML-KEM device sessions or ML-driven live HTTP detection in this release. Existing KEM self-tests remain.
- Windows sound depends on working speakers/audio and the gateway running on Windows. No claim of remote alarm delivery.
- The alarm engine is in-process; it does not persist its event deduplication ledger after a process restart.
- Live gateway uses localhost; no physical IoT device connection or real network intrusion detection.

## Test
Run `python -m unittest discover -s Tests -p test_major_090.py` from the project root with `SourceCode` on PYTHONPATH, or add `SourceCode` to PYTHONPATH. Manually verify Windows sound, SQL Server and Streamlit UI after installation.
