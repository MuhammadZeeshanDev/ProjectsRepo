"""Admin-only separation of models, datasets, splits, folds, and evidence provenance."""
import io,json,csv
import streamlit as st
import pandas as pd
from .. import research_catalog as catalog
from . import ml_lab
def show_evidence():
    st.subheader('Existing benchmark evidence · kept separate by model, split and fold')
    st.caption('Historical experiment records are evidence, not live predictions.')
    edition=st.selectbox('Protocol',list(catalog.DATASETS),key='rs_ed')
    version=catalog.DATASETS[edition]
    table=st.selectbox('Result table',list(catalog.FILES[version]),key='rs_tab')
    try: rows=catalog.load(version,table)
    except (FileNotFoundError,ValueError) as e:st.error('Evidence files unavailable: '+str(e));return
    if not rows:st.warning('No rows in this table');return
    c1,c2,c3=st.columns(3)
    model=c1.selectbox('Model',['All']+catalog.options(rows,'Model'),key='rs_model')
    split=c2.selectbox('Split',['All']+catalog.options(rows,'Split'),key='rs_split')
    fold=c3.selectbox('Fold',['All']+catalog.options(rows,'Fold'),key='rs_fold')
    balancing=st.selectbox('Balancing',['All']+catalog.options(rows,'Balancing'),key='rs_balancing')
    selection=catalog.select(rows,model=None if model=='All' else model,split=None if split=='All' else split,fold=None if fold=='All' else fold,balancing=None if balancing=='All' else balancing)
    st.caption(f'{len(selection)} of {len(rows)} source records; SHA256 {catalog.file_sha256(version,table)[:16]}…')
    if selection:
        st.dataframe(pd.DataFrame(selection),use_container_width=True,height=320)
        st.download_button('Export filtered CSV',pd.DataFrame(selection).to_csv(index=False).encode(),'filtered_experiments.csv','text/csv')
    else:st.warning('No matching records')

def show(actor):
    if actor.get('RoleName')!='Admin':st.error('Administrator only');return
    show_evidence()
