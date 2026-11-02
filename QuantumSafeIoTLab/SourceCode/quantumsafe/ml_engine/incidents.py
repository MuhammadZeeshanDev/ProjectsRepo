"""SWI-Prolog/Python severity review from actual gateway incident log evidence.

Rules may recommend critical/high alerts, but never directly contact police,
block a network adapter, isolate a device or rotate secrets by themselves.
"""
from __future__ import annotations
import hashlib
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from .selector import find_swipl

RULES=Path(__file__).resolve().parents[1]/'rules'/'ids_incident_policy.pl'


def _summaries(events):
    aggregate={}
    for e in (events or [])[:5000]:
        if not isinstance(e,dict) or e.get('decision')!='BLOCK':continue
        device=str(e.get('device') or 'unknown')[:64]
        text=(str(e.get('reason') or '')+' '+str(e.get('attack_type') or '')).casefold()
        counts=aggregate.setdefault(device,Counter())
        counts['blocked']+=1
        if 'replay' in text or 'nonce' in text:counts['replay']+=1
        if any(k in text for k in ('invalid hmac','invalid signature','invalid mac','tampering','crypto fail')):
            counts['crypto']+=1
        if 'not registered' in text or 'unregistered' in text or 'unknown device' in text:
            counts['unknown']+=1
        if 'rate limit' in text:counts['rate']+=1
    return aggregate


def _fallback(counts):
    out={}
    for device,c in counts.items():
        if c['replay']>=3 or c['crypto']>=3:severity='critical'
        elif c['blocked']>=5 or c['unknown']>=2 or c['rate']>=3:severity='high'
        else:severity='medium'
        advice=[]
        if c['crypto']>=2:advice.append('rotate_review')
        if c['replay']>=3 or c['unknown']>=2:advice.append('quarantine_review')
        if c['blocked']>=1:advice.append('investigate')
        out[device]={'severity':severity,'recommendations':sorted(advice),'blocked':c['blocked']}
    return out


def audit(events,swipl=None):
    sums=_summaries(events)
    expected=_fallback(sums)
    exe=find_swipl(swipl)
    if not exe:return {'engine':'Python rules fallback (SWI-Prolog unavailable)','devices':expected}
    labels={}
    facts=[]
    for dev,c in sums.items():
        tok='d'+hashlib.sha256(dev.encode()).hexdigest()[:24]
        labels[tok]=dev
        facts.append(f"event_counts({tok},{c['blocked']},{c['replay']},{c['crypto']},{c['unknown']},{c['rate']}).")
    with tempfile.TemporaryDirectory(prefix='qs_incident_facts_') as tmp:
        path=Path(tmp)/'facts.pl';path.write_text('\n'.join(facts)+'\n',encoding='ascii')
        try:
            response=subprocess.run([exe,'-q','-s',str(RULES),'-s',str(path),'-g','run,halt'],
                                    capture_output=True,text=True,timeout=10,check=True)
        except (OSError,subprocess.SubprocessError) as exc:
            return {'engine':f'Python fallback (Prolog execution failed: {type(exc).__name__})', 'devices':expected}
    received={dev:{'severity':None,'recommendations':[],'blocked':sums[dev]['blocked']} for dev in sums}
    for line in response.stdout.splitlines():
        parts=line.strip().split('|')
        if len(parts)!=3 or parts[1] not in labels:
            raise ValueError('Invalid SWI-Prolog incident policy output; refusing to use it.')
        typ,token,val=parts;entry=received[labels[token]]
        if typ=='risk' and val in ('medium','high','critical'):entry['severity']=val
        elif typ=='advice' and val in ('rotate_review','quarantine_review','investigate'):
            entry['recommendations'].append(val)
        else: raise ValueError('Unexpected Prolog policy output')
    for d in received:received[d]['recommendations'].sort()
    if received != expected:raise ValueError('Native Prolog and independent Python policy disagree; fail closed')
    return {'engine':'SWI-Prolog native','devices':received}
