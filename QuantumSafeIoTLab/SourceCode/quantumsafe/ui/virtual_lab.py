"""Local loopback gateway lab and legacy simulated scenarios."""
import pandas as pd
import streamlit as st
from ..virtual_gateway_sim import SCENARIOS, evaluate
from ..virtual_network import VirtualGateway

@st.cache_resource
def get_gateway():
    return VirtualGateway()

def show(actor):
    st.title('🧩 Virtual IoT Security Gateway')
    st.info('LOCAL LAB: Virtual clients send real HTTP requests to 127.0.0.1. No external devices, packet sniffing, ML or network-wide blocking.')
    gateway = get_gateway()
    c1,c2 = st.columns(2)
    if c1.button('🟢 Start local gateway',disabled=bool(gateway.server)):
        gateway.start()
    if c2.button('🔴 Stop local gateway',disabled=not bool(gateway.server)):
        gateway.stop()
    st.metric('Local gateway',f'127.0.0.1:{gateway.port}' if gateway.server else 'Stopped')
    st.subheader('🌐 Send real local HTTP request')
    scenario = st.selectbox('Virtual client / test', ['CCTV','Router','Sensor','Unauthorized access','Tampered message','Replay attack','Rate limit'])
    if st.button('▶️ Send request',type='primary',disabled=not bool(gateway.server)):
        try:
            event = gateway.send(scenario)
            (st.success if event['decision']=='ALLOW' else st.error)(f"{event['decision']} — {event['reason']}")
        except Exception as exc:
            st.error(f'Local request failed: {exc}')
    st.caption('Replay and rate-limit tests send multiple HTTP requests. Rate limits reset after 10 seconds; restart gateway to reset counters.')
    events = list(gateway.events)
    a,b,c=st.columns(3)
    a.metric('HTTP events',len(events))
    b.metric('Allowed',sum(e['decision']=='ALLOW' for e in events))
    c.metric('Blocked',sum(e['decision']=='BLOCK' for e in events))
    if events:
        df = pd.DataFrame(events)
        st.bar_chart(df['decision'].value_counts().reindex(['ALLOW','BLOCK'],fill_value=0))
        st.dataframe(df,hide_index=True,use_container_width=True)
        st.download_button('⬇️ Export HTTP event CSV',df.to_csv(index=False).encode(),'virtual_http_events.csv','text/csv')
    st.divider()
    with st.expander('Older offline policy simulation (v0.2.2)'):
        old = st.selectbox('Offline scenario',list(SCENARIOS))
        if st.button('Run offline simulation'):
            result=evaluate(old)
            st.json(result)
    st.warning('Security scope: This is a localhost training gateway. It does not inspect CCTV video, router packets, or prevent attacks elsewhere on the computer/network.')
