"""Virtual gateway controls and live monitoring of loopback HTTP events."""
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from ..virtual_gateway_sim import SCENARIOS, evaluate
from ..virtual_network import VirtualGateway
from .. import gateway_event_store as sql_store
from ..message_policy import assess_content
import base64, io, math, struct, wave
import streamlit.components.v1 as components

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
        st.dataframe(alerts[['timestamp_utc', 'device', 'reason', 'source']], hide_index=True, use_container_width=True)
    st.subheader('📝 Recent HTTP events')
    st.dataframe(df, hide_index=True, use_container_width=True)
    st.download_button('⬇️ Export events CSV', df.to_csv(index=False).encode('utf-8'),
                       file_name='quantumsafe_virtual_events.csv', mime='text/csv', key='export_live_http_events')




def _alarm_html():
    """Generate a short local WAV; audio playback requires browser permission."""
    rate=16000
    samples=[]
    for i in range(int(rate*.65)):
        tone=0.35*math.sin(2*math.pi*880*i/rate) if (i//2400)%2==0 else 0
        samples.append(struct.pack('<h',int(32767*tone)))
    out=io.BytesIO()
    with wave.open(out,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(b''.join(samples))
    audio=base64.b64encode(out.getvalue()).decode('ascii')
    return f'<audio controls autoplay><source src="data:audio/wav;base64,{audio}" type="audio/wav"></audio>'

def message_test(gateway):
    st.subheader('🚨 Suspicious message / link test')
    st.caption('Paste text or a URL. The lab checks local demonstration rules; it never opens the link. BLOCK applies only inside this lab, not to your browser or network.')
    value=st.text_area('Message or URL',placeholder='Example: Urgent bank verification: send your password',key='qs_manual_content')
    if st.button('🔍 Check & test alert',type='primary',key='qs_check_content'):
        try:
            event=assess_content(value)
            with gateway.lock:
                gateway.events.appendleft(event)
            if gateway.event_sink:
                try:
                    gateway.event_sink(event)
                    gateway.last_persist_error=None
                except Exception as exc:
                    gateway.last_persist_error=f'{type(exc).__name__}: {exc}'
            if event['decision']=='BLOCK':
                st.error('🔴 BLOCK — '+event['reason'])
                components.html(_alarm_html(),height=70)
                st.warning('If you hear no sound, click the audio play control. Browsers can prevent automatic sound.')
            else:
                st.success('🟢 ALLOW in this simple rule demo — no configured pattern matched.')
                st.warning('ALLOW does NOT mean a link is safe. Unknown phishing links may pass these basic rules.')
        except ValueError as exc:st.warning(str(exc))


def show(actor):
    from ..version import APP_VERSION
    st.title(f'🧩 Virtual IoT Security Gateway · v{APP_VERSION}')
    st.info('LOCAL TEST LAB: HTTP requests to 127.0.0.1 only. Rule-based gateway monitoring; the Edge-IIoTset ML model is a separate offline CSV analysis tool.')
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
            gateway.start(port=8765)
            st.success('Local HTTP gateway started.')
        except Exception as exc:
            st.error(f'Gateway could not start: {exc}')
    if c2.button('🔴 Stop local gateway', disabled=not bool(gateway.server)):
        gateway.stop()
        st.warning('Local HTTP gateway stopped.')
    st.metric('Gateway status', f'Running on 127.0.0.1:{gateway.port}' if gateway.server else 'Stopped')
    st.caption('Independent attacker console: open a second terminal and run SourceCode/attacker_console.py. It uses port 8765 and receives NO trusted credentials. Localhost is one PC, not a separate network host.')
    message_test(gateway)
    st.divider()
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
    with st.expander('🧪 Why was this request allowed or blocked?'):
        st.write('CCTV/Router/Sensor: valid token + valid HMAC signature + unused nonce + within rate limit → ALLOW.')
        st.write('Unauthorized: wrong token → BLOCK. Tampered: message changed after signing → BLOCK. Replay: reused nonce → BLOCK. Rate limit: more than 8 requests per 10 seconds → BLOCK.')
        st.caption('These are application-level HTTP rules, NOT Random Forest predictions or captured network packets.')
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
    st.warning('Monitoring covers only this app’s local HTTP test gateway. Live panel uses last 200 in-memory events. SQL history survives restart when enabled. No packet sniffing, ML IDS, or network-wide firewall is included.')
