"""Separate attacker simulation UI: credential-free localhost requests only."""
import streamlit as st
from quantumsafe.attacker_client import DEVICES, TESTS, send_test, send_untrusted_to
st.set_page_config(page_title='QuantumSafe | PC B',page_icon='🧪')
st.title('🧪 PC B · Security Test Station')
st.warning('Controlled simulation only · 127.0.0.1:8765 · No defender credentials or real-device attacks')
device=st.selectbox('1. Choose virtual target',list(DEVICES),format_func=lambda x:DEVICES[x])
test=st.selectbox('2. Choose test',list(TESTS[device]),format_func=lambda x:TESTS[device][x][0])
name,description,affected=TESTS[device][test]
st.info(f'**What this test does:** {description}\n\n**Potentially affected:** {affected}\n\n**Expected defense:** Gateway rejects requests lacking valid device credentials.')
if st.button('▶ 3. Run controlled test',type='primary'):
 try:
  results=send_test(test,device)
  for event in results:
   st.error(f"{event['decision']} · {event['reason']} · {event['device']}") if event['decision']=='BLOCK' else st.warning(str(event))
  st.success(f'{len(results)} request(s) delivered. Review PC A security alerts, alarm and event log.')
 except Exception as exc:st.error(f'{type(exc).__name__}: {exc}')
st.caption('Because this client has no credentials, all scenarios exercise authorization rejection. Tampering/replay require an authorized test harness, not this independent attacker.')

st.divider()
st.subheader('Test a newly registered virtual device')
custom_id = st.text_input('Target device ID (from LAN Lab inventory)', placeholder='virtual-camera-02')
if st.button('Test unauthorized access to this device', disabled=not custom_id):
 try:
  event = send_untrusted_to(custom_id.strip())
  (st.error if event.get('decision')=='BLOCK' else st.warning)(f"{event.get('decision')} · {event.get('reason')} · {event.get('device')}")
 except Exception as exc:
  st.error(f'{type(exc).__name__}: {exc}')
