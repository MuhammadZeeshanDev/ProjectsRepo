"""Local SWI-Prolog-backed selection of validated model *shadow* routes.

Uses conservative fixed facts, code reviewed static Prolog rule file and bounded
independent held-out metrics. Python fallback calculates exactly same score.
"""
from __future__ import annotations
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from . import registry

RULES=Path(__file__).resolve().parents[1]/'rules'/'ids_model_selector.pl'


def find_swipl(path=None):
    candidates=[]
    if path:candidates.append(path)
    if os.getenv('QUANTUMSAFE_SWIPL'):candidates.append(os.getenv('QUANTUMSAFE_SWIPL'))
    v=shutil.which('swipl')
    if v:candidates.append(v)
    if os.name=='nt':
        for key in ('ProgramFiles','ProgramFiles(x86)'):
            root=os.environ.get(key)
            if not root:continue
            parent=Path(root)
            candidates.append(str(parent/'swipl'/'bin'/'swipl.exe'))
            candidates += [str(x) for x in (parent/'SWI-Prolog').glob('*/bin/swipl.exe')]
    for c in candidates:
        if not c:continue
        try:
            p=Path(c).resolve()
            if not p.is_file() or p.name.lower() not in ('swipl','swipl.exe'):continue
            result=subprocess.run([str(p),'--version'],capture_output=True,timeout=4)
            if result.returncode==0:return str(p)
        except (OSError, subprocess.SubprocessError):pass
    return None


def _facts_for(rows,base):
    facts=[];mapping={};reason=[]
    for row in rows:
        if row['status']=='retired':continue
        # Known shortcut in Edge-IIoTset experiments: this feature can reveal
        # data formatting instead of the actual attack. Never auto-route it.
        dataset=str(row.get('dataset_file') or '').casefold()
        if ('edge' in dataset and 'iot' in dataset and
                'mqtt.protoname' in row['features']):
            reason.append(f'Model {row["id"]}: excluded from automatic routing; Edge-IIoTset mqtt.protoname label-shortcut risk')
            continue
        try:
            folder=Path(base or registry.BASE)
            path=(folder/row['checkpoint']).resolve()
            if path.parent != (folder/'models').resolve():raise ValueError('path')
            if not path.is_file():raise ValueError('file missing')
            h=hashlib.sha256()
            with path.open('rb') as f:
                for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
            if h.hexdigest()!=row['sha256']:raise ValueError('hash mismatch')
        except (ValueError,OSError) as exc:
            reason.append(f'Model {row["id"]}: checkpoint integrity not verified ({exc})')
            continue
        latency=row['metrics'].get('latency_ms_per_row')
        if latency is None:continue
        for threat,score in row['class_metrics'].items():
            if threat==row['normal_label']:continue
            p=score.get('precision'); r=score.get('recall'); fpr=score.get('false_positive_rate')
            support=score.get('support',0)
            if p is None or r is None or fpr is None:continue
            if not all(0<=float(x)<=1 for x in (p,r,fpr)):continue
            if not 0<=float(latency)<=100000:continue
            token='t'+hashlib.sha256(threat.encode('utf-8')).hexdigest()[:20]
            mid=f'm{int(row["id"])}'
            mapping[token]=threat
            ints=(round(float(r)*1000),round(float(p)*1000),round(float(fpr)*1000),
                  round(float(latency)*1000),int(support),1)
            facts.append((mid,token,*ints))
    return facts,mapping,reason


def _allowed(fact):
    m,t,r,p,f,lat,sup,integrity=fact
    return integrity==1 and sup>=5 and r>=600 and f<=200 and lat<=500000


def _score(fact):
    _,_,r,p,f,lat,_,_=fact
    return 6*r+3*p-8*f-(lat//10)


def _python_engine(facts):
    chosen={}
    for fact in facts:
        if not _allowed(fact):continue
        mid,threat= fact[0],fact[1]
        score=_score(fact)
        old=chosen.get(threat)
        if old is None or score>old[1] or (score==old[1] and mid<old[0]):
            chosen[threat]=(mid,score)
    return chosen


def _prolog_engine(facts,exe):
    # No CSV fields or raw data interpolated into Prolog. Token atoms/numbers only.
    with tempfile.TemporaryDirectory(prefix='qs_prolog_ids_') as td:
        fact_file=Path(td)/'facts.pl'
        fact_file.write_text('\n'.join('eligible(%s,%s,%d,%d,%d,%d,%d,%d).'%f for f in facts)+'\n',encoding='ascii')
        cmd=[exe,'-q','-s',str(RULES),'-s',str(fact_file),'-g','run,halt']
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=15,check=True)
    result={}
    for line in proc.stdout.splitlines():
        parts=line.strip().split('|')
        if len(parts)!=3 or not re.fullmatch('t[0-9a-f]{20}',parts[0]) or not re.fullmatch('m[0-9]+',parts[1]):
            raise ValueError('Prolog returned an unexpected fact')
        result[parts[0]]=(parts[1],int(parts[2]))
    if result!=_python_engine(facts):
        raise ValueError('Prolog/Python independent rule agreement failed: no routes saved.')
    return result


def rank(*,root=None,dataset_sha=None,swipl=None,persist=True):
    all_models=registry.models(root)
    if not all_models: return {'engine':'none','routes':{},'reason':['No local evaluated models']}
    if dataset_sha is None:dataset_sha=all_models[0]['dataset_sha256']
    selected=[m for m in all_models if m['dataset_sha256']==dataset_sha]
    facts,mapping,errors=_facts_for(selected,root)
    # A model trained from a DIFFERENT dataset is never silently compared.
    exe=find_swipl(swipl)
    if exe and RULES.exists():
        try:
            decision=_prolog_engine(facts,exe)
            engine='SWI-Prolog native'
        except (OSError, subprocess.SubprocessError,ValueError) as exc:
            # Fail closed on wrong rules. For executable errors, explicit fallback.
            if 'agreement failed' in str(exc):raise
            errors.append(f'SWI-Prolog issue: {type(exc).__name__}: {exc}')
            decision=_python_engine(facts)
            engine='Python fallback (native Prolog unavailable)'
    else:
        decision=_python_engine(facts)
        engine='Python fallback (native Prolog not installed)'
    output={mapping[t]:{'model_id':int(mid[1:]),'score':score,'mode':'shadow_only'} for t,(mid,score) in decision.items()}
    if persist:registry.save_routes(output,engine,root)
    return {'engine':engine,'dataset_sha256':dataset_sha,'routes':output,
            'reason':errors,'facts_evaluated':len(facts),
            'notice':'Route selection does not enable network-wide detection, blocking or unattended model promotion.'}
