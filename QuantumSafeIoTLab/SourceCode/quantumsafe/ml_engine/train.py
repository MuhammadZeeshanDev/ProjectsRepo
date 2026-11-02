"""Validated supervised training of arbitrary labelled IoT CSVs, backend only."""
from __future__ import annotations
import importlib
import time
import numpy as np
import pandas as pd
from . import data, registry


def estimator_names():
    names=['Random Forest']
    try:import xgboost; names.append('XGBoost')
    except ImportError:pass
    try:import lightgbm; names.append('LightGBM')
    except ImportError:pass
    try:
        from quantumsafe.ml_engine.custom_estimators import CUSTOM_ESTIMATORS
        if isinstance(CUSTOM_ESTIMATORS,dict): names += sorted(CUSTOM_ESTIMATORS)
    except ImportError:pass
    return names


def get_estimator(name,seed=42):
    if name=='Random Forest':
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(n_estimators=100,max_depth=20,n_jobs=-1,random_state=seed,
                                      class_weight='balanced_subsample')
    if name=='XGBoost':
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=100,max_depth=5,learning_rate=.08,
                             n_jobs=2,random_state=seed,eval_metric='mlogloss')
    if name=='LightGBM':
        from lightgbm import LGBMClassifier
        return LGBMClassifier(n_estimators=100,max_depth=-1,num_leaves=31,
                              learning_rate=.07,n_jobs=2,random_state=seed,verbosity=-1)
    from quantumsafe.ml_engine.custom_estimators import CUSTOM_ESTIMATORS
    if name not in CUSTOM_ESTIMATORS:raise ValueError('Unknown algorithm. Run `list-algorithms`.')
    estimator=CUSTOM_ESTIMATORS[name](seed)
    if not all(hasattr(estimator,method) for method in ('fit','predict','get_params')):
        raise ValueError('Custom estimator needs fit(), predict(), get_params().')
    return estimator


def choose_schema(df, features, *, drop_high_cardinality=True):
    """Fit schema once on training data; drop high cardinality default ID leaks."""
    numerics=[];categories=[]; dropped=[]
    for feat in features:
        col=df[feat]
        numeric=pd.to_numeric(col,errors='coerce')
        frac=float(numeric.notna().sum())/max(1,int(col.notna().sum()))
        if frac>=.96:
            numerics.append(feat)
        elif col.nunique(dropna=True) <= 100:
            categories.append(feat)
        elif drop_high_cardinality:
            dropped.append(feat)
        else:
            raise ValueError(f'High-cardinality categorical column {feat} ({col.nunique()} unique). Exclude it.')
    if not numerics and not categories:
        raise ValueError('No usable features after numeric/categorical screening.')
    return {'numeric':numerics,'categorical':categories,'excluded_high_cardinality':dropped,
            'features':numerics+categories}


def to_schema(df,schema):
    out=pd.DataFrame(index=df.index)
    for col in schema['numeric']:
        out[col]=pd.to_numeric(df[col],errors='coerce').replace([np.inf,-np.inf],np.nan)
    for col in schema['categorical']:
        out[col]=df[col].astype('string').fillna('__missing__').astype(str)
    return out


def build_pipeline(name,schema,seed,estimator_override=None):
    from sklearn.pipeline import Pipeline
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import OneHotEncoder
    pre=[]
    if schema['numeric']:
        pre.append(('numbers',SimpleImputer(strategy='median',add_indicator=False),schema['numeric']))
    if schema['categorical']:
        pre.append(('categories',OneHotEncoder(handle_unknown='ignore',max_categories=40,
                                               sparse_output=False),schema['categorical']))
    return Pipeline([('preprocess',ColumnTransformer(pre,sparse_threshold=0)),
                     ('classifier',estimator_override if estimator_override is not None else get_estimator(name,seed))])


def metrics(y_true,y_pred,classes,normal):
    from sklearn.metrics import accuracy_score, f1_score, balanced_accuracy_score, confusion_matrix, precision_recall_fscore_support
    n=len(classes)
    cm=confusion_matrix(y_true,y_pred,labels=list(range(n)))
    precision,recall,f1,support=precision_recall_fscore_support(y_true,y_pred,labels=list(range(n)),zero_division=0)
    normal_id=classes.index(normal) if normal in classes else None
    benign=int(cm[normal_id].sum()) if normal_id is not None else 0
    out={}
    for i,name in enumerate(classes):
        if normal_id is not None and i!=normal_id:
            fpr = float(cm[normal_id,i]/benign) if benign else None
        else:
            tn_like=int(cm.sum()-cm[i].sum())
            fp_like=int(cm[:,i].sum()-cm[i,i])
            fpr = float(fp_like/tn_like) if tn_like else None
        out[name]={'precision':round(float(precision[i]),6),'recall':round(float(recall[i]),6),
                   'f1':round(float(f1[i]),6),'support':int(support[i]),
                   'false_positive_rate':round(fpr,6) if fpr is not None else None}
    return {'accuracy':round(float(accuracy_score(y_true,y_pred)),6),
            'macro_f1':round(float(f1_score(y_true,y_pred,average='macro',zero_division=0)),6),
            'balanced_accuracy':round(float(balanced_accuracy_score(y_true,y_pred)),6),
            'confusion_matrix':cm.tolist()},out


def fit_csv(path, *, algorithm='Random Forest', label=None, features=None, normal=None,
            binary=False, max_rows=30000, folds=3, test_fraction=.3,
            seed=42, root=None, parent_id=None, notes='', prepared=None):
    from sklearn.model_selection import train_test_split,StratifiedKFold
    from sklearn.preprocessing import LabelEncoder
    if algorithm not in estimator_names(): raise ValueError(f'Algorithm unavailable: {algorithm}; available {estimator_names()}')
    if folds not in (3,5) or not (.15 <= test_fraction <= .35):
        raise ValueError('Choose 3/5 folds, test fraction between 0.15 and 0.35.')
    sample=prepared if prepared is not None else data.scan_csv(path,label=label,features=features,normal=normal,
                         binary=binary,max_rows=max_rows,seed=seed)
    frame=sample['frame']; target=sample['target']
    names=frame[target].astype(str)
    le=LabelEncoder(); y=le.fit_transform(names); classes=[str(c) for c in le.classes_]
    nclasses=len(classes)
    if nclasses>40:
        raise ValueError(f'{nclasses} classes makes reliable supervised IDS training impractical. Use --binary with verified normal label or reduce target taxonomy.')
    # Check normal-class mapping BEFORE any CV/model fitting so bad labels
    # fail quickly instead of wasting minutes on an invalid experiment.
    requested_normal=normal
    if binary:
        normal='normal'
    elif normal is not None:
        lookup={x.casefold():x for x in classes}
        normal=lookup.get(str(normal).strip().casefold())
        if normal is None:raise ValueError(f'Normal label {requested_normal!r} not present; observed classes: {classes[:15]}')
    else:
        lookup={x.casefold():x for x in classes}
        normal=next((lookup[x] for x in ('normal','benign','0','non-attack','non_attack') if x in lookup),None)
        if normal is None:raise ValueError('Normal class unclear; select exact normal-label value in UI.')
    counts=np.bincount(y,minlength=nclasses)
    if np.min(counts)<max(folds+3,8):
        raise ValueError(f'Each target class requires at least {max(folds+3,8)} sampled rows; smallest {int(counts.min())}. Increase --max-rows or use --binary.')
    X=frame[sample['features']].copy()
    x_train,x_test,y_train,y_test=train_test_split(X,y,test_size=test_fraction,
                                                  stratify=y,random_state=seed)
    if np.bincount(y_train,minlength=nclasses).min()<folds:
        raise ValueError('Insufficient training samples for stratified folds after holdout.')
    schema=choose_schema(x_train,sample['features'])
    train_X=to_schema(x_train,schema);test_X=to_schema(x_test,schema)
    cv=StratifiedKFold(n_splits=folds,shuffle=True,random_state=seed)
    fold_results=[]
    for k,(tr,va) in enumerate(cv.split(train_X,y_train),start=1):
        classifier=build_pipeline(algorithm,schema,seed)
        classifier.fit(train_X.iloc[tr],y_train[tr])
        pred=classifier.predict(train_X.iloc[va])
        from sklearn.metrics import f1_score,accuracy_score
        fold_results.append({'fold':k,'rows_train':len(tr),'rows_validation':len(va),
                             'macro_f1':round(float(f1_score(y_train[va],pred,average='macro',zero_division=0)),6),
                             'accuracy':round(float(accuracy_score(y_train[va],pred)),6)})
    final=build_pipeline(algorithm,schema,seed)
    start=time.perf_counter()
    final.fit(train_X,y_train)
    test_pred=final.predict(test_X)
    elapsed=time.perf_counter()-start
    start=time.perf_counter()
    _=final.predict(test_X.iloc[:min(len(test_X),500)])
    latency_ms=1000*(time.perf_counter()-start)/max(1,min(len(test_X),500))
    summary,classes_metrics=metrics(y_test,test_pred,classes,normal)
    summary.update({'latency_ms_per_row':round(float(latency_ms),6),'fit_seconds':round(float(elapsed),4),
                    'test_rows':len(y_test),'train_rows':len(y_train),'dataset_rows_seen':sample['rows_seen'],
                    'sample_rows':sample['sampled_rows'],'source_class_counts':sample['source_class_counts'],
                    'sample_class_counts':sample['sample_class_counts'],
                    'notice':'Evaluation uses sampled records; independent device/temporal holdout is NOT proven.'})
    bundle={'pipeline':final,'classes':classes,'schema':schema,'label':target,'normal_label':normal,
            'algorithm':algorithm,'version':2,'seed':seed}
    metadata={'algorithm':algorithm,'parent_id':parent_id,
              'dataset_file':sample['source_path'],'dataset_sha256':sample['source_sha256'],
              'source_rows':sample['rows_seen'],'sample_rows':sample['sampled_rows'],
              'label':target,'normal_label':normal,'classes':classes,'features':schema['features'],
              'metrics':summary,'folds':fold_results,'class_metrics':classes_metrics,
              'split_fraction':test_fraction,'notes':__import__('json').dumps({'comments':notes,'binary':binary,'source_normal':requested_normal})}
    mid=registry.register_model(bundle,metadata,root)
    return {'model_id':mid,'algorithm':algorithm,'features':schema['features'],
            'excluded_columns':schema['excluded_high_cardinality'],
            'classes':classes,'normal_class':normal,
            'heldout':summary,'per_class':classes_metrics,'folds':fold_results}


def retrain_model(model_id,path,*,root=None,max_rows=30000,folds=3):
    """Safe clean refit from a new CSV with the same feature schema/algorithm.

    RF/XGB/LGBM don't support unbiased online partial_fit. This creates a NEW,
    immutable version; old checkpoint is preserved for rollback.
    """
    old=registry.get_model(model_id,root)
    if old['status']=='retired':raise ValueError('Cannot retrain a retired model.')
    import json
    try: state=json.loads(old['notes'])
    except (TypeError,ValueError):state={}
    as_binary=bool(state.get('binary'))
    source_normal=state.get('source_normal') if as_binary else old['normal_label']
    return fit_csv(path,algorithm=old['algorithm'],label=old['label'],features=old['features'],
                   normal=source_normal,binary=as_binary,max_rows=max_rows,folds=folds,
                   test_fraction=old['split_fraction'],root=root,parent_id=int(model_id),
                   notes=f'Clean retrain of model {model_id}, not incremental partial_fit.')
