"""QuantumSafe: focused beginner-friendly IoT security lab."""
import streamlit as st
from quantumsafe.version import APP_VERSION
from quantumsafe import users
from quantumsafe.permissions import may_run, may_manage_users
from quantumsafe.ui import login, dashboard, virtual_lab, ml_lab, demo, lan_page, admin_page, research_studio, ai_advisor_page
st.set_page_config(page_title=f'QuantumSafe IoT Lab v{APP_VERSION}', page_icon='🔐',layout='wide')
actor_id=st.session_state.get('actor_id')
if not actor_id:
    login.show(); st.stop()
try:
    actor=users.active_actor(int(actor_id))
except Exception:
    st.session_state.pop('actor_id',None)
    st.warning('Sign in again.'); st.stop()
st.sidebar.title(f'🔐 QuantumSafe v{APP_VERSION}')
st.sidebar.caption(f"{actor['Username']} · {'Administrator' if actor['RoleName']=='Admin' else 'Security Operator' if actor['RoleName']=='Researcher' else 'Read-only Observer'}")
options=['🏠 Overview']
if may_run(actor['RoleName']):
    options+=['🛡️ Device Security & Tests']
if actor['RoleName']=='Admin':
    options+=['🧬 ML Research Studio','✨ AI Research Advisor','🤖 Model Training','🔒 Secure Connection Lab','🌐 LAN Lab']
if may_manage_users(actor['RoleName']):options+=['👥 Team Accounts']
page=st.sidebar.radio('Lab screens',options,key='nav_page')
if st.sidebar.button('🚪 Log out'):
    st.session_state.clear();st.rerun()
st.sidebar.caption('Virtual demonstrations only · not a browser firewall')
if page=='🏠 Overview':dashboard.show(actor)
elif page=='🛡️ Device Security & Tests':virtual_lab.show(actor)
elif page=='🧬 ML Research Studio':research_studio.show(actor)
elif page=='✨ AI Research Advisor':ai_advisor_page.show(actor)
elif page=='🤖 Model Training':ml_lab.show(actor)
elif page=='🔒 Secure Connection Lab':demo.show(actor)
elif page=='🌐 LAN Lab':lan_page.show(actor)
elif page=='👥 Team Accounts':admin_page.show(actor)
