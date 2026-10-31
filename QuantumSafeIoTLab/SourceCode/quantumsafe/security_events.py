"""Save security event METADATA only; no secret, keys or sensor readings."""
from . import db
from .users import active_actor


def save(actor_id, item):
    db.execute(
        'INSERT INTO dbo.SecurityEvents (ActorId, EventName, Outcome, SourceIp, Algorithm) '
        'VALUES (?, ?, ?, ?, ?)',
        (actor_id, item['event'][:40], item['outcome'], item.get('source_ip'),
         item.get('algorithm'))
    )


def history(actor_id):
    active_actor(actor_id)
    return db.rows(
        'SELECT TOP 200 EventId, EventName, Outcome, SourceIp, Algorithm, CreatedAtUtc '
        'FROM dbo.SecurityEvents ORDER BY EventId DESC'
    )


def ready():
    try:
        return bool(db.one("SELECT OBJECT_ID('dbo.SecurityEvents', 'U') AS TableId")['TableId'])
    except Exception:
        return False
