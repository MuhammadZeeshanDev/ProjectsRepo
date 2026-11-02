"""Administrator actions for local virtual IDS/IPS; no physical network controls."""
import pandas as pd
import streamlit as st


def show_ips_controls(actor, gw):
    if actor.get('RoleName')!='Admin':
        st.error('Administrator permission required')
        return
    st.divider()
    st.subheader('🛡 Virtual IPS — Response Policies')
    st.caption('Real enforcement is limited to the enrolled localhost virtual HTTP gateway. No Windows firewall/router blocks, remote camera configuration, or automatic emergency services calls.')
    cfg=gw.ips.settings()
    a,b,c=st.columns(3)
    a.metric('Response mode','AUTO (opt-in)' if cfg['auto_quarantine'] else 'MANUAL')
    b.metric('Active quarantines',len([x for x in gw.ips.entries() if x['active']]))
    c.metric('Identity-verified violation threshold',f"{cfg['threshold']} / {cfg['window_seconds']}s")
    with st.expander('⚙ Administrator response-policy settings'):
        st.warning('Auto containment can interrupt legitimate devices. It is OFF by default. Only repeated, authenticated tamper/replay/rate-limit events trigger a temporary virtual quarantine. Unknown/invalid-token attempts never quarantine a victim device.')
        enabled=st.toggle('Auto-quarantine for verified repeated violations',value=cfg['auto_quarantine'],key='ips_auto_toggle')
        approval=st.checkbox('I understand this is a local virtual gateway policy and can interrupt test devices',key='ips_policy_ack')
        if st.button('Save IDS/IPS policy',disabled=not approval):
            try:
                gw.ips.set_auto(bool(enabled),actor)
                st.success('Policy saved to local persistent database')
                st.rerun()
            except Exception as exc:st.error(str(exc))
    with st.expander('🔒 Quarantine or release a registered virtual device'):
        inventory=[d for d in gw.registry.inventory() if d['status']=='active']
        options=[d['id'] for d in inventory]
        if not options:st.info('No active enrolled devices available')
        else:
            did=st.selectbox('Enrolled virtual device',options,key='ips_target')
            seconds=st.selectbox('Temporary isolation duration',[60,120,300,600,1800],index=2,key='ips_ttl')
            confirmation=st.text_input(f'Type {did} to confirm security action',key='ips_confirm')
            c1,c2=st.columns(2)
            if c1.button('🚫 Quarantine device',type='primary'):
                if confirmation!=did:st.error('Device ID confirmation mismatch')
                else:
                    try:
                        gw.ips.quarantine(did,actor,seconds=seconds,enrolled=did in gw.registered_devices)
                        st.success('Virtual gateway is now rejecting this enrolled device until released or time expires')
                        st.rerun()
                    except Exception as exc:st.error(str(exc))
            if c2.button('✅ Release device from IPS quarantine'):
                if confirmation!=did:st.error('Device ID confirmation mismatch')
                else:
                    try:
                        gw.ips.release(did,actor)
                        st.success('Local quarantine released')
                        st.rerun()
                    except Exception as exc:st.error(str(exc))
    with st.expander('📋 Containment activity & audit trail'):
        entries=gw.ips.entries()
        active=[e for e in entries if e['active']]
        st.dataframe(pd.DataFrame(active),hide_index=True,use_container_width=True)
        audit=gw.ips.audit(100)
        if audit:
            st.dataframe(pd.DataFrame(audit),hide_index=True,use_container_width=True)
        else:st.info('No policy changes recorded yet.')
