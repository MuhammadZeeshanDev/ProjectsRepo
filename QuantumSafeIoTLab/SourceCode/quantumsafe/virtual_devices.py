"""Controlled virtual-device telemetry loop. Simulated traffic stays on localhost."""
import math, threading, time
from datetime import datetime, timezone

class VirtualDeviceRunner:
    def __init__(self):
        self.lock=threading.RLock()
        self._active={}
        self._threads={}

    def running(self):
        with self.lock:
            return sorted(key for key,flag in self._active.items() if flag.is_set())

    def start(self,gw,device_id,interval=5):
        if not 2<=interval<=60:raise ValueError('Interval must be between 2 and 60 seconds.')
        with self.lock:
            if device_id not in gw.registered_devices:raise ValueError('Device not registered or disabled.')
            if device_id in self._active and self._active[device_id].is_set():return False
            flag=threading.Event();flag.set();self._active[device_id]=flag
            thread=threading.Thread(target=self._run,args=(gw,device_id,interval,flag),daemon=True,
                                    name='QS_Virtual_'+device_id[:25])
            self._threads[device_id]=thread;thread.start()
            return True

    def stop(self,device_id):
        with self.lock:
            flag=self._active.get(device_id)
            if flag:flag.clear()

    def _run(self,gw,device_id,interval,flag):
        tick=0
        while flag.is_set():
            if device_id not in gw.registered_devices or not gw.server:
                flag.clear();break
            try:
                # Simulated reading: not a real device sensor value.
                reading=round(22+3*math.sin(tick*0.21),2)
                gw.send('Sensor',device_override=device_id,reading=reading)
            except (OSError,RuntimeError,ValueError,KeyError):
                flag.clear();break
            tick+=1
            for _ in range(int(interval*10)):
                if not flag.is_set():break
                time.sleep(0.1)
