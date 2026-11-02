"""Auditable response policy for the LOCAL virtual HTTP IoT gateway only.

Does not manage Windows firewall, routers, physical device isolation, or emergency dispatch.
Default automatic quarantine OFF; admin can enable after review.
"""
from __future__ import annotations
import sqlite3
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / 'Data' / 'virtual_ips.sqlite3'
SUSPECT = frozenset({'Message integrity check failed', 'Replay nonce detected', 'Rate limit: 8 requests per 10 seconds'})


def utc():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class VirtualIPS:
    def __init__(self, db_path=None, clock=None):
        self.db_path = Path(db_path or DB)
        self.clock = clock or time.time
        self.lock = threading.RLock()
        self.recent = defaultdict(deque)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS policy (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS quarantine (
                    device TEXT PRIMARY KEY, expires_unix REAL NOT NULL,
                    reason TEXT NOT NULL, actor TEXT NOT NULL, created_utc TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp_utc TEXT NOT NULL,
                    action TEXT NOT NULL, device TEXT NOT NULL, actor TEXT NOT NULL,
                    reason TEXT NOT NULL);
            ''')
            db.execute("INSERT OR IGNORE INTO policy(key,value) VALUES('auto_quarantine','0')")

    def _db(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def settings(self):
        with self.lock, self._db() as db:
            value=db.execute("SELECT value FROM policy WHERE key='auto_quarantine'").fetchone()[0]
            return {'auto_quarantine': value=='1', 'threshold':3,
                    'window_seconds':60,'quarantine_seconds':120,
                    'scope':'local_virtual_HTTP_only'}

    def set_auto(self, enabled, actor):
        if actor.get('RoleName')!='Admin':raise PermissionError('Administrator required')
        with self.lock, self._db() as db:
            db.execute("UPDATE policy SET value=? WHERE key='auto_quarantine'",('1' if enabled else '0',))
            self._audit(db, 'set_auto', '*', actor.get('Username','Admin'), 'enabled' if enabled else 'disabled')

    def _audit(self, db, action, device, actor, reason):
        db.execute('INSERT INTO audit(timestamp_utc,action,device,actor,reason) VALUES (?,?,?,?,?)',
                   (utc(),action,str(device)[:64],str(actor)[:80],str(reason)[:240]))

    def active(self, device):
        """Check local containment, honoring expiry even after restart."""
        with self.lock, self._db() as db:
            r=db.execute('SELECT expires_unix FROM quarantine WHERE device=?',(str(device),)).fetchone()
            return bool(r and float(r['expires_unix'])>self.clock())

    def entries(self):
        with self.lock, self._db() as db:
            rows=db.execute('SELECT * FROM quarantine ORDER BY created_utc DESC').fetchall()
        now=self.clock()
        return [dict(r,active=float(r['expires_unix'])>now,
                     seconds_remaining=max(0,int(float(r['expires_unix'])-now))) for r in rows]

    def quarantine(self, device, actor, *, reason='Administrator isolation', seconds=300, enrolled=True):
        if actor.get('RoleName')!='Admin':raise PermissionError('Administrator required')
        if not enrolled:raise ValueError('Only enrolled devices can be quarantined')
        if not isinstance(seconds,int) or not 30<=seconds<=3600:raise ValueError('Duration must be 30 to 3600 seconds')
        with self.lock, self._db() as db:
            self._apply(db,device,actor.get('Username','Admin'),reason,seconds)
        return True

    def _apply(self, db,device,actor,reason,seconds):
        db.execute('INSERT OR REPLACE INTO quarantine(device,expires_unix,reason,actor,created_utc) VALUES (?,?,?,?,?)',
                   (str(device),float(self.clock()+seconds),str(reason)[:240],str(actor)[:80],utc()))
        self._audit(db,'quarantine',device,actor,reason)

    def release(self, device, actor):
        if actor.get('RoleName')!='Admin':raise PermissionError('Administrator required')
        with self.lock, self._db() as db:
            db.execute('DELETE FROM quarantine WHERE device=?',(str(device),))
            self.recent.pop(str(device),None)
            self._audit(db,'release',device,actor.get('Username','Admin'),'Manual release')

    def observe(self, event, *, trusted_identity=False, enrolled=False):
        """Auto-contain only repeated violations from a sender with valid credentials.

        An attacker using an unknown device ID or invalid token cannot quarantine
        a legitimate device just by claiming its name.
        """
        if not trusted_identity or not enrolled or event.get('reason') not in SUSPECT:
            return False
        device=str(event.get('device',''))
        if not device:return False
        with self.lock:
            now=self.clock()
            recent=self.recent[device]
            while recent and now-recent[0]>=60:recent.popleft()
            recent.append(now)
            if len(recent)<3 or self.active(device):return False
            with self._db() as db:
                enabled=db.execute("SELECT value FROM policy WHERE key='auto_quarantine'").fetchone()[0]=='1'
                if not enabled:return False
                self._apply(db,device,'virtual-ips-policy','3 authenticated high-confidence violations in 60 seconds',120)
            recent.clear()
            return True

    def audit(self,limit=100):
        with self.lock, self._db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id DESC LIMIT ?', (max(1,min(int(limit),500)),))]
