"""Administrator-controlled locally trained model catalog and bounded CSV inference.

Only checkpoints produced by the local training workflow are eligible for
this evaluator. External pickle/joblib imports remain untrusted and unexecuted.
The catalog is NOT a production deployment switch: no live packet features
are emitted by the current HTTP gateway.
"""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
ROOT = BASE / 'ML_Artifacts'
DB = ROOT / 'validated_models.sqlite3'


def _now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _connect():
    ROOT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA busy_timeout=20000')
    con.execute('''CREATE TABLE IF NOT EXISTS trained_models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_utc TEXT NOT NULL,
        run_id INTEGER,
        algorithm TEXT NOT NULL,
        source_name TEXT NOT NULL,
        target TEXT NOT NULL,
        split TEXT NOT NULL,
        fold_count INTEGER NOT NULL,
        features_json TEXT NOT NULL,
        classes_json TEXT NOT NULL,
        metrics_json TEXT NOT NULL,
        folds_json TEXT NOT NULL,
        target_mode TEXT NOT NULL,
        dataset_variant TEXT NOT NULL DEFAULT 'Original',
        feature_protocol TEXT NOT NULL DEFAULT 'Manual',
        sample_meta_json TEXT NOT NULL DEFAULT '{}',
        sample_sha256 TEXT NOT NULL DEFAULT '',
        file_name TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        bytes INTEGER NOT NULL,
        state TEXT NOT NULL DEFAULT 'stored',
        review_note TEXT NOT NULL DEFAULT '',
        reviewed_utc TEXT
    )''')
    con.execute('''CREATE TABLE IF NOT EXISTS model_evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, model_id INTEGER NOT NULL,
        created_utc TEXT NOT NULL, source_file TEXT NOT NULL,
        rows INTEGER NOT NULL, labeled_rows INTEGER NOT NULL,
        prediction_counts_json TEXT NOT NULL,
        metrics_json TEXT, output_path TEXT NOT NULL
    )''')
    con.commit()
    return con


def _one(model_id):
    with _connect() as c:
        row = c.execute('SELECT * FROM trained_models WHERE id=?', (int(model_id),)).fetchone()
    if not row:
        raise ValueError('Trained model not found in the local catalog')
    return dict(row)


def list_models(limit=100):
    with _connect() as c:
        rows = c.execute('''SELECT id,created_utc,run_id,algorithm,source_name,target,split,
                fold_count,metrics_json,target_mode,dataset_variant,feature_protocol,sample_meta_json,state,review_note,sha256 FROM trained_models
                ORDER BY id DESC LIMIT ?''', (min(max(int(limit),1),500),)).fetchall()
    out=[]
    for r in rows:
        item=dict(r)
        item['metrics']=json.loads(item.pop('metrics_json'))
        item.pop('sample_meta_json',None)
        out.append(item)
    return out


def save_trained(result, *, source_name, target, run_id=None):
    """Persist trained pipeline, full preprocessing, original class encoder, run evidence.

    A checkpoint is always stored as `stored`, never silently activated.
    """
    import joblib
    algo = str(result['algorithm'])
    if algo not in ('Random Forest','XGBoost','LightGBM'):
        raise ValueError('Unexpected algorithm')
    if not hasattr(result['pipeline'],'predict') or not hasattr(result['label_encoder'],'inverse_transform'):
        raise ValueError('Fitted pipeline and label encoder required')
    features = result['features']
    if not (1 <= len(features) <= 30) or len(set(features))!=len(features):
        raise ValueError('Invalid feature schema')
    bundle={'format':'QuantumSafeLocallyTrained-v1',
            'model':result['pipeline'], 'label_encoder':result['label_encoder'],
            'features':list(features), 'algorithm':algo,
            'classes':list(map(str,result['classes'])),
            'split':result['split'], 'folds':result['folds'],
            'metrics':result['heldout'], 'target':str(target),
            'target_mode':result.get('target_mode','original_multiclass'),
            'dataset_variant':result.get('dataset_variant','Original'),
            'feature_protocol':result.get('feature_protocol','Manual'),
            'sample_sha256':result.get('data_sha256','')}
    location = ROOT/'trained_checkpoints'
    location.mkdir(parents=True,exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='qs-model-',suffix='.joblib.tmp',dir=location)
    os.close(fd)
    try:
        joblib.dump(bundle, tmp)
        size = Path(tmp).stat().st_size
        if not 0 < size <= 250*1024*1024:
            raise ValueError('Trained checkpoint size must be 1–250 MiB')
        with open(tmp,'rb') as stream:
            digest = hashlib.file_digest(stream,'sha256').hexdigest() if hasattr(hashlib,'file_digest') else hashlib.sha256(stream.read()).hexdigest()
        name=digest+'.joblib'
        final=location/name
        if not final.exists(): os.replace(tmp,final)
        with _connect() as c:
            cur=c.execute('''INSERT INTO trained_models
             (created_utc,run_id,algorithm,source_name,target,split,fold_count,features_json,
              classes_json,metrics_json,folds_json,target_mode,dataset_variant,feature_protocol,sample_meta_json,sample_sha256,file_name,sha256,bytes,state)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (_now(),run_id,algo,Path(source_name).name,str(target),result['split'],len(result['folds']),
               json.dumps(features),json.dumps(bundle['classes']),json.dumps(result['heldout']),
               json.dumps(result['folds']),bundle['target_mode'],bundle['dataset_variant'],bundle['feature_protocol'],
               json.dumps(result.get('source_sample') or {}),bundle['sample_sha256'],name,digest,size,'stored'))
            c.commit()
            return cur.lastrowid
    finally:
        Path(tmp).unlink(missing_ok=True)


def inspect_model(model_id):
    row=_one(model_id)
    row['features']=json.loads(row.pop('features_json'))
    row['classes']=json.loads(row.pop('classes_json'))
    row['metrics']=json.loads(row.pop('metrics_json'))
    row['folds']=json.loads(row.pop('folds_json'))
    row['source_sample']=json.loads(row.pop('sample_meta_json'))
    return row


def _trusted_bundle(row):
    """Never load imported artifacts. Verify catalog record and checksum FIRST."""
    import joblib
    filename = row['file_name']
    if filename != row['sha256']+'.joblib' or '/' in filename or '\\' in filename:
        raise ValueError('Checkpoint filename is invalid')
    p=ROOT/'trained_checkpoints'/filename
    if not p.is_file():
        raise ValueError('Checkpoint file missing')
    with p.open('rb') as f:
        digest = hashlib.file_digest(f,'sha256').hexdigest() if hasattr(hashlib,'file_digest') else hashlib.sha256(f.read()).hexdigest()
    if digest!=row['sha256']:
        raise ValueError('Checkpoint checksum mismatch; refused to load')
    # joblib deserialization is only suitable for trusted, host-local artifacts.
    bundle=joblib.load(p)
    if not isinstance(bundle,dict) or bundle.get('format')!='QuantumSafeLocallyTrained-v1':
        raise ValueError('Unexpected checkpoint format')
    if bundle.get('features')!=json.loads(row['features_json']):
        raise ValueError('Checkpoint feature schema differs from registry')
    if list(map(str,bundle.get('classes',[])))!=json.loads(row['classes_json']):
        raise ValueError('Checkpoint label mapping differs from registry')
    if bundle.get('algorithm')!=row['algorithm']:
        raise ValueError('Checkpoint algorithm differs from registry')
    if bundle.get('dataset_variant')!=row['dataset_variant'] or bundle.get('feature_protocol')!=row['feature_protocol']:
        raise ValueError('Checkpoint experiment metadata differs from registry')
    return bundle


def mark_candidate(model_id, note, *, approved=False):
    """Document Administrator offline approval only. NOT live activation."""
    row=_one(model_id)
    if row['state']=='retired':
        raise ValueError('Retired model cannot be approved')
    if approved:
        metrics=json.loads(row['metrics_json'])
        if metrics.get('accuracy') is None or metrics.get('macro_f1') is None:
            raise ValueError('Missing holdout evidence')
        _trusted_bundle(row)
    state='reviewed_candidate' if approved else 'stored'
    with _connect() as c:
        c.execute('UPDATE trained_models SET state=?,review_note=?,reviewed_utc=? WHERE id=?',
                  (state,str(note)[:500],_now(),model_id))
        c.commit()
    return state


def retire_model(model_id, reason=''):
    _one(model_id)
    with _connect() as c:
        c.execute('UPDATE trained_models SET state=?,review_note=?,reviewed_utc=? WHERE id=?',
                  ('retired',str(reason)[:500],_now(),int(model_id)))
        c.commit()


def evaluate_csv(model_id, csv_path, *, chunk_size=5000, preview_rows=30, progress=None):
    """Bounded-memory local CSV test with new model, no auto-enforcement.

    Strict schema, no silent invented feature defaults. Scikit-learn pipeline
    persists imputation behavior learned from training records.
    """
    import numpy as np
    import pandas as pd
    from sklearn.metrics import confusion_matrix
    from .large_csv import checked_csv, headers
    row=_one(model_id)
    if row['state']=='retired': raise ValueError('Retired checkpoint cannot be evaluated')
    path=checked_csv(csv_path)
    bundle=_trusted_bundle(row)
    columns=headers(path)
    features=bundle['features']
    missing=[f for f in features if f not in columns]
    if missing: raise ValueError('CSV missing required features: '+', '.join(missing))
    target=bundle.get('target')
    labeled = bool(target in columns)
    classes=list(bundle['classes'])
    confusion=np.zeros((len(classes),len(classes)),dtype=np.int64)
    totals={c:0 for c in classes}
    total=0; label_count=0; preview=[]
    # This mapping must match training's explicit binary-normal mapping.
    normal_names={'normal','benign','0','non-attack','non_attack','legitimate'}
    output_dir=ROOT/'predictions';output_dir.mkdir(parents=True,exist_ok=True)
    handle,tmp=tempfile.mkstemp(prefix=f'prediction_{model_id}_',suffix='.csv',dir=output_dir)
    os.close(handle)
    successful=False
    try:
        for chunk in pd.read_csv(path,chunksize=int(chunk_size),low_memory=False):
            if chunk.empty: continue
            x=chunk[features].copy()
            preprocess = bundle['model'].named_steps['preprocessing']
            numeric_features = []
            categorical_features = []
            for name, _, feature_names in preprocess.transformers_:
                if name == 'numeric': numeric_features.extend(feature_names)
                if name == 'categories': categorical_features.extend(feature_names)
            for col in numeric_features:
                original=x[col]
                casted=pd.to_numeric(original,errors='coerce')
                if (original.notna() & casted.isna()).any():
                    raise ValueError(f'CSV contains nonnumeric values in trained numeric feature {col}')
                x[col]=casted
            for col in categorical_features:
                # Match the same categorical missing-value preparation as training.
                x[col]=x[col].astype('string').fillna('missing').astype(str)
            labels=bundle['model'].predict(x)
            labels=np.asarray(labels,dtype=int)
            predicted=bundle['label_encoder'].inverse_transform(labels).astype(str)
            if len(preview)<preview_rows:
                preview.extend([{'row':total+i+1, 'prediction':str(p)} for i,p in enumerate(predicted[:preview_rows-len(preview)])])
            for c,n in zip(*np.unique(predicted,return_counts=True)):
                totals[str(c)]=totals.get(str(c),0)+int(n)
            with open(tmp,'a',encoding='utf-8',newline='') as out:
                pd.DataFrame({'QuantumSafe_Prediction':predicted}).to_csv(out,index=False,header=(total==0))
            if labeled:
                truth=chunk[target].astype('string').str.strip()
                if bundle['target_mode']=='binary_normal_vs_attack':
                    # Raw normal class was not persisted in v1.5; only pre-mapped samples.
                    # Do not fabricate truth labels when source uses original multiclass.
                    if not set(truth.dropna().astype(str)).issubset(set(classes)):
                        raise ValueError('Binary model: test CSV must have normal/attack labels already mapped; original multiclass labels are not auto-mapped.')
                valid=truth.notna() & truth.astype(str).isin(classes)
                if valid.any():
                    truth_codes=bundle['label_encoder'].transform(truth[valid].astype(str))
                    confusion+=confusion_matrix(truth_codes,labels[valid.to_numpy()],labels=range(len(classes)))
                    label_count+=int(valid.sum())
            total+=len(chunk)
            if progress:progress(total)
        if not total:raise ValueError('CSV has zero records')
        success_path=output_dir/f'predictions_model_{model_id}_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")}.csv'
        os.replace(tmp,success_path)
        successful=True
        metrics={}
        if label_count:
            metrics={'evaluated_labeled_rows':label_count,'accuracy':round(float(np.trace(confusion)/label_count),6),
                     'macro_f1':None,
                     'confusion_matrix':confusion.tolist()}
            # Macro F1 computed from accumulated confusion matrix without storing labels.
            f1s=[]
            for i in range(len(classes)):
                tp=confusion[i,i]; fp=confusion[:,i].sum()-tp;fn=confusion[i,:].sum()-tp
                f1s.append(float(2*tp/(2*tp+fp+fn)) if 2*tp+fp+fn else 0.0)
            metrics['macro_f1']=round(sum(f1s)/len(f1s),6)
            if len(classes)==2:
                normals=[i for i,c in enumerate(classes) if str(c).casefold() in normal_names]
                if len(normals)==1:
                    ni=normals[0]; denominator=confusion[ni].sum()
                    metrics['false_positive_rate']=round(float(confusion[ni,1-ni]/denominator),6) if denominator else None
        outcome={'model_id':model_id,'rows':total,'prediction_counts':totals,'labeled_rows':label_count,
                 'metrics':metrics or None, 'preview':preview,'output_path':str(success_path)}
        with _connect() as c:
            c.execute('INSERT INTO model_evaluations (model_id,created_utc,source_file,rows,labeled_rows,prediction_counts_json,metrics_json,output_path) VALUES (?,?,?,?,?,?,?,?)',
                      (model_id,_now(),path.name,total,label_count,json.dumps(totals),json.dumps(outcome['metrics']),str(success_path)))
            c.commit()
        return outcome
    finally:
        if not successful:Path(tmp).unlink(missing_ok=True)


def recent_evaluations(limit=100):
    with _connect() as c:
        rows = c.execute("""SELECT id, model_id,created_utc,source_file,rows,labeled_rows,
                            metrics_json,output_path FROM model_evaluations ORDER BY id DESC LIMIT ?""",
                         (min(max(int(limit),1),500),)).fetchall()
    results=[]
    for row in rows:
        x=dict(row)
        x['metrics']=json.loads(x.pop('metrics_json') or 'null')
        results.append(x)
    return results
