"""Persist local model training evaluations, excluding model objects and raw data."""
import json, sqlite3
from pathlib import Path
from datetime import datetime, timezone
DB = Path(__file__).resolve().parents[2] / 'ML_Artifacts' / 'training_history.sqlite3'
def _db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=15)
    conn.execute('CREATE TABLE IF NOT EXISTS training_runs (id INTEGER PRIMARY KEY AUTOINCREMENT, created_utc TEXT NOT NULL, source_file TEXT, target TEXT, algorithm TEXT, split TEXT, classes_json TEXT, folds_json TEXT, metrics_json TEXT, features_json TEXT, sample_rows INTEGER, target_mode TEXT)')
    conn.commit()
    return conn
def save_run(result, source_file, target):
    with _db() as conn:
        cursor=conn.execute('INSERT INTO training_runs (created_utc,source_file,target,algorithm,split,classes_json,folds_json,metrics_json,features_json,sample_rows,target_mode) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            (datetime.now(timezone.utc).isoformat(), str(source_file), str(target), result['algorithm'], result['split'], json.dumps(result['classes']), json.dumps(result['folds']), json.dumps(result['heldout']), json.dumps(result['features']), int(result['sample_rows']), result.get('target_mode','original_multiclass')))
        conn.commit()
        return cursor.lastrowid
def recent_runs(limit=100):
    with _db() as conn:
        rows=conn.execute('SELECT id,created_utc,source_file,target,algorithm,split,metrics_json,sample_rows,target_mode FROM training_runs ORDER BY id DESC LIMIT ?', (min(max(int(limit),1),500),)).fetchall()
    out=[]
    for r in rows:
        metrics=json.loads(r[6]);out.append(dict(id=r[0],created_utc=r[1],source_file=r[2],target=r[3],algorithm=r[4],split=r[5],accuracy=metrics.get('accuracy'),macro_f1=metrics.get('macro_f1'),sample_rows=r[7],target_mode=r[8]))
    return out
