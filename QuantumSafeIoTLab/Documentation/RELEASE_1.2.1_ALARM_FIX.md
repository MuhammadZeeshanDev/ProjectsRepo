# QuantumSafe v1.2.1 — Windows alarm compatibility fix

Prerequisite: v1.2.0; install this ZIP using UPDATE_APP.bat with only this update in Updates.

Fix: Python winsound does not define SND_SYNC. PlaySound without SND_ASYNC is synchronous by default. The alert now calls `winsound.PlaySound(..., winsound.SND_ALIAS)` and still attempts Beep fallback when system sounds fail.

This update only replaces SourceCode/quantumsafe/realtime_alarm.py. ML Lab, AI, columns, Pakistan timestamps, and PC B are not changed.

Test the Windows speaker button, then trigger an authorized simulated unauthorized-access test from PC B. Audio playback still depends on Windows speaker settings and the machine hosting the gateway.
