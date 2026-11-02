"""QuantumSafe v1.8.0 — admin-driven ML + device installation, operator monitor."""
import streamlit as st
from quantumsafe import users
from quantumsafe.version import APP_VERSION
from quantumsafe.ui import login,admin_page,security_monitor

st.set_page_config(page_title=f'QuantumSafe v{APP_VERSION}',page_icon='🔐',layout='wide')
from quantumsafe.ui.console_theme import apply_theme
apply_theme()
actor_id=st.session_state.get('actor_id')
if not actor_id:login.show();st.stop()
try:actor=users.active_actor(int(actor_id))
except Exception:
    st.session_state.pop('actor_id',None);st.error('Session unavailable; sign in again.');st.stop()
role=actor.get('RoleName')
if role not in ('Admin','Researcher'):
    st.session_state.clear();st.error('Unsupported role');st.stop()
st.sidebar.title('🔐 QuantumSafe IoT Security')
st.sidebar.caption(f"{actor.get('Username')} · {'Administrator' if role=='Admin' else 'Security Operator'}")
options=['📊 Live Security Monitoring']
if role=='Admin':
    options+=['🌐 Devices & Installation','🧠 ML & AI Control','🧪 PC B Security Tests','👥 Team Accounts']
page=st.sidebar.radio('Main panels',options,key='qs_main_nav_v180')
if st.sidebar.button('🚪 Sign out'):
    st.session_state.clear();st.rerun()
if page=='🌐 Devices & Installation':
    from quantumsafe.ui import device_control
    device_control.show(actor)
elif page=='🧠 ML & AI Control':
    from quantumsafe.ui import admin_ml
    admin_ml.show(actor)
elif page=='🧪 PC B Security Tests':
    from quantumsafe.ui import pc_b_station
    pc_b_station.show(actor)
elif page=='👥 Team Accounts':admin_page.show(actor)
else:security_monitor.show(actor)
