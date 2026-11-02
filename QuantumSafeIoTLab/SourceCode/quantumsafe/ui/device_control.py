"""Administrator-facing install/manage virtual IoT identities, live localhost readings."""
from datetime import datetime,timezone
import pandas as pd
import streamlit as st
from ..device_registry import TYPES
from ..virtual_devices import VirtualDeviceRunner

@st.cache_resource
def resources():
    from .virtual_lab import get_gateway
    return get_gateway(),VirtualDeviceRunner()

@st.fragment(run_every='3s')
def live_state(gw,runner):
    from .virtual_lab import snapshot_events
    events=snapshot_events(gw)
    last={}
    for e in events:
        did=e.get('device')
        if did and did not in last and e.get('decision')=='ALLOW':last[did]=e
    devices=[]
    for row in gw.registry.inventory():
        e=last.get(row['id']); age=None
        if e:
            try:age=(datetime.now(timezone.utc)-datetime.fromisoformat(e['timestamp_utc'])).total_seconds()
            except (ValueError,TypeError):pass
        online=(row['status']=='active' and age is not None and age<=30)
        devices.append({'Device ID':row['id'],'Name':row['name'],'Type':row['type'],
            'Configured virtual IP':row.get('virtual_ip') or 'Not set',
            'Configured virtual MAC':row.get('virtual_mac') or 'Not set',
            'Enrollment':row['status'].upper(),'Observed':('🟢 ACTIVE' if online else '⚪ NO RECENT HEARTBEAT'),
            'Last seen UTC':e.get('timestamp_utc') if e else 'Never',
            'Observed IP':e.get('source_ip') if e else 'Not observed',
            'Last virtual reading':e.get('reading') if e else None,
            'Generator':('RUNNING' if row['id'] in runner.running() else 'Stopped')})
    st.dataframe(pd.DataFrame(devices),hide_index=True,use_container_width=True)
    st.caption('Observed IP comes from actual localhost HTTP request. 127.0.0.1 is NOT a physical device IP; virtual readings are synthetic.')
    st.metric('Recent blocked attempts',sum(e.get('decision')=='BLOCK' for e in events))


def show(actor):
    if actor.get('RoleName')!='Admin':st.error('Administrator only');return
    st.title('🌐 Install & Manage IoT Devices')
    st.caption('Local virtual gateway first. Register device identities and generate live loopback readings. No network scan, DHCP discovery, physical installation or real gateway routing claimed.')
    gw,runner=resources()
    c1,c2,c3=st.columns(3)
    c1.metric('Gateway','🟢 RUNNING' if gw.server else '🔴 STOPPED')
    c2.metric('Enrolled active',len(gw.registered_devices))
    c3.metric('Virtual devices sending',len(runner.running()))
    l,r=st.columns(2)
    if l.button('▶ Start virtual gateway',disabled=bool(gw.server),type='primary'):
        try:
            gw.start(8765)
            from .. import gateway_event_store
            try:
                if gateway_event_store.is_initialized():gw.event_sink=gateway_event_store.insert_event
            except Exception:pass
            st.success('Gateway started at 127.0.0.1:8765')
            st.rerun()
        except Exception as exc:st.error(f'Gateway start failed: {exc}')
    if r.button('■ Stop gateway',disabled=not bool(gw.server)):
        for d in runner.running():runner.stop(d)
        gw.stop();st.rerun()
    st.divider()
    with st.expander('➕ Install new virtual device',expanded=True):
        with st.form('enroll_virtual'):
            col1,col2=st.columns(2)
            device_id=col1.text_input('Device ID',placeholder='virtual-camera-02')
            device_name=col2.text_input('Device name',placeholder='Entrance camera')
            kind=st.selectbox('Device type',TYPES)
            virtual_ip=st.text_input('Virtual IP for lab diagram (NOT actual assigned IP)',placeholder='192.168.50.12')
            virtual_mac=st.text_input('Virtual MAC (optional, simulated)',placeholder='02:00:00:00:00:12')
            confirmed=st.checkbox('Approve creating a virtual IoT device identity with new credentials')
            submit=st.form_submit_button('Register device',type='primary')
        if submit:
            if not confirmed:st.warning('Please approve enrollment.')
            else:
                try:
                    did=gw.manage_device('register',device_id,actor,name=device_name,kind=kind,
                        virtual_ip=virtual_ip,virtual_mac=virtual_mac)
                    st.success(f'{did} registered. Start its live virtual telemetry below.')
                    st.rerun()
                except Exception as exc:st.error(str(exc))
    st.subheader('📟 Registered devices & real-time readings')
    live_state(gw,runner)
    active=list(gw.registered_devices)
    if active:
        with st.expander('📡 Run a device / test connection',expanded=True):
            selected=st.selectbox('Virtual device',active,format_func=lambda x:f'{gw.registered_devices[x]} ({x})')
            interval=st.slider('Reading interval (seconds)',2,30,5)
            c1,c2,c3=st.columns(3)
            if c1.button('▶ Start live readings',disabled=not bool(gw.server)):
                try:runner.start(gw,selected,interval);st.success('Virtual device generator running.');st.rerun()
                except Exception as exc:st.error(str(exc))
            if c2.button('📨 Send single test',disabled=not bool(gw.server)):
                try:
                    event=gw.send('Sensor',device_override=selected)
                    (st.success if event['decision']=='ALLOW' else st.error)(event['decision']+' · '+event['reason'])
                except Exception as exc:st.error(str(exc))
            if c3.button('■ Stop readings'):
                runner.stop(selected);st.info('Generator stopped.');st.rerun()
    editable=[r for r in gw.registry.inventory() if r['status']!='retired']
    if editable:
        with st.expander('🔒 Device access, keys & removal'):
            target=st.selectbox('Manage enrolled ID',[r['id'] for r in editable])
            current=next(r for r in editable if r['id']==target)
            actions=(['disable'] if current['status']=='active' else ['enable'])+['rotate','retire']
            change=st.selectbox('Action',actions,format_func={'disable':'Disable device','enable':'Enable device',
                'rotate':'Rotate credentials','retire':'Permanently remove / retire ID'}.get)
            st.warning('Disable or retire immediately blocks future requests. Retired ID cannot be re-used; historical events remain.')
            challenge=st.text_input(f'Type {target} to confirm',key='dev_confirm_'+target)
            if st.button('Apply device change'):
                if challenge!=target:st.error('Confirmation does not match device ID.')
                else:
                    try:
                        gw.manage_device(change,target,actor)
                        if change in ('disable','retire'):runner.stop(target)
                        st.success('Applied: '+change);st.rerun()
                    except Exception as exc:st.error(str(exc))
    st.info('To connect a REAL camera/router later, a separate authenticated provisioning agent, secure key exchange and a routing/collector integration are required. This release simulates devices on localhost.')
