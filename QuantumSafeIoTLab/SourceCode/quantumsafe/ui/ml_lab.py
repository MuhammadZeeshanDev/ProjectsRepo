"""Safe ML artifact registry + CSV/ZIP profiling. No untrusted pickle execution."""
import csv, hashlib, io, json, os, re, shutil, sqlite3, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st

BASE = Path(__file__).resolve().parents[3]
STORE = BASE / 'ML_Artifacts'
DB = STORE / 'registry.sqlite3'
MAX_UPLOAD = 1024 * 1024 * 1024
MAX_EXTRACT = 1024 * 1024 * 1024

def connection():
    STORE.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.execute('CREATE TABLE IF NOT EXISTS models (id INTEGER PRIMARY KEY, name TEXT NOT NULL, dataset TEXT, algorithm TEXT, filename TEXT NOT NULL, sha256 TEXT NOT NULL, size_bytes INTEGER, status TEXT NOT NULL, features_json TEXT, notes TEXT, created_utc TEXT NOT NULL)')
    db.commit()
    return db

def safe_name(s):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', str(s))[:100]

def import_artifact(name, dataset, algorithm, file_name, data, features, notes):
    if not data or len(data) > 60 * 1024 * 1024: raise ValueError('Model checkpoint exceeds 60 MB; this restriction is for model imports only.')
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
    if not raw: raise ValueError('Dataset is empty.')
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
        st.caption('Dataset profile: previews first 10,000 rows. For large datasets use the Prediction tab for full processing.')
        upload=st.file_uploader('Choose CSV for sample profiling (up to 1 GB with large-file launcher)',type=['csv'],key='ml_dataset')
        if upload is not None:
            try:
                import pandas as pd
                upload.seek(0)
                cols=pd.read_csv(upload,nrows=0).columns.tolist()
                label=st.selectbox('Class label (optional)',['(none)']+cols)
                if st.button('Analyze dataset'):
                    upload.seek(0)
                    frame=pd.read_csv(upload,nrows=10000,low_memory=False)
                    if frame.empty: raise ValueError('CSV is empty')
                    st.caption('Statistics below describe only the first 10,000 rows.')
                    a,b,c=st.columns(3)
                    a.metric('Sample rows',len(frame));b.metric('Columns',len(frame.columns));c.metric('Duplicate sample rows',int(frame.duplicated().sum()))
                    st.dataframe(frame.head(20),use_container_width=True)
                    stats=pd.DataFrame({'column':frame.columns,'type':[str(t) for t in frame.dtypes],'missing':[int(frame[x].isna().sum()) for x in frame.columns]})
                    st.dataframe(stats,use_container_width=True)
                    if label != '(none)': st.bar_chart(frame[label].astype(str).value_counts().head(30))
                    st.download_button('Download sample quality report',stats.to_csv(index=False).encode(),'quality_report.csv','text/csv')
            except Exception as e: st.error(f'Cannot profile CSV: {e}')
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
        st.subheader('SA-HFS v3 Random Forest — 70/30')
        st.caption('Uses your existing saved model. No retraining or automatic gateway blocking.')
        st.warning('Metrics from arbitrary CSV rows are exploratory, not independent research validation.')
        import sklearn
        st.caption(f'Installed scikit-learn: {sklearn.__version__}')
        st.info('Upload a large Edge-IIoTset CSV (up to 1 GB when launched with the large-file command), or enter its local Windows path. Predictions process 10,000 rows at a time.')
        local_path = st.text_input('Local CSV full path (Windows)', placeholder=r'D:\Datasets\Edge_IIoTset_Cleaned.csv', key='edge_rf_local_path')
        uploaded = st.file_uploader('Or upload Edge-IIoTset CSV (up to 1 GB with large-file launcher)', type=['csv'], key='edge_rf_csv')
        if st.button('▶ Run saved Random Forest', key='edge_rf_run'):
            try:
                from quantumsafe.edge_rf_inference import predict_local_csv, predict_csv
                if local_path.strip():
                    with st.spinner('Processing local CSV in batches. This can take a while...'):
                        result = predict_local_csv(local_path.strip().strip('"'))
                    st.session_state['edge_rf_result'] = result
                elif uploaded is not None:
                    import tempfile
                    from pathlib import Path
                    with st.spinner('Saving upload temporarily and predicting in 10,000-row batches...'):
                        with tempfile.NamedTemporaryFile(prefix='quantumsafe_uploaded_', suffix='.csv', delete=False) as tmp:
                            temp_path = Path(tmp.name)
                            try:
                                uploaded.seek(0)
                                while True:
                                    block = uploaded.read(4 * 1024 * 1024)
                                    if not block: break
                                    tmp.write(block)
                            except Exception:
                                temp_path.unlink(missing_ok=True)
                                raise
                        try:
                            result = predict_local_csv(str(temp_path))
                        finally:
                            temp_path.unlink(missing_ok=True)
                    st.session_state['edge_rf_result'] = result
                else:
                    st.error('Enter a local CSV path or upload a CSV.')
            except AttributeError as e:
                if '_RemainderColsList' in str(e):
                    st.error('Model was saved using a different scikit-learn version. Install the matching training version in the app virtual environment, then restart the app. See update README for commands.')
                else:
                    st.error(f'Prediction failed: {e}')
            except Exception as e:
                st.error(f'Prediction failed: {e}')
        result = st.session_state.get('edge_rf_result')
        if result:
            st.success(f"Processed {result['rows']:,} records")
            a,b = st.columns(2)
            a.metric('Normal (0)',result['counts'].get(0,0))
            b.metric('Attack (1)',result['counts'].get(1,0))
            st.dataframe(result['preview'],use_container_width=True)
            metrics = result.get('metrics')
            if metrics:
                st.subheader('Exploratory evaluation')
                for key in ('Accuracy','Precision (attack=1)','Recall (attack=1)','F1 (attack=1)'):
                    st.metric(key, f"{metrics[key]:.2%}")
                st.write('Confusion matrix (rows actual 0/1, columns predicted 0/1)')
                import pandas as pd
                st.dataframe(pd.DataFrame(metrics['Confusion matrix'],index=['Actual 0','Actual 1'],columns=['Predicted 0','Predicted 1']))
            if 'csv_bytes' in result:
                st.download_button('⬇ Download predictions CSV',result['csv_bytes'],'QuantumSafe_predictions.csv','text/csv')
            elif 'output_path' in result:
                st.info('Full predictions CSV saved locally at: '+result['output_path'])
                st.caption('Large files are saved to disk instead of being loaded into browser memory.')
