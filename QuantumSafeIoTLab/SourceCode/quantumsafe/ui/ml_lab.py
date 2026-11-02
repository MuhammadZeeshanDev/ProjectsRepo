"""Safe ML artifact registry + CSV/ZIP profiling. No untrusted pickle execution."""
import csv, hashlib, io, json, os, re, shutil, sqlite3, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st
import pandas as pd

BASE = Path(__file__).resolve().parents[3]
STORE = BASE / 'ML_Artifacts'
DB = STORE / 'registry.sqlite3'
MAX_UPLOAD = 60 * 1024 * 1024
MAX_EXTRACT = 120 * 1024 * 1024

def connection():
    STORE.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.execute('CREATE TABLE IF NOT EXISTS models (id INTEGER PRIMARY KEY, name TEXT NOT NULL, dataset TEXT, algorithm TEXT, filename TEXT NOT NULL, sha256 TEXT NOT NULL, size_bytes INTEGER, status TEXT NOT NULL, features_json TEXT, notes TEXT, created_utc TEXT NOT NULL)')
    db.commit()
    return db

def safe_name(s):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', str(s))[:100]

def import_artifact(name, dataset, algorithm, file_name, data, features, notes):
    if not data or len(data) > MAX_UPLOAD: raise ValueError('Model file empty or over 60 MB. Use a smaller checkpoint or offline import later.')
    ext = Path(file_name).suffix.lower()
    if ext not in ('.joblib','.pkl','.json','.ubj','.txt','.onnx','.zip'): raise ValueError('Unsupported model file type.')
    if ext == '.zip':
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if z.testzip() is not None: raise ValueError('Corrupt ZIP')
            if sum(x.file_size for x in z.infolist()) > MAX_EXTRACT: raise ValueError('ZIP expanded size exceeds limit')
    digest = hashlib.sha256(data).hexdigest()
    folder = STORE / 'models' / digest[:2]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (digest + ext)
    if not path.exists(): path.write_bytes(data)
    with connection() as db:
        db.execute('INSERT INTO models (name,dataset,algorithm,filename,sha256,size_bytes,status,features_json,notes,created_utc) VALUES (?,?,?,?,?,?,?,?,?,?)',
                   (name,dataset,algorithm,str(path.relative_to(STORE)),digest,len(data),'Stored — not validated',json.dumps(features),notes,datetime.now(timezone.utc).isoformat()))
        db.commit()
    return digest

def profile_csv(raw, label):
    import pandas as pd
    if len(raw)>MAX_UPLOAD: raise ValueError('Dataset over 60 MB. Use a smaller sample for profiling.')
    frame=pd.read_csv(io.BytesIO(raw),nrows=10000,low_memory=False)
    if frame.empty: raise ValueError('No records found')
    st.caption('Preview limited to first 10,000 records; statistics describe this sample, not necessarily the full dataset.')
    a,b,c=st.columns(3); a.metric('Sample rows',len(frame));b.metric('Columns',len(frame.columns));c.metric('Duplicate sample rows',int(frame.duplicated().sum()))
    st.dataframe(frame.head(20),use_container_width=True)
    stats=pd.DataFrame({'column':frame.columns,'type':[str(t) for t in frame.dtypes], 'missing':[int(frame[x].isna().sum()) for x in frame.columns]})
    st.dataframe(stats,use_container_width=True)
    if label and label in frame:
        st.subheader('Class distribution (sample)')
        st.bar_chart(frame[label].astype(str).value_counts().head(30))
    st.download_button('Download sample quality report CSV',stats.to_csv(index=False).encode(),'quality_report.csv','text/csv')

def show(actor):
    if actor.get('RoleName')!='Admin':
        st.error('Administrator only.');return
    st.title('🤖 ML Lab — Training, Models & AI')
    st.caption('Administrator workspace: train and compare models, inspect individual folds, evaluate using AI guidance and check deployment safety.')
    tabs=st.tabs(['🎯 Train & compare','📦 Model library','✨ AI & improvement','🔌 Deployment checks'])
    with tabs[0]:
        from ..local_training import algorithms,run_experiment
        st.info('Local supervised training with a held-out test set. Preprocessing is fitted on each training fold only. A test-set score is NOT proof of live IoT detection.')
        dataset=st.file_uploader('Training dataset CSV (up to 60 MB, first 20,000 rows)',type=['csv'],key='train_csv')
        if dataset:
            raw=dataset.getvalue()
            if len(raw)>MAX_UPLOAD:st.error('File too large')
            else:
                try:
                    import pandas as pd
                    columns=pd.read_csv(io.BytesIO(raw),nrows=0).columns.tolist()
                    label=st.selectbox('Target label / attack class',columns,key='train_label')
                    selected=st.multiselect('Input features (never include target)',[x for x in columns if x!=label],default=[x for x in columns if x!=label][:min(10,len(columns)-1)],max_selections=30)
                    a,b,c=st.columns(3)
                    algo=a.selectbox('Algorithm',algorithms(),key='train_algo')
                    split=b.selectbox('Holdout split',['70/30','80/20'],key='train_split')
                    folds=c.selectbox('Stratified CV folds',[3,5],key='train_folds')
                    st.caption('Algorithms only appear when installed. Original, ROS and SA-HFS protocols must be supplied as explicitly prepared datasets; this form never claims to reproduce those protocols automatically.')
                    if st.button('▶️ Train and evaluate now',type='primary'):
                        with st.spinner('Training on bounded local sample...'):
                            result=run_experiment(raw,label,selected,algo,0.3 if split=='70/30' else 0.2,folds)
                        st.session_state['qs_training_result']=result
                        st.session_state['qs_training_details']=(dataset.name,label,split,folds)
                except Exception as e:st.error('Training setup failed: '+str(e))
        result=st.session_state.get('qs_training_result')
        if result:
            st.subheader('Last completed experiment (session only)')
            st.write('Algorithm:',result['algorithm'],' • Split:',result['split'],' • Training records:',result['training_rows'],' • Test records:',result['test_rows'])
            st.dataframe(pd.DataFrame(result['folds']),hide_index=True,use_container_width=True)
            st.caption('Each validation fold stays separate; held-out test metrics are reported independently.')
            st.json({'held_out_metrics':result['heldout'],'class_order':result['classes'],'confusion_matrix':result['confusion_matrix'],'dataset_truncated':result['truncated_to_first_rows']})
            st.warning('The held-out split is evaluated ONCE after CV; no online learning, live gateway connection or automatic deployment is performed.')
            if st.button('💾 Save trained checkpoint locally'):
                import joblib
                bundle={'model':result['pipeline'],'label_encoder':result['label_encoder'],'features':result['features'],'dataset_sha256':result['data_sha256'],'class_order':result['classes']}
                buff=io.BytesIO();joblib.dump(bundle,buff)
                if buff.tell()>MAX_UPLOAD:st.error('Checkpoint over allowed size')
                else:
                    name,lab,split_name,nfolds=st.session_state.get('qs_training_details',('dataset','label','split',3))
                    digest=import_artifact(f'{result["algorithm"]} {split_name} {nfolds}fold',name,result['algorithm'],'trained.joblib',buff.getvalue(),result['features'],'Locally trained trusted checkpoint. Not validated for live gateway inference. Target: '+lab)
                    st.success('Checkpoint stored (NOT deployed). SHA256: '+digest[:20])
    with tabs[1]:
        _model_library()
    with tabs[2]:
        from . import ai_advisor_page
        ai_advisor_page.show_embedded(actor)
    with tabs[3]:
        from .. import deployment_readiness
        deployment_readiness.show()

def _model_library():
    st.subheader('Imported and trained model checkpoints')
    st.caption('Untrusted .pkl/.joblib files are stored but not loaded automatically. Full deployment requires a verified feature adapter and controlled validation.')
    t1,t2=st.tabs(['📥 Import checkpoint','📋 Saved models'])
    with t1:
        with st.form('import_model'):
            name=st.text_input('Checkpoint name')
            dataset=st.selectbox('Dataset',['Edge-IIoTset','CICIoT2023','TON_IoT','Other'])
            algo=st.selectbox('Algorithm',['Random Forest','XGBoost','LightGBM','Other'])
            model=st.file_uploader('Model file',type=['joblib','pkl','json','ubj','txt','onnx','zip'])
            features=st.text_area('Input features (one per line)')
            notes=st.text_area('Training notes')
            submitted=st.form_submit_button('Save checkpoint (do not execute)')
        if submitted:
            if not name.strip() or model is None:st.error('Name and model file required')
            else:
                try:
                    digest=import_artifact(name.strip(),dataset,algo,model.name,model.getvalue(),[x.strip() for x in features.splitlines() if x.strip()],notes)
                    st.success('Stored (NOT deployed). SHA256 '+digest[:20])
                except Exception as e:st.error(str(e))
    with t2:
        with connection() as db:
            rows=db.execute('SELECT id,name,dataset,algorithm,status,size_bytes,created_utc,sha256 FROM models ORDER BY id DESC').fetchall()
        if rows:st.dataframe(pd.DataFrame(rows,columns=['ID','Name','Dataset','Algorithm','Status','Bytes','Imported UTC','SHA256']),use_container_width=True,hide_index=True)
        else:st.info('No model checkpoints in local library.')
