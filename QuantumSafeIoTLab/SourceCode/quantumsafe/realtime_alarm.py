"""Gateway-side first-event alarm. Works independently of Streamlit reruns.

On Windows the Python gateway host plays winsound; elsewhere the incident is
recorded and UI/browser fallback may play sound. No remote-machine claim.
"""
import sys
import threading
import queue

CONFIRMED_REASONS = frozenset({
    'Invalid gateway token', 'Invalid per-device credential',
    'Message integrity check failed', 'Replay nonce detected',
    'Rate limit: 8 requests per 10 seconds',
})

def should_alarm(event):
    return (isinstance(event, dict)
            and event.get('source') == 'LOCAL_HTTP'
            and event.get('decision') == 'BLOCK'
            and event.get('reason') in CONFIRMED_REASONS)

class AlarmEngine:
    def __init__(self, player=None):
        self.player = player or _windows_player
        self._queue = queue.Queue(maxsize=32)
        self._seen = set()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()
        self.total_alerts = 0

    def notify(self, event):
        if not should_alarm(event):
            return False
        key = str(event.get('event_id') or '')
        if not key:
            return False
        with self._lock:
            if key in self._seen:
                return False
            self._seen.add(key)
            if len(self._seen) > 10000:
                self._seen = {key}
            try:
                self._queue.put_nowait(dict(event))
            except queue.Full:
                self._seen.discard(key)
                return False
            self.total_alerts += 1
            return True

    def _run(self):
        while True:
            event = self._queue.get()
            try:
                self.player(event)
            except Exception:
                pass  # Audio failure never blocks gateway decisions.
            finally:
                self._queue.task_done()

def _windows_player(event):
    if sys.platform != 'win32':
        return
    import winsound
    for frequency in (1250, 1600, 1250):
        winsound.Beep(frequency, 180)
