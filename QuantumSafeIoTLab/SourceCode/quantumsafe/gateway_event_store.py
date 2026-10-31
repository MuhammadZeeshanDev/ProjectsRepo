"""SQL Server event storage for local virtual HTTP gateway.

Creates a dedicated table only when the user explicitly initializes it.
All queries use parameterized values. No changes to existing tables.
"""
from datetime import datetime, timezone
from .db import connection

_TABLE = 'dbo.VirtualGatewayEvents'


def initialize():
    with connection() as con:
        cur = con.cursor()
        cur.execute("""
        IF OBJECT_ID(N'dbo.VirtualGatewayEvents', N'U') IS NULL
        BEGIN
            CREATE TABLE dbo.VirtualGatewayEvents (
                EventId BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                EventTimeUtc DATETIME2(3) NOT NULL,
                DeviceId NVARCHAR(64) NOT NULL,
                Decision VARCHAR(8) NOT NULL,
                Reason NVARCHAR(256) NOT NULL,
                EventSource VARCHAR(32) NOT NULL,
                RequestType VARCHAR(32) NOT NULL,
                CONSTRAINT CK_VGE_Decision CHECK (Decision IN ('ALLOW','BLOCK'))
            );
        END
        """)
    return True


def is_initialized():
    with connection() as con:
        cur = con.cursor()
        cur.execute("SELECT CASE WHEN OBJECT_ID(N'dbo.VirtualGatewayEvents', N'U') IS NULL THEN 0 ELSE 1 END")
        return bool(cur.fetchone()[0])


def insert_event(event):
    # Event timestamps come from the gateway, already UTC and timezone aware.
    stamp = datetime.fromisoformat(event['timestamp_utc'].replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('Event timestamp must be timezone-aware')
    stamp = stamp.astimezone(timezone.utc).replace(tzinfo=None)
    decision = event['decision']
    if decision not in ('ALLOW', 'BLOCK'):
        raise ValueError('Invalid decision')
    with connection() as con:
        con.cursor().execute("""
            INSERT INTO dbo.VirtualGatewayEvents
            (EventTimeUtc, DeviceId, Decision, Reason, EventSource, RequestType)
            VALUES (?, ?, ?, ?, ?, ?)
        """, stamp, str(event.get('device', ''))[:64], decision,
             str(event.get('reason', ''))[:256], str(event.get('source', ''))[:32],
             str(event.get('request_type', ''))[:32])


def recent_events(limit=1000):
    limit = max(1, min(int(limit), 5000))
    with connection() as con:
        cur = con.cursor()
        cur.execute(f"""
            SELECT TOP ({limit}) EventId, EventTimeUtc, DeviceId, Decision,
                   Reason, EventSource, RequestType
            FROM dbo.VirtualGatewayEvents ORDER BY EventId DESC
        """)
        results = []
        for row in cur.fetchall():
            results.append({
                'event_id': int(row[0]),
                'timestamp_utc': row[1].isoformat(timespec='milliseconds') + 'Z',
                'device': row[2], 'decision': row[3], 'reason': row[4],
                'source': row[5], 'request_type': row[6],
            })
        return results


def counts():
    with connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT COUNT_BIG(*),
                   COALESCE(SUM(CASE WHEN Decision = 'ALLOW' THEN CAST(1 AS BIGINT) ELSE 0 END),0),
                   COALESCE(SUM(CASE WHEN Decision = 'BLOCK' THEN CAST(1 AS BIGINT) ELSE 0 END),0)
            FROM dbo.VirtualGatewayEvents
        """)
        row = cur.fetchone()
        return {'total': int(row[0]), 'allowed': int(row[1]), 'blocked': int(row[2])}
