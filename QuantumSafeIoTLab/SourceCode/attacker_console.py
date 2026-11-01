"""Separate-process virtual PC B; no defender session, token, or signing key."""
import streamlit as st
from quantumsafe.attacker_client import TESTS, send_test

st.set_page_config(page_title='QuantumSafe — Virtual PC B', page_icon='🧪')
st.title('🧪 Virtual PC B — Independent Test Console')
st.warning('Authorized LOCAL lab only. Requests are restricted to 127.0.0.1:8765. No access to defender secrets.')
st.write('**Target:** Virtual CCTV 01  |  **Gateway:** 127.0.0.1:8765')
st.info('Step 1: Choose a controlled test. Step 2: Review the request. Step 3: Send it. Step 4: Inspect defender alerts and event history.')
selected = st.selectbox('Choose controlled test', list(TESTS), format_func=lambda k: TESTS[k])
st.markdown('**What PC B sends:** a telemetry request naming CCTV-01, with an untrusted token and no valid device signature. PC B never receives the defender key.')
st.caption('The gateway first checks device registration, then credentials and message integrity. The response records why access was denied.')
if st.button('▶ Send test request', type='primary'):
    try:
        results = send_test(selected)
        for event in results:
            if event['decision'] == 'BLOCK':
                st.error(f"BLOCK — {event['reason']}")
            else:
                st.warning(f"Unexpected {event['decision']} — {event['reason']}")
        st.caption(f'{len(results)} request(s) sent. Open the defender Gateway & Alerts screen to inspect SQL/event history.')
    except Exception as exc:
        st.error(f'{type(exc).__name__}: {exc}')
st.info('Unknown source is denied because it has no valid token. IP reputation, packet capture, ML and automatic retraining are NOT implemented in this release.')
