"""QuantumSafe v2.0.0 — supervised virtual IDS/IPS & live monitoring."""
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
options=['📊 Live Security Monitoring','📈 Security Analytics & Charts']
if role=='Admin':
    options+=['🌐 Devices & Installation','🧠 ML & AI Control','🧪 PC B Security Tests','👥 Team Accounts']
page=st.sidebar.radio('Main panels',options,key='qs_main_nav_v180')
if st.sidebar.button('🚪 Sign out'):
    try:
        from quantumsafe.ui.virtual_lab import get_gateway
        viewer=st.session_state.get('qs_monitor_viewer')
        if viewer:get_gateway().revoke_viewer(viewer['token'])
    except Exception:pass
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
elif page=='📈 Security Analytics & Charts':
    from quantumsafe.ui import analytics_panel
    analytics_panel.show(actor)
else:security_monitor.show(actor)
