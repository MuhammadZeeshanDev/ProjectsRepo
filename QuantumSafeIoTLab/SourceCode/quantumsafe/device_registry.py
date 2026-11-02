"""Persistent local virtual IoT enrollment; no remote provisioning claim.

Secrets are host-local and never included in UI inventory. Back up the Data folder.
"""
from __future__ import annotations
import json, os, re, secrets, tempfile, ipaddress
from pathlib import Path
from datetime import datetime, timezone
from threading import RLock

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_FILE=ROOT/'Data'/'virtual_devices.json'
TYPES=('Camera','Router','Sensor','Smart Plug','Other')
DEFAULTS={'virtual-cctv-01':('CCTV camera','Camera'),'virtual-router-01':('Router','Router'),'virtual-sensor-01':('Temperature sensor','Sensor')}
ID=re.compile(r'^[a-z0-9][a-z0-9-]{2,63}$')

def stamp():return datetime.now(timezone.utc).isoformat(timespec='seconds')

class DeviceRegistry:
    def __init__(self,path=None):
        self.path=Path(path or DEFAULT_FILE)
        self.lock=RLock()
        if self.path.exists():
            self._data=json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(self._data,dict) or self._data.get('version')!=1 or not isinstance(self._data.get('devices'),dict):
                raise ValueError('Device registry corrupted; refusing to overwrite credentials.')
        else:
            self._data=self._migrate_legacy() or {'version':1,'devices':{x:self._new(n,t) for x,(n,t) in DEFAULTS.items()}}
            self._persist(self._data)

    def _migrate_legacy(self):
        # v1.5 stored credentials in Data/device_registry.json. Preserve them
        # without changing or deleting the legacy file. Never rotate silently.
        legacy=self.path.parent/'device_registry.json'
        if not legacy.is_file() or legacy==self.path:return None
        old=json.loads(legacy.read_text(encoding='utf-8'))
        if old.get('version')!=1 or not isinstance(old.get('devices'),dict):
            raise ValueError('Legacy device registry format invalid; cannot migrate safely')
        devices={}
        for id_,record in old['devices'].items():
            state=record.get('state',record.get('status','active'))
            item={'name':record['name'],'kind':record['kind'],'status':state,
                  'created':record.get('created_utc',stamp()),
                  'modified':record.get('updated_utc',stamp()),
                  'virtual_ip':record.get('virtual_ip',''), 'virtual_mac':record.get('virtual_mac','')}
            if state!='retired':
                key=record.get('key_hex');token=record.get('token')
                if not key or not token:raise ValueError('Legacy active credentials missing; refusing migration')
                bytes.fromhex(key)
                item.update(key_hex=key,token=token)
            devices[id_]=item
        return {'version':1,'devices':devices}

    def _new(self,name,kind):
        return {'name':name,'kind':kind,'status':'active','created':stamp(),'modified':stamp(),
                'key_hex':secrets.token_hex(32),'token':secrets.token_urlsafe(32),
                'virtual_ip':'','virtual_mac':''}

    def _persist(self,obj):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,temp=tempfile.mkstemp(prefix='.qs_devices_',suffix='.tmp',dir=self.path.parent)
        try:
            try:os.fchmod(fd,0o600)
            except (OSError,AttributeError):pass
            with os.fdopen(fd,'w',encoding='utf-8') as stream:
                json.dump(obj,stream,indent=2,sort_keys=True)
                stream.flush();os.fsync(stream.fileno())
            os.replace(temp,self.path)
        finally:
            if os.path.exists(temp):os.unlink(temp)

    def _change(self,device,record):
        candidate={'version':1,'devices':dict(self._data['devices'])}
        candidate['devices'][device]=record
        self._persist(candidate)
        self._data=candidate

    def inventory(self):
        with self.lock:
            return [{'id':id_,'name':r['name'],'type':r['kind'],'status':r['status'],
                     'created_utc':r.get('created'),'modified_utc':r.get('modified'),
                     'virtual_ip':r.get('virtual_ip',''),'virtual_mac':r.get('virtual_mac','')}
                    for id_,r in sorted(self._data['devices'].items())]

    def credentials(self):
        with self.lock:
            return {id_:(r['name'],bytes.fromhex(r['key_hex']),r['token'])
                    for id_,r in self._data['devices'].items() if r['status']=='active'}

    def apply(self,action,device_id,*,name=None,kind=None,virtual_ip='',virtual_mac='',actor='Administrator'):
        device_id=str(device_id).strip().lower()
        if not ID.fullmatch(device_id):raise ValueError('Device ID: 3–64 lower-case letters, numbers, hyphens.')
        with self.lock:
            previous=self._data['devices'].get(device_id)
            if action=='register':
                if previous is not None:raise ValueError('Device ID already registered or previously retired.')
                name=str(name or '').strip()
                if not 2<=len(name)<=80:raise ValueError('Device name must be 2–80 characters.')
                if kind not in TYPES:raise ValueError('Invalid virtual device type.')
                # Optional simulated address is INVENTORY METADATA, not DHCP assignment.
                virtual_ip=str(virtual_ip or '').strip()
                virtual_mac=str(virtual_mac or '').strip().lower()
                if virtual_ip:
                    parsed=ipaddress.ip_address(virtual_ip)
                    if parsed.version!=4 or parsed.is_multicast or parsed.is_unspecified:
                        raise ValueError('Virtual IP must be a unicast IPv4 address')
                    if any(x.get('virtual_ip')==virtual_ip and x.get('status')!='retired' for x in self._data['devices'].values()):
                        raise ValueError('Virtual IP already assigned in inventory')
                if virtual_mac and not re.fullmatch(r'[0-9a-f]{2}(:[0-9a-f]{2}){5}',virtual_mac):
                    raise ValueError('MAC format must be AA:BB:CC:DD:EE:FF')
                record=self._new(name,kind)
                record['virtual_ip']=virtual_ip
                record['virtual_mac']=virtual_mac
            else:
                if previous is None or previous['status']=='retired':raise ValueError('Device ID missing or retired permanently.')
                record=dict(previous,modified=stamp())
                if action=='disable':record['status']='disabled'
                elif action=='enable':record['status']='active'
                elif action=='rotate':
                    record['key_hex']=secrets.token_hex(32)
                    record['token']=secrets.token_urlsafe(32)
                elif action=='retire':
                    record['status']='retired';record.pop('key_hex',None);record.pop('token',None)
                else:raise ValueError('Unsupported operation.')
            self._change(device_id,record)
            with (self.path.parent/'device_actions.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps({'utc':stamp(),'actor':str(actor)[:80],
                    'action':action,'device_id':device_id})+'\n')
            return device_id
