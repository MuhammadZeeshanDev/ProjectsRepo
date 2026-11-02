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
