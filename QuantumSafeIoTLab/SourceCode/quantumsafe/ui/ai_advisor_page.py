"""Offline local AI & Prolog reasoning inside Administrator's ML Lab."""
import streamlit as st
from ..local_prolog_ai import analyze

def show_embedded(actor):
    if actor.get('RoleName') != 'Admin':
        st.error('Administrator only.')
        return
    st.subheader('🧠 Local AI + Prolog Security Advisor')
    st.caption('100% local evidence analysis. No API key, internet or cloud AI required. Prolog applies explainable security rules; it is not a generative language model.')
    result=st.session_state.get('qs_training_result')
    events=[]
    try:
        from .virtual_lab import get_gateway, snapshot_events
        # Avoid creating/starting the gateway merely to load the AI page.
        from .. import virtual_network
        from .virtual_lab import get_gateway
        # Gateway object is cached across pages; constructing it does not start the HTTP listener.
        gateway=get_gateway()
        events=snapshot_events(gateway)
    except Exception as exc:
        st.caption('Live gateway event evidence unavailable: '+type(exc).__name__)
    output=analyze(result,events)
    a,b,c=st.columns(3)
    a.metric('Local model trained', 'Yes' if output['evidence']['has_training'] else 'No')
    b.metric('Recent gateway events',output['evidence']['recent_gateway_events'])
    c.metric('Blocked events',output['evidence']['blocked_events'])
    if output['engine'].startswith('SWI-Prolog'):
        st.success('Reasoning engine: SWI-Prolog — running locally')
    else:
        st.warning('Reasoning engine: local Python rules fallback. Install SWI-Prolog and add swipl to PATH to run native Prolog rules.')
    if output['diagnostic']:st.caption(output['diagnostic'])
    st.markdown('**Evidence-backed recommendations**')
    for row in output['recommendations']:
        with st.expander(row['title'], expanded=row['rule']=='live_unverified'):
            st.write(row['action'])
            st.caption('Applied rule: '+row['rule'])
    with st.expander('Data used (local only)'):
        st.json(output['evidence'])
        st.caption('Input: latest training session metrics and last 200 in-memory gateway events. No raw data rows, model binaries or secrets are loaded by the advisor.')
    st.download_button('Export local AI assessment (JSON)', __import__('json').dumps(output,indent=2).encode('utf-8'),
                       'quantumsafe_local_ai_report.json', 'application/json')
    st.info('The advisor explains available evidence. It cannot automatically retrain models, identify unknown threats with a language model, or claim live ML prediction. Model evaluation and deployment require explicit administrator action.')

def show(actor):
    show_embedded(actor)
