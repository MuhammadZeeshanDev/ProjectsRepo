"""Loopback-only HTTP virtual IoT gateway. Not packet capture or network-wide firewall."""
import uuid
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
        self.registered_devices = {'virtual-cctv-01':'CCTV camera', 'virtual-router-01':'Router', 'virtual-sensor-01':'Temperature sensor'}
        # Independent credentials per enrolled virtual device; never exposed to PC B.
        self.device_keys = {device: secrets.token_bytes(32) for device in self.registered_devices}
        self.device_tokens = {device: secrets.token_urlsafe(24) for device in self.registered_devices}
        self.event_sink = None  # optional SQL writer; called after in-memory event append
        self.last_persist_error = None

    def start(self, port=8765):
        if self.server:
            return self.port
        gateway = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
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
        self.server = ThreadingHTTPServer(('127.0.0.1', int(port)), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.port

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=3)
            self.server = None
            self.thread = None
            self.port = None

    def sign(self, device, nonce, value):
        msg = json.dumps([device, nonce, value], separators=(',', ':'), ensure_ascii=True).encode()
        return hmac.new(self.device_keys[device], msg, hashlib.sha256).hexdigest()

    def evaluate(self, data, source_ip="local"):
        device = str(data.get('device',''))[:64]
        nonce = str(data.get('nonce',''))[:100]
        value = data.get('value')
        signature = str(data.get('signature',''))
        authenticated = hmac.compare_digest(str(data.get('token','')), self.token)
        now = time.monotonic()
        with self.lock:
            if device not in self.registered_devices:
                decision, reason = 'BLOCK', 'Device is not registered'
            elif not authenticated:
                decision, reason = 'BLOCK', 'Invalid gateway token'
            elif not hmac.compare_digest(str(data.get('device_token', '')), self.device_tokens[device]):
                decision, reason = 'BLOCK', 'Invalid per-device credential'
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
            }.get(reason, ('No confirmed attack', 'Device telemetry', 'Continue monitoring'))
            event = {'event_id':uuid.uuid4().hex, 'attack_type': attack_type, 'affected_component': affected, 'precaution': precaution, 'timestamp_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                     'device':device,'decision':decision,'reason':reason,'source':'LOCAL_HTTP',
                     'request_type':'telemetry', 'source_ip':source_ip, 'identity_verified': decision == 'ALLOW'}
            self.events.appendleft(event)
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

    def send(self, scenario, device_override=None):
        if not self.server:
            raise RuntimeError('Start the virtual gateway first')
        device = {'CCTV':'virtual-cctv-01','Router':'virtual-router-01','Sensor':'virtual-sensor-01'}.get(scenario,'virtual-cctv-01')
        if device_override is not None:
            if device_override not in self.registered_devices: raise ValueError('Unknown virtual device')
            device = device_override
        nonce = secrets.token_hex(12)
        payload = {'device':device,'nonce':nonce,'value':42,'token':self.token, 'device_token':self.device_tokens[device]}
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
