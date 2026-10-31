"""Main-app GUI controls for gateway listener, peer tests and SQL audit."""
import socket
import streamlit as st
import pandas as pd
from .. import lan_protocol as p, lan_client, security_events
from ..lan_gateway import GatewayController
from ..permissions import may_manage_users
from . import peer_page


@st.cache_resource
def controller():
    """Keep listener alive across Streamlit reruns and navigation."""
    return GatewayController()


def show(actor):
    st.title('🌐 Two-Computer Secure IoT Lab')
    st.caption('Real communication between Python programs over a PRIVATE LAN. Not an IDS.')
    gateway_tab, sender_tab, logs_tab = st.tabs(['🖥️ Gateway controls', '📡 Send / attack tests', '📋 Security events'])
    with gateway_tab:
        _gateway_controls(actor)
    with sender_tab:
        peer_page.show(inside_main_app=True)
    with logs_tab:
        _events(actor)


def _gateway_controls(actor):
    c = controller()
    st.subheader('Computer A — Gateway (receiver)')
    st.info('This computer runs the receiver. Computer B runs Peer Console (sender). '
            'The *same* secret must be copied to both, using a trusted method.')
    st.metric('Gateway', '🟢 ON' if c.running else '⚪ OFF')
    if c.running:
        st.code(f'Listening: {c.bind}:{c.port} | Port: {c.port}')
        st.caption('If bind is 0.0.0.0, enter Computer A private IPv4 address on Computer B.')
        if c.gateway:
            st.json(c.gateway.snapshot()['counts'], expanded=False)
    if not may_manage_users(actor['RoleName']):
        st.info('Only Admin can start or stop the LAN listener. Researchers can send tests.')
        return
    if 'lab_secret' not in st.session_state:
        st.session_state['lab_secret'] = ''
    if st.button('🎲 Generate strong shared secret', disabled=c.running):
        st.session_state['lab_secret'] = p.generate_secret()
    secret = st.text_input('Shared lab secret (32+ characters)', type='password',
                           key='lab_secret', disabled=c.running)
    if st.checkbox('👁️ Show secret so I can copy it to Computer B') and secret:
        st.code(secret)
    port = st.number_input('Gateway port', min_value=1024, max_value=65535,
                           value=int(c.port or 8765), step=1, disabled=c.running)
    lan = st.checkbox('Allow another computer on my private LAN', value=False,
                      disabled=c.running)
    st.caption('Log out does not stop an already running gateway. Press Stop Gateway when finished.')
    st.warning('Only use an isolated/trusted lab LAN. Do NOT port-forward this service '
               'to the internet. This is an educational prototype, not production security.')
    col1, col2 = st.columns(2)
    if col1.button('▶️ Start Gateway', disabled=c.running, type='primary'):
        try:
            def sink(item):
                security_events.save(int(actor['UserId']), item)
            c.start(secret, int(port), lan, sink, owner_id=int(actor['UserId']))
            st.success('Gateway started. Keep VS Code/Streamlit running.')
            st.rerun()
        except (ValueError, RuntimeError, OSError) as exc:
            st.error(f'Could not start: {exc}')
    if col2.button('⏹️ Stop Gateway', disabled=not c.running):
        c.stop()
        st.success('Gateway stopped.')
        st.rerun()
    if st.button('🔄 Refresh Gateway Status'):
        st.rerun()
    if st.button('📍 Show my computer name / private IP'):
        name = socket.gethostname()
        st.write('Computer name:', name)
        try:
            st.write('Suggested LAN IPv4:', socket.gethostbyname(name))
        except OSError:
            st.info('Open Windows Settings → Network → Properties to find your IPv4 address.')
    if c.running and c.gateway:
        st.subheader('Latest receiver events (in memory)')
        events = c.gateway.snapshot()['events']
        if events:
            st.dataframe(pd.DataFrame(events), hide_index=True, width='stretch')
        else:
            st.info('No messages yet.')


def _events(actor):
    st.subheader('Events stored in SQL Server')
    if not security_events.ready():
        st.error('SecurityEvents table is missing. Run Database/02_upgrade_v02.sql in SSMS.')
        return
    if st.button('🔄 Refresh Saved Events'):
        st.rerun()
    try:
        events = security_events.history(int(actor['UserId']))
    except Exception as exc:
        st.error(f'Could not read events from SQL Server: {exc}')
        return
    if not events:
        st.info('No security events saved yet. Start Gateway, then send a test.')
        return
    df = pd.DataFrame(events)
    st.dataframe(df, hide_index=True, width='stretch')
    st.download_button('⬇️ Export Events CSV', df.to_csv(index=False).encode('utf-8'),
                       'quantumsafe_security_events.csv', 'text/csv')
    st.caption('Stores event type, outcome, time, source IP and algorithm, not readings or keys.')
