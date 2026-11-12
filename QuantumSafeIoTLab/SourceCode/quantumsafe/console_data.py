"""Data adapter for the reference-style dashboard; NO invented traffic or firewall claims.

Reads already observed virtual HTTP gateway events and enrolled devices. The dashboard
is deliberately read-only: application actions retain their Streamlit role checks.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ACK_DB = Path(__file__).resolve().parents[2] / 'Data' / 'console_alerts.sqlite3'


def parsed_time(stamp):
    try:
        if isinstance(stamp, datetime):
            dt = stamp
        else:
            dt = datetime.fromisoformat(str(stamp or '').replace('Z', '+00:00'))
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def identity(event):
    # EventId is a SQL auto-increment value; event_id is a gateway uuid, so
    # instead use a canonical fingerprint shared across both storage systems.
    ts=parsed_time(event.get('timestamp_utc'))
    normalized_time=ts.isoformat(timespec='seconds') if ts else str(event.get('timestamp_utc') or '')
    stable = [normalized_time] + [str(event.get(k) or '') for k in
              ('device', 'decision', 'reason', 'source_ip', 'request_type')]
    return hashlib.sha256(json.dumps(stable, ensure_ascii=True).encode()).hexdigest()[:24]


def persistent_alert_uid(event):
    """Prefer gateway's immutable event UUID for stable alert acknowledgement.

    SQL mirroring can replace the in-memory version of the same event, and
    ordinal/fingerprint identifiers can then shift. The gateway UUID is
    preserved by the SQL outbox and survives that transition.
    """
    event_id = event.get('event_id')
    if isinstance(event_id, str) and re.fullmatch(r'[0-9a-fA-F]{32}', event_id):
        return hashlib.sha256(('gateway:' + event_id.lower()).encode('ascii')).hexdigest()[:24]
    return None


def _connect(db_path=None):
    path=Path(db_path or ACK_DB)
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path, timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS alert_ack (event_uid TEXT PRIMARY KEY, acknowledged_utc TEXT NOT NULL, actor TEXT NOT NULL)')
    db.commit()
    return db


def acknowledge(event_uid, actor, db_path=None):
    if not isinstance(event_uid, str) or len(event_uid)!=24 or any(c not in '0123456789abcdef' for c in event_uid):
        raise ValueError('Invalid alert identifier')
    if not actor or actor.get('RoleName')!='Admin':
        raise PermissionError('Only Administrator can acknowledge an alert')
    with _connect(db_path) as db:
        db.execute('INSERT OR IGNORE INTO alert_ack VALUES (?,?,?)',
                   (event_uid, datetime.now(timezone.utc).isoformat(),str(actor.get('Username','Admin'))[:80]))


def acked_uids(db_path=None):
    with _connect(db_path) as db:
        return {r[0] for r in db.execute('SELECT event_uid FROM alert_ack')}


def merge_events(local_events, sql_events=None):
    """Merge mirrored stores as event multisets: do not collapse simultaneous attacks.

    SQL Server records and the local deque can contain the same request. They may
    also contain *distinct* requests with identical second-level time and reason.
    For every fingerprint retain max(SQL count, local count), not one or the sum.
    """
    sql_groups=defaultdict(list);local_groups=defaultdict(list)
    for group, records in ((sql_groups,sql_events or []),(local_groups,local_events or [])):
        for ev in records:
            if isinstance(ev,dict) and ev.get('decision') in ('ALLOW','BLOCK'):
                group[identity(ev)].append(ev)
    combined=[]
    for fingerprint in set(sql_groups)|set(local_groups):
        sql=sql_groups[fingerprint];local=local_groups[fingerprint]
        # SQL is the durable source of truth. When both sides carry gateway UUIDs,
        # merge by UUID, NOT list position: newest-local-first versus SQL sync order
        # are not guaranteed to align. Positional fallback is only for legacy rows
        # without immutable gateway UUIDs.
        sql_ids={persistent_alert_uid(x) for x in sql}
        if sql_ids and all(persistent_alert_uid(x) for x in local):
            chosen=sql+[x for x in local if persistent_alert_uid(x) not in sql_ids]
        else:
            chosen=(sql + local[len(sql):]) if len(sql)<=len(local) else sql
        for ordinal,ev in enumerate(chosen):
            legacy_uid=hashlib.sha256(f'{fingerprint}/{ordinal}'.encode()).hexdigest()[:24]
            uid=persistent_alert_uid(ev) or legacy_uid
            combined.append(dict(ev,console_uid=uid,legacy_console_uid=legacy_uid))
    return sorted(combined,key=lambda x:parsed_time(x.get('timestamp_utc')) or datetime.min.replace(tzinfo=timezone.utc),reverse=True)


def severity(event):
    reason=str(event.get('reason') or '').lower()
    if 'integrity' in reason or 'tamper' in reason or 'authentication failed' in reason or 'quarantine' in reason: return 'critical'
    if 'replay' in reason or 'gateway token' in reason or 'per-device credential' in reason:return 'high'
    if 'rate limit' in reason or 'not registered' in reason:return 'medium'
    return 'medium'


def snapshot(gateway, sql_events=None, acked=None, now=None, model_count=0, routes=0):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('now must be timezone-aware')
    gateway_running=bool(gateway.server)
    # A gateway request thread may append while the monitor is refreshing.
    with gateway.lock:
        local_events=list(gateway.events)
    events=merge_events(local_events, sql_events)
    acked=set(acked or ())
    recent_24h=[e for e in events if (dt:=parsed_time(e.get('timestamp_utc'))) is not None and dt>=now-timedelta(hours=24)]
    # "requests" is not packet throughput. It is a COUNT of telemetry HTTP events.
    req=[0]*90
    blocked=[0]*90
    for ev in recent_24h:
        stamp=parsed_time(ev.get('timestamp_utc'))
        sec=(now-stamp).total_seconds()
        if 0<=sec<90:
            idx=89-int(sec)
            req[idx]+=1
            if ev['decision']=='BLOCK':blocked[idx]+=1
    frac=[round(blocked[i]/req[i],4) if req[i] else 0 for i in range(90)]
    latest_allow={};latest_block={}
    for ev in events:
        dev=str(ev.get('device') or '')
        if ev['decision']=='ALLOW' and dev not in latest_allow:latest_allow[dev]=ev
        if ev['decision']=='BLOCK' and dev not in latest_block:latest_block[dev]=ev
    active_quarantines=set()
    try:
        active_quarantines={x['device'] for x in gateway.ips.entries() if x['active']}
    except AttributeError:pass  # backward-compatible fake gateways in legacy tests
    devices=[]
    for item in gateway.registry.inventory():
        if item['status']=='retired':continue
        did=item['id']; allowed=latest_allow.get(did); rejected=latest_block.get(did)
        allow_time=parsed_time(allowed.get('timestamp_utc')) if allowed else None
        block_time=parsed_time(rejected.get('timestamp_utc')) if rejected else None
        active=bool(gateway_running and item['status']=='active' and allow_time and 0<=(now-allow_time).total_seconds()<=30)
        targeted=bool(gateway_running and item['status']=='active' and block_time and 0<=(now-block_time).total_seconds()<=30)
        status='quarantined' if item['status']=='disabled' or did in active_quarantines else ('attack' if targeted else ('online' if active else 'offline'))
        value=allowed.get('reading') if active and allowed else None
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):value=None
        # Configured IP is just a metadata label, not an assigned subnet host.
        devices.append({'id':did,'name':item['name'],'code':str(item['type'])[:3].upper(),
                        'type':item['type'],'zone':item['type']+' · virtual', 'ip':item.get('virtual_ip') or 'No virtual IP',
                        'unit':'reading', 'lo':0,'hi':max(100,value or 0),'base':None,'value':value,
                        'dec':2,'status':status,'observed_ip':allowed.get('source_ip') if allowed else None,
                        'last_seen_utc':allow_time.isoformat() if allow_time else None,
                        'enrollment':item['status']})
    alerts=[]
    for ev in events:
        if ev['decision']!='BLOCK':continue
        dt=parsed_time(ev.get('timestamp_utc'))
        alerts.append({'id':ev['console_uid'],'ts':dt.isoformat() if dt else str(ev.get('timestamp_utc','')),
                       'severity':severity(ev),'title':str(ev.get('reason') or 'Rejected request')[:200],
                       'engine':'Virtual secure mesh · cryptography' if ev.get('request_type')=='encrypted_mesh' else 'Virtual HTTP gateway · rules','source_ip':str(ev.get('source_ip') or 'Unknown')[:70],
                       'device_id':str(ev.get('device') or ''),'action':str(ev.get('ips_action') or 'Request rejected by local gateway'),
                       'acknowledged':(ev['console_uid'] in acked or ev['legacy_console_uid'] in acked)})
        if len(alerts)>=40:break
    rejected_count=sum(e['decision']=='BLOCK' for e in recent_24h)
    msg=('Local virtual gateway active — data is from authenticated HTTP telemetry, encrypted virtual device messages and recorded rejections. '
         'Not physical LAN packet capture, not firewall isolation, and not live ML-based IPS. '
         f'{model_count} saved model(s), {routes} shadow route(s).') if gateway_running else (
         'Virtual gateway stopped. Historical events may still appear. Start virtual gateway in Devices & Installation. '
         'No live traffic monitoring is occurring.')
    return {'gateway_running':gateway_running, 'devices':devices,'alerts':alerts,
            'blocked_24h':rejected_count,'visible_events_24h':len(recent_24h),
            'traffic':{'requests':req,'rejected_fraction':frac},'model_count':model_count,
            'route_count':routes,'footer':msg,
            'events':events[:200], 'source':'existing QuantumSafe virtual gateway registry + event history'}


def public_snapshot(snapshot_data):
    # Exclude raw event objects and backend-only values from JS embed.
    return {k:snapshot_data[k] for k in ('gateway_running','devices','alerts','blocked_24h','traffic','footer')}
