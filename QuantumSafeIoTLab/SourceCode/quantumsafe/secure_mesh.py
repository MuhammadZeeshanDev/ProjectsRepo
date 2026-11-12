"""Authenticated *virtual* device-to-device ML-KEM-768 + HKDF + AES-256-GCM.

Security boundary: the relay accepts an envelope (encrypted bytes + public
routing metadata) and never receives a session key or plaintext argument.
Virtual endpoint agents all run within the SAME PC A Python process, not separate
physical device processes. Not a LAN-wide packet interception mechanism.
"""
from __future__ import annotations
import base64
import hashlib
import json
import secrets
import threading
from collections import deque
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from . import crypto_engine

ALGORITHM = 'ML-KEM-768'
MAX_PLAINTEXT = 4096


def _aad(sender: str, receiver: str, nonce: bytes) -> bytes:
    return json.dumps({'v': 1, 'src': sender, 'dst': receiver,
                       'algorithm': ALGORITHM, 'nonce': base64.b64encode(nonce).decode('ascii')},
                      sort_keys=True, separators=(',', ':')).encode('ascii')


def _key(shared: bytes, sender: str, receiver: str, nonce: bytes) -> bytes:
    # Fresh ML-KEM shared secret and nonce/context-bound domain separation.
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=nonce,
                info=b'QuantumSafe-IoT-virtual-mesh-v1\0'+sender.encode()+b'\0'+receiver.encode()).derive(shared)


class MeshRejected(ValueError):
    """Unauthorized or invalid virtual encrypted delivery."""


@dataclass
class _Agent:
    """A virtual DEVICE endpoint; private key stays in agent memory only."""
    device_id: str
    public_key: bytes
    secret_key: bytes
    credential_fingerprint: str

    @classmethod
    def create(cls, device_id: str, credential: bytes):
        pk, sk = crypto_engine.make_keys(ALGORITHM)
        return cls(device_id, pk, sk, hashlib.sha256(credential).hexdigest())

    def decrypt(self, envelope: dict) -> str:
        if envelope['receiver'] != self.device_id:
            raise MeshRejected('Destination mismatch')
        nonce = envelope['nonce']
        shared = crypto_engine.decapsulate(ALGORITHM, self.secret_key, envelope['kem_ciphertext'])
        payload = AESGCM(_key(shared,envelope['sender'],self.device_id,nonce)).decrypt(
            nonce, envelope['ciphertext'], _aad(envelope['sender'],self.device_id,nonce))
        return payload.decode('utf-8', errors='strict')


class SecureMesh:
    """In-process virtual endpoints joined by a ciphertext-only relay."""
    def __init__(self, gateway):
        self.gateway = gateway
        self._agents = {}
        self._used = set()
        self._recent = deque(maxlen=10000)
        self._lock = threading.RLock()

    def purge_revoked(self):
        """Erase references to virtual private keys when an identity changes."""
        with self._lock:
            for did in list(self._agents):
                cred=self.gateway.device_keys.get(did)
                if cred is None or self._agents[did].credential_fingerprint != hashlib.sha256(cred).hexdigest():
                    self._agents.pop(did,None)

    def _current_agent(self, device_id):
        # Device enrollment/disable/rekey/retire changes are enforced before dispatch.
        credential = self.gateway.device_keys.get(device_id)
        if credential is None:
            raise MeshRejected('Sender or recipient is not enrolled and active')
        fingerprint = hashlib.sha256(credential).hexdigest()
        existing = self._agents.get(device_id)
        if existing is None or existing.credential_fingerprint != fingerprint:
            existing = _Agent.create(device_id, credential)
            self._agents[device_id] = existing
        return existing

    def _relay(self, envelope):
        """Gateway relay sees ciphertext, routing IDs and nonce only."""
        sender, receiver = envelope['sender'], envelope['receiver']
        if sender == receiver:
            raise MeshRejected('Choose two different enrolled devices')
        if (sender not in self.gateway.registered_devices or
                receiver not in self.gateway.registered_devices):
            raise MeshRejected('Unregistered or disabled device')
        if self.gateway.ips.active(sender) or self.gateway.ips.active(receiver):
            raise MeshRejected('Virtual IPS quarantine blocks encrypted traffic')
        marker = (sender, receiver, envelope['nonce'])
        if marker in self._used:
            raise MeshRejected('Encrypted packet replay blocked')
        destination = self._current_agent(receiver)
        try:
            delivered = destination.decrypt(envelope)
        except Exception as exc:
            # No internal crypto exception/secret exposed to the UI.
            raise MeshRejected('Encrypted packet authentication failed (tampering or invalid key)') from exc
        self._used.add(marker)
        self._recent.append(marker)
        if len(self._used) > 10000:
            self._used = set(self._recent)
        return delivered

    def exchange(self, sender, receiver, text, *, scenario='normal'):
        """Simulated source encodes; relay passes ciphertext; destination decrypts.

        Return only non-secret observable evidence; decrypted text shown explicitly
        to the Administrator for the demonstration, never written to SQL/events.
        """
        if scenario not in ('normal','tamper','replay'):
            raise ValueError('Unknown simulation scenario')
        raw = str(text).encode('utf-8')
        if not raw or len(raw)>MAX_PLAINTEXT:
            raise ValueError('Text must be between 1 and 4096 UTF-8 bytes')
        with self._lock:
            if not self.gateway.server:
                raise RuntimeError('Start the virtual gateway before secure communication')
            # Both endpoints are registered virtual identities. No keys to relay.
            self._current_agent(sender)
            recipient = self._current_agent(receiver)
            nonce=secrets.token_bytes(12)
            kem_ciphertext, shared=crypto_engine.encapsulate(ALGORITHM, recipient.public_key)
            encrypted=AESGCM(_key(shared,sender,receiver,nonce)).encrypt(nonce,raw,_aad(sender,receiver,nonce))
            envelope={'sender':sender,'receiver':receiver,'nonce':nonce,
                      'kem_ciphertext':kem_ciphertext,'ciphertext':encrypted}
            observed={**envelope}
            if scenario=='tamper':
                corrupted=bytearray(encrypted);corrupted[-1]^=0x01
                observed['ciphertext']=bytes(corrupted)
            decrypted=None; initial=None
            if scenario=='replay':
                initial=self._relay(envelope)  # legitimate first delivery
            try:
                decrypted=self._relay(observed)
                decision,reason='ALLOW','ML-KEM-768 + AES-256-GCM: receiver authenticated and decrypted'
            except MeshRejected as exc:
                decision,reason='BLOCK',str(exc)
            return {'decision':decision, 'reason':reason,'algorithm':ALGORITHM,
                    'encryption':'AES-256-GCM', 'kdf':'HKDF-SHA256',
                    'sender':sender,'receiver':receiver,'scenario':scenario,
                    'receiver_opened':decrypted is not None,
                    'delivered_text':decrypted, # UI demo only; NEVER persist
                    'first_delivery':initial is not None,
                    'nonce_bytes':len(nonce),'kem_ciphertext_bytes':len(kem_ciphertext),
                    'ciphertext_bytes':len(encrypted),
                    'ciphertext_sha256':hashlib.sha256(observed['ciphertext']).hexdigest(),
                    'recipient_public_key_fingerprint':hashlib.sha256(recipient.public_key).hexdigest()[:24]}
