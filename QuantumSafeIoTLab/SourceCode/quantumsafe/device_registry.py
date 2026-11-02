"""Local, persistent allowlist for virtual lab devices.

Credentials never appear in inventory data. The file is a *host-local* secret
store, NOT a hardware TPM or enterprise vault. Back it up securely.
"""
from __future__ import annotations
import json
import os
import re
import secrets
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = ROOT / 'Data' / 'device_registry.json'
DEFAULT_DEVICES = {
    'virtual-cctv-01': ('CCTV camera', 'Camera'),
    'virtual-router-01': ('Router', 'Router'),
    'virtual-sensor-01': ('Temperature sensor', 'Sensor'),
}
_ID = re.compile(r'^[a-z0-9][a-z0-9-]{2,63}$')
TYPES = ('Camera', 'Router', 'Sensor', 'Other')


def _stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class DeviceRegistry:
    def __init__(self, path=None):
        self.path = Path(path or DEFAULT_PATH)
        self._lock = RLock()
        self._data = self._load()

    def _record(self, name, kind):
        return {'name': name, 'kind': kind, 'state': 'active',
                'key_hex': secrets.token_hex(32), 'token': secrets.token_urlsafe(32),
                'created_utc': _stamp(), 'updated_utc': _stamp()}

    def _load(self):
        if self.path.is_file():
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('devices'), dict):
                raise ValueError('Device registry has an unsupported or invalid format; it was not overwritten.')
            return data
        data = {'version': 1, 'devices': {id_: self._record(name, kind) for id_, (name, kind) in DEFAULT_DEVICES.items()}}
        self._save(data)
        return data

    def _save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix='.devices-', suffix='.tmp', dir=self.path.parent)
        try:
            try:
                os.fchmod(fd, 0o600)
            except (OSError, AttributeError):
                pass
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, self.path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def _update(self, device_id, record):
        # Copy-on-write: disk failure never leaves the process using unpersisted keys.
        next_data = {'version': 1, 'devices': dict(self._data['devices'])}
        next_data['devices'][device_id] = record
        self._save(next_data)
        self._data = next_data

    def inventory(self):
        with self._lock:
            return [{'device_id': k, 'name': v['name'], 'type': v['kind'],
                     'status': v['state'], 'created_utc': v.get('created_utc', ''),
                     'updated_utc': v.get('updated_utc', '')}
                    for k, v in sorted(self._data['devices'].items())]

    def active_credentials(self):
        with self._lock:
            return {k: (v['name'], bytes.fromhex(v['key_hex']), v['token'])
                    for k, v in self._data['devices'].items() if v['state'] == 'active'}

    def enroll(self, device_id, name, kind):
        device_id = str(device_id).strip().lower()
        name = str(name).strip()
        if not _ID.fullmatch(device_id):
            raise ValueError('Device ID: 3–64 lowercase letters, numbers and hyphens.')
        if not (2 <= len(name) <= 80):
            raise ValueError('Device display name must be 2–80 characters.')
        if kind not in TYPES:
            raise ValueError('Unsupported device type')
        with self._lock:
            if device_id in self._data['devices']:
                raise ValueError('This device ID already exists or was retired. Choose another ID.')
            self._update(device_id, self._record(name, kind))

    def set_state(self, device_id, state):
        if state not in ('active', 'disabled', 'retired'):
            raise ValueError('Unsupported device state')
        with self._lock:
            old = self._data['devices'].get(device_id)
            if not old or old['state'] == 'retired':
                raise ValueError('Device is unknown or permanently retired')
            record = dict(old, state=state, updated_utc=_stamp())
            if state == 'retired':
                record.pop('key_hex', None)
                record.pop('token', None)
            self._update(device_id, record)

    def rotate(self, device_id):
        with self._lock:
            old = self._data['devices'].get(device_id)
            if not old or old['state'] == 'retired':
                raise ValueError('Device not found or retired')
            record = dict(old, key_hex=secrets.token_hex(32), token=secrets.token_urlsafe(32), updated_utc=_stamp())
            self._update(device_id, record)

    def audit(self, action, device_id, actor):
        """Best effort non-secret lifecycle trail. Existing gateway telemetry history remains untouched."""
        entry = json.dumps({'time_utc': _stamp(), 'actor': str(actor)[:80],
                            'action': str(action)[:40], 'device_id': device_id}, sort_keys=True)
        log = self.path.parent / 'device_audit.jsonl'
        with log.open('a', encoding='utf-8') as f:
            f.write(entry + '\n')
