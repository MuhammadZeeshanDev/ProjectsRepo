"""Bounded, explicit, local supervised training; never labels HTTP events as TCP/MQTT samples."""
import io, json, hashlib
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

def algorithms():
    out=['Random Forest']
    try: import xgboost; out.append('XGBoost')
    except ImportError: pass
    try: import lightgbm; out.append('LightGBM')
    except ImportError: pass
    return out

def run_experiment(raw, label, features, algo, split, folds, seed=42, max_rows=20000):
    from sklearn.model_selection import train_test_split, StratifiedKFold
    from sklearn.pipeline import Pipeline
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import OneHotEncoder, LabelEncoder
    from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
    from sklearn.ensemble import RandomForestClassifier
    if not raw or len(raw)>60*1024*1024:raise ValueError('CSV required; max 60 MB')
    if split not in (0.2,0.3):raise ValueError('Only 80/20 or 70/30 split is supported')
    if folds not in (3,5):raise ValueError('Choose 3 or 5 folds')
    df=pd.read_csv(io.BytesIO(raw),nrows=max_rows+1,low_memory=False)
    truncated=len(df)>max_rows
    df=df.iloc[:max_rows].copy()
    if label not in df or not features or label in features:raise ValueError('Valid label and non-label features required')
    if len(features)>30 or any(f not in df for f in features):raise ValueError('Max 30 available features allowed')
    df=df.dropna(subset=[label]); classes=df[label].astype(str)
    nclasses = classes.nunique()
    if nclasses < 2: raise ValueError('Only one target class found. Select an attack-label column with both normal and attack samples.')
    if nclasses > 100: raise ValueError(f'Target has {nclasses} distinct values (max 100). You probably selected an ID, timestamp or continuous column instead of an attack label. Select a class label or use binary normal-vs-attack mapping.')
    X=df[features].copy()
    for f in X.columns:
        if X[f].dtype=='object': X[f]=X[f].astype('string').fillna('missing').astype(str)
    encoder=LabelEncoder();y=encoder.fit_transform(classes)
    counts=np.bincount(y)
    if counts.min()<folds+2:raise ValueError(f'At least {folds+2} records required for EACH class (smallest has {counts.min()}). Try fewer folds or binary labels.')
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=split,random_state=seed,stratify=y)
    if np.bincount(y_train,minlength=len(counts)).min()<folds:raise ValueError('Too few training examples per class for selected folds')
    numerical=list(X.select_dtypes(include=['number','bool']).columns)
    categorical=[c for c in features if c not in numerical]
    # Low-cardinality guard reduces accidental memory exhaustion.
    if any(X_train[c].nunique()>100 for c in categorical):raise ValueError('Categorical feature has >100 unique values; encode or select another column')
    def new_model():
        if algo=='Random Forest':return RandomForestClassifier(n_estimators=80,max_depth=18,n_jobs=1,random_state=seed,class_weight='balanced')
        if algo=='XGBoost':
            from xgboost import XGBClassifier
            return XGBClassifier(n_estimators=80,max_depth=5,n_jobs=1,random_state=seed,eval_metric='logloss')
        if algo=='LightGBM':
            from lightgbm import LGBMClassifier
            return LGBMClassifier(n_estimators=80,max_depth=6,n_jobs=1,random_state=seed,verbosity=-1)
        raise ValueError('Algorithm unavailable')
    if algo not in algorithms():raise ValueError(f'{algo} not installed in Python environment')
    def pipeline():
        steps=[]
        if numerical:steps.append(('numeric',Pipeline([('imputer',SimpleImputer(strategy='median'))]),numerical))
        if categorical:steps.append(('categories',Pipeline([('imputer',SimpleImputer(strategy='most_frequent')),('onehot',OneHotEncoder(handle_unknown='ignore'))]),categorical))
        return Pipeline([('preprocessing',ColumnTransformer(steps)),('classifier',new_model())])
    cv=StratifiedKFold(n_splits=folds,shuffle=True,random_state=seed)
    records=[]
    for idx,(train_idx,val_idx) in enumerate(cv.split(X_train,y_train),1):
        m=pipeline();m.fit(X_train.iloc[train_idx],y_train[train_idx]);pred=m.predict(X_train.iloc[val_idx])
        records.append({'fold':idx,'train_rows':len(train_idx),'validation_rows':len(val_idx),'accuracy':round(float(accuracy_score(y_train[val_idx],pred)),6),'macro_f1':round(float(f1_score(y_train[val_idx],pred,average='macro',zero_division=0)),6)})
    final=pipeline();final.fit(X_train,y_train);pred=final.predict(X_test)
    cm=confusion_matrix(y_test,pred,labels=list(range(len(encoder.classes_))))
    metrics={'accuracy':round(float(accuracy_score(y_test,pred)),6),'macro_f1':round(float(f1_score(y_test,pred,average='macro',zero_division=0)),6)}
    if len(encoder.classes_)==2:
        tn,fp,fn,tp=cm.ravel();metrics['false_positive_rate']=round(float(fp/(fp+tn)),6) if fp+tn else None
    return {'algorithm':algo,'split':f'{int((1-split)*100)}/{int(split*100)}','folds':records,'heldout':metrics,'confusion_matrix':cm.tolist(),'classes':encoder.classes_.tolist(),'training_rows':len(y_train),'test_rows':len(y_test),'sample_rows':len(df),'truncated_to_first_rows':truncated,'features':features,'seed':seed,'pipeline':final,'label_encoder':encoder,'data_sha256':hashlib.sha256(raw).hexdigest()}
