"""Backend shadow routing for an external *real-field* JSONL feature collector.

No fake network packets, no fabricated TCP/MQTT feature values, no firewall action.
"""
from __future__ import annotations
import pandas as pd
from . import registry
from .train import to_schema


class ShadowRouter:
    def __init__(self,root=None):
        self.root=root
        selected=registry.active_routes(root)
        self.routes=[]
        self.models={}
        for r in selected:
            if r['model_id'] not in self.models:
                self.models[r['model_id']]=registry.load_model(r['model_id'],root)
            bundle,_=self.models[r['model_id']]
            if r['threat'] not in bundle['classes']:
                raise ValueError('Route threat/class mismatch for model '+str(r['model_id']))
            self.routes.append(r)

    def process(self,event):
        if not isinstance(event,dict):raise ValueError('Event must be JSON object of real network features')
        checked={};missing=[];detections=[]
        for r in self.routes:
            mid=r['model_id'];bundle,_=self.models[mid]
            schema=bundle['schema']
            needed=set(schema['features'])-set(event)
            if needed:
                missing.append({'model_id':mid,'required_features_missing':sorted(needed)})
                continue
            if mid not in checked:
                row=pd.DataFrame([{name:event[name] for name in schema['features']}])
                checked[mid]=bundle['classes'][int(bundle['pipeline'].predict(to_schema(row,schema))[0])]
            if checked[mid]==r['threat']:
                detections.append({'threat':r['threat'],'model_id':mid,'model_score':r['score']})
        for hit in detections:
            registry.record_predictions([{'model_id':hit['model_id'],'threat':hit['threat'],
                    'prediction':hit['threat'],'source':'external_real_feature_feed',
                    'mode':'shadow_only'}],self.root)
        return {'mode':'shadow_only','classification':'REVIEW' if detections else 'NOT_FLAGGED',
                'matches':detections,'models_evaluated':len(checked),
                'incompatible_models':missing,
                'action':'no_network_blocking_or_key_rotation'}
