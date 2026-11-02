"""Administrator-verified import of a QuantumSafe-compatible model bundle.

CAUTION: joblib is pickle. Never deserialize Internet downloads or untrusted files.
An imported checkpoint starts in quarantine; it cannot be Prolog-routed until
validated against a separately supplied labeled CSV.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from . import registry, train, data

IMPORTS=registry.BASE/'Trusted_Imports'

def import_trusted(path, *, trust=False, root=None):
    if not trust:raise PermissionError('Administrator must acknowledge trusted pickle deserialization')
    import joblib
    folder=Path(root or registry.BASE)/'Trusted_Imports'
    p=Path(path).resolve(strict=True)
    if p.parent!=folder.resolve() or p.suffix.lower()!='.joblib':
        raise ValueError('Import only .joblib files copied to ML_Artifacts/IDS_Engine/Trusted_Imports')
    if not p.is_file():raise ValueError('Checkpoint file not found')
    # This line can execute arbitrary pickle code. File must be supplied and explicitly
    # trusted by local Administrator, never by operator or remote unauthenticated user.
    bundle=joblib.load(p)
    if not isinstance(bundle,dict) or not all(k in bundle for k in ('pipeline','classes','schema','normal_label','label')):
        raise ValueError('Unsupported model: export compatible QuantumSafe bundle with pipeline/classes/schema/normal_label/label.')
    schema=bundle['schema']; classes=list(map(str,bundle['classes']))
    if not hasattr(bundle['pipeline'],'predict') or not isinstance(schema,dict):raise ValueError('Missing predict() or feature schema')
    if not isinstance(schema.get('features'),list) or not schema['features'] or len(schema['features'])>100:
        raise ValueError('Import must include 1–100 feature names')
    if not isinstance(schema.get('numeric'),list) or not isinstance(schema.get('categorical'),list):
        raise ValueError('Schema must have numeric and categorical feature lists')
    if sorted(set(schema['numeric']+schema['categorical']))!=sorted(set(schema['features'])):
        raise ValueError('Features must exactly match numeric + categorical schema')
    if len(classes)<2 or len(classes)>40 or len(set(classes))!=len(classes):
        raise ValueError('Model must have 2–40 unique target classes')
    if str(bundle['normal_label']) not in classes:raise ValueError('Normal class not present in model class labels')
    meta={'algorithm':str(bundle.get('algorithm','Imported Pipeline'))[:80],
          'dataset_file':'IMPORTED_UNVERIFIED:'+p.name,
          'dataset_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
          'source_rows':0,'sample_rows':0,
          'label':str(bundle['label'])[:80],'normal_label':str(bundle['normal_label']),
          'classes':classes,'features':schema['features'],
          'metrics':{'notice':'Not validated! Must evaluate on independent labeled CSV before Prolog selection'},
          'folds':[],'class_metrics':{},'split_fraction':0.2,
          'notes':json.dumps({'trusted_import':p.name,'validation_required':True})}
    mid=registry.register_model(bundle,meta,root)
    registry.set_status(mid,'unverified_import',root)
    return {'model_id':mid,'status':'unverified_import','algorithm':meta['algorithm'],
            'features':meta['features'],'notice':'Cannot automatically route until labeled CSV validation.'}


def validate_import(model_id,csv_path,*,max_rows=100000,root=None):
    """Evaluate quarantined model on independent labeled data; never refit here."""
    from sklearn.metrics import confusion_matrix
    record=registry.get_model(model_id,root)
    if record['status']!='unverified_import':raise ValueError('Only unverified imported model can be validated')
    path,cols=data.inspect_headers(csv_path)
    bundle,_=registry.load_model(model_id,root)
    expected=bundle['schema']['features']; label=bundle['label'];classes=list(map(str,bundle['classes']))
    missing=set(expected+[label])-set(cols)
    if missing:raise ValueError('Independent validation CSV missing: '+', '.join(sorted(missing)))
    if not 200<=max_rows<=500000:raise ValueError('Validation rows 200–500000')
    acc=np.zeros((len(classes),len(classes)),dtype=np.int64)
    class_to_id={x:i for i,x in enumerate(classes)}
    total=0
    for chunk in pd.read_csv(path,usecols=list(dict.fromkeys([*expected,label])),chunksize=5000):
        # Independent validation: use prefix bounded by max_rows; no training.
        if total>=max_rows:break
        chunk=chunk.iloc[:max_rows-total]
        inputs=train.to_schema(chunk,bundle['schema'])
        preds=bundle['pipeline'].predict(inputs)
        pred_labels=[]
        for v in preds:
            if isinstance(v,(int,np.integer)) and 0<=int(v)<len(classes):pred_labels.append(classes[int(v)])
            else:pred_labels.append(str(v))
        real=chunk[label].astype(str).str.strip().tolist()
        if any(x not in class_to_id for x in real):raise ValueError('Validation CSV contains a class not in the imported checkpoint.')
        if any(x not in class_to_id for x in pred_labels):raise ValueError('Checkpoint produced an unexpected class value.')
        acc+=confusion_matrix([class_to_id[x] for x in real],
                              [class_to_id[x] for x in pred_labels],labels=list(range(len(classes))))
        total+=len(real)
    if total<200:raise ValueError('At least 200 labeled validation rows required.')
    from sklearn.metrics import accuracy_score
    correct=int(np.trace(acc)); overall=float(correct/total)
    normal=str(bundle['normal_label']);normal_ix=class_to_id[normal];benign=int(acc[normal_ix,:].sum())
    metrics={'accuracy':round(overall,6),'test_rows':total,'sample_rows':total,
             'macro_f1':0.0,'latency_ms_per_row':None,
             'notice':'Imported model independently evaluated; no 3-fold CV or training provenance asserted.'}
    class_metrics={};f_scores=[]
    for i,name in enumerate(classes):
        tp=int(acc[i,i]);support=int(acc[i,:].sum());positive=int(acc[:,i].sum());
        precision=tp/positive if positive else 0.0
        recall=tp/support if support else 0.0
        f1=2*precision*recall/(precision+recall) if (precision+recall)>0 else 0.0
        fp=(int(acc[normal_ix,i])/benign if benign and i!=normal_ix else None)
        class_metrics[name]={'precision':round(precision,6),'recall':round(recall,6),'f1':round(f1,6),
                             'support':support,'false_positive_rate':round(fp,6) if fp is not None else None}
        f_scores.append(f1)
    metrics['macro_f1']=round(sum(f_scores)/len(f_scores),6)
    metrics['confusion_matrix']=acc.tolist()
    # Imported model latency is not measured yet: deliberately ineligible for Prolog routing.
    registry.update_validation(model_id,dataset_sha=data._hash(path),dataset_path=path,
                               metrics=metrics,class_metrics=class_metrics,root=root)
    return {'model_id':model_id,'total_rows':total,'metrics':metrics,'classes':class_metrics,
            'routing':'NOT ELIGIBLE UNTIL INDEPENDENT TIMING + PROVENANCE REVIEW'}


def detect_algorithm_template(path, *, trust=False, root=None):
    """Recognize a previously trained RF/XGB/LGBM estimator for CLEAN retraining.

    Does not imply incremental weight reuse or deploy unvalidated pickles.
    """
    if not trust:raise PermissionError('Trusted Administrator import confirmation required')
    import joblib
    folder=Path(root or registry.BASE)/'Trusted_Imports'
    p=Path(path).resolve(strict=True)
    if p.parent!=folder.resolve() or p.suffix.lower()!='.joblib':raise ValueError('Use trusted import folder and .joblib format')
    item=joblib.load(p)  # WARNING: pickle: only explicitly trusted admin file
    if isinstance(item,dict):item=item.get('pipeline',item.get('model'))
    from sklearn.pipeline import Pipeline
    if isinstance(item,Pipeline):item=item.steps[-1][1]
    name=type(item).__name__
    mapping={'RandomForestClassifier':'Random Forest','XGBClassifier':'XGBoost','LGBMClassifier':'LightGBM'}
    algorithm=mapping.get(name)
    if algorithm is None:
        raise ValueError(f'Estimator {name} is not a supported RF/XGBoost/LightGBM template. Use a compatible QuantumSafe bundle.')
    if algorithm not in train.estimator_names():
        raise ValueError(f'{algorithm} package not installed on this host')
    return {'algorithm':algorithm,'file':p.name,
            'strategy':'clean_refit_on_new_CSV; original checkpoint weights are NOT incrementally updated'}
