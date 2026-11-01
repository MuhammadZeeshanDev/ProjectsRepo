"""SQL Server virtual-lab incident history; adds optional columns without deleting prior records."""
from datetime import datetime, timezone
from .db import connection

_EXTRA = {
    'SourceIp': 'NVARCHAR(64)', 'AttackType': 'NVARCHAR(128)',
    'AffectedComponent': 'NVARCHAR(128)', 'Precaution': 'NVARCHAR(512)'
}

def initialize():
    with connection() as con:
        cur=con.cursor()
        cur.execute("""IF OBJECT_ID(N'dbo.VirtualGatewayEvents', N'U') IS NULL
        CREATE TABLE dbo.VirtualGatewayEvents (
            EventId BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            EventTimeUtc DATETIME2(3) NOT NULL,
            DeviceId NVARCHAR(64) NOT NULL,
            Decision VARCHAR(8) NOT NULL,
            Reason NVARCHAR(256) NOT NULL,
            EventSource VARCHAR(32) NOT NULL,
            RequestType VARCHAR(32) NOT NULL,
            CONSTRAINT CK_VGE_Decision CHECK (Decision IN ('ALLOW','BLOCK'))
        )""")
        for column, sqltype in _EXTRA.items():
            cur.execute(f"IF COL_LENGTH('dbo.VirtualGatewayEvents', '{column}') IS NULL ALTER TABLE dbo.VirtualGatewayEvents ADD [{column}] {sqltype} NULL")
    return True

def is_initialized():
    with connection() as con:
        cur=con.cursor()
        cur.execute("SELECT CASE WHEN OBJECT_ID(N'dbo.VirtualGatewayEvents', N'U') IS NULL THEN 0 ELSE 1 END")
        return bool(cur.fetchone()[0])

def _utc_stamp(event):
    stamp=datetime.fromisoformat(event['timestamp_utc'].replace('Z','+00:00'))
    if stamp.tzinfo is None: raise ValueError('Event timestamp must be timezone-aware')
    return stamp.astimezone(timezone.utc).replace(tzinfo=None)

def insert_event(event):
    if event['decision'] not in ('ALLOW','BLOCK'):
        return False  # REVIEW and UNKNOWN are not confirmed gateway security decisions
    initialize()  # Safe for existing installations; adds missing optional columns.
    with connection() as con:
        con.cursor().execute("""INSERT INTO dbo.VirtualGatewayEvents
          (EventTimeUtc, DeviceId, Decision, Reason, EventSource, RequestType,
           SourceIp, AttackType, AffectedComponent, Precaution)
          VALUES (?,?,?,?,?,?,?,?,?,?)""",
          _utc_stamp(event), str(event.get('device',''))[:64], event['decision'],
          str(event.get('reason',''))[:256],str(event.get('source',''))[:32],
          str(event.get('request_type',''))[:32],str(event.get('source_ip',''))[:64],
          str(event.get('attack_type',''))[:128],str(event.get('affected_component',''))[:128],
          str(event.get('precaution',''))[:512])
    return True

def recent_events(limit=1000):
    limit=max(1,min(int(limit),5000))
    with connection() as con:
        cur=con.cursor()
        cur.execute(f"""SELECT TOP ({limit}) EventId, EventTimeUtc, DeviceId, Decision,
          Reason, EventSource, RequestType, SourceIp, AttackType, AffectedComponent, Precaution
          FROM dbo.VirtualGatewayEvents ORDER BY EventId DESC""")
        return [dict(event_id=int(r[0]),timestamp_utc=r[1].isoformat(timespec='milliseconds')+'Z',
          device=r[2],decision=r[3],reason=r[4],source=r[5],request_type=r[6],
          source_ip=r[7],attack_type=r[8],affected_component=r[9],precaution=r[10]) for r in cur.fetchall()]

def counts():
    with connection() as con:
        cur=con.cursor()
        cur.execute("""SELECT COUNT_BIG(*),
          COALESCE(SUM(CASE WHEN Decision='ALLOW' THEN CAST(1 AS BIGINT) ELSE 0 END),0),
          COALESCE(SUM(CASE WHEN Decision='BLOCK' THEN CAST(1 AS BIGINT) ELSE 0 END),0)
          FROM dbo.VirtualGatewayEvents""")
        r=cur.fetchone()
        return dict(total=int(r[0]),allowed=int(r[1]),blocked=int(r[2]))
