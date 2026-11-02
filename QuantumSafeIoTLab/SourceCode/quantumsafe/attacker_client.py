"""Independent credential-free localhost-only virtual PC B. No exploit payloads."""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
PORT=8765
DEVICES={
 'virtual-cctv-01': 'CCTV Camera',
 'virtual-router-01': 'Network Router',
 'virtual-sensor-01': 'Temperature Sensor',
}
TESTS={
 'virtual-cctv-01': {'camera_unauthorized':('Camera: unauthorized viewer','Attempts camera telemetry access without credentials','Device access'), 'camera_repeated':('Camera: repeated access attempts','Sends five unauthenticated camera requests','Camera access availability')},
 'virtual-router-01': {'router_unauthorized':('Router: unauthorized management','Attempts router telemetry access without credentials','Router management access'), 'router_repeated':('Router: repeated login attempts','Sends five unauthenticated router requests','Gateway availability')},
 'virtual-sensor-01': {'sensor_unauthorized':('Sensor: unauthorized reading','Attempts to submit sensor telemetry without credentials','Sensor data trust'), 'sensor_repeated':('Sensor: repeated data submissions','Sends five unauthenticated sensor requests','Sensor telemetry availability')},
}
def send_test(test,device='virtual-cctv-01',port=PORT):
 if device not in TESTS or test not in TESTS[device]:raise ValueError('Unsupported lab device or test')
 if type(port) is not int or not 1<=port<=65535:raise ValueError('Invalid port')
 attempts=5 if test.endswith('_repeated') else 1
 results=[]
 for i in range(attempts):
  payload={'device':device,'nonce':f'pc-b-{test}-{i}','value':42,'token':'untrusted-client','device_token':'untrusted-device','signature':'0'*64}
  req=Request(f'http://127.0.0.1:{port}/telemetry',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
  try:
   with urlopen(req,timeout=3) as response: results.append(json.loads(response.read()))
  except HTTPError as exc:
   if exc.code!=403:raise
   results.append(json.loads(exc.read()))
  except URLError as exc:raise ConnectionError('Start defender gateway on 127.0.0.1:8765') from exc
 return results

def send_untrusted_device(device_id,port=PORT):
    """Custom virtual target test; deliberately never receives trusted credentials."""
    import re,secrets
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,63}',str(device_id)):
        raise ValueError('Valid target ID: 3–64 lowercase alphanumeric/hyphen')
    if type(port) is not int or not 1<=port<=65535:raise ValueError('Invalid port')
    payload={'device':device_id,'nonce':secrets.token_hex(12),'value':42,
             'token':'untrusted-client','device_token':'untrusted-device','signature':'0'*64}
    req=Request(f'http://127.0.0.1:{port}/telemetry',data=json.dumps(payload).encode(),
                headers={'Content-Type':'application/json'},method='POST')
    try:
        with urlopen(req,timeout=3) as result:return json.loads(result.read())
    except HTTPError as exc:
        if exc.code!=403:raise
        return json.loads(exc.read())
    except URLError as exc:raise ConnectionError('Start virtual gateway before PC B test') from exc


def discover_targets():
    """Read-only enrolled virtual device list from the shared same-PC registry.

    No gateway token, private device key, or device auth token is returned.
    This is local lab inventory, not discovery of physical devices / other PCs.
    """
    from .device_registry import DeviceRegistry
    rows=DeviceRegistry().inventory()
    return [{'id':row['id'],'name':row['name'],'type':row['type'],
             'virtual_ip':row.get('virtual_ip') or '', 'status':row['status']}
            for row in rows if row['status']!='retired']


def send_dynamic_test(device_id,case='unauthorized',port=PORT):
    """Credential-free, bounded local HTTP requests to any newly registered ID."""
    if case not in ('unauthorized','repeated'):raise ValueError('Unsupported PC B test')
    from secrets import token_hex
    import re
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,63}',str(device_id)):
        raise ValueError('Invalid virtual target')
    if type(port) is not int or not 1<=port<=65535:raise ValueError('Invalid lab port')
    output=[]
    for _ in range(5 if case=='repeated' else 1):
        payload={'device':device_id,'nonce':token_hex(12),'value':42,
                 'token':'untrusted-client','device_token':'untrusted-device','signature':'0'*64}
        request=Request(f'http://127.0.0.1:{port}/telemetry',data=json.dumps(payload).encode(),
                        headers={'Content-Type':'application/json'},method='POST')
        try:
            with urlopen(request,timeout=4) as response:output.append(json.loads(response.read()))
        except HTTPError as exc:
            if exc.code!=403:raise
            output.append(json.loads(exc.read()))
        except URLError as exc:raise ConnectionError('Start gateway on PC A first') from exc
    return output
