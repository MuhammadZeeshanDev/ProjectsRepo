"""Read-only, independently identifiable research results. No trained models invented."""
from pathlib import Path
import csv, hashlib, json
ROOT=Path(__file__).resolve().parents[2] / 'Assets' / 'ResearchEvidence'
DATASETS={'v3 historical':'v3','v4 group-aware':'v4'}
FILES={'v3':{'CV folds / Original':'fold_original.csv','CV folds / ROS':'fold_ros.csv','All CV records':'cv_all.csv','Held-out 70/30':'heldout_70_30.csv','Held-out 80/20':'heldout_80_20.csv'},'v4':{'CV records (468)':'cv_468.csv','Configurations (156)':'config_156.csv','Frozen experiment plan':'feature_plan.csv'}}
ALGORITHMS=('Random Forest','XGBoost','LightGBM')
SPLITS=('70_30','80_20')
def get_path(version,table):
    if version not in FILES or table not in FILES[version]:raise ValueError('Unknown evidence selection')
    p=(ROOT/version/FILES[version][table]).resolve()
    if ROOT.resolve() not in p.parents:raise ValueError('Invalid evidence path')
    return p
def load(version,table,limit=10000):
    path=get_path(version,table)
    with path.open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f)
        return [row for i,row in enumerate(r) if i<limit]
def options(records,key):return sorted({str(x.get(key,'')).strip() for x in records if x.get(key) not in (None,'')})
def select(records,model=None,split=None,fold=None,balancing=None,method=None):
    def norm(x):return str(x or '').strip().lower().replace(' ','').replace('-','_')
    result=[]
    for r in records:
        if model and norm(r.get('Model'))!=norm(model):continue
        if split and norm(r.get('Split'))!=norm(split):continue
        if fold and norm(r.get('Fold'))!=norm(fold):continue
        if balancing and norm(r.get('Balancing'))!=norm(balancing):continue
        if method and norm(r.get('Method'))!=norm(method):continue
        result.append(r)
    return result
def file_sha256(version,table):return hashlib.sha256(get_path(version,table).read_bytes()).hexdigest()
def report(rows,metric='Macro_F1'):
    # CSVs contain measured historical records, never new predictions.
    vals=[]
    for row in rows:
        try:vals.append(float(row[metric]))
        except (ValueError,TypeError,KeyError):pass
    return {'n':len(vals),'average':sum(vals)/len(vals) if vals else None,'min':min(vals) if vals else None,'max':max(vals) if vals else None}
