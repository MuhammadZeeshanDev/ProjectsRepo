"""Persistent metadata for admin-submitted training jobs, one local worker thread.

Jobs continue while Streamlit reruns. Stopping the app stops the worker; unfinished
jobs are marked interrupted at next startup, never reported as success.
"""
from __future__ import annotations
import json,sqlite3,threading,traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from . import registry,train,data,selector

DB=registry.BASE/'admin_jobs.sqlite3'
_lock=threading.RLock()
_executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='QS_Admin_Training')

def utc():return datetime.now(timezone.utc).isoformat(timespec='seconds')

def _connect(path=None):
    path=Path(path or DB);path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=30)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA busy_timeout=30000')
    db.execute('CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, created_utc TEXT, updated_utc TEXT, status TEXT, step TEXT, request_json TEXT, result_json TEXT, error TEXT)')
    db.commit();return db

def recover_interrupted(path=None):
    with _lock, _connect(path) as db:
        db.execute("UPDATE jobs SET status='interrupted',step='Server restarted during job',updated_utc=? WHERE status IN ('running','queued')",(utc(),))
        db.commit()

def _update(jid,*,status=None,step=None,result=None,error=None,path=None):
    updates={'updated_utc':utc()}
    if status is not None:updates['status']=status
    if step is not None:updates['step']=step
    if result is not None:updates['result_json']=json.dumps(result,default=str)
    if error is not None:updates['error']=str(error)[:2500]
    keys=list(updates)
    with _lock, _connect(path) as db:
        db.execute('UPDATE jobs SET '+','.join(x+'=?' for x in keys)+' WHERE id=?',[updates[x] for x in keys]+[jid])
        db.commit()

def list_jobs(limit=20,path=None):
    with _lock, _connect(path) as db:
        rows=db.execute('SELECT * FROM jobs ORDER BY id DESC LIMIT ?', (max(1,min(int(limit),100)),)).fetchall()
    out=[]
    for row in rows:
        d=dict(row)
        d['request']=json.loads(d.pop('request_json') or '{}')
        d['result']=json.loads(d.pop('result_json') or 'null')
        out.append(d)
    return out

def submit_training(request,path=None,root=None):
    # Validate BEFORE scheduling a potentially expensive job. Path is local to PC A.
    if request.get('kind') not in ('train','retrain'):raise ValueError('Invalid job kind')
    filename,cols=data.inspect_headers(request['csv'])
    if request['kind']=='train':
        data.pick_label(cols,request.get('label'))
        algorithms=request.get('algorithms',[])
        if not algorithms or any(a not in train.estimator_names() for a in algorithms):raise ValueError('Select installed algorithms')
    else:
        registry.get_model(int(request['model_id']),root)
    if int(request.get('max_rows',30000)) not in range(200,500001):raise ValueError('Sample rows 200–500000')
    if int(request.get('folds',3)) not in (3,5):raise ValueError('3 or 5 folds only')
    if request.get('binary') and not str(request.get('normal','')).strip():raise ValueError('Normal label required for binary mode')
    payload=dict(request,csv=str(filename))
    with _lock, _connect(path) as db:
        cur=db.execute('INSERT INTO jobs (created_utc,updated_utc,status,step,request_json) VALUES (?,?,?,?,?)',
            (utc(),utc(),'queued','Waiting for local training worker',json.dumps(payload)))
        jid=cur.lastrowid;db.commit()
    _executor.submit(_execute,jid,payload,path,root)
    return jid

def _execute(jid,request,path,root):
    try:
        _update(jid,status='running',step='Validating and sampling CSV',path=path)
        output=[]
        if request['kind']=='retrain':
            _update(jid,step='Creating a new trained version of existing model',path=path)
            output=[train.retrain_model(int(request['model_id']),request['csv'],root=root,
                      max_rows=int(request['max_rows']),folds=int(request['folds']))]
            dataset_sha=registry.get_model(output[0]['model_id'],root)['dataset_sha256']
        else:
            sampled=data.scan_csv(request['csv'],label=request.get('label'),
                  features=request.get('features'),binary=bool(request.get('binary')),
                  normal=request.get('normal'),max_rows=int(request['max_rows']))
            dataset_sha=sampled['source_sha256']
            for algo in request['algorithms']:
                _update(jid,step='Training and cross-validating '+algo,path=path)
                try:
                    result=train.fit_csv(request['csv'],algorithm=algo,prepared=sampled,
                        normal=request.get('normal'),binary=bool(request.get('binary')),
                        folds=int(request['folds']),test_fraction=float(request['test_fraction']),
                        max_rows=int(request['max_rows']),root=root,
                        notes='Administrator UI training, evaluated before routing')
                    output.append({'algorithm':algo,'status':'saved',**result})
                except Exception as exc:
                    output.append({'algorithm':algo,'status':'failed','error':f'{type(exc).__name__}: {exc}'})
        if not any(x.get('model_id') for x in output):
            raise RuntimeError('All model training attempts failed: '+str(output)[:1500])
        _update(jid,step='Evaluating Prolog facts and selecting shadow routes',path=path)
        try:
            selection=selector.rank(dataset_sha=dataset_sha,root=root,
                                   swipl=request.get('swipl'),persist=True)
        except Exception as exc:
            selection={'error':f'{type(exc).__name__}: {exc}'}
        _update(jid,status='completed',step='Training saved; shadow routes evaluated',
                result={'models':output,'prolog_selection':selection},path=path)
    except Exception as exc:
        _update(jid,status='failed',step='Job failed; see error',
                error=f'{type(exc).__name__}: {exc}',path=path)
