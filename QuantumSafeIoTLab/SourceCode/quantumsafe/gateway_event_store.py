"""Persistent SQL Server 2022 gateway audit and non-secret virtual device inventory.

Stores successful/rejected HTTP telemetry events and the last known virtual device
metadata. No private keys, per-device tokens or gateway secrets are sent to SQL.
"""
from datetime import datetime, timezone
from threading import Lock
from .db import connection

_SCHEMA_LOCK = Lock()
_SCHEMA_READY = False

def initialize():
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return True
    with _SCHEMA_LOCK:
        if _SCHEMA_READY:
            return True
        with connection() as con:
            cur = con.cursor()
            cur.execute("""IF OBJECT_ID(N'dbo.VirtualGatewayEvents',N'U') IS NULL
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
            extra = {
                'SourceIp':'NVARCHAR(64)', 'AttackType':'NVARCHAR(128)',
                'AffectedComponent':'NVARCHAR(128)', 'Precaution':'NVARCHAR(512)',
                'GatewayEventUid':'NVARCHAR(64)', 'Reading':'FLOAT',
                'IdentityVerified':'BIT', 'IpsAction':'NVARCHAR(250)',
                'CryptoAlgorithm':'NVARCHAR(64)', 'CryptoRecipient':'NVARCHAR(64)',
                'CryptoVerified':'BIT', 'CryptoCiphertextBytes':'INT',
                'CryptoKEMCiphertextBytes':'INT', 'CryptoCiphertextSha256':'CHAR(64)',
            }
            for col, dtype in extra.items():
                # Fixed, developer-owned identifiers only; no user SQL strings.
                cur.execute(f"IF COL_LENGTH('dbo.VirtualGatewayEvents','{col}') IS NULL ALTER TABLE dbo.VirtualGatewayEvents ADD [{col}] {dtype} NULL")
            cur.execute("""IF NOT EXISTS (SELECT 1 FROM sys.indexes
                WHERE name=N'UX_VGE_GatewayEventUid' AND object_id=OBJECT_ID(N'dbo.VirtualGatewayEvents'))
                CREATE UNIQUE NONCLUSTERED INDEX UX_VGE_GatewayEventUid
                ON dbo.VirtualGatewayEvents(GatewayEventUid) WHERE GatewayEventUid IS NOT NULL""")
            cur.execute("""IF OBJECT_ID(N'dbo.VirtualDeviceInventory',N'U') IS NULL
            CREATE TABLE dbo.VirtualDeviceInventory (
                DeviceId NVARCHAR(64) NOT NULL PRIMARY KEY,
                DeviceName NVARCHAR(128) NOT NULL,
                DeviceType NVARCHAR(64) NOT NULL,
                EnrollmentStatus NVARCHAR(24) NOT NULL,
                VirtualIp NVARCHAR(80) NULL,
                VirtualMac NVARCHAR(80) NULL,
                UpdatedAtUtc DATETIME2(3) NOT NULL
            )""")
        _SCHEMA_READY = True
        return True

def is_initialized():
    with connection() as con:
        cur=con.cursor()
        cur.execute("SELECT CASE WHEN OBJECT_ID(N'dbo.VirtualGatewayEvents',N'U') IS NULL THEN 0 ELSE 1 END")
        return bool(cur.fetchone()[0])

def _utc_stamp(event):
    stamp=datetime.fromisoformat(event['timestamp_utc'].replace('Z','+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('Event timestamp must be timezone-aware')
    return stamp.astimezone(timezone.utc).replace(tzinfo=None)

def insert_event(event):
    if event.get('decision') not in ('ALLOW','BLOCK'):
        return False
    initialize()
    reading = event.get('reading')
    if isinstance(reading,bool) or not isinstance(reading,(float,int)):
        reading = None
    uid=str(event.get('event_id',''))[:64] or None
    with connection() as con:
        con.cursor().execute("""INSERT INTO dbo.VirtualGatewayEvents
          (EventTimeUtc, DeviceId, Decision, Reason, EventSource, RequestType,
           SourceIp, AttackType, AffectedComponent, Precaution,
           GatewayEventUid, Reading, IdentityVerified, IpsAction)
          SELECT ?,?,?,?,?,?,?,?,?,?,?,?,?,?
          WHERE ? IS NULL OR NOT EXISTS (
             SELECT 1 FROM dbo.VirtualGatewayEvents WITH (UPDLOCK, HOLDLOCK)
             WHERE GatewayEventUid = ?)""",
          _utc_stamp(event),str(event.get('device',''))[:64],event['decision'],
          str(event.get('reason',''))[:256],str(event.get('source',''))[:32],
          str(event.get('request_type',''))[:32],str(event.get('source_ip',''))[:64],
          str(event.get('attack_type',''))[:128],str(event.get('affected_component',''))[:128],
          str(event.get('precaution',''))[:512],uid,reading,
          bool(event.get('identity_verified',False)),str(event.get('ips_action',''))[:250],uid,uid)
        if event.get('request_type')=='encrypted_mesh':
            con.cursor().execute("""UPDATE dbo.VirtualGatewayEvents SET
              CryptoAlgorithm=?, CryptoRecipient=?, CryptoVerified=?, CryptoCiphertextBytes=?,
              CryptoKEMCiphertextBytes=?, CryptoCiphertextSha256=?
              WHERE GatewayEventUid=? AND RequestType='encrypted_mesh'""",
              str(event.get('crypto_algorithm',''))[:64],str(event.get('crypto_recipient',''))[:64],
              bool(event.get('crypto_verified',False)),int(event.get('crypto_ciphertext_bytes') or 0),
              int(event.get('crypto_kem_ciphertext_bytes') or 0),
              str(event.get('crypto_ciphertext_sha256',''))[:64],uid)
    return True

def upsert_device(item):
    """Mirror non-sensitive enrollment metadata; JSON device registry remains auth source."""
    initialize()
    did=str(item['id'])[:64]
    with connection() as con:
        con.cursor().execute("""UPDATE dbo.VirtualDeviceInventory SET
                DeviceName=?, DeviceType=?, EnrollmentStatus=?, VirtualIp=?, VirtualMac=?,
                UpdatedAtUtc=SYSUTCDATETIME() WHERE DeviceId=?;
            IF @@ROWCOUNT=0 INSERT INTO dbo.VirtualDeviceInventory
                (DeviceId,DeviceName,DeviceType,EnrollmentStatus,VirtualIp,VirtualMac,UpdatedAtUtc)
                VALUES (?,?,?,?,?,?,SYSUTCDATETIME());""",
            str(item.get('name',''))[:128],str(item.get('type',''))[:64],
            str(item.get('status',''))[:24],str(item.get('virtual_ip',''))[:80],
            str(item.get('virtual_mac',''))[:80],did,
            did,str(item.get('name',''))[:128],str(item.get('type',''))[:64],
            str(item.get('status',''))[:24],str(item.get('virtual_ip',''))[:80],
            str(item.get('virtual_mac',''))[:80])
    return True

def event_exists(uid):
    initialize()
    with connection() as con:
        cur=con.cursor()
        cur.execute('SELECT COUNT_BIG(*) FROM dbo.VirtualGatewayEvents WHERE GatewayEventUid=?',str(uid)[:64])
        return int(cur.fetchone()[0])>0

def recent_events(limit=1000):
    limit=max(1,min(int(limit),5000))
    with connection() as con:
        cur=con.cursor()
        cur.execute(f"""SELECT TOP ({limit}) EventId, EventTimeUtc, DeviceId, Decision,
          Reason, EventSource, RequestType, SourceIp, AttackType, AffectedComponent,
          Precaution, GatewayEventUid, Reading, IdentityVerified, IpsAction,
          CryptoAlgorithm, CryptoRecipient, CryptoVerified, CryptoCiphertextBytes,
          CryptoKEMCiphertextBytes, CryptoCiphertextSha256
          FROM dbo.VirtualGatewayEvents ORDER BY EventId DESC""")
        return [dict(event_id=r[11] or str(r[0]),sql_event_id=int(r[0]),
          timestamp_utc=r[1].isoformat(timespec='milliseconds')+'Z',
          device=r[2],decision=r[3],reason=r[4],source=r[5],request_type=r[6],
          source_ip=r[7],attack_type=r[8],affected_component=r[9],precaution=r[10],
          reading=r[12],identity_verified=bool(r[13]),ips_action=r[14],
          crypto_algorithm=r[15],crypto_recipient=r[16],crypto_verified=bool(r[17]),
          crypto_ciphertext_bytes=r[18],crypto_kem_ciphertext_bytes=r[19],
          crypto_ciphertext_sha256=r[20])
          for r in cur.fetchall()]

def counts():
    with connection() as con:
        cur=con.cursor()
        cur.execute("""SELECT COUNT_BIG(*),
          COALESCE(SUM(CASE WHEN Decision='ALLOW' THEN CAST(1 AS BIGINT) ELSE 0 END),0),
          COALESCE(SUM(CASE WHEN Decision='BLOCK' THEN CAST(1 AS BIGINT) ELSE 0 END),0)
          FROM dbo.VirtualGatewayEvents""")
        r=cur.fetchone()
        return dict(total=int(r[0]),allowed=int(r[1]),blocked=int(r[2]))

def device_count():
    with connection() as con:
        r=con.cursor().execute('SELECT COUNT_BIG(*) FROM dbo.VirtualDeviceInventory').fetchone()
        return int(r[0])
