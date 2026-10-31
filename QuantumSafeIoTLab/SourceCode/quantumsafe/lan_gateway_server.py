"""HTTP parsing for lab requests; business logic lives in lan_gateway_core."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from . import lan_protocol as p


class LabHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def build_handler(gateway):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # No sensitive request details are printed.

        def _answer(self, status, body):
            data = json.dumps(body).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == '/health':
                return self._answer(200, {'service': p.PROTOCOL, 'status': 'ready'})
            return self._answer(404, {'error': 'Unknown route.'})

        def do_POST(self):
            if self.path not in ('/hello', '/deliver'):
                return self._answer(404, {'error': 'Unknown route.'})
            try:
                size = int(self.headers.get('Content-Length', '-1'))
                if not 0 < size <= p.MAX_BODY_BYTES:
                    return self._answer(413, {'error': 'Request size is invalid.'})
                payload = json.loads(self.rfile.read(size).decode('utf-8'))
                if not isinstance(payload, dict):
                    raise ValueError('Expected an object.')
                ip = self.client_address[0]
                if self.path == '/hello':
                    status, body = gateway.hello(payload.get('algorithm'), ip)
                else:
                    status, body = gateway.deliver(payload, ip)
                return self._answer(status, body)
            except (ValueError, UnicodeDecodeError):
                return self._answer(400, {'error': 'Malformed JSON request.'})
            except Exception:
                return self._answer(500, {'error': 'Gateway error; see local checks.'})
    return Handler
