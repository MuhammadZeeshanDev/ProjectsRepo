"""Pure, deterministic alert selection for the virtual lab.

Only confirmed gateway/policy BLOCK decisions may ring the alarm.
This is not a malware classifier or an IP reputation service.
"""

def event_identity(event):
    """Stable within the current gateway process; event_id preferred for persisted records."""
    return str(event.get('event_id') or id(event))


def alarm_eligible(event):
    if not isinstance(event, dict):
        return False
    return (str(event.get('decision', '')).upper() == 'BLOCK'
            and event.get('source') in ('LOCAL_HTTP', 'MANUAL_CONTENT_RULES'))


def next_alarm_event(events_newest_first, previously_seen, max_history=500):
    """Return newest *new* qualifying incident and updated bounded ledger.

    Seen includes normal events too, so refreshes cannot resurrect old alerts.
    """
    seen = set(previously_seen)
    fresh = [e for e in events_newest_first if event_identity(e) not in seen]
    new_seen = [event_identity(e) for e in events_newest_first[:max_history]]
    # Keep IDs not in the current window to avoid duplicates across short refreshes.
    combined = list(dict.fromkeys(new_seen + list(previously_seen)))[:max_history]
    for event in fresh:
        if alarm_eligible(event):
            return event, combined
    return None, combined
