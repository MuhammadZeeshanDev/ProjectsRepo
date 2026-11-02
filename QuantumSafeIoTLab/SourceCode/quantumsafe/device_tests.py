"""Admin-only virtual device security acceptance suite with SQLite audit.

Tests the REAL localhost HTTP gateway signing, not mocked ALLOW/BLOCK badges.
A 'safe login' here means an enrolled device presenting valid gateway and device
credentials plus a fresh signed request; user account login remains SQL-backed.
"""
from __future__ import annotations
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB=Path(__file__).resolve().parents[2]/'Data'/'device_acceptance.sqlite3'


def _db(path=None):
    p=Path(path or DEFAULT_DB)
    p.parent.mkdir(parents=True,exist_ok=True)
    connection=sqlite3.connect(p,timeout=10)
    connection.execute('''CREATE TABLE IF NOT EXISTS device_tests (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp_utc TEXT NOT NULL, actor TEXT NOT NULL,
      device_id TEXT NOT NULL, case_name TEXT NOT NULL, expected TEXT NOT NULL,
      actual TEXT NOT NULL, passed INTEGER NOT NULL, reason TEXT NOT NULL)''')
    connection.commit()
    return connection


def _case(gw, device_id, name):
    if name=='valid_signed_telemetry':
        ev=gw.send('Sensor',device_override=device_id,reading=36)
        return 'ALLOW',ev
    if name=='unauthorized_credentials':
        ev=gw.send('Unauthorized access',device_override=device_id,reading=36)
        return 'BLOCK',ev
    if name=='tampered_signature':
        ev=gw.send('Tampered message',device_override=device_id,reading=36)
        return 'BLOCK',ev
    if name=='replayed_nonce':
        ev=gw.send('Replay attack',device_override=device_id,reading=36)
        return 'BLOCK',ev
    if name=='unknown_device':
        from .attacker_client import send_untrusted_device
        ev=send_untrusted_device('unknown-'+secrets.token_hex(4),port=gw.port)
        return 'BLOCK',ev
    raise ValueError('Unsupported test case')


def run_case(gw,device_id,actor,name,db_path=None):
    if not isinstance(actor,dict) or actor.get('RoleName')!='Admin':
        raise PermissionError('Administrator required')
    if not gw.server:raise RuntimeError('Start gateway first')
    if device_id not in gw.registered_devices:raise ValueError('Device must be enrolled and active')
    if gw.ips.active(device_id):raise ValueError('Release IPS quarantine before normal acceptance tests')
    expected,event=_case(gw,device_id,name)
    actual=event.get('decision','ERROR')
    # For the signed case, require the verified decision reason, not any ALLOW.
    ok=(actual==expected and
        (expected!='ALLOW' or (event.get('identity_verified') is True and
        event.get('reason')=='Authenticated and integrity verified')))
    row={'timestamp_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
         'device_id':device_id,'case':name,'expected':expected,'actual':actual,
         'passed':ok,'reason':str(event.get('reason','')),'event_id':event.get('event_id')}
    with _db(db_path) as connection:
        connection.execute('''INSERT INTO device_tests(timestamp_utc,actor,device_id,
           case_name,expected,actual,passed,reason) VALUES (?,?,?,?,?,?,?,?)''',
           (row['timestamp_utc'],actor.get('Username','Admin'),device_id,name,
            expected,actual,int(ok),row['reason']))
    return row


def history(limit=100, db_path=None):
    with _db(db_path) as connection:
        connection.row_factory=sqlite3.Row
        return [dict(row) for row in connection.execute(
            'SELECT * FROM device_tests ORDER BY id DESC LIMIT ?',
            (max(1,min(int(limit),500)),))]
