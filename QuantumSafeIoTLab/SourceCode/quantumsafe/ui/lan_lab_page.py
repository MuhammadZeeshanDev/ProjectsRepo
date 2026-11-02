"""Operator-visible LAN Lab inventory; changes require Administrator role."""
import pandas as pd
import streamlit as st
from .virtual_lab import get_gateway
from ..device_registry import TYPES
from ..pakistan_time import display as pkt_display


def show(actor):
    st.title('🌐 LAN Lab & Device Manager')
    st.caption('Control virtual device enrollment and inspect private-LAN connectivity. Physical discovery, remote device control and LAN-wide packet detection are not implemented.')
    gateway = get_gateway()
    tab_devices, tab_lan = st.tabs(['📟 Device inventory', '🔗 Private LAN connection'])
    with tab_devices:
        _devices(gateway, actor)
    with tab_lan:
        st.info('Private LAN communication uses a separate ML-KEM/AES-GCM message listener. Its shared-secret protocol is NOT yet connected to the virtual HTTP device enrollment registry.')
        from . import lan_page
        lan_page.show(actor)


def _devices(gateway, actor):
    inventory = gateway.registry.inventory()
    active = sum(1 for r in inventory if r['status'] == 'active')
    disabled = sum(1 for r in inventory if r['status'] == 'disabled')
    one, two, three = st.columns(3)
    one.metric('Active devices', active)
    two.metric('Disabled devices', disabled)
    three.metric('Retired IDs', len(inventory) - active - disabled)
    if inventory:
        rows = [{
            'Device ID': r['device_id'], 'Device': r['name'], 'Type': r['type'],
            'Status': r['status'].upper(), 'Modified (Islamabad PKT)': pkt_display(r['updated_utc'])
        } for r in inventory]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.download_button('⬇️ Export inventory (no credentials)', pd.DataFrame(rows).to_csv(index=False).encode(),
                           'device_inventory.csv', mime='text/csv')
    else:
        st.info('No registered devices.')
    st.caption('ACTIVE means enrolled and permitted to authenticate; it does not prove a device is currently online. DISABLED/RETIRED identities are blocked immediately.')
    if actor['RoleName'] != 'Admin':
        st.info('Security Operator: view-only. Only Administrator can register, disable, remove or rotate device credentials.')
        return
    with st.expander('➕ Register new virtual device', expanded=False):
        with st.form('qs_new_device'):
            did = st.text_input('Unique ID', placeholder='virtual-camera-02', max_chars=64)
            name = st.text_input('Display name', placeholder='Front gate camera', max_chars=80)
            kind = st.selectbox('Device type', TYPES)
            approved = st.checkbox('I approve enrolling this device into the virtual gateway')
            submitted = st.form_submit_button('Register device', type='primary')
        if submitted:
            if not approved: st.warning('Approve registration to proceed.')
            else:
                try:
                    gateway.manage_device('enroll', did.strip().lower(), actor['RoleName'], actor['Username'], name, kind)
                    st.success('Device registered with fresh independent credentials. Existing devices remain unchanged.')
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    editable = [x for x in inventory if x['status'] != 'retired']
    if not editable:
        return
    with st.expander('🛡️ Change device access / credentials'):
        chosen = st.selectbox('Device', [x['device_id'] for x in editable], format_func=lambda k: next((f"{r['name']} · {k} ({r['status']})" for r in editable if r['device_id'] == k), k))
        state = next(x['status'] for x in editable if x['device_id'] == chosen)
        actions = (['disable'] if state == 'active' else ['enable']) + ['rotate', 'retire']
        action = st.selectbox('Action', actions, format_func={
            'disable': 'Disable access immediately', 'enable': 'Enable access',
            'rotate': 'Rotate device credentials', 'retire': 'Remove permanently (retire ID)'}.get)
        if action == 'retire':
            st.warning('Retiring permanently revokes credentials. The device ID cannot be reused. Historical security logs are retained.')
        if action == 'rotate':
            st.warning('Previous credentials stop working immediately; trusted virtual test clients receive new internal credentials.')
        confirm = st.text_input(f'Type device ID {chosen} to confirm', key=f'confirm_{chosen}_{action}')
        if st.button('Apply device change', type='primary'):
            if confirm != chosen:
                st.error('Device ID confirmation does not match.')
            else:
                try:
                    gateway.manage_device(action, chosen, actor['RoleName'], actor['Username'])
                    st.success(f'{chosen}: {action} completed.')
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    st.caption('Device secrets are stored locally in Data/device_registry.json (not shown in UI). Restrict host access and back up this file securely. No automatic network scanning occurs.')
