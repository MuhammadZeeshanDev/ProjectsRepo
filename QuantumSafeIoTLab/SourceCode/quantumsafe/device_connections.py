"""Virtual device connection observations; never claim real network connectivity."""
from datetime import datetime, timezone

DEVICE_TYPES = {
    'virtual-cctv-01': 'CCTV camera',
    'virtual-router-01': 'Network router',
    'virtual-sensor-01': 'Temperature sensor',
}

def connection_rows(events, registered_devices, now=None, active_seconds=30):
    """Report recent authenticated successful telemetry, not physical network state.

    A blocked request does not change a previously healthy device into malicious.
    """
    now = now or datetime.now(timezone.utc)
    latest_good = {}
    latest_attempt = {}
    counts = {device: {'allowed': 0, 'blocked': 0} for device in registered_devices}
    for event in events:
        device = str(event.get('device', ''))
        if device not in registered_devices:
            continue
        decision = str(event.get('decision', '')).upper()
        if event.get('source') != 'LOCAL_HTTP' or decision not in ('ALLOW', 'BLOCK'):
            continue
        counts[device]['allowed' if decision == 'ALLOW' else 'blocked'] += 1
        when = _time(event.get('timestamp_utc'))
        if when is None:
            continue
        if device not in latest_attempt or when > latest_attempt[device]:
            latest_attempt[device] = when
        if decision == 'ALLOW' and (device not in latest_good or when > latest_good[device]):
            latest_good[device] = when
    rows = []
    for device, label in registered_devices.items():
        last = latest_good.get(device)
        age = (now - last).total_seconds() if last else None
        status = 'ACTIVE (observed)' if age is not None and 0 <= age <= active_seconds else ('IDLE (last seen)' if last else 'NOT OBSERVED')
        rows.append({'Device ID': device, 'Type': label, 'Connection observation': status,
                     'Last trusted activity (UTC)': last.isoformat(timespec='seconds') if last else 'Never',
                     'Allowed': counts[device]['allowed'], 'Blocked attempts': counts[device]['blocked'],
                     'Identity': 'Registered (virtual)'})
    return rows

def unknown_attempts(events, registered_devices):
    """Unknown claimed device IDs; cannot verify real source identity from a string."""
    return [e for e in events if e.get('source') == 'LOCAL_HTTP'
            and str(e.get('device', '')) not in registered_devices]

def _time(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None
