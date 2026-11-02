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
    tabs=st.tabs(['🎯 Train & compare','🔬 Test CSV','📦 Model library','🧠 Local AI + Prolog','🔌 Deployment checks'])
    with tabs[0]:
        from ..local_training import algorithms, run_experiment
        from ..large_csv import checked_csv, headers, representative_sample, stage_upload, MAX_CSV_BYTES
        st.info('Local training on a representative sample from an entire CSV up to 3 GiB. Validation folds and the held-out test set are separate. Large CSV acceptance is NOT full-data training.')
        source = st.radio('Select CSV source', ['Local file path (recommended for large CSV)', 'Upload CSV in browser'], horizontal=True, key='qs_csv_source')
        local_path, dataset = '', None
        columns = []
        if source.startswith('Local'):
            local_path = st.text_input('Full CSV path on the PC running QuantumSafe', placeholder=r'C:\Datasets\EdgeIIoTset.csv', key='qs_train_path')
            if local_path:
                try:
                    checked = checked_csv(local_path)
                    columns = headers(checked)
                    st.caption(f'CSV found: {checked.name} — {checked.stat().st_size / 1024**3:.3f} GiB (max 3 GiB)')
                except Exception as exc:
                    st.warning(str(exc))
        else:
            dataset = st.file_uploader('Upload CSV (up to 3 GiB; memory-dependent)', type=['csv'], key='train_csv')
            if dataset:
                if dataset.size > MAX_CSV_BYTES:
                    st.error('File exceeds the 3 GiB limit.')
                else:
                    try:
                        dataset.seek(0)
                        columns = pd.read_csv(dataset, nrows=0).columns.tolist()
                        dataset.seek(0)
                    except Exception as exc:
                        st.error('Cannot read CSV header: ' + str(exc))
                    st.caption(f'Upload size: {dataset.size / 1024**3:.3f} GiB. Browser upload can require substantial RAM; local file path is safer for 3 GiB.')
        if columns:
            label = st.selectbox('Target label / attack class', columns, key='train_label')
            target_mode = st.radio('Target preparation', ['Use selected label as-is (2–100 classes)', 'Convert to binary: normal vs attack'], horizontal=True, key='qs_target_mode')
            normal_value = st.text_input('Exact normal class value (case-insensitive; other values become attack)', value='Normal', key='qs_normal_value') if target_mode.startswith('Convert') else ''
            st.caption('Choose a real attack-label column, not an IP, timestamp or unique record ID. Binary conversion requires a verified normal-class name.')
            features = st.multiselect('Input features (maximum 30)', [c for c in columns if c != label],
                                      default=[c for c in columns if c != label][:min(10, len(columns)-1)], max_selections=30)
            a, b, c = st.columns(3)
            algo = a.selectbox('Algorithm (installed)', algorithms(), key='train_algo')
            split = b.selectbox('Holdout split', ['70/30', '80/20'], key='train_split')
            folds = c.selectbox('Validation folds', [3, 5], key='train_folds')
            st.caption('Original/ROS and different feature-selection protocols must be trained as separate explicitly labeled datasets. Each fold is evaluated independently.')
            if st.button('▶️ Sample full CSV, train and evaluate', type='primary'):
                try:
                    with st.spinner('Scanning CSV in bounded chunks; then training selected algorithm...'):
                        if dataset is not None:
                            with tempfile.TemporaryDirectory(prefix='qs_train_upload_') as tmp:
                                sample = representative_sample(stage_upload(dataset, Path(tmp)/'uploaded.csv'), features, label)
                        else:
                            sample = representative_sample(local_path, features, label)
                        if normal_value:
                            observed = sample['sample'][label].dropna().astype(str).str.strip().str.casefold()
                            if normal_value.strip().casefold() not in set(observed):
                                raise ValueError(f'Normal class {normal_value!r} not present in sampled target. Choose correct label or exact normal value.')
                            sample['sample'][label] = observed.ne(normal_value.strip().casefold()).map({False:'normal', True:'attack'})
                        raw = sample['sample'].to_csv(index=False).encode('utf-8')
                        if len(raw) > MAX_UPLOAD:
                            raise ValueError('Selected feature sample exceeds 60 MiB; choose fewer features or shorter categorical values.')
                        result = run_experiment(raw, label, features, algo, 0.3 if split == '70/30' else 0.2, folds)
                        result['target_mode'] = 'binary_normal_vs_attack' if normal_value else 'original_multiclass'
                        result['truncated_to_first_rows'] = sample['sampled_rows'] < sample['total_rows']
                        result['source_sample'] = {k:v for k,v in sample.items() if k != 'sample'}
                        st.session_state['qs_training_result'] = result
                        st.session_state['qs_training_details'] = (sample['source_file'], label, split, folds)
                        from ..training_history import save_run
                        run_id = save_run(result, sample['source_file'], label)
                        st.session_state['qs_last_run_id'] = run_id
                    st.success(f"Training finished on {sample['sampled_rows']:,} sampled rows from {sample['total_rows']:,} parsed CSV rows.")
                except Exception as exc:
                    st.error('Training failed: '+type(exc).__name__+': '+str(exc))
        else:
            st.caption('Choose an accessible CSV to configure training.')
        result=st.session_state.get('qs_training_result')
        if result:
            st.subheader('Last completed training')
            st.caption('Metrics are saved locally. Checkpoint is saved separately using the button below.')
            st.write('Algorithm:',result['algorithm'],' • Split:',result['split'],' • Training records:',result['training_rows'],' • Test records:',result['test_rows'])
            st.dataframe(pd.DataFrame(result['folds']),hide_index=True,use_container_width=True)
            st.caption('Each validation fold stays separate; held-out test metrics are reported independently.')
            st.json({'held_out_metrics':result['heldout'],'class_order':result['classes'],'confusion_matrix':result['confusion_matrix'],'sampled_from_full_csv':result.get('source_sample'), 'dataset_sampled':result['truncated_to_first_rows']})
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
        st.subheader('Test trusted Edge-IIoTset RF checkpoint on a local CSV')
        st.caption('Supports up to 3 GiB streamed in chunks. The included 10-feature Random Forest checkpoint is the only preverified model for this test. CSV MUST contain original expected TCP/MQTT features.')
        test_path = st.text_input('CSV file path for offline model testing', placeholder=r'C:\Datasets\test.csv', key='qs_test_path')
        chunk_size = st.selectbox('Prediction rows per chunk', [1000, 5000, 10000, 20000], index=2)
        if st.button('▶️ Run checkpoint inference', disabled=not bool(test_path)):
            try:
                from ..edge_rf_inference import predict_local_csv
                from ..large_csv import checked_csv
                checked_csv(test_path)
                with st.spinner('Processing CSV in bounded chunks...'):
                    outcome = predict_local_csv(test_path, chunk_size=chunk_size)
                st.session_state['qs_csv_test_result'] = outcome
            except Exception as exc:
                st.error(type(exc).__name__ + ': ' + str(exc))
        outcome = st.session_state.get('qs_csv_test_result')
        if outcome:
            st.metric('CSV rows tested', outcome['rows'])
            st.json({'prediction_counts':outcome['counts'], 'metrics_if_labels_exist':outcome['metrics']})
            st.dataframe(outcome['preview'], hide_index=True, use_container_width=True)
            st.code(outcome['output_path'])
            st.caption('Prediction CSV saved at the local path above. Check free disk space: output can be larger than the input. These are offline predictions, NOT live gateway detections.')
    with tabs[2]:
        _model_library()
        from ..training_history import recent_runs
        st.subheader('Saved training history (persistent)')
        rows = recent_runs()
        if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else: st.info('No completed training runs saved yet.')
    with tabs[3]:
        from . import ai_advisor_page
        ai_advisor_page.show_embedded(actor)
    with tabs[4]:
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
