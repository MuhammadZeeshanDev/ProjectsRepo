"""Focused home screen; detailed instructions live in Documentation/USER_MANUAL.md."""
import streamlit as st
from ..version import APP_VERSION
from .. import db, gateway_event_store, ml_run_store

def show(actor):
    st.title(f'QuantumSafe IoT Lab · v{APP_VERSION}')
    st.write('**Virtual IoT security training lab** — send test requests, observe gateway decisions, run the existing Edge-IIoTset model, and review saved activity.')
    st.caption('Role: '+actor['RoleName']+' | Live browser/network blocking is not implemented.')
    try:
        online=db.database_ready()
    except Exception:online=False
    a,b=st.columns(2)
    a.metric('SQL Server','Connected' if online else 'Unavailable')
    try:
        c=gateway_event_store.counts() if gateway_event_store.is_initialized() else None
        b.metric('Gateway blocked events (SQL)',c['blocked'] if c else 'Not initialized')
    except Exception:b.metric('Gateway blocked events (SQL)','Unavailable')
    st.subheader('Practical demo order')
    st.write('**1. Gateway & Alerts:** test normal request, suspicious message, unauthorized request, and audible alarm.')
    st.write('**2. ML Detection:** analyze Edge-IIoTset CSV with the saved Random Forest. This is offline, not live gateway ML.')
    st.write('**3. ML-KEM Secure Demo:** compare secure key establishment using 512, 768 and 1024.')
    st.write('**4. Manage Users (Admin):** create users and assign roles; no self-registration.')
    st.info('Separate user manual: Documentation/USER_MANUAL.md')
