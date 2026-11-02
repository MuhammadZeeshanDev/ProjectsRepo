"""SQLite persistence of ML evaluation, trusted model files, routing and shadow predictions.

Existing SQL Server accounts and gateway events remain untouched. Local ML metadata
is a separate SQLite database; do not mistake it for the SQL Server audit database.
"""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[3] / 'ML_Artifacts' / 'IDS_Engine'


def utc(): return datetime.now(timezone.utc).isoformat()


def connect(root=None):
    folder=Path(root or BASE)
    folder.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(folder/'ids_models.sqlite3', timeout=30)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA busy_timeout=30000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS models (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      created_utc TEXT NOT NULL, parent_id INTEGER, algorithm TEXT NOT NULL,
      dataset_file TEXT, dataset_sha256 TEXT, source_rows INTEGER, sample_rows INTEGER,
      label TEXT NOT NULL, normal_label TEXT, classes_json TEXT NOT NULL,
      features_json TEXT NOT NULL, metrics_json TEXT NOT NULL, folds_json TEXT NOT NULL,
      class_metrics_json TEXT NOT NULL, split_fraction REAL NOT NULL,
      checkpoint TEXT NOT NULL, sha256 TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'evaluated',
      notes TEXT NOT NULL DEFAULT '', FOREIGN KEY(parent_id) REFERENCES models(id)
    );
    CREATE TABLE IF NOT EXISTS routes (
      threat TEXT NOT NULL, model_id INTEGER NOT NULL, engine TEXT NOT NULL,
      selected_utc TEXT NOT NULL, score INTEGER NOT NULL,
      PRIMARY KEY (threat), FOREIGN KEY(model_id) REFERENCES models(id)
    );
    CREATE TABLE IF NOT EXISTS predictions (
      id INTEGER PRIMARY KEY AUTOINCREMENT, time_utc TEXT NOT NULL,
      model_id INTEGER, threat TEXT, prediction TEXT, mode TEXT NOT NULL,
      source TEXT NOT NULL, FOREIGN KEY(model_id) REFERENCES models(id)
    );
    CREATE INDEX IF NOT EXISTS idx_predictions_time ON predictions(time_utc);
    ''')
    db.commit()
    return db


@contextmanager
def session(root=None):
    db=connect(root)
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()

def _blob_hash(data): return hashlib.sha256(data).hexdigest()


def register_model(bundle, metadata, root=None):
    import joblib
    folder=Path(root or BASE)
    folder.mkdir(parents=True,exist_ok=True)
    # Never overwrite a saved checkpoint. Write temp then atomically rename.
    mfolder=folder/'models';mfolder.mkdir(exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=mfolder,suffix='.joblib.tmp')
    os.close(fd)
    try:
        joblib.dump(bundle,tmp,compress=3)
        data=Path(tmp).read_bytes()
        sha=_blob_hash(data)
        relative=f'models/{sha}.joblib'
        target=folder/relative
        if not target.exists(): os.replace(tmp,target)
        with session(folder) as conn:
            result=conn.execute('''INSERT INTO models
              (created_utc,parent_id,algorithm,dataset_file,dataset_sha256,source_rows,sample_rows,label,normal_label,classes_json,features_json,metrics_json,folds_json,class_metrics_json,split_fraction,checkpoint,sha256,status,notes)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (utc(),metadata.get('parent_id'),metadata['algorithm'],metadata.get('dataset_file'),metadata.get('dataset_sha256'),
               metadata.get('source_rows'),metadata.get('sample_rows'),metadata['label'],metadata.get('normal_label'),
               json.dumps(metadata['classes']),json.dumps(metadata['features']),json.dumps(metadata['metrics']),
               json.dumps(metadata['folds']),json.dumps(metadata['class_metrics']),metadata['split_fraction'],
               relative,sha,'evaluated',metadata.get('notes','')))
            conn.commit()
            return result.lastrowid
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def models(root=None):
    with session(root) as db:
        rows=db.execute('SELECT * FROM models ORDER BY id DESC').fetchall()
    out=[]
    for row in rows:
        d=dict(row)
        for k in ('classes_json','features_json','metrics_json','folds_json','class_metrics_json'):
            d[k[:-5]]=json.loads(d.pop(k))
        out.append(d)
    return out


def get_model(model_id,root=None):
    with session(root) as db:
        r=db.execute('SELECT * FROM models WHERE id=?',(int(model_id),)).fetchone()
    if r is None:raise ValueError(f'Model ID {model_id} not found.')
    d=dict(r)
    for k in ('classes_json','features_json','metrics_json','folds_json','class_metrics_json'):
        d[k[:-5]]=json.loads(d.pop(k))
    return d


def load_model(model_id,root=None):
    import joblib
    m=get_model(model_id,root)
    if m['status']=='retired':raise ValueError('Model was retired; cannot execute.')
    folder=Path(root or BASE)
    rel=Path(m['checkpoint'])
    if rel.is_absolute() or '..' in rel.parts:raise ValueError('Invalid model checkpoint path')
    path=(folder/rel).resolve()
    if folder.resolve() not in path.parents:raise ValueError('Checkpoint is outside trusted store')
    if not path.is_file():raise ValueError('Checkpoint missing; restore ML_Artifacts backup.')
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):digest.update(chunk)
    if digest.hexdigest()!=m['sha256']:
        raise ValueError('Checkpoint integrity mismatch! Model will not be deserialized.')
    # joblib pickle: ONLY locally created models and files explicitly imported by
    # trusted administrator. Never offer a public upload-and-execute path.
    bundle=joblib.load(path)
    if not isinstance(bundle,dict) or 'pipeline' not in bundle or 'classes' not in bundle:
        raise ValueError('Unsupported checkpoint bundle')
    return bundle,m


def set_status(model_id,status,root=None):
    if status not in ('evaluated','shadow_approved','retired','unverified_import'):
        raise ValueError('Invalid model status.')
    with session(root) as db:
        r=db.execute('SELECT status FROM models WHERE id=?',(int(model_id),)).fetchone()
        if r is None:raise ValueError('Unknown model')
        db.execute('UPDATE models SET status=? WHERE id=?',(status,int(model_id)))
        if status=='retired':db.execute('DELETE FROM routes WHERE model_id=?',(int(model_id),))
        db.commit()


def save_routes(routes,engine,root=None):
    with session(root) as db:
        db.execute('DELETE FROM routes')
        for threat, info in routes.items():
            db.execute('INSERT INTO routes (threat,model_id,engine,selected_utc,score) VALUES (?,?,?,?,?)',
                       (threat,int(info['model_id']),engine,utc(),int(info['score'])))
        db.commit()


def active_routes(root=None):
    with session(root) as db:
        rows=db.execute('SELECT * FROM routes ORDER BY threat').fetchall()
    return [dict(r) for r in rows]


def record_predictions(items,root=None):
    with session(root) as db:
        db.executemany('INSERT INTO predictions (time_utc,model_id,threat,prediction,mode,source) VALUES (?,?,?,?,?,?)',
                       [(utc(),x['model_id'],x.get('threat'),str(x['prediction']),x['mode'],str(x['source'])[:180]) for x in items])
        db.commit()


def recent_predictions(limit=100,root=None):
    with session(root) as db:
        rows=db.execute('SELECT time_utc,model_id,threat,prediction,mode,source FROM predictions ORDER BY id DESC LIMIT ?',
                        (min(500,max(1,int(limit))),)).fetchall()
    return [dict(r) for r in rows]


def update_validation(model_id, *, dataset_sha, dataset_path, metrics, class_metrics, root=None):
    with session(root) as db:
        row=db.execute('SELECT status FROM models WHERE id=?',(int(model_id),)).fetchone()
        if row is None or row['status']!='unverified_import':
            raise ValueError('Only quarantined imported checkpoints can be validated here.')
        db.execute("UPDATE models SET metrics_json=?,class_metrics_json=?,dataset_file=?,dataset_sha256=?,status='evaluated' WHERE id=?",
           (json.dumps(metrics),json.dumps(class_metrics),str(dataset_path),dataset_sha,int(model_id)))
        db.commit()
