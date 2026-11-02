"""Local Prolog + optional on-device language model, integrated inside ML Lab."""
import json
import streamlit as st
from ..local_prolog_ai import analyze
from ..local_ai_runtime import find_prolog, local_models, ask_local_model, evidence_summary


def show_embedded(actor):
    if actor.get('RoleName') != 'Admin':
        st.error('Administrator only.'); return
    st.subheader('🧠 Local AI + SWI-Prolog')
    st.caption('No cloud or API key. Prolog analyzes security facts; optional Ollama adds conversational answers using the same local evidence.')
    prolog_input = st.text_input('SWI-Prolog executable (optional, if automatic detection fails)',
                                placeholder=r'C:\Program Files\swipl\bin\swipl.exe', key='qs_prolog_path')
    executable = find_prolog(prolog_input)
    if executable:
        st.success('SWI-Prolog detected locally: ' + executable)
    else:
        st.warning('SWI-Prolog not found. Python rule fallback remains available; provide path to swipl.exe if installed.')
    training = st.session_state.get('qs_training_result')
    events, event_source = [], 'None'
    try:
        from .virtual_lab import get_gateway, snapshot_events
        events = snapshot_events(get_gateway())
        event_source = 'Gateway memory (max 200)'
    except Exception:
        pass
    st.selectbox('SQL incident history depth (when enabled)', [200, 1000, 5000], index=1, key='qs_prolog_sql_limit')
    if st.checkbox('Include SQL Server gateway history', value=False, help='Read up to 5,000 locally stored events; no cloud transfer'):
        try:
            from ..gateway_event_store import recent_events
            sql_limit = st.session_state.get('qs_prolog_sql_limit', 1000)
            sql_events = recent_events(sql_limit)
            def key(x):
                return (str(x.get('timestamp_utc', ''))[:19], str(x.get('device','')),
                        str(x.get('decision','')), str(x.get('reason','')), str(x.get('source_ip','')))
            seen = {key(x) for x in events}
            events = (events + [x for x in sql_events if key(x) not in seen])[:5000]
            event_source = 'Gateway memory + SQL Server (max 5,000)'
        except Exception as exc:
            st.warning('SQL evidence unavailable: ' + type(exc).__name__)
    inventory, models = [], []
    try:
        from .virtual_lab import get_gateway
        inventory = get_gateway().registry.inventory()
    except Exception:
        pass
    try:
        from .ml_lab import connection
        with connection() as db:
            rows = db.execute('SELECT name,algorithm,status,created_utc FROM models ORDER BY id DESC LIMIT 40').fetchall()
        models = [{'name': r[0], 'algorithm': r[1], 'status': r[2], 'created_utc': r[3]} for r in rows]
    except Exception:
        pass
    # Include locally saved training evidence, including across application restarts.
    try:
        from ..model_lifecycle import list_models
        trusted_models=list_models(limit=40)
        models.extend([{'name':f"Local checkpoint #{r['id']}", 'algorithm':r['algorithm'],
                        'status':r['state'], 'split':r['split'], 'metrics':r['metrics']}
                       for r in trusted_models])
        if training is None and trusted_models:
            # Recovered metrics are real saved evidence; no claim of live model activity.
            from ..model_lifecycle import inspect_model
            last=inspect_model(trusted_models[0]['id'])
            training={'heldout':last['metrics'],'folds':last['folds'],
                      'truncated_to_first_rows':True}
    except (ValueError, OSError, KeyError, ImportError):
        pass
    report = analyze(training, events, prolog_executable=executable or '', devices=inventory, models=models)
    a, b, c = st.columns(3)
    a.metric('ML training evidence', 'Loaded' if report['evidence']['has_training'] else 'Not loaded')
    b.metric('Recent events', report['evidence']['recent_gateway_events'])
    c.metric('Blocked events', report['evidence']['blocked_events'])
    if report['diagnostic']: st.error(report['diagnostic'])
    st.caption('Reasoning engine: ' + report['engine'])
    for row in report['recommendations']:
        with st.expander(row['title']):
            st.write(row['action'])
            st.caption('Triggered rule: ' + row['rule'])
    evidence = evidence_summary(report, models, inventory, event_source, len(events))
    with st.expander('Evidence available to local AI (no credentials)'):
        st.json(evidence)
    st.download_button('Download Prolog assessment JSON', json.dumps(report, indent=2).encode(), 'local_prolog_assessment.json', 'application/json')
    st.divider()
    st.subheader('💬 Ask local AI (optional Ollama model)')
    available = local_models()
    if available:
        chosen = st.selectbox('Installed local model', available)
        question = st.text_area('Ask about folds, errors, device events, or improving model readiness',
                                placeholder='Compare my latest split and fold results; what should be improved?')
        if st.button('Analyze using local AI', type='primary'):
            try:
                with st.spinner('Running local model...'):
                    st.session_state['qs_local_ai_last'] = ask_local_model(question, chosen, evidence)
            except Exception as exc:
                st.error(str(exc))
        if st.session_state.get('qs_local_ai_last'):
            st.markdown(st.session_state['qs_local_ai_last'])
    else:
        st.info('No local Ollama model detected. SWI-Prolog works without it. For conversational AI, install Ollama on PC A and pull a model; no API key is needed.')
    st.warning('AI and Prolog provide local advice based on stored evidence. They never execute model changes automatically or claim live ML coverage.')


def show(actor):
    show_embedded(actor)
