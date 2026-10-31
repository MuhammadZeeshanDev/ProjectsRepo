"""Deterministic, offline, educational gateway policy simulation. NOT live packet filtering."""
from datetime import datetime, timezone

SCENARIOS = {
    'Normal CCTV telemetry': ('cctv-01', 'telemetry', True, False, False, 1),
    'Unauthorized camera access': ('cctv-01', 'access', False, False, False, 1),
    'Repeated message (replay)': ('sensor-01', 'telemetry', True, True, False, 1),
    'Modified message (tamper)': ('cctv-01', 'telemetry', True, False, True, 1),
    'Excessive request rate': ('router-01', 'telemetry', True, False, False, 120),
}

def evaluate(name):
    if name not in SCENARIOS:
        raise ValueError('Unknown test scenario')
    device, action, authenticated, replay, tamper, requests = SCENARIOS[name]
    if not authenticated:
        outcome, reason = 'BLOCK', 'Authentication failed'
    elif replay:
        outcome, reason = 'BLOCK', 'Replay protection policy'
    elif tamper:
        outcome, reason = 'BLOCK', 'Integrity check failed'
    elif requests > 60:
        outcome, reason = 'BLOCK', 'Simulated rate limit exceeded'
    else:
        outcome, reason = 'ALLOW', 'Passed simulated gateway policies'
    return {'timestamp_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'device': device, 'scenario': name, 'request_type': action,
            'requests': requests, 'decision': outcome, 'reason': reason,
            'source': 'SIMULATED'}
