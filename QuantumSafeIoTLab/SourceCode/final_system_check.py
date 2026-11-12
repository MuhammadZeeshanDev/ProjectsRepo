"""Local Windows preflight, no keys, plaintext or credentials printed."""
import sys
from quantumsafe.crypto_engine import self_test
from quantumsafe.ml_engine.selector import find_swipl
from quantumsafe.ml_engine.incidents import audit

def main():
    print('QuantumSafe FINAL VIRTUAL DEMO - local verification')
    print('Python:',sys.version.split()[0])
    try:
        from quantumsafe import db, gateway_event_store
        with db.connection() as conn:
            server, database=conn.cursor().execute('SELECT @@SERVERNAME, DB_NAME()').fetchone()
        gateway_event_store.initialize()
        counts=gateway_event_store.counts()
        print('[PASS] SQL Server connected and gateway table initialized:',server,'/',database)
        print('  Confirmed SQL gateway events:',counts['total'])
    except Exception as exc:
        print('[NOT VERIFIED] SQL Server:',type(exc).__name__,str(exc))
    try:
        r=self_test('ML-KEM-768')
        print('[PASS] Real ML-KEM-768 agreement / decapsulation:',r['sizes'])
    except Exception as exc:
        print('[NOT VERIFIED] Real ML-KEM-768:',type(exc).__name__,str(exc))
    exe=find_swipl()
    print('SWI-Prolog executable:',exe if exe else '[NOT DETECTED] (Python rule fallback)')
    try:
        evidence=[dict(decision='BLOCK',device='virtual-cctv-01',reason='Encrypted packet replay blocked') for _ in range(3)]
        r=audit(evidence)
        print('[PASS] Reasoning engine:',r['engine'], 'risk=',r['devices']['virtual-cctv-01']['severity'])
    except Exception as exc:
        print('[NOT VERIFIED] Incident policy:',type(exc).__name__,str(exc))
    try:
        from quantumsafe.ml_engine.train import estimator_names
        available=estimator_names()
        print('ML algorithms:',', '.join(available))
    except Exception as exc:
        print('[NOT VERIFIED] ML engine:',type(exc).__name__,str(exc))
    print('\nNote: Real network router IPS is NOT implemented. Virtual localhost gateway only.')

if __name__=='__main__':main()
