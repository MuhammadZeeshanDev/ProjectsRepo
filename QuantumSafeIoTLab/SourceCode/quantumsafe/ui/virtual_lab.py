"""Virtual gateway controls and live monitoring of loopback HTTP events."""
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from ..virtual_gateway_sim import SCENARIOS, evaluate
from ..virtual_network import VirtualGateway
from .. import gateway_event_store as sql_store

@st.cache_resource
def get_gateway():
    return VirtualGateway()


def _event_frame(gateway):
    with gateway.lock:
        snapshot = list(gateway.events)
    return pd.DataFrame(snapshot, columns=['timestamp_utc', 'device', 'decision', 'reason', 'source', 'request_type'])


@st.fragment(run_every='3s')
def live_monitor(gateway):
    st.subheader('📊 Live monitoring · refresh every 3 seconds')
    df = _event_frame(gateway)
    allow = int((df['decision'] == 'ALLOW').sum()) if not df.empty else 0
    blocked = int((df['decision'] == 'BLOCK').sum()) if not df.empty else 0
    a, b, c, d = st.columns(4)
    a.metric('HTTP events (last 200)', len(df))
    b.metric('Allowed', allow)
    c.metric('Blocked / alerts', blocked)
    d.metric('Unique device IDs seen', int(df['device'].nunique()) if not df.empty else 0)
    if df.empty:
        st.info('No HTTP events yet. Start the gateway and send a request. Monitoring updates automatically.')
        return
    st.caption('Counts cover the last 200 events in memory, not the whole network or all-time totals.')
    chart = df['decision'].value_counts().reindex(['ALLOW', 'BLOCK'], fill_value=0)
    st.bar_chart(chart)
    st.subheader('📷 Virtual device activity')
    devices = df[df['device'].astype(str).str.len() > 0].copy()
    if not devices.empty:
        latest = devices.drop_duplicates('device', keep='first')[['device', 'timestamp_utc', 'decision']].copy()
        latest.columns = ['Device ID', 'Last seen (UTC)', 'Last decision']
        st.dataframe(latest, hide_index=True, use_container_width=True)
    st.caption('Last seen means a request was observed; it does NOT mean the device is currently connected.')
    st.subheader('🚨 Security alerts')
    alerts = df[df['decision'] == 'BLOCK']
    if alerts.empty:
        st.success('No blocked requests in the current event window.')
    else:
        st.dataframe(alerts[['timestamp_utc', 'device', 'reason']], hide_index=True, use_container_width=True)
    st.subheader('📝 Recent HTTP events')
    st.dataframe(df, hide_index=True, use_container_width=True)
    st.download_button('⬇️ Export events CSV', df.to_csv(index=False).encode('utf-8'),
                       file_name='quantumsafe_virtual_events.csv', mime='text/csv', key='export_live_http_events')


def show(actor):
    from ..version import APP_VERSION
    st.title(f'🧩 Virtual IoT Security Gateway · v{APP_VERSION}')
    st.info('LOCAL TEST LAB: HTTP requests to 127.0.0.1 only. This is not real router/CCTV packet monitoring or ML-based intrusion detection.')
    gateway = get_gateway()
    st.subheader('🗄️ SQL Server event storage')
    try:
        ready = sql_store.is_initialized()
    except Exception as exc:
        ready = False
        st.error(f'SQL Server unavailable: {type(exc).__name__}: {exc}')
    if ready:
        gateway.event_sink = sql_store.insert_event
        st.success('SQL persistence enabled. New HTTP events are saved to SQL Server.')
    else:
        gateway.event_sink = None
        st.warning('SQL event table is not initialized. Gateway still works in memory.')
        if st.button('🗄️ Initialize SQL event table (one time)'):
            try:
                sql_store.initialize()
                gateway.event_sink = sql_store.insert_event
                st.success('SQL event table initialized. Persistence enabled.')
                st.rerun()
            except Exception as exc:
                st.error(f'Could not initialize SQL table: {type(exc).__name__}: {exc}')
    c1, c2 = st.columns(2)
    if c1.button('🟢 Start local gateway', disabled=bool(gateway.server)):
        try:
            gateway.start()
            st.success('Local HTTP gateway started.')
        except Exception as exc:
            st.error(f'Gateway could not start: {exc}')
    if c2.button('🔴 Stop local gateway', disabled=not bool(gateway.server)):
        gateway.stop()
        st.warning('Local HTTP gateway stopped.')
    st.metric('Gateway status', f'Running on 127.0.0.1:{gateway.port}' if gateway.server else 'Stopped')
    st.subheader('🌐 Send a virtual device request')
    scenario = st.selectbox('Virtual client / test',
        ['CCTV', 'Router', 'Sensor', 'Unauthorized access', 'Tampered message', 'Replay attack', 'Rate limit'])
    if st.button('▶️ Send request', type='primary', disabled=not bool(gateway.server)):
        try:
            event = gateway.send(scenario)
            message = f"{event['decision']} — {event['reason']}"
            (st.success if event['decision'] == 'ALLOW' else st.error)(message)
        except Exception as exc:
            st.error(f'Local request failed: {exc}')
    st.caption('Replay and rate-limit tests may generate multiple events. Rate-limit window is 10 seconds.')
    if gateway.last_persist_error:
        st.error('Last SQL event save failed: ' + gateway.last_persist_error)
    live_monitor(gateway)
    st.divider()
    st.subheader('📚 Persistent SQL Server event history')
    if ready:
        try:
            counts = sql_store.counts()
            c_a, c_b, c_c = st.columns(3)
            c_a.metric('All-time SQL events', counts['total'])
            c_b.metric('All-time allowed', counts['allowed'])
            c_c.metric('All-time blocked', counts['blocked'])
            limit = st.selectbox('SQL history rows to load', [100, 500, 1000, 5000], index=1)
            history = pd.DataFrame(sql_store.recent_events(limit))
            if history.empty:
                st.info('No SQL events saved yet. Send a virtual device request.')
            else:
                st.dataframe(history, hide_index=True, use_container_width=True)
                st.bar_chart(history.groupby(['device', 'decision']).size().unstack(fill_value=0))
                st.download_button('⬇️ Export SQL history CSV', history.to_csv(index=False).encode('utf-8'),
                                   file_name='quantumsafe_sql_events.csv', mime='text/csv', key='export_sql_events')
        except Exception as exc:
            st.error(f'Unable to load SQL history: {type(exc).__name__}: {exc}')
    else:
        st.info('Initialize the SQL event table to enable permanent event history.')
    st.divider()
    with st.expander('Older offline policy simulation (v0.2.2)'):
        old = st.selectbox('Offline scenario', list(SCENARIOS))
        if st.button('Run offline simulation'):
            st.json(evaluate(old))
    st.warning('Monitoring covers only this app’s local HTTP test gateway. Live panel uses last 200 in-memory events. SQL history survives restart when enabled. No packet sniffing, ML IDS, or network-wide firewall is included.')
