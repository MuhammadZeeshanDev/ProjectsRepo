"""Strict-schema chunked offline and external-stream SHADOW inference."""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path
import pandas as pd
from . import registry
from .train import to_schema


def predict_csv(model_id,path,*,output=None,chunk_rows=5000,root=None):
    p=Path(path).expanduser().resolve(strict=True)
    if not p.is_file() or p.suffix.lower()!='.csv':raise ValueError('Prediction input must be a local CSV.')
    if chunk_rows<100 or chunk_rows>50000:raise ValueError('chunk rows must be 100–50000')
    bundle,record=registry.load_model(model_id,root)
    features=bundle['schema']['features']
    header=pd.read_csv(p,nrows=0).columns.tolist()
    missing=sorted(set(features)-set(header))
    if missing:raise ValueError(f'Cannot infer: {len(missing)} input columns are missing: {missing[:25]}. No synthetic features will be invented.')
    outfile=Path(output).expanduser().resolve() if output else p.with_suffix('.quantumsafe_predictions.csv')
    if outfile==p:raise ValueError('Do not overwrite source dataset')
    outfile.parent.mkdir(parents=True,exist_ok=True)
    total=0; counts={}; examples=[]
    # Avoid buffering all predictions; preserve one output row per input record.
    with outfile.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['row_number','model_id','prediction','mode'])
        writer.writeheader()
        for chunk in pd.read_csv(p,usecols=features,chunksize=chunk_rows,low_memory=False):
            incoming=to_schema(chunk,bundle['schema'])
            pred=bundle['pipeline'].predict(incoming)
            entries=[]
            for ix,y in enumerate(pred):
                label=bundle['classes'][int(y)]
                total+=1;counts[label]=counts.get(label,0)+1
                writer.writerow({'row_number':total,'model_id':model_id,'prediction':label,'mode':'offline_shadow'})
                if label!=bundle['normal_label'] and len(examples)<1500:
                    entries.append({'model_id':int(model_id),'threat':label,'prediction':label,
                                    'mode':'offline_shadow','source':p.name})
                    examples.append({'row_number':total,'label':label})
            if entries:registry.record_predictions(entries,root)
    return {'model_id':int(model_id),'rows':total,'counts':counts,'output':str(outfile),
            'stored_alert_examples':len(examples),
            'warning':'Offline predictions are NOT network enforcement; model performance on this CSV is unknown without labels.'}


def infer_event(model_id, event, *,root=None,record=True):
    bundle,meta=registry.load_model(model_id,root)
    if not isinstance(event,dict):raise ValueError('Stream event must be JSON object')
    missing=set(bundle['schema']['features'])-set(event)
    if missing:raise ValueError('Input missing required real network fields: '+str(sorted(missing)))
    row=pd.DataFrame([{k:event[k] for k in bundle['schema']['features']}])
    prediction=bundle['classes'][int(bundle['pipeline'].predict(to_schema(row,bundle['schema']))[0])]
    result={'model_id':model_id,'prediction':prediction,'mode':'shadow_only','source':'external_jsonl_feed'}
    if record and prediction!=bundle['normal_label']:
        registry.record_predictions([{'model_id':int(model_id),'prediction':prediction,
                                      'threat':prediction,'mode':'shadow_only','source':'external_jsonl_feed'}],root)
    return result
