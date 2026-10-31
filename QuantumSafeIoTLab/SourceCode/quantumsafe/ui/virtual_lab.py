"""Streamlit demonstration of a virtual gateway, no live network interception."""
import pandas as pd
import streamlit as st
from ..virtual_gateway_sim import SCENARIOS, evaluate


def show(actor):
    st.title('🧩 Virtual IoT Security Gateway')
    st.warning('SIMULATION ONLY: No real packets are captured, routed or blocked. '
               'No ML attack classifier is connected yet. Decisions below are rule-based examples.')
    st.write('Virtual CCTV, router and sensor send simulated events to a gateway policy checker.')
    scenario = st.selectbox('Choose a test', list(SCENARIOS))
    if 'qs_virtual_events' not in st.session_state:
        st.session_state.qs_virtual_events = []
    a, b = st.columns(2)
    if a.button('▶️ Run virtual test', type='primary'):
        event = evaluate(scenario)
        st.session_state.qs_virtual_events.insert(0, event)
        st.session_state.qs_virtual_events = st.session_state.qs_virtual_events[:100]
        if event['decision'] == 'BLOCK':
            st.error(f"🔴 Simulated BLOCK — {event['reason']}")
        else:
            st.success('🟢 Simulated ALLOW — policy checks passed')
    if b.button('🧹 Clear simulated events'):
        st.session_state.qs_virtual_events = []
    events = st.session_state.qs_virtual_events
    c1, c2, c3 = st.columns(3)
    c1.metric('Simulated events', len(events))
    c2.metric('Allowed', sum(x['decision'] == 'ALLOW' for x in events))
    c3.metric('Blocked', sum(x['decision'] == 'BLOCK' for x in events))
    if events:
        df = pd.DataFrame(events)
        st.subheader('📊 Gateway decisions')
        counts = df['decision'].value_counts().reindex(['ALLOW', 'BLOCK'], fill_value=0)
        st.bar_chart(counts)
        st.subheader('📋 Simulated security log')
        st.dataframe(df, hide_index=True, use_container_width=True)
        st.download_button('⬇️ Export simulation CSV', df.to_csv(index=False).encode('utf-8'),
                           'virtual_gateway_simulation.csv', 'text/csv')
    else:
        st.info('Select a scenario and click Run virtual test to see a decision and graph.')
    st.caption('Next phase: isolated virtual network gateway, real traffic collection, '
               'and validated RF/XGBoost/LightGBM models. This page is a safe first UI prototype.')
