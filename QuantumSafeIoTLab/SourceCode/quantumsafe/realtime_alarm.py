"""Non-blocking gateway security alarm with visible diagnostics (Windows host only)."""
import queue
import sys
import threading
import time

SECURITY_REASONS = frozenset({
    'Device is not registered',
    'Invalid gateway token',
    'Invalid per-device credential',
    'Message integrity check failed',
    'Replay nonce detected',
    'Rate limit: 8 requests per 10 seconds',
})


def should_alarm(event):
    return (isinstance(event, dict)
            and event.get('source') == 'LOCAL_HTTP'
            and event.get('decision') == 'BLOCK'
            and event.get('reason') in SECURITY_REASONS)


class AlarmEngine:
    def __init__(self, player=None):
        self.player = player if player is not None else _windows_player
        self._queue = queue.Queue(maxsize=64)
        self._seen = set()
        self._lock = threading.Lock()
        self.total_alerts = 0
        self.played = 0
        self.failures = 0
        self.last_error = None
        self.last_alarm_event_id = None
        self.last_alarm_time = None
        self._worker = threading.Thread(target=self._run, daemon=True, name='QuantumSafeAlarm')
        self._worker.start()

    def notify(self, event):
        if not should_alarm(event):
            return False
        key = str(event.get('event_id') or '')
        if not key:
            return False
        with self._lock:
            if key in self._seen:
                return False
            try:
                self._queue.put_nowait(dict(event))
            except queue.Full:
                self.last_error = 'Alarm queue full'
                self.failures += 1
                return False
            self._seen.add(key)
            if len(self._seen) > 10000:
                self._seen = {key}
            self.total_alerts += 1
            self.last_alarm_event_id = key
            return True

    def test_sound(self):
        """Send a user-requested speaker test without inventing a security event."""
        try:
            self._queue.put_nowait({'_test': True})
            return True
        except queue.Full:
            self.last_error = 'Alarm queue full'
            self.failures += 1
            return False

    def _run(self):
        while True:
            event = self._queue.get()
            try:
                result = self.player(event)
                if result is False:
                    raise RuntimeError('Audio backend reports no output')
                with self._lock:
                    self.played += 1
                    self.last_error = None
                    self.last_alarm_time = time.time()
            except Exception as exc:
                with self._lock:
                    self.failures += 1
                    self.last_error = f'{type(exc).__name__}: {exc}'
            finally:
                self._queue.task_done()


def _windows_player(event):
    if sys.platform != 'win32':
        raise RuntimeError('Windows sound is only available on the Windows gateway host')
    import winsound
    errors = []
    # Prefer system-alert audio, which follows the Windows sound configuration.
    try:
        winsound.PlaySound('SystemExclamation', winsound.SND_ALIAS)  # synchronous by default; SND_SYNC does not exist
        # SND_ALIAS may silently map to no sound when Windows scheme is muted.
        # Beep adds a second audible signal if supported by the audio driver.
        try:
            for hz in (1050, 1350, 1050):
                winsound.Beep(hz, 220)
        except (RuntimeError, OSError, AttributeError) as exc:
            errors.append(str(exc))
        return True
    except (RuntimeError, OSError, AttributeError) as exc:
        errors.append(str(exc))
    try:
        for hz in (1050, 1350, 1050):
            winsound.Beep(hz, 220)
        return True
    except (RuntimeError, OSError, AttributeError) as exc:
        errors.append(str(exc))
    raise RuntimeError('Windows sound failed: ' + '; '.join(errors))
