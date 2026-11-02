"""QuantumSafe administrator backend CLI. No training or model uploads exposed to viewers.

Run ONLY on the administrator machine using local OS access controls.
Example: python SourceCode/manage_ml.py train-all --csv C:\\Data\\iot.csv --label Attack_label --normal-label 0
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path


def main(argv=None):
    parser=argparse.ArgumentParser(description='QuantumSafe offline IDS model administrator CLI (local-only)')
    parser.add_argument('--model-store',default=None,help='Alternate local ML data directory (tests/advanced use)')
    sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('list-algorithms')
    train_opts=[]
    for name in ('train','train-all'):
        p=sub.add_parser(name,help='Train locally from labelled CSV, without browser uploads')
        p.add_argument('--csv',required=True)
        p.add_argument('--label',default=None)
        p.add_argument('--normal-label',default=None)
        p.add_argument('--binary',action='store_true',help='Convert verified normal class to normal; all others attack')
        p.add_argument('--features',nargs='+',default=None,help='Exact IoT CSV input feature names; otherwise automatically screened')
        p.add_argument('--max-rows',type=int,default=30000,help='Bounded training sample; default 30000; max 500000')
        p.add_argument('--folds',type=int,choices=[3,5],default=3)
        p.add_argument('--test-fraction',type=float,choices=[.2,.3],default=.3)
        p.add_argument('--algorithm',default='Random Forest' if name=='train' else None)
        p.add_argument('--notes',default='')
    p=sub.add_parser('retrain',help='Create a new immutable model version using original algorithm/schema and new CSV')
    p.add_argument('--model-id',required=True,type=int);p.add_argument('--csv',required=True)
    p.add_argument('--max-rows',type=int,default=30000)
    p.add_argument('--folds',type=int,choices=[3,5],default=3)
    p=sub.add_parser('import-and-retrain',help='Trusted existing local .joblib/.pkl: read algorithm/features then CLEAN REFIT from CSV')
    p.add_argument('--checkpoint',required=True)
    p.add_argument('--csv',required=True)
    p.add_argument('--i-trust-local-pickle',action='store_true',help='Required: importing pickle can execute code')
    p.add_argument('--features',nargs='+',default=None)
    p.add_argument('--label',default=None)
    p.add_argument('--normal-label',default=None)
    p.add_argument('--max-rows',type=int,default=30000)
    p=sub.add_parser('models')
    p=sub.add_parser('rank',help='Evaluate saved held-out facts via local Prolog and select shadow-only routes')
    p.add_argument('--dataset-sha',default=None)
    p.add_argument('--swipl',default=None,help='Path to your installed swipl.exe (Windows)')
    p=sub.add_parser('predict',help='Offline inference with a trained and verified saved model')
    p.add_argument('--model-id',required=True,type=int);p.add_argument('--csv',required=True)
    p.add_argument('--output',default=None);p.add_argument('--chunk-rows',type=int,default=5000)
    p=sub.add_parser('shadow-jsonl',help='Process exact-schema JSON lines from external collector; no blocking')
    p.add_argument('--model-id',required=True,type=int)
    sub.add_parser('auto-shadow-jsonl',help='Use saved Prolog per-threat model routes on external real-feature JSON lines; advisory only')
    p=sub.add_parser('retire',help='Retire local model version and remove its saved route')
    p.add_argument('--model-id',required=True,type=int)
    args=parser.parse_args(argv)
    from quantumsafe.ml_engine import train, registry, selector, predict
    root=args.model_store
    def dump(x):print(json.dumps(x,ensure_ascii=False,indent=2,default=str))
    try:
        if args.action=='list-algorithms':dump({'algorithms':train.estimator_names()})
        elif args.action in ('train','train-all'):
            names=train.estimator_names() if args.action=='train-all' else [args.algorithm]
            outcome=[]
            prepared=None
            if args.action=='train-all':
                from quantumsafe.ml_engine.data import scan_csv
                prepared=scan_csv(args.csv,label=args.label,features=args.features,
                                  normal=args.normal_label,binary=args.binary,max_rows=args.max_rows)
            for algo in names:
                try:
                    info=train.fit_csv(args.csv,algorithm=algo,label=args.label,features=args.features,
                                       normal=args.normal_label,binary=args.binary,max_rows=args.max_rows,
                                       folds=args.folds,test_fraction=args.test_fraction,notes=args.notes,root=root,prepared=prepared)
                    outcome.append({'algorithm':algo,'status':'saved','model_id':info['model_id'],
                                    'heldout':info['heldout'],'per_class':info['per_class'],
                                    'features':info['features'],'excluded_columns':info['excluded_columns']})
                except Exception as exc:
                    outcome.append({'algorithm':algo,'status':'failed','reason':f'{type(exc).__name__}: {exc}'})
            # Rank eligible models automatically after every completed backend training batch.
            # Native SWI-Prolog is preferred when installed; Python fallback is explicit.
            if any(x['status']=='saved' for x in outcome):
                try:
                    selection=selector.rank(root=root)
                    dump({'automatic_rule_selection':selection})
                except Exception as exc:
                    dump({'automatic_rule_selection_error':f'{type(exc).__name__}: {exc}'})
            dump(outcome)
            if all(x['status']=='failed' for x in outcome):return 2
        elif args.action=='retrain':dump(train.retrain_model(args.model_id,args.csv,root=root,
                                                              max_rows=args.max_rows,folds=args.folds))
        elif args.action=='import-and-retrain':
            if not args.i_trust_local_pickle:
                raise ValueError('Untrusted pickle deserialization is dangerous. Only run with --i-trust-local-pickle for models YOU created and trust.')
            import joblib
            from sklearn.pipeline import Pipeline
            path=Path(args.checkpoint).expanduser().resolve(strict=True)
            if path.suffix.lower() not in ('.joblib','.pkl'):
                raise ValueError('Supported trusted checkpoint types: .joblib or .pkl')
            imported=joblib.load(path)  # ONLY explicit, local admin opt-in
            previous=imported if isinstance(imported,dict) else {}
            candidate=previous.get('pipeline',previous.get('model',imported))
            if isinstance(candidate,Pipeline): candidate=candidate.steps[-1][1]
            cname=type(candidate).__name__
            algorithm={'RandomForestClassifier':'Random Forest',
                       'XGBClassifier':'XGBoost','LGBMClassifier':'LightGBM'}.get(cname)
            if algorithm is None:
                raise ValueError(f'Existing estimator {cname} is not one of RF/XGBoost/LightGBM; register a reviewed trusted adapter first.')
            feats=args.features or previous.get('features')
            if not feats:
                raise ValueError('Model contains no feature schema: provide --features with exact CSV columns.')
            dump({'trusted_model_algorithm':algorithm,'strategy':'clean_refit_not_partial_fit',
                  'notes':'Previous model bytes/weights remain untouched; a new checkpoint is created.'})
            dump(train.fit_csv(args.csv,algorithm=algorithm,label=args.label,features=feats,
                               normal=args.normal_label,max_rows=args.max_rows,root=root,
                               notes=f'Clean retrain from trusted {path.name}'))
        elif args.action=='models':
            dump([{'id':x['id'],'parent_id':x['parent_id'],'algorithm':x['algorithm'],
                   'status':x['status'],'dataset_file':x['dataset_file'],
                   'sample_rows':x['sample_rows'],'heldout':x['metrics'],
                   'features':x['features']} for x in registry.models(root)])
        elif args.action=='rank':dump(selector.rank(root=root,dataset_sha=args.dataset_sha,swipl=args.swipl))
        elif args.action=='predict':dump(predict.predict_csv(args.model_id,args.csv,root=root,
                                                               output=args.output,chunk_rows=args.chunk_rows))
        elif args.action=='retire':registry.set_status(args.model_id,'retired',root);dump({'status':'retired','id':args.model_id})
        elif args.action=='auto-shadow-jsonl':
            from quantumsafe.ml_engine.shadow import ShadowRouter
            router=ShadowRouter(root)
            for line in sys.stdin:
                if not line.strip():continue
                try:dump(router.process(json.loads(line)))
                except Exception as exc:dump({'error':f'{type(exc).__name__}: {exc}'})
        elif args.action=='shadow-jsonl':
            for line in sys.stdin:
                if not line.strip():continue
                try:dump(predict.infer_event(args.model_id,json.loads(line),root=root))
                except Exception as exc:dump({'error':f'{type(exc).__name__}: {exc}'})
    except Exception as exc:
        print(f'ERROR: {type(exc).__name__}: {exc}',file=sys.stderr)
        return 2
    return 0

if __name__=='__main__':sys.exit(main())
