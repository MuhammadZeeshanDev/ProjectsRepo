"""Pure event summaries; works with virtual gateway events and SQL history."""
from collections import Counter

def device_summary(events, registered_devices):
    rows=[]
    for device_id, kind in registered_devices.items():
        own=[e for e in events if e.get('device')==device_id]
        rows.append({'Device ID':device_id,'Device type':kind,
          'Observed requests':len(own),'Allowed':sum(e.get('decision')=='ALLOW' for e in own),
          'Blocked':sum(e.get('decision')=='BLOCK' for e in own),
          'Last observed UTC':next((e.get('timestamp_utc','') for e in own),'Never'),
          'Connection status':'Not verified (event history only)'})
    return rows

def incident_summary(events):
    blocked=[e for e in events if e.get('decision')=='BLOCK']
    return {'observed':len(events),'blocked':len(blocked),
      'by_target':dict(Counter(e.get('device','unknown') for e in blocked)),
      'by_reason':dict(Counter(e.get('reason','unknown') for e in blocked))}
