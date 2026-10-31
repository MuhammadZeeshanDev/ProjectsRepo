"""Start/stop the virtual LAN gateway from Streamlit GUI buttons."""
import threading
from .lan_gateway_core import Gateway, SESSION_TTL_SEC
from .lan_gateway_server import LabHTTPServer, build_handler
from . import lan_protocol as p


class GatewayController:
    """Start/stop the listener with Streamlit buttons, not terminal commands."""

    def __init__(self):
        self._server = None
        self._thread = None
        self.gateway = None
        self.bind = None
        self.port = None
        self.owner_id = None
        self._lock = threading.Lock()

    @property
    def running(self):
        return self._server is not None and self._thread is not None and self._thread.is_alive()

    def start(self, secret, port=8765, allow_lan=False, event_sink=None, owner_id=None):
        p.check_secret(secret)
        if type(port) is not int or not 1024 <= port <= 65535:
            raise ValueError('Choose a port between 1024 and 65535.')
        with self._lock:
            if self.running:
                raise RuntimeError('Gateway already started. Stop it first.')
            gateway = Gateway(secret, event_sink)
            bind = '0.0.0.0' if allow_lan else '127.0.0.1'
            server = LabHTTPServer((bind, port), build_handler(gateway))
            thread = threading.Thread(target=server.serve_forever, daemon=True,
                                      name='QuantumSafeLabGateway')
            thread.start()
            self._server, self._thread = server, thread
            self.gateway, self.bind, self.port, self.owner_id = gateway, bind, port, owner_id

    def stop(self):
        with self._lock:
            if self._server:
                self._server.shutdown()
                self._server.server_close()
                self._thread.join(timeout=3)
            self._server = None
            self._thread = None
            self.gateway = None
            self.bind = self.port = self.owner_id = None
