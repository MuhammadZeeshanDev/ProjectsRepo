"""Admin-only ML operating console, no CLI required for routine operations."""
from __future__ import annotations
from pathlib import Path
import shutil
import pandas as pd
import streamlit as st
from ..ml_engine import data, train, registry, selector, predict, jobs, importer

@st.cache_resource
def _init_jobs():
    jobs.recover_interrupted()
    return True


def _source(key):
    source=st.radio('CSV source',['Local path on PC A (best for huge CSVs)','Upload CSV from browser'],
                    horizontal=True,key=key+'_source')
    if source.startswith('Local'):
        text=st.text_input('Full CSV path on this Windows computer',placeholder=r'D:\Datasets\iot_network.csv',key=key+'_path')
        return text.strip() or None
    up=st.file_uploader('CSV file (browser memory limits apply)',type=['csv'],key=key+'_upload')
    if up is None:return None
    if up.size>256*1024*1024:
        st.warning('Browser upload is capped at 256 MiB in this panel; use local path for large CSVs.')
        return None
    folder=registry.BASE/'Admin_CSV_Uploads';folder.mkdir(parents=True,exist_ok=True)
    # A deterministic upload copy for the same browser session; never trust client filename as path.
    import hashlib
    up.seek(0)
    fingerprint=hashlib.sha256(up.getbuffer()).hexdigest()[:20]
    p=folder/(fingerprint+'.csv')
    if not p.exists():
        with p.open('wb') as dst:
            up.seek(0);shutil.copyfileobj(up,dst,1024*1024)
    return str(p)


def _train():
    st.subheader('📚 Train models from your IoT / network CSV')
    st.caption('Admin controls training here. The backend validates CSV, samples across the full file, runs cross-validation, saves versioned checkpoints and asks Prolog to rank eligible models for shadow monitoring.')
    path=_source('ml_train')
    columns=[]
    if path:
        try:
            p,columns=data.inspect_headers(path)
            st.success(f'CSV found: {p.name} · {p.stat().st_size/1024**2:,.1f} MiB · {len(columns)} columns')
        except Exception as exc:st.error(f'CSV unavailable: {exc}')
    if not columns:return
    default=next((x for x in data.LABEL_NAMES if x in columns),columns[-1])
    label=st.selectbox('Actual target/attack label (must contain normal and attack examples)',columns,index=columns.index(default))
    st.warning('Labels are required for supervised learning. Do not use IP, timestamps or record identifiers as labels. If your CSV is unlabeled, it cannot train a trustworthy supervised IDS classifier.')
    binary=st.checkbox('Group all attacks into binary Normal vs Attack',value=False)
    normal=st.text_input('Normal class (exact dataset value: 0, Normal, Benign...)',value='0' if label.casefold()=='attack_label' else 'Normal')
    candidates=data.auto_features(columns,label)
    st.caption(f'Proposed network features: {len(candidates)} (IP/ID/time/leaky mqtt.protoname excluded by default).')
    with st.expander('Customize features (advanced)'):
        features=st.multiselect('Features; leave defaults to automatic screened set',
                                [x for x in columns if x!=label],default=candidates[:min(len(candidates),30)])
        st.warning('Adding ID, IP, time or label-proxy fields can create false accuracy. Admin must review them.')
    names=[a for a in ('Random Forest','XGBoost','LightGBM') if a in train.estimator_names()]
    algorithms=st.multiselect('Algorithms to train',names,default=names)
    c1,c2,c3=st.columns(3)
    sample_rows=c1.selectbox('Training sample rows', [2000,5000,10000,30000,50000,100000,250000,500000],index=3)
    split=c2.selectbox('Test holdout',['70/30','80/20'])
    folds=c3.selectbox('CV folds',[3,5])
    if st.button('🚀 Start training all selected models',type='primary',disabled=not bool(algorithms)):
        try:
            jid=jobs.submit_training({'kind':'train','csv':path,'label':label,'normal':normal.strip() or None,
               'binary':binary,'features':features,'algorithms':algorithms,'max_rows':sample_rows,
               'test_fraction':.3 if split=='70/30' else .2,'folds':folds})
            st.success(f'Training job #{jid} submitted to backend. You can view Monitoring while it runs.')
            st.rerun()
        except Exception as exc:st.error(type(exc).__name__+': '+str(exc))


def _models():
    st.subheader('📦 Model library, retraining & CSV tests')
    rows=registry.models()
    if not rows:
        st.info('No saved model yet. Train one first.');return
    st.dataframe(pd.DataFrame([{'ID':r['id'],'Algorithm':r['algorithm'],'Status':r['status'],
        'Classes':len(r['classes']),'Sampled rows':r['sample_rows'],
        'Macro F1':r['metrics'].get('macro_f1'),'Dataset':Path(r['dataset_file'] or '').name}
        for r in rows]),hide_index=True,use_container_width=True)
    choose=st.selectbox('Select saved model ID',[r['id'] for r in rows],format_func=lambda x:f'#{x} · '+next(r['algorithm'] for r in rows if r['id']==x))
    model=next(r for r in rows if r['id']==choose)
    with st.expander('📋 Saved model details'):
        st.json({'id':model['id'],'algorithm':model['algorithm'],'source':model['dataset_file'],
                 'normal':model['normal_label'],'features':model['features'],'classes':model['classes'],
                 'metrics':model['metrics'],'folds':model['folds'],'class_metrics':model['class_metrics']})
    if model['status']=='unverified_import':
        st.warning('Imported model is quarantined; it requires independent evaluation and timing review. It cannot auto-route.')
        validpath=st.text_input('Independent LABELED CSV path to validate imported model',key='import_valid_csv')
        if st.button('Validate imported model',disabled=not bool(validpath)):
            try:
                result=importer.validate_import(choose,validpath)
                st.json(result);st.rerun()
            except Exception as exc:st.error(str(exc))
    elif model['status']!='retired':
        with st.expander('🔁 Retrain from a new CSV (new version)'):
            new_path=st.text_input('New CSV path, same label and required columns',key='retrain_path')
            if st.button('Start clean retraining',disabled=not bool(new_path)):
                try:
                    jid=jobs.submit_training({'kind':'retrain','csv':new_path,'model_id':choose,
                       'max_rows':30000,'folds':3})
                    st.success(f'Retraining job #{jid} queued; previous checkpoint stays saved.')
                except Exception as exc:st.error(str(exc))
        with st.expander('🧪 Offline CSV prediction test'):
            test_path=st.text_input('Local CSV with EXACT model feature columns',key='predict_path')
            if st.button('Test selected model',disabled=not bool(test_path)):
                try:st.json(predict.predict_csv(choose,test_path,chunk_rows=5000))
                except Exception as exc:st.error(type(exc).__name__+': '+str(exc))
    if model['status']!='retired':
        if st.button('Retire selected model'):
            registry.set_status(choose,'retired');st.warning('Model retired; checkpoint retained for audit.');st.rerun()


def _import():
    st.subheader('📥 Import your previously trained checkpoint')
    st.warning('Security: .joblib files can execute Python code when opened. Import ONLY checkpoint files you created/trust. Never upload random downloaded models. Security Operator has no access to this screen.')
    st.caption('Expected format: QuantumSafe-compatible .joblib bundle containing pipeline, classes, schema (numeric/categorical/features), label and normal_label. A plain incompatible sklearn model needs a reviewed adapter.')
    mode=st.radio('Import goal',['Register compatible model bundle (quarantine until tested)',
                                  'Reuse RF/XGB/LightGBM algorithm as a training template'],key='ml_import_mode')
    if mode.startswith('Reuse'):
        imported_path=st.text_input('New labeled IoT CSV for clean retraining',placeholder=r'D:\Datasets\iot_network.csv',key='ml_retrain_import_csv')
        target_label=st.text_input('Target label column',value='Attack_label',key='ml_retrain_import_label')
        normal=st.text_input('Normal label value',value='0',key='ml_retrain_import_normal')
        st.caption('Same algorithm, NEW fitted weights. No unsafe reuse of incompatible old preprocessing or training samples.')
    upload=st.file_uploader('Trusted .joblib checkpoint',type=['joblib'],key='ml_import_upload')
    trust=st.checkbox('I created/trust this checkpoint and authorize loading its Python serialization',key='ml_import_trust')
    if st.button('Import trusted model / start retrain',disabled=upload is None or not trust):
        try:
            import uuid
            folder=registry.BASE/'Trusted_Imports';folder.mkdir(parents=True,exist_ok=True)
            p=folder/(uuid.uuid4().hex+'.joblib')
            upload.seek(0)
            with p.open('wb') as dest:shutil.copyfileobj(upload,dest,1024*1024)
            if mode.startswith('Reuse'):
                template=importer.detect_algorithm_template(p,trust=True)
                jid=jobs.submit_training({'kind':'train','csv':imported_path,'label':target_label,
                    'normal':normal,'binary':False,'features':None,'algorithms':[template['algorithm']],
                    'max_rows':30000,'folds':3,'test_fraction':.3})
                st.success(f'Imported {template["algorithm"]} template; clean retrain job #{jid} submitted.')
                st.json(template)
            else:
                res=importer.import_trusted(p,trust=True)
                st.success('Imported into quarantine. Validate using independent labeled CSV in Model Library.')
                st.json(res)
        except Exception as exc:st.error(type(exc).__name__+': '+str(exc))


def _ai():
    st.subheader('🧠 Prolog-based model selection')
    st.caption('Local facts: per-attack recall/precision/FPR/support + prediction latency + checkpoint SHA-256. No hosted AI or API key.')
    candidate=st.text_input('Optional path to installed swipl.exe',placeholder=r'C:\Program Files\swipl\bin\swipl.exe')
    detected=selector.find_swipl(candidate or None)
    if detected:st.success('Native SWI-Prolog: '+detected)
    else:st.warning('SWI-Prolog not detected. Conservative local Python rule fallback will be clearly labeled.')
    if st.button('Evaluate saved model evidence and refresh shadow recommendations'):
        try:st.json(selector.rank(swipl=detected))
        except Exception as exc:st.error(str(exc))
    routes=registry.active_routes()
    if routes:st.dataframe(pd.DataFrame(routes),hide_index=True,use_container_width=True)
    else:st.info('No eligible evaluated models routed. Training quality or compatibility might be insufficient.')
    st.error('Shadow selection NEVER implies autonomous live firewall/IPS activation. Live packet feature capture, supervised tests and policy gates are required.')


def _jobs():
    st.subheader('⚙️ Background training jobs')
    for j in jobs.list_jobs(15):
        icon={'completed':'✅','failed':'🔴','running':'🟡','queued':'🟠','interrupted':'⚠️'}.get(j['status'],'•')
        with st.expander(f"{icon} #{j['id']} · {j['status']} · {j['step']}",expanded=j['status'] in ('running','failed')):
            st.caption(j['created_utc'])
            if j['error']:st.error(j['error'])
            if j['result']:st.json(j['result'])
    if st.button('Refresh job status'):st.rerun()


def show(actor):
    if actor.get('RoleName')!='Admin':st.error('Administrator-only ML & AI controls');return
    _init_jobs()
    st.title('🧠 IDS ML & AI — Administrator Control Center')
    st.info('You control datasets and model imports here. Trained models, metrics and Prolog route decisions are persisted locally. Operator frontend remains read-only.')
    tab1,tab2,tab3,tab4,tab5=st.tabs(['🚀 Train IoT CSV','📦 Saved models','📥 Import model','🧠 Prolog decisions','⚙️ Job history'])
    with tab1:_train()
    with tab2:_models()
    with tab3:_import()
    with tab4:_ai()
    with tab5:_jobs()
