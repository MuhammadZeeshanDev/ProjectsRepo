"""Durable, bounded-batch SQL Server 2022 mirroring for virtual gateway evidence.

Accepted requests are first written to an on-disk SQLite outbox, then asynchronously
mirrored into SQL Server. Database errors are NEVER shown as confirmed SQL writes.
No secrets or model pickle objects are queued.
"""
import json
import sqlite3
import threading
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from . import gateway_event_store

DEFAULT_OUTBOX = Path(__file__).resolve().parents[2] / 'Data' / 'sql_sync_outbox.sqlite3'

class SqlSync:
    def __init__(self, path=None, event_writer=None, device_writer=None, retry_seconds=12):
        self.path = Path(path or DEFAULT_OUTBOX)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._event_writer = event_writer or gateway_event_store.insert_event
        self._device_writer = device_writer or gateway_event_store.upsert_device
        self.retry_seconds = max(1, int(retry_seconds))
        self._lock = threading.Lock()
        self._flush_lock = threading.Lock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread = None
        self.last_error = None
        self.last_ok_utc = None
        with self._open() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS pending (
                id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL,
                created_utc TEXT NOT NULL)""")
            db.execute('CREATE INDEX IF NOT EXISTS idx_pending_utc ON pending(created_utc)')

    def _connect(self):
        db=sqlite3.connect(self.path, timeout=20)
        db.execute('PRAGMA busy_timeout=20000')
        return db

    @contextmanager
    def _open(self):
        db=self._connect()
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _put(self, identity, kind, payload):
        with self._open() as db:
            db.execute('INSERT OR REPLACE INTO pending (id,kind,payload,created_utc) VALUES (?,?,?,?)',
                       (identity,kind,json.dumps(payload, ensure_ascii=True,allow_nan=False),
                        datetime.now(timezone.utc).isoformat()))
        self._wake.set()

    def enqueue_event(self,event):
        if event.get('decision') not in ('ALLOW','BLOCK'):return
        # No token/key/signature should be copied into the database outbox.
        allowed=('event_id','timestamp_utc','device','decision','reason','source',
                 'request_type','source_ip','attack_type','affected_component',
                 'precaution','reading','identity_verified','ips_action',
                 'crypto_algorithm','crypto_recipient','crypto_verified','crypto_ciphertext_bytes',
                 'crypto_kem_ciphertext_bytes','crypto_ciphertext_sha256')
        safe={k:event[k] for k in allowed if k in event}
        if not safe.get('event_id'):raise ValueError('Gateway event ID is required')
        self._put('event:'+str(safe['event_id']),'event',safe)

    def stage_device(self,item):
        allowed=('id','name','type','status','virtual_ip','virtual_mac')
        safe={k:item.get(k) for k in allowed}
        if not safe.get('id'):raise ValueError('Missing device ID')
        self._put('device:'+str(safe['id']),'device',safe)

    def stage_inventory(self,items):
        for item in items:self.stage_device(item)

    def pending_counts(self):
        with self._open() as db:
            grouped=db.execute('SELECT kind,COUNT(*) FROM pending GROUP BY kind').fetchall()
        return dict(events=sum(n for k,n in grouped if k=='event'),
                    devices=sum(n for k,n in grouped if k=='device'))

    def flush_once(self,limit=25):
        """One exclusive batch. Returns number confirmed by SQL Server."""
        with self._flush_lock:
            with self._open() as db:
                items=db.execute('SELECT id,kind,payload FROM pending ORDER BY created_utc,id LIMIT ?',
                                 (max(1,min(100,int(limit))),)).fetchall()
            saved=0
            for key,kind,payload in items:
                try:
                    item=json.loads(payload)
                    if kind=='event':
                        result=self._event_writer(item)
                    elif kind=='device':
                        result=self._device_writer(item)
                    else:raise ValueError('Unrecognized SQL outbox record type')
                    if result is False:raise RuntimeError('SQL writer did not confirm save')
                    with self._open() as db:
                        # A newer inventory update must not be removed after a stale SQL sync.
                        db.execute('DELETE FROM pending WHERE id=? AND payload=?',(key,payload))
                    self.last_ok_utc=datetime.now(timezone.utc).isoformat()
                    self.last_error=None
                    saved+=1
                except Exception as exc:
                    self.last_error=f'{type(exc).__name__}: {exc}'
                    break  # preserve remaining rows and retry later
            return saved

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():return
            self._stop.clear()
            self._thread=threading.Thread(target=self._loop,daemon=True,name='QuantumSafeSqlSync')
            self._thread.start()

    def _loop(self):
        while not self._stop.is_set():
            self._wake.wait(timeout=self.retry_seconds)
            self._wake.clear()
            if self._stop.is_set():break
            # bounded batch avoids hogging SQL during bursts; pending rows stay durable.
            try:
                self.flush_once(30)
            except Exception as exc:
                self.last_error=f'{type(exc).__name__}: {exc}'

    def stop(self):
        self._stop.set();self._wake.set()
        th=self._thread
        if th and th.is_alive():th.join(timeout=1.0)
