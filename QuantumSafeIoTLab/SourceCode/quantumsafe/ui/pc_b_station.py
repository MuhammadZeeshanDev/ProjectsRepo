"""Restore independent PC B security-test station in Administrator navigation."""
import streamlit as st

def show(actor):
    if actor.get('RoleName')!='Admin':st.error('Administrator only');return
    st.title('🧪 PC B — Independent Security Testing')
    st.info('PC B is an isolated UNTRUSTED attacker simulation, not the real network connection and not a device installer. For virtual device enrollment use Devices & Installation.')
    from ..pc_b_launcher import console_is_running,launch_console
    st.metric('PC B console','🟢 AVAILABLE' if console_is_running() else '⚪ NOT RUNNING')
    if st.button('💻 Start / Open PC B Test Station',type='primary'):
        try:
            address=launch_console(open_browser=True)
            st.success('Independent PC B station ready: '+address)
        except Exception as exc:st.error(f'{type(exc).__name__}: {exc}')
    st.link_button('Open existing PC B console','http://127.0.0.1:8502')
    st.caption('PC B sends untrusted requests to the virtual gateway on 127.0.0.1:8765. Both simulated stations run on one PC by default. Physical two-PC LAN support needs separate secure provisioning and network configuration.')
    st.caption('Windows shortcut: SourceCode/Launch_PC_B.pyw')
