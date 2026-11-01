"""Home dashboard with honest, source-separated monitoring."""
import streamlit as st
from .. import db, crypto_engine
from ..permissions import may_run
from ..version import APP_VERSION
from .. import gateway_event_store as gateway_store
from .. import ml_run_store

def show(actor):
    st.title(f'🏠 QuantumSafe IoT Lab · v{APP_VERSION}')
    st.write(f"Welcome, **{actor['Username']}** ({actor['RoleName']}).")
    a,b,c=st.columns(3)
    try: ready=db.database_ready()
    except Exception: ready=False
    a.metric('SQL Server', '🟢 Connected' if ready else '🔴 Offline')
    try:
        crypto_engine._engine('ML-KEM-512'); crypt='🟢 Installed'
    except Exception: crypt='🔴 Unavailable'
    b.metric('ML-KEM library',crypt)
    c.metric('App version',APP_VERSION)
    st.subheader('🌐 Local virtual gateway — SQL event history')
    try:
        if gateway_store.is_initialized():
            counts=gateway_store.counts()
            cols=st.columns(3)
            cols[0].metric('Stored gateway events',counts['total'])
            cols[1].metric('Allowed requests',counts['allowed'])
            cols[2].metric('Blocked requests',counts['blocked'])
            st.caption('These are rule-based decisions from the **local simulated HTTP gateway**, not ML predictions or live internet attacks.')
        else: st.info('Gateway event table not initialized. Open Virtual Gateway to initialize it.')
    except Exception as exc: st.warning(f'Gateway SQL summary unavailable: {type(exc).__name__}')
    st.subheader('🤖 Offline Edge-IIoTset model — saved runs')
    try:
        if ml_run_store.is_initialized():
            runs=ml_run_store.recent_runs(10)
            if runs:
                latest=runs[0]
                x,y,z=st.columns(3)
                x.metric('Latest run rows',f"{latest['rows_processed']:,}")
                y.metric('Predicted normal',f"{latest['normal_count']:,}")
                z.metric('Predicted attack',f"{latest['attack_count']:,}")
                st.dataframe(runs,hide_index=True,use_container_width=True)
            else: st.info('No ML runs saved yet. Run a compatible CSV in ML Lab.')
        else: st.info('ML history not initialized. Open ML Lab to enable saving run summaries.')
    except Exception as exc: st.warning(f'ML SQL history unavailable: {type(exc).__name__}')
    st.warning('Lab simulation and offline ML classification are separate. No real device packet capture, automatic ML gateway blocking or production firewall is implemented.')
    if may_run(actor['RoleName']):
        st.subheader('▶ Team demo shortcuts')
        for label,page in [('📘 Start Here','📘 Start Here'),('🧩 Virtual Gateway','🧩 Virtual Gateway'),('🤖 ML Lab','🤖 ML Lab')]:
            if st.button(label,key='home_'+page):
                st.session_state['nav_page']=page
                st.rerun()
