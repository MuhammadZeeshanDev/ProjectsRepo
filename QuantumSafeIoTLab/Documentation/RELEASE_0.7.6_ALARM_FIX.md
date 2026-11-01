# QuantumSafe 0.7.6 — alarm correctness update

Requires 0.7.5 installed. Copy this ZIP alone to Updates and run UPDATE_APP.bat.

## Fixed
- Alarm/desktop notification attempts only for **new** `BLOCK` security incidents from the virtual HTTP gateway or manual content policy.
- `ALLOW`, `REVIEW`, and `UNKNOWN` events do not ring alarms.
- A bounded per-operator-session incident ledger suppresses repeat alarms on Streamlit's 3-second refresh and on later normal events.
- Virtual HTTP events now include a unique `event_id`, avoiding timestamp collisions.
- Incident table includes actual target, reason, source, affected component and prevention guidance when available.
- Manual content checks no longer create a second alarm widget. The monitoring panel owns alarms.

## Limitations
- Browser autoplay/notification permissions may prevent audible or desktop delivery. Click Enable sound / notifications and Test alarm; this is not a Windows background alarm service.
- Existing event source is loopback-only virtual gateway. Unknown IP alone is NOT proof of malware.
- This release does not implement real IoT network scanning, independent device connectivity or authenticated ML-KEM sessions.
- Event history is in memory unless SQL event storage is configured.

## Acceptance tests
1. Start PC A and enable alarm; 10 normal requests -> no automatic alarm.
2. PC B sends one unauthorized request -> one blocked incident and one attempted alarm.
3. Wait 15 seconds -> no repeated alarms.
4. Send normal telemetry -> no new alarm.
5. Enter a plain website URL -> UNKNOWN, no alarm.
6. A direct-IP URL -> REVIEW, no alarm.
7. Enter configured credential-phishing text -> BLOCK, one alarm.

## Next milestones
- v0.7.7: device connection lifecycle, identity and per-device evidence.
- v0.8.x: authenticated ML-KEM sessions and admin ML Studio foundation.
