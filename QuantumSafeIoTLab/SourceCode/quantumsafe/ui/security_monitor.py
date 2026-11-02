"""Read-only operational monitoring for every signed-in user.

No CSV uploads, ML training controls, Prolog commands or arbitrary file loading.
"""
from __future__ import annotations
import pandas as pd
from datetime import datetime, timezone
import streamlit as st
from ..version import APP_VERSION


def _render():
    from .. import gateway_event_store, db
    from ..ml_engine import registry
    st.subheader('🟢 Local Security Monitoring')
    st.caption('Virtual gateway observations and offline/shadow IDS results. Not a verified whole-network firewall.')
    status='Unavailable';gateway_events=[]
    try:
        status='Connected' if db.database_ready() else 'Unavailable'
        if status=='Connected' and gateway_event_store.is_initialized():
            gateway_events=gateway_event_store.recent_events(150)
    except Exception:
        pass
    model_rows=[];route_rows=[];prediction_rows=[]
    try:
        model_rows=registry.models()
        route_rows=registry.active_routes()
        prediction_rows=registry.recent_predictions(100)
    except Exception as exc:
        st.warning('Local IDS engine data unavailable: '+type(exc).__name__)
    a,b,c,d=st.columns(4)
    a.metric('SQL Server',status)
    b.metric('Saved IDS models',len(model_rows))
    c.metric('Shadow model routes',len(route_rows))
    d.metric('Security incidents (recent SQL)',sum(str(x.get('decision'))=='BLOCK' for x in gateway_events))
    if gateway_events:
        try:
            from ..ml_engine.incidents import audit
            severity=audit(gateway_events)
            at_risk=[{'Device':dev,'Severity':row['severity'].upper(),
                      'Blocked':row['blocked'],
                      'Recommended review':', '.join(row['recommendations'])}
                     for dev,row in severity['devices'].items()]
            if at_risk:
                if any(x['Severity']=='CRITICAL' for x in at_risk):
                    st.error('🚨 CRITICAL gateway incident pattern recorded. Contact your configured security responder immediately.')
                elif any(x['Severity']=='HIGH' for x in at_risk):
                    st.warning('⚠️ HIGH gateway incident pattern. Security review recommended.')
                st.caption('Policy decision engine: '+severity['engine']+' · Recommendations are read-only.')
                st.dataframe(pd.DataFrame(at_risk),hide_index=True,use_container_width=True)
        except Exception as exc:
            st.warning('Security policy evidence unavailable: '+type(exc).__name__)
    if route_rows:
        st.subheader('🧠 Active model-selection advice (Prolog / local rules)')
        st.caption('Selected routes are for compatible input in SHADOW mode only. They do not block network traffic.')
        st.dataframe(pd.DataFrame([{'Threat':r['threat'],'Best model ID':r['model_id'],
                                   'Selector':r['engine'],'Selected UTC':r['selected_utc']} for r in route_rows]),
                     hide_index=True,use_container_width=True)
    else:
        st.info('No trusted model routes selected yet. Administrator trains and ranks models locally in backend.')
    st.subheader('📡 Device observations')
    # An IP/device in the event store is an observation, NOT automatic physical enrollment.
    if gateway_events:
        latest={}
        for event in gateway_events:
            device=str(event.get('device') or '').strip()
            if device and device not in latest:latest[device]=event
        now=datetime.now(timezone.utc)
        rows=[]
        for device,x in latest.items():
            try:
                stamp=datetime.fromisoformat(str(x.get('timestamp_utc')).replace('Z','+00:00'))
                seconds=max(0,(now-stamp).total_seconds())
            except (ValueError,TypeError): seconds=float('inf')
            trusted=x.get('decision')=='ALLOW'
            rows.append({'Device ID':device,'Source IP (observed)':x.get('source_ip') or 'Unknown',
                         'Connection observation':'Recent trusted event' if trusted and seconds<=30 else 'Not confirmed online',
                         'Last decision':x.get('decision'),'Last seen UTC':x.get('timestamp_utc')})
        st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
        st.caption('A recent allowed request is evidence of activity within 30 seconds, not a continuous device link. IP addresses here are HTTP gateway observations.')
    else:
        st.info('No device activity recorded in SQL Server yet.')
    st.subheader('🚨 Recent gateway activity')
    if gateway_events:
        rows=[{'Time UTC':x.get('timestamp_utc'), 'Device':x.get('device'),
               'Decision':x.get('decision'),'Reason':x.get('reason'),
               'Source IP':x.get('source_ip')} for x in gateway_events[:50]]
        st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    else:
        st.caption('No SQL-backed gateway events available yet. Start and test the virtual gateway separately.')
    st.subheader('📊 Latest ML evidence')
    if model_rows:
        view=[{'Model ID':r['id'],'Algorithm':r['algorithm'],'State':r['status'],
               'Macro F1 (offline)':r['metrics'].get('macro_f1'),
               'Sample rows':r['sample_rows'],'Created UTC':r['created_utc']} for r in model_rows[:10]]
        st.dataframe(pd.DataFrame(view),hide_index=True,use_container_width=True)
    if prediction_rows:
        st.subheader('🔎 Recent offline / external-feed shadow detections')
        st.dataframe(pd.DataFrame(prediction_rows[:35]),hide_index=True,use_container_width=True)
    st.warning('Protection status: actual TCP/MQTT live collection and IPS enforcement are NOT connected yet. Existing virtual HTTP gateway rules operate independently of ML.')


def show(actor):
    st.title(f'🛡️ QuantumSafe IoT Security · v{APP_VERSION}')
    st.caption(f"Signed in: {actor.get('Username','User')} · {'Administrator' if actor.get('RoleName')=='Admin' else 'Security Operator'}")
    if hasattr(st,'fragment'):
        st.fragment(run_every='4s')(_render)()
    else:
        _render()
