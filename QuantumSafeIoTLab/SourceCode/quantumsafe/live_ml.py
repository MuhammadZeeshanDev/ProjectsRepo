"""Non-blocking best-effort shadow inference from REAL observed HTTP telemetry fields.

No crafted TCP/DNS/MQTT fields and no model-driven blocking. An ML route whose
feature schema doesn't match the collected HTTP fields is reported as incompatible.
"""
from __future__ import annotations
import queue
import threading
import time
from .ml_engine import registry
from .ml_engine.shadow import ShadowRouter


class LiveShadowWorker:
    def __init__(self, router_factory=None, route_provider=None):
        self.router_factory = router_factory or ShadowRouter
        self.route_provider = route_provider or registry.active_routes
        self.queue = queue.Queue(maxsize=128)
        self.lock = threading.Lock()
        self.status = {'submitted': 0, 'processed': 0, 'dropped': 0,
                       'matches': 0, 'incompatible': 0, 'last_error': None,
                       'last_result': None, 'mode': 'shadow_only'}
        self._stop=threading.Event()
        self._thread=None
        self._router=None
        self._signature=None

    def start(self):
        if self._thread and self._thread.is_alive():return
        self._stop.clear()
        self._thread=threading.Thread(target=self._run, name='QuantumSafeShadowML',daemon=True)
        self._thread.start()

    def submit(self, event):
        """Only enqueue allowed telemetry with actually observed fields."""
        if event.get('decision')!='ALLOW' or event.get('reading') is None:return False
        self.start()
        observation={k:event[k] for k in ('device','source_ip','reading','request_type','identity_verified') if k in event}
        observation['value']=event['reading']  # exact numeric observed reading, not synthetic network feature
        try:
            self.queue.put_nowait(observation)
        except queue.Full:
            with self.lock:self.status['dropped']+=1
            return False
        with self.lock:self.status['submitted']+=1
        return True

    def snapshot(self):
        with self.lock:return dict(self.status,queued=self.queue.qsize())

    def _run(self):
        while not self._stop.is_set():
            try:observation=self.queue.get(timeout=.3)
            except queue.Empty:continue
            try:
                routes=self.route_provider()
                fingerprint=tuple((r['model_id'],r['threat']) for r in routes)
                if not routes:
                    with self.lock:
                        self.status['last_result']='No eligible shadow ML routes; gateway rule-based checks still active.'
                    continue
                if fingerprint!=self._signature:
                    self._router=self.router_factory()
                    self._signature=fingerprint
                result=self._router.process(observation)
                with self.lock:
                    self.status['processed']+=1
                    self.status['matches']+=len(result.get('matches',[]))
                    self.status['incompatible']=len(result.get('incompatible_models',[]))
                    self.status['last_result']=result
                    self.status['last_error']=None
            except Exception as exc:
                with self.lock:self.status['last_error']=f'{type(exc).__name__}: {str(exc)[:250]}'
            finally:self.queue.task_done()

    def stop(self):
        self._stop.set()
        if self._thread:self._thread.join(timeout=1)
