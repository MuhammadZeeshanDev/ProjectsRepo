"""One-page Administrator acceptance tests: genuine device authorization, attacks and audio."""
import time
import pandas as pd
import streamlit as st
from .. import device_tests

CASES={
 'valid_signed_telemetry':'✅ Safe device login / signed reading → ALLOW',
 'unauthorized_credentials':'🚫 Wrong device credentials → BLOCK',
 'tampered_signature':'🛡 Signed message modified → BLOCK',
 'replayed_nonce':'🔁 Reused signed nonce → BLOCK',
 'unknown_device':'🔎 Unknown virtual device ID → BLOCK',
}


def show(actor,gw):
    if actor.get('RoleName')!='Admin':st.error('Administrator access required');return
    st.subheader('🧪 Device acceptance & safe-login demo')
    st.caption('Real requests pass through localhost gateway. Success requires ALLOW for authenticated telemetry, and BLOCK for unauthorized attempts.')
    choices=list(gw.registered_devices)
    if not choices:
        st.warning('No active devices enrolled. Install one above.');return
    target=st.selectbox('Choose an enrolled virtual device for tests', choices,
                        format_func=lambda d:f'{gw.registered_devices[d]} ({d})',key='qs_accept_device')
    selected=st.multiselect('Security checks to run',list(CASES),default=['valid_signed_telemetry','unauthorized_credentials'],
                            format_func=lambda k:CASES[k],key='qs_accept_cases')
    left,right=st.columns(2)
    if left.button('▶ Run selected device tests',disabled=not gw.server or not selected,type='primary'):
        results=[]
        for name in selected:
            try:results.append(device_tests.run_case(gw,target,actor,name))
            except Exception as exc:results.append({'device_id':target,'case':name,'passed':False,'actual':'ERROR','expected':'see case','reason':f'{type(exc).__name__}: {exc}'})
        st.dataframe(pd.DataFrame(results),hide_index=True,use_container_width=True)
        if all(r['passed'] for r in results):st.success('All selected checks passed against the real local gateway')
        else:st.error('One or more device tests failed. Inspect reason before trusting protection.')
    if right.button('🔊 TEST WINDOWS SECURITY SIREN',disabled=not gw.server):
        if gw.alarm_engine.test_sound():st.info('Siren queued on the Windows gateway host. See audio diagnostics below.')
        else:st.error('Siren could not be queued')
    engine=gw.alarm_engine
    c1,c2,c3=st.columns(3)
    c1.metric('Threat alerts queued',engine.total_alerts)
    c2.metric('Siren playback completed',engine.played)
    c3.metric('Audio failures',engine.failures)
    if engine.last_error:st.error('Audio backend: '+engine.last_error)
    st.caption('System audio plays on the Windows computer running the gateway. Check Windows volume and output device. Browser dashboard has a separate Sound On button.')
    with st.expander('🔐 Actual SQL account login verification (Administrator only)'):
        st.caption('Uses the real SQL Server login check and audit log. No fake user passwords or demo bypass. Login test does not replace your current session.')
        with st.form('qs_actual_login_check'):
            username=st.text_input('Existing account username',key='qs_test_username')
            password=st.text_input('Account password',type='password',key='qs_test_password')
            clicked=st.form_submit_button('Verify actual user login')
        if clicked:
            if time.monotonic()-st.session_state.get('qs_login_last_attempt',0)<3:
                st.warning('Try again in a few seconds')
            else:
                st.session_state['qs_login_last_attempt']=time.monotonic()
                try:
                    from ..auth import sign_in
                    outcome=sign_in(username,password)
                    if outcome:st.success('ALLOW — verified SQL user: '+outcome['RoleName'])
                    else:st.error('DENY — incorrect credentials or inactive account')
                except Exception as exc:st.error('SQL login test unavailable: '+type(exc).__name__)
    with st.expander('📋 Previous test results (persistent)'):
        h=device_tests.history()
        if h:st.dataframe(pd.DataFrame(h),hide_index=True,use_container_width=True)
        else:st.info('No test runs saved yet.')
