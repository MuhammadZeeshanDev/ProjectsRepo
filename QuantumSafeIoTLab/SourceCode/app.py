"""QuantumSafe v1.7: operator UI is monitoring-only, training lives on admin CLI."""
import streamlit as st
from importlib.util import find_spec
from quantumsafe.version import APP_VERSION
from quantumsafe import users
from quantumsafe.permissions import may_manage_users
from quantumsafe.ui import login, admin_page, security_monitor

st.set_page_config(page_title=f'QuantumSafe Security v{APP_VERSION}',page_icon='🔐',layout='wide')
actor_id=st.session_state.get('actor_id')
if not actor_id:
    login.show();st.stop()
try:
    actor=users.active_actor(int(actor_id))
except Exception:
    st.session_state.pop('actor_id',None)
    st.warning('Please sign in again.');st.stop()
role=actor.get('RoleName')
if role not in ('Admin','Researcher'):
    st.session_state.clear();st.error('Account role not supported.');st.stop()
st.sidebar.title(f'🔐 QuantumSafe v{APP_VERSION}')
st.sidebar.caption(f"{actor['Username']} · {'Administrator' if role=='Admin' else 'Security Operator'}")
options=['📊 Security Monitoring']
if may_manage_users(role):options+=['🌐 Gateway & Devices', '👥 Team Accounts']
page=st.sidebar.radio('Navigation',options,key='qs_monitor_nav')
if st.sidebar.button('🚪 Log out'):
    st.session_state.clear();st.rerun()
st.sidebar.caption('Local ML administration: manage_ml.py on administrator PC only')
if page=='👥 Team Accounts' and role=='Admin':
    admin_page.show(actor)
elif page=='🌐 Gateway & Devices' and role=='Admin':
    from quantumsafe.ui import virtual_lab
    if find_spec('quantumsafe.ui.lan_lab_page') is not None:
        from quantumsafe.ui import lan_lab_page
        tab1,tab2=st.tabs(['Manage virtual devices','Virtual gateway controls'])
        with tab1:lan_lab_page.show(actor)
        with tab2:virtual_lab.show(actor)
    else:
        virtual_lab.show(actor)
else:
    security_monitor.show(actor)
