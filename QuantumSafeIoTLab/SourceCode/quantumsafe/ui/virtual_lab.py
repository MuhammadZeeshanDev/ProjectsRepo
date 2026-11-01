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
    st.subheader('📊 Device activity · refresh every 3 seconds')
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
    st.caption('To enable audible alerts, click Enable sound & notifications once. Some browsers block automatic playback or embedded notifications.')
    alerts = df[df['decision'] == 'BLOCK']
    if alerts.empty:
        st.success('No blocked requests in the current event window.')
    else:
        latest = alerts.iloc[0]
        components.html(_alarm_html(str(latest['timestamp_utc']) + str(latest['device']) + str(latest['reason'])), height=85)
        st.dataframe(alerts[['timestamp_utc', 'device', 'reason', 'source']], hide_index=True, use_container_width=True)
    st.subheader('📝 Recent HTTP events')
    st.dataframe(df, hide_index=True, use_container_width=True)
    st.download_button('⬇️ Export events CSV', df.to_csv(index=False).encode('utf-8'),
                       file_name='quantumsafe_virtual_events.csv', mime='text/csv', key='export_live_http_events')




def _alarm_html(event_key):
    """Client-side audio/notification; browser requires user gesture to unlock sound."""
    import json
    key = json.dumps(str(event_key))
    return """<div style='font-family:sans-serif'>
    <button id='enable'>🔔 Enable sound & notifications</button>
    <button id='play'>🔊 Test alarm</button>
    <span id='status' style='font-size:12px'>Browser permission may be required.</span>
    </div><script>
    const eventKey=KEY;
    const status=document.getElementById('status');
    function alarm(){
      try { const C=window.AudioContext||window.webkitAudioContext; const c=new C();
        c.resume().then(()=>{for(let i=0;i<4;i++){
          const o=c.createOscillator(),g=c.createGain(),t=c.currentTime+i*0.23;
          o.type='square';o.frequency.value=(i%2?1250:950);
          g.gain.setValueAtTime(0.0001,t);g.gain.exponentialRampToValueAtTime(0.13,t+0.02);
          g.gain.exponentialRampToValueAtTime(0.0001,t+0.19);
          o.connect(g);g.connect(c.destination);o.start(t);o.stop(t+0.2);
        }});
      } catch(e){status.textContent='Audio unavailable: '+e.message;}
    }
    document.getElementById('play').onclick=alarm;
    document.getElementById('enable').onclick=async()=>{
      alarm();if('Notification' in window){try {await Notification.requestPermission();}catch(e){}}
      status.textContent='Sound test played. Keep browser tab open; auto-play depends on browser settings.';
    };
    if(eventKey && eventKey!=='none'){
      alarm();
      if('Notification' in window && Notification.permission==='granted'){
        try{new Notification('QuantumSafe: blocked request',{body:'Security event detected. Open PC A alerts.'});}catch(e){}
      }
    }
    </script>""".replace('KEY',key)

def message_test(gateway):
    st.subheader('🔎 Optional message / URL screening (offline)')
    st.caption('This optional offline checker does NOT verify websites, detect malicious domains, or block browser connections. A plain website URL is UNKNOWN, and an IP-based URL requires REVIEW; neither proves safety or danger. Automatic gateway checks run without this form.')
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
                components.html(_alarm_html(event['timestamp_utc'] + event['reason']),height=85)
                st.warning('If you hear no sound, click the audio play control. Browsers can prevent automatic sound.')
            elif event['decision']=='REVIEW':
                st.warning('🟡 REVIEW — '+event['reason']+' (not proof of malware)')
            else:
                st.info('⚪ UNKNOWN — no configured indicators matched. Link safety has NOT been verified.')
        except ValueError as exc:st.warning(str(exc))


def show(actor):
    from ..version import APP_VERSION
    st.title(f'🛡️ IoT Devices & Security · v{APP_VERSION}')
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
    if actor['RoleName']=='Admin':
        message_test(gateway)
    st.divider()
    st.subheader('📡 Registered virtual devices')
    st.dataframe(pd.DataFrame([{'Device ID':k,'Device':v,'Connection':'Virtual / registered','KEM capability':'Enabled in lab'} for k,v in gateway.registered_devices.items()]),hide_index=True,use_container_width=True)
    st.caption('Registered means configured in this virtual gateway; not proof of a physical connection. KEM capability is a lab assumption, not a completed handshake.')
    if actor['RoleName']=='Admin':
        st.subheader('🔐 Test ML-KEM on every virtual device')
        if st.button('Run secure connection checks (all devices)'):
            from ..crypto_engine import self_test, ALGORITHMS
            results=[]
            for device in gateway.registered_devices:
                for algorithm in ALGORITHMS:
                    try:
                        outcome=self_test(algorithm)
                        results.append({'Device':device,'KEM':algorithm,'Result':'PASS' if outcome['passed'] else 'FAIL','Detail':'Local key agreement verified'})
                    except Exception as exc:
                        results.append({'Device':device,'KEM':algorithm,'Result':'FAIL','Detail':type(exc).__name__+': '+str(exc)[:120]})
            st.dataframe(pd.DataFrame(results),hide_index=True,use_container_width=True)
            st.warning('These checks run a fresh local cryptographic self-test per virtual device and KEM type. They do not prove a remote device connection, identity authentication, or encrypted IoT telemetry.')
    if actor['RoleName']=='Admin':
        st.subheader('🧪 Security tests (Administrator)')
        device_choice = st.selectbox('1. Device to test', ['CCTV camera', 'Network router', 'Temperature sensor'])
        scenario_options = {'CCTV camera': [('Camera: trusted telemetry','CCTV'), ('Camera: tampered reading','Tampered message'), ('Camera: replay protection','Replay attack')],
                            'Network router': [('Router: trusted telemetry','Router'), ('Router: request limit','Rate limit'), ('Router: invalid access','Unauthorized access')],
                            'Temperature sensor': [('Sensor: trusted reading','Sensor'), ('Sensor: tampered reading','Tampered message'), ('Sensor: replay protection','Replay attack')]}
        selected = st.selectbox('2. Security check', [x[0] for x in scenario_options[device_choice]])
        scenario = next(v for label,v in scenario_options[device_choice] if label==selected)
        st.caption('Admin diagnostic tests use a trusted test harness. PC B tests are independent and have no trusted credentials.')
        if st.button('▶️ Send request', type='primary', disabled=not bool(gateway.server)):
            try:
                event = gateway.send(scenario, device_override={"CCTV camera":"virtual-cctv-01", "Network router":"virtual-router-01", "Temperature sensor":"virtual-sensor-01"}[device_choice])
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
