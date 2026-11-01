"""Safe ML artifact registry + CSV/ZIP profiling. No untrusted pickle execution."""
import csv, hashlib, io, json, os, re, shutil, sqlite3, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st

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
    st.title('🤖 ML Lab — Dataset Manager & Model Registry')
    st.info('Research notebook is not automatically a trained model. Import exported checkpoints separately. Imported .pkl/.joblib files are stored but NEVER executed here.')
    t1,t2,t3,t4=st.tabs(['📂 Dataset profile','📥 Import model','📋 Model registry','🎯 Edge-IIoTset RF Prediction'])
    with t1:
        upload=st.file_uploader('CSV or ZIP containing CSV (max 60 MB upload)',type=['csv','zip'],key='ml_dataset')
        if upload:
            data=upload.getvalue()
            if len(data)>MAX_UPLOAD: st.error('File exceeds 60 MB limit')
            else:
                try:
                    if upload.name.lower().endswith('.zip'):
                        with zipfile.ZipFile(io.BytesIO(data)) as z:
                            candidates=[x for x in z.infolist() if not x.is_dir() and x.filename.lower().endswith('.csv') and not x.filename.startswith('/') and '..' not in Path(x.filename).parts and x.file_size<=MAX_UPLOAD]
                            if not candidates: raise ValueError('No CSV under 60 MB uncompressed found in ZIP')
                            chosen=st.selectbox('Choose CSV',range(len(candidates)),format_func=lambda i:candidates[i].filename)
                            with z.open(candidates[chosen]) as f: raw=f.read(MAX_UPLOAD+1)
                    else: raw=data
                    if len(raw)>MAX_UPLOAD: raise ValueError('CSV too large')
                    import pandas as pd
                    cols=pd.read_csv(io.BytesIO(raw),nrows=0).columns.tolist()
                    label=st.selectbox('Class label (optional)',['(none)']+cols)
                    if st.button('Analyze dataset'):
                        profile_csv(raw,None if label=='(none)' else label)
                except Exception as e: st.error(f'Cannot read dataset: {e}')
    with t2:
        with st.form('import_model'):
            name=st.text_input('Model name',placeholder='Edge-IIoTset RF SA-HFS K12')
            dataset=st.selectbox('Training dataset',['Edge-IIoTset','CICIoT2023','TON_IoT','Other'])
            algo=st.selectbox('Algorithm',['Random Forest','XGBoost','LightGBM','Other'])
            model=st.file_uploader('Exported checkpoint (.joblib, .pkl, .json, .ubj, .onnx, .zip)',type=['joblib','pkl','json','ubj','txt','onnx','zip'])
            features=st.text_area('Selected features (one per line; optional)')
            notes=st.text_area('Preprocessing and label mapping notes (optional)')
            submitted=st.form_submit_button('Save model to registry')
        if submitted:
            if not name.strip() or model is None: st.error('Enter a model name and choose a checkpoint file.')
            else:
                try:
                    sha=import_artifact(name.strip(),dataset,algo,model.name,model.getvalue(),[x.strip() for x in features.splitlines() if x.strip()],notes)
                    st.success('Model file stored. SHA256: '+sha[:20]+'… Status: NOT VALIDATED; predictions are disabled.')
                except Exception as e: st.error(str(e))
    with t3:
        with connection() as db:
            rows=db.execute('SELECT id,name,dataset,algorithm,status,size_bytes,created_utc,sha256,features_json FROM models ORDER BY id DESC').fetchall()
        if rows:
            import pandas as pd
            df=pd.DataFrame(rows,columns=['ID','Name','Dataset','Algorithm','Status','Bytes','Imported (UTC)','SHA256','Features JSON'])
            st.dataframe(df,use_container_width=True)
        else: st.info('No imported models yet.')
        st.caption('This release does not run training, model inference, cross-dataset evaluation or live blocking. Those require verified feature/preprocessing compatibility and trusted model loading.')

    with t4:
        st.subheader('SA-HFS v3 Random Forest — 70/30 (existing trained checkpoint)')
        st.caption('Offline CSV inference only. No retraining, no new datasets, no gateway blocking.')
        st.warning('Exploratory results only: uploaded rows may overlap training data. Do not report these metrics as independent research results.')
        upload_rf = st.file_uploader('Upload compatible Edge-IIoTset CSV (up to 60 MB)', type=['csv'], key='edge_rf_csv')
        if upload_rf is not None and st.button('▶ Run saved Random Forest', key='edge_rf_run'):
            try:
                from quantumsafe.edge_rf_inference import predict_csv
                with st.spinner('Running saved model...'):
                    output, metrics = predict_csv(upload_rf.getvalue())
                st.success(f'Predicted {len(output):,} records (first 10,000 rows maximum).')
                counts = output['QuantumSafe_Prediction'].value_counts()
                a, b = st.columns(2)
                a.metric('Normal (0)', int(counts.get(0, 0)))
                b.metric('Attack (1)', int(counts.get(1, 0)))
                st.dataframe(output.head(100), use_container_width=True)
                if metrics:
                    st.subheader('Evaluation (only when Attack_label is 0/1)')
                    mcols = st.columns(4)
                    for col, (key, value) in zip(mcols, [(k,v) for k,v in metrics.items() if k != 'Confusion matrix']):
                        col.metric(key, f'{value:.2%}')
                    st.write('Confusion matrix: rows actual [0,1], columns predicted [0,1]')
                    st.dataframe(__import__('pandas').DataFrame(metrics['Confusion matrix'], index=['Actual 0','Actual 1'], columns=['Predicted 0','Predicted 1']))
                else:
                    st.info('No valid binary Attack_label found. Predictions shown without accuracy metrics.')
                st.download_button('⬇ Download predictions CSV', output.to_csv(index=False).encode('utf-8'), 'QuantumSafe_EdgeIIoT_predictions.csv', 'text/csv', key='edge_rf_download')
            except ImportError as e:
                st.error(f'Missing ML dependency: {e}. Install scikit-learn and joblib in the app virtual environment (see update README).')
            except Exception as e:
                st.error(f'Prediction could not run: {e}')
