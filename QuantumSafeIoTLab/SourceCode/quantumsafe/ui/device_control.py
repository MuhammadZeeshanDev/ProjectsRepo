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
            'IPS policy':('QUARANTINED' if gw.ips.active(row['id']) else 'clear'),
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
    from .secure_mesh_panel import show as show_secure_mesh
    show_secure_mesh(actor,gw)
    from .ips_control import show_ips_controls
    show_ips_controls(actor,gw)
    st.divider()
    from . import acceptance_station
    acceptance_station.show(actor,gw)
    _sql_diagnostics(gw)
    st.info('ML-KEM device-to-device messaging above uses real cryptography in an in-process virtual simulation. REAL devices additionally require an authenticated provisioning agent, independent endpoint key storage and network routing/collector integration.')


def _sql_diagnostics(gw):
    """Admin-only visible SQL health and real event read-back."""
    from .. import gateway_event_store as sql_store
    from .. import db
    with st.expander("🗄️ SQL Server 2022 · Persistence & Diagnostics", expanded=False):
        sync=getattr(gw,"sql_sync",None)
        if sync is None:
            st.error("Gateway update incomplete. Restart app and install v2.0.2.")
            return
        pending=sync.pending_counts()
        a,b,c=st.columns(3)
        a.metric("Queued SQL events",pending["events"])
        b.metric("Queued device updates",pending["devices"])
        c.metric("Last confirmed SQL save",sync.last_ok_utc or "Not verified")
        if sync.last_error:st.error("SQL write unavailable: "+sync.last_error)
        if gw.last_persist_error:st.error("Local queue failure: "+gw.last_persist_error)
        st.caption("Queued = durable local SQLite only, NOT yet saved to SQL Server. Passwords/device keys are NOT mirrored. Models are stored in ML_Artifacts SQLite, not SQL Server.")
        if st.button("🔌 Check SQL connection, initialize and sync", key="qs_sql_health"):
            try:
                with db.connection() as con:
                    row=con.cursor().execute("SELECT @@SERVERNAME, DB_NAME()").fetchone()
                sql_store.initialize()
                sync.stage_inventory(gw.registry.inventory())
                n=sync.flush_once(40)
                counts=sql_store.counts()
                if sync.last_error:
                    st.warning(f"SQL connected: {row[0]} / {row[1]}, but sync still failing: {sync.last_error}")
                else:
                    st.success(f"SQL connected: {row[0]} / {row[1]} · {n} queued records confirmed · {counts['total']} gateway events in SQL")
            except Exception as exc:
                st.error(f"SQL verification FAILED: {type(exc).__name__}: {exc}")
                st.info("Check project .env SQL_SERVER / SQL_DATABASE, Windows account access, ODBC Driver 18, and CREATE TABLE/INSERT permissions.")
        if gw.server and gw.registered_devices:
            if st.button("🧪 Write and read back a real ALLOW event", key="qs_sql_readback"):
                try:
                    did=next(iter(gw.registered_devices))
                    result=gw.send("Sensor",device_override=did)
                    if result["decision"]!="ALLOW":
                        st.warning("Gateway did not allow the test request: "+result["reason"])
                    else:
                        sync.flush_once(40)
                        if sql_store.event_exists(result["event_id"]):
                            st.success("PASS: This actual HTTP request was saved AND read back from SQL Server 2022.")
                        else:
                            st.warning("Request allowed and queued, but NOT YET verified in SQL. Check queue status and retry.")
                except Exception as exc:
                    st.error(f"SQL write/read-back FAILED: {type(exc).__name__}: {exc}")
        else:
            st.info("Start the virtual gateway to test actual SQL write/read-back.")
