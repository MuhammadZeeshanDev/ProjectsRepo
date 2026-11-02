"""Read-only measured virtual gateway evidence and local IDS model statistics.

No fabricated packet totals, device telemetry, or predictive attack probabilities.
The underlying local gateway deque is limited and may contain only recent events.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import math
from datetime import datetime, timezone, timedelta
from . import console_data


def rows(events, now=None, *, hours=24):
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(hours=hours)
    clean = []
    for event in events:
        if event.get('decision') not in ('ALLOW', 'BLOCK'):continue
        when = console_data.parsed_time(event.get('timestamp_utc'))
        if when is None or when > now + timedelta(seconds=5) or when < start:continue
        clean.append({
            'time_utc':when, 'device':str(event.get('device') or 'unknown')[:64],
            'decision':event['decision'],
            'reason':str(event.get('reason') or 'unknown')[:160],
            'source_ip':str(event.get('source_ip') or 'unknown')[:70],
            'attack_type':str(event.get('attack_type') or 'Unclassified')[:100],
            'reading':event.get('reading') if isinstance(event.get('reading'),(int,float)) and not isinstance(event.get('reading'),bool) and math.isfinite(event['reading']) else None,
        })
    return sorted(clean,key=lambda x:x['time_utc'])


def aggregate(events, now=None, *, hours=24, bin_minutes=15):
    """Deterministic result for the analytics view; zero-value intervals are NOT synthesized."""
    safe = rows(events,now,hours=hours)
    by_device=defaultdict(lambda:{'ALLOW':0,'BLOCK':0})
    reasons=Counter(); by_bucket=defaultdict(lambda:{'ALLOW':0,'BLOCK':0})
    readings=defaultdict(list)
    for e in safe:
        by_device[e['device']][e['decision']]+=1
        stamp=e['time_utc']; minute=stamp.minute - stamp.minute % bin_minutes
        b=stamp.replace(minute=minute,second=0,microsecond=0)
        by_bucket[b][e['decision']]+=1
        if e['decision']=='BLOCK':reasons[e['reason']]+=1
        if e['decision']=='ALLOW' and e['reading'] is not None:
            readings[e['device']].append({'time_utc':stamp,'reading':float(e['reading'])})
    return {'rows':safe, 'allow':sum(e['decision']=='ALLOW' for e in safe),
            'block':sum(e['decision']=='BLOCK' for e in safe),
            'by_device':dict(by_device),'reasons':dict(reasons),
            'by_bucket':dict(sorted(by_bucket.items())),
            'readings':{k:v[-300:] for k,v in readings.items()},
            'total':len(safe)}


def model_summary(registry_rows):
    result=[]
    for m in registry_rows:
        if not isinstance(m,dict):continue
        metrics=m.get('metrics') or m.get('heldout') or {}
        if not isinstance(metrics,dict):continue
        result.append({'id':int(m['id']),'algorithm':str(m.get('algorithm','Unknown'))[:70],
                       'status':str(m.get('status') or 'unknown'),
                       'macro_f1':metrics.get('macro_f1'),
                       'accuracy':metrics.get('accuracy'),
                       'latency_ms_per_row':metrics.get('latency_ms_per_row'),
                       'fit_seconds':metrics.get('fit_seconds'),
                       'rows':m.get('sample_rows'),
                       'features':len(m.get('features') or []),
                       'dataset_sha':str(m.get('dataset_sha256') or '')[:12]})
    return result
