"""One simple entry point for the main application: streamlit run SourceCode/app.py."""
import streamlit as st
from quantumsafe import users
from quantumsafe.permissions import may_run, may_manage_users
from quantumsafe.ui import (
    login, dashboard, demo, benchmark_page, results, admin_page,
    lan_page, test_center, virtual_lab
)

st.set_page_config(page_title='QuantumSafe IoT Lab v0.2.4', page_icon='🔐',
                   layout='wide', initial_sidebar_state='expanded')

actor_id = st.session_state.get('actor_id')
if not actor_id:
    login.show()
    st.stop()

try:
    actor = users.active_actor(int(actor_id))
except Exception:
    st.session_state.pop('actor_id', None)
    st.warning('Please sign in again. Your session may have expired.')
    st.stop()

st.sidebar.title('🔐 QuantumSafe v0.2.4')
st.sidebar.caption(f"{actor['Username']} · {actor['RoleName']}")
options = ['🏠 Dashboard']
if may_run(actor['RoleName']):
    options += ['🔒 Secure Demo', '🌐 LAN Lab', '🧩 Virtual Gateway', '⚡ Run Benchmark', '🧪 Test Center']
options += ['📊 Results']
if may_manage_users(actor['RoleName']):
    options += ['👥 Users']
page = st.sidebar.radio('Open screen', options, key='nav_page')
if st.sidebar.button('🚪 Log out'):
    st.session_state.clear()
    st.rerun()
st.sidebar.divider()
st.sidebar.caption('Local HTTP virtual gateway with live event monitoring. No packet capture or ML IDS yet.')

if page == '🏠 Dashboard':
    dashboard.show(actor)
elif page == '🔒 Secure Demo':
    demo.show(actor)
elif page == '🌐 LAN Lab':
    lan_page.show(actor)
elif page == '🧩 Virtual Gateway':
    virtual_lab.show(actor)
elif page == '⚡ Run Benchmark':
    benchmark_page.show(actor)
elif page == '🧪 Test Center':
    test_center.show(actor)
elif page == '📊 Results':
    results.show(actor)
elif page == '👥 Users':
    admin_page.show(actor)
