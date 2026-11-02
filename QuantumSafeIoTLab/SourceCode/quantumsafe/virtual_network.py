"""Loopback-only HTTP virtual IoT gateway. Not packet capture or network-wide firewall."""
import uuid
import re
import hashlib
import hmac
import json
import secrets
import threading
import time
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from .realtime_alarm import AlarmEngine
from .device_registry import DeviceRegistry
from .permissions import require_role
from .virtual_ips import VirtualIPS
from .live_ml import LiveShadowWorker
from .sql_sync import SqlSync

class VirtualGateway:
    def __init__(self):
        self.key = secrets.token_bytes(32)
        self.token = secrets.token_urlsafe(24)
        self.events = deque(maxlen=200)
        self.nonces = set()
        self.calls = {}
        self.lock = threading.Lock()
        self.server = None
        self.thread = None
        self.port = None
        self.registry = DeviceRegistry()
        self._reload_registry()
        self.sql_sync = SqlSync()  # durable local queue -> SQL Server 2022 mirror
        self.event_sink = self.sql_sync.enqueue_event
        self.last_persist_error = None
        self.alarm_engine = AlarmEngine()
        self._viewers = {}  # Short-lived, unpredictable local dashboard access tokens.
        self.ips = VirtualIPS()
        self.live_shadow = LiveShadowWorker()

    def _reload_registry(self):
        credentials=self.registry.credentials()
        self.registered_devices={d:r[0] for d,r in credentials.items()}
        self.device_keys={d:r[1] for d,r in credentials.items()}
        self.device_tokens={d:r[2] for d,r in credentials.items()}

    def manage_device(self,action,device_id,actor,*,name=None,kind=None,virtual_ip='',virtual_mac=''):
        # Authorization enforced by the service, not just hidden UI buttons.
        require_role(actor.get('RoleName'),('Admin',))
        with self.lock:
            result=self.registry.apply(action,device_id,name=name,kind=kind,
                                       virtual_ip=virtual_ip,virtual_mac=virtual_mac,
                                       actor=actor.get('Username','Admin'))
            self._reload_registry()
            # Registry JSON is authoritative for credentials; SQL gets metadata only.
            try:
                item=next(x for x in self.registry.inventory() if x['id']==result)
                self.sql_sync.stage_device(item)
            except Exception as exc:
                self.last_persist_error=f'Local SQL queue error: {type(exc).__name__}: {exc}'
            self.nonces={n for n in self.nonces if n[0]!=result}
            self.calls.pop(result,None)
            return result

    def start(self, port=8765):
        if self.server:
            return self.port
        gateway = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                # Explicit bearer-gated localhost viewer. No credentials, control
                # endpoints, model files or raw secret material exposed here.
                try:
                    path=self.path.split('?',1)[0]
                    matched=re.fullmatch(r'/viewer/([a-zA-Z0-9_-]{32,100})(/state)?', path)
                    if not matched:
                        self.send_error(404);return
                    token=matched.group(1)
                    if not gateway.valid_viewer(token):
                        self.send_error(403);return
                    if matched.group(2):
                        raw=json.dumps(gateway.viewer_state(),ensure_ascii=True,allow_nan=False).encode('utf-8')
                        kind='application/json; charset=utf-8'
                    else:
                        from .ui.security_console import render_html
                        raw=render_html(gateway.viewer_state(),polling=True).encode('utf-8')
                        kind='text/html; charset=utf-8'
                    self.send_response(200)
                    self.send_header('Content-Type',kind)
                    self.send_header('Content-Length',str(len(raw)))
                    self.send_header('Cache-Control','no-store, private')
                    self.send_header('Referrer-Policy','no-referrer')
                    self.send_header('X-Content-Type-Options','nosniff')
                    self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors http://localhost:8501 http://127.0.0.1:8501")
                    self.end_headers();self.wfile.write(raw)
                except Exception:
                    self.send_error(500)

            def do_POST(self):
                if self.path != '/telemetry':
                    self.send_error(404)
                    return
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                    if size <= 0 or size > 8192:
                        self.send_error(413)
                        return
                    data = json.loads(self.rfile.read(size))
                    if not isinstance(data, dict):
                        raise ValueError('Expected object')
                    result = gateway.evaluate(data, source_ip=self.client_address[0])
                    encoded = json.dumps(result).encode('utf-8')
                    self.send_response(200 if result['decision'] == 'ALLOW' else 403)
                    self.send_header('Content-Type','application/json')
                    self.send_header('Content-Length',str(len(encoded)))
                    self.end_headers()
                    self.wfile.write(encoded)
                except (ValueError, TypeError, UnicodeError, json.JSONDecodeError):
                    self.send_error(400)
        self.sql_sync.start()
        self.sql_sync.stage_inventory(self.registry.inventory())
        self.server = ThreadingHTTPServer(('127.0.0.1', int(port)), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.port

    def issue_viewer(self, actor, *, lifetime=1200):
        """Caller must revalidate actor via SQL-backed active_actor first."""
        if not isinstance(actor,dict) or actor.get('RoleName') not in ('Admin','Researcher') or not actor.get('UserId'):
            raise PermissionError('Authenticated application user required')
        token=secrets.token_urlsafe(32)
        with self.lock:
            now=time.time()
            self._viewers={k:v for k,v in self._viewers.items() if v>now}
            self._viewers[token]=now+int(lifetime)
        return token

    def valid_viewer(self, token):
        with self.lock:
            expiry=self._viewers.get(token,0)
            return bool(expiry>time.time())

    def revoke_viewer(self, token):
        with self.lock:self._viewers.pop(token,None)

    def viewer_state(self):
        from . import console_data
        return console_data.public_snapshot(console_data.snapshot(self,[],set()))

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=3)
            self.server = None
            self.thread = None
            self.port = None
            with self.lock:self._viewers.clear()

    def sign(self, device, nonce, value):
        msg = json.dumps([device, nonce, value], separators=(',', ':'), ensure_ascii=True).encode()
        return hmac.new(self.device_keys[device], msg, hashlib.sha256).hexdigest()

    def evaluate(self, data, source_ip="local"):
        device = str(data.get('device',''))[:64]
        nonce = str(data.get('nonce',''))[:100]
        value = data.get('value')
        signature = str(data.get('signature',''))
        authenticated = hmac.compare_digest(str(data.get('token','')), self.token)
        # Only a valid enrolled device token counts as an authenticated device
        # identity for optional IPS auto-containment. Attacker-supplied names
        # and invalid tokens must never disable a legitimate device.
        quarantined = self.ips.active(device)
        now = time.monotonic()
        with self.lock:
            enrolled = device in self.registered_devices
            trusted_identity = (enrolled and authenticated and
                hmac.compare_digest(str(data.get('device_token', '')), self.device_tokens[device]))
            if device not in self.registered_devices:
                decision, reason = 'BLOCK', 'Device is not registered'
            elif not authenticated:
                decision, reason = 'BLOCK', 'Invalid gateway token'
            elif not hmac.compare_digest(str(data.get('device_token', '')), self.device_tokens[device]):
                decision, reason = 'BLOCK', 'Invalid per-device credential'
            elif quarantined:
                decision, reason = 'BLOCK', 'Virtual IPS quarantine active'
            elif not device or not nonce or not isinstance(value,(int,float,str)) or isinstance(value,bool):
                decision, reason = 'BLOCK', 'Invalid telemetry'
            elif not hmac.compare_digest(signature, self.sign(device,nonce,value)):
                decision, reason = 'BLOCK', 'Message integrity check failed'
            elif (device, nonce) in self.nonces:
                decision, reason = 'BLOCK', 'Replay nonce detected'
            else:
                history = [t for t in self.calls.get(device, []) if now-t < 10]
                self.calls[device] = history
                if len(history) >= 8:
                    decision, reason = 'BLOCK', 'Rate limit: 8 requests per 10 seconds'
                else:
                    self.calls[device].append(now)
                    self.nonces.add((device, nonce))
                    decision, reason = 'ALLOW', 'Authenticated and integrity verified'
            attack_type, affected, precaution = {
                'Invalid device token': ('Unauthorized connection', 'Device access', 'Verify device enrollment and source'),
                'Invalid gateway token': ('Unauthorized connection', 'Gateway access', 'Verify authorized sender'),
                'Invalid per-device credential': ('Device impersonation attempt', 'Device identity', 'Verify enrolled device credentials and rotate compromised credentials'),
                'Device is not registered': ('Unknown device identity', 'Device registry', 'Review attempted device identity'),
                'Message integrity check failed': ('Message tampering', 'Telemetry integrity', 'Reject modified data; inspect sender'),
                'Replay nonce detected': ('Replay attempt', 'Session freshness', 'Require unique nonces'),
                'Rate limit: 8 requests per 10 seconds': ('Excessive requests', 'Gateway availability', 'Apply temporary throttling'),
                'Virtual IPS quarantine active': ('Virtual IPS containment', 'Device telemetry', 'Investigate and release from Administrator console'),
            }.get(reason, ('No confirmed attack', 'Device telemetry', 'Continue monitoring'))
            event = {'event_id':uuid.uuid4().hex, 'attack_type': attack_type, 'affected_component': affected, 'precaution': precaution, 'timestamp_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                     'device':device,'decision':decision,'reason':reason,'source':'LOCAL_HTTP',
                     'request_type':'telemetry', 'source_ip':source_ip, 'identity_verified': decision == 'ALLOW',
                     'reading':value if decision=='ALLOW' and isinstance(value,(int,float)) and not isinstance(value,bool) else None}
            self.events.appendleft(event)
        # After a normal decision, apply the optional risk-response policy.
        # A recorded BLOCK from an invalid gateway/device token NEVER causes
        # victim-device quarantine; that would enable a denial of service.
        if self.ips.observe(event, trusted_identity=trusted_identity, enrolled=enrolled):
            event['ips_action'] = 'Temporary virtual quarantine activated (120s)'
        if event['decision']=='ALLOW' and event['reading'] is not None:
            self.live_shadow.submit(event)
        # Alarm is queued on the FIRST qualifying request, not on a UI refresh.
        self.alarm_engine.notify(event)
        # Never hold the gateway lock while performing database I/O.
        # A failed DB write does not change the gateway's security decision.
        sink = self.event_sink
        if sink is not None:
            try:
                sink(event)
                self.last_persist_error = None
            except Exception as exc:
                self.last_persist_error = f'{type(exc).__name__}: {exc}'
        return event

    def send(self, scenario, device_override=None, reading=42):
        if not self.server:
            raise RuntimeError('Start the virtual gateway first')
        device = {'CCTV':'virtual-cctv-01','Router':'virtual-router-01','Sensor':'virtual-sensor-01'}.get(scenario,'virtual-cctv-01')
        if device_override is not None:
            if device_override not in self.registered_devices: raise ValueError('Unknown virtual device')
            device = device_override
        nonce = secrets.token_hex(12)
        payload = {'device':device,'nonce':nonce,'value':reading,'token':self.token, 'device_token':self.device_tokens[device]}
        payload['signature'] = self.sign(device,nonce,payload['value'])
        if scenario == 'Unauthorized access':
            payload['device_token'] = 'invalid-device-credential'
        if scenario == 'Tampered message':
            payload['value'] = 999
        if scenario == 'Replay attack':
            self._post(payload)
        if scenario == 'Rate limit':
            for _ in range(8):
                n = secrets.token_hex(12)
                p = dict(payload,nonce=n)
                p['signature'] = self.sign(device,n,p['value'])
                self._post(p)
            n = secrets.token_hex(12)
            payload['nonce'] = n
            payload['signature'] = self.sign(device,n,payload['value'])
        return self._post(payload)

    def _post(self, payload):
        req = Request('http://127.0.0.1:%d/telemetry'%self.port,
                      data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
        try:
            with urlopen(req,timeout=4) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            if exc.code == 403:
                return json.loads(exc.read())
            raise
