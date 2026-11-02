"""PC B: isolated, credential-free tests against installed virtual devices."""
import streamlit as st
from quantumsafe.attacker_client import discover_targets,send_dynamic_test
st.set_page_config(page_title='QuantumSafe | PC B',page_icon='🧪',layout='wide')
st.title('🧪 QuantumSafe · PC B Security Tests')
st.warning('Controlled local simulation only — untrusted client, no enrolled-device keys, no remote targeting.')

@st.fragment(run_every='5s')
def targets():
    try:rows=discover_targets()
    except Exception as exc:
        st.error('Device inventory unavailable: '+str(exc));return
    if not rows:
        st.info('No devices. Administrator must enroll a device on PC A.');return
    st.caption('Auto-discovered from shared local device registry, refreshed every 5 seconds. A newly registered device will appear here without restarting PC B.')
    active=[r for r in rows if r['status']=='active']
    if not active:st.warning('All devices disabled. PC B can only run tests against active devices.');return
    ids=[r['id'] for r in active]
    dev=st.selectbox('🎯 Select current device',ids,key='pc_b_target',
        format_func=lambda x:next(f"{r['name']} · {r['type']} · {r['virtual_ip'] or 'no virtual IP'} ({x})" for r in active if r['id']==x))
    case=st.radio('Test type',['unauthorized','repeated'],horizontal=True,
                  format_func=lambda x:'Invalid credential (1 request)' if x=='unauthorized' else 'Repeated untrusted requests (5)')
    if st.button('🚫 Send untrusted access test',type='primary'):
        try:
            events=send_dynamic_test(dev,case)
            if all(e.get('decision')=='BLOCK' for e in events):
                st.success(f'Gateway BLOCKED {len(events)} of {len(events)} requests — expected defense')
            else:st.error('Unexpected ALLOW detected! Review gateway immediately.')
            for e in events:
                st.write(f"{e.get('decision')} · {e.get('reason')} · {e.get('device')}")
        except Exception as exc:st.error(f'{type(exc).__name__}: {exc}')
    st.dataframe([{'Device ID':r['id'],'Name':r['name'],'Type':r['type'],
                  'Virtual IP':r['virtual_ip'],'Enrollment':r['status']} for r in rows],
                 hide_index=True,use_container_width=True)

targets()
st.divider()
st.caption('For a legitimate ALLOW demo, Administrator → Devices & Installation → Device acceptance & safe-login demo. PC B NEVER receives valid credentials. Physical two-PC discovery requires a separately secured protocol.')
