"""Admin-only separation of models, datasets, splits, folds, and evidence provenance."""
import io,json,csv
import streamlit as st
import pandas as pd
from .. import research_catalog as catalog
from . import ml_lab
def show(actor):
    if actor.get('RoleName')!='Admin':
        st.error('Only Administrator can access ML Research Studio.');return
    st.title('🧬 ML Research Studio · SA-HFS')
    st.info('Evidence browser — historical results, NOT live predictions. Model families, split ratios and every CV fold stay separate. v3 and v4 are distinct research protocols.')
    t1,t2,t3=st.tabs(['📊 Research evidence','📦 Actual model checkpoints','⚠️ Deployment boundaries'])
    with t1:
        edition=st.selectbox('Research edition',list(catalog.DATASETS),key='rs_ed')
        edition_key=catalog.DATASETS[edition]
        table=st.selectbox('Result type',list(catalog.FILES[edition_key]),key='rs_tab')
        data=catalog.load(edition_key,table)
        if not data:
            st.warning('No rows in selected evidence.');return
        model=st.selectbox('Model / algorithm',['All']+catalog.options(data,'Model'),key='rs_model')
        split=st.selectbox('Training / validation split',['All']+catalog.options(data,'Split'),key='rs_split')
        balancing=st.selectbox('Balancing',['All']+catalog.options(data,'Balancing'),key='rs_balancing')
        fold=st.selectbox('Cross-validation fold',['All']+catalog.options(data,'Fold'),key='rs_fold')
        method=st.selectbox('Feature selection method',['All']+catalog.options(data,'Method'),key='rs_method')
        rows=catalog.select(data,model=None if model=='All' else model,split=None if split=='All' else split,fold=None if fold=='All' else fold,balancing=None if balancing=='All' else balancing,method=None if method=='All' else method)
        st.caption(f'{len(rows)} of {len(data)} recorded rows · source SHA256 {catalog.file_sha256(edition_key,table)[:16]}…')
        if rows:
            frame=pd.DataFrame(rows)
            st.dataframe(frame,use_container_width=True,height=370)
            for metric in ('Macro_F1','FPR','Accuracy'):
                s=catalog.report(rows,metric)
                if s['n']:st.metric(f'{metric} · mean across {s["n"]} records',f'{s["average"]:.5f}')
            if 'Fold' in frame.columns and 'Macro_F1' in frame.columns:
                graph=frame[['Fold','Model','Macro_F1']].copy();graph['Macro_F1']=pd.to_numeric(graph['Macro_F1'],errors='coerce');graph=graph.dropna()
                if not graph.empty:st.line_chart(graph.pivot_table(index='Fold',columns='Model',values='Macro_F1',aggfunc='mean'))
            output=io.StringIO();writer=csv.DictWriter(output,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            st.download_button('Download exactly these filtered evidence rows',output.getvalue().encode(),'research_filtered.csv','text/csv')
        else:st.warning('No matching records. Try another fold, split or model.')
        st.caption('Held-out sets and cross-validation folds are different evaluation procedures. Never pool their metrics into a single claimed score.')
    with t2:
        st.warning('Only an exported compatible trained checkpoint enables inference. Research CSVs do not contain a trained model. Other missing checkpoints must be imported separately; do not relabel RF as XGBoost or LightGBM.')
        ml_lab.show(actor)
    with t3:
        st.markdown('**Historical evidence:** v3 and v4 metrics are preserved separately, including both 70/30 and 80/20 splits and original/ROS balancing where recorded.')
        st.markdown('**Live gateway:** HTTP telemetry has no raw TCP/MQTT capture. These classifiers cannot validly score it without a real compatible feature extraction pipeline.')
        st.markdown('**Checkpoint safety:** Imported pickle/joblib artifacts must never be auto-executed. Use known-origin hashes and a trusted isolated evaluator.')
