"""Reference-style monitoring dashboard for existing authenticated QuantumSafe users."""
from __future__ import annotations
import io
import csv
import streamlit as st
import streamlit.components.v1 as components
from ..version import APP_VERSION
from . import security_console
from .. import console_data


@st.fragment(run_every='5s')
def _live_console():
    try:
        data,sql_status=security_console.collect()
        # Sandbox iframe displays read-only data; NO unauthenticated websocket or simulator.
        components.html(security_console.render_html(data),height=1310,scrolling=True)
        c1,c2,c3,c4=st.columns(4)
        c1.metric('Gateway','RUNNING' if data['gateway_running'] else 'STOPPED')
        c2.metric('Enrolled virtual devices',len(data['devices']))
        c3.metric('Saved ML models',data['model_count'])
        c4.metric('Shadow ML routes',data['route_count'])
        st.caption(sql_status+' · Counts reflect available gateway event history; NOT captured network packets.')
        return data
    except Exception as exc:
        st.error(f'Security console could not load: {type(exc).__name__}: {exc}')
        return None


def _admin_alert_tools(actor):
    if actor.get('RoleName')!='Admin':return
    with st.expander('🛠 Administrator · Alert actions and evidence export'):
        data,_=security_console.collect()
        pending=[a for a in data['alerts'] if not a['acknowledged']]
        if pending:
            label={a['id']:f"{a['ts']} · {a['device_id']} · {a['title']}" for a in pending}
            aid=st.selectbox('Select rejected event to acknowledge',list(label),format_func=lambda x:label[x])
            if st.button('✓ Acknowledge selected event'):
                # Re-read pending events to prevent acknowledgement of arbitrary IDs.
                if aid not in {a['id'] for a in security_console.collect()[0]['alerts']}:
                    st.error('Event is no longer in the active alert feed.')
                else:
                    console_data.acknowledge(aid,actor)
                    st.success('Acknowledgement saved. Refresh the screen to see it.')
                    st.rerun()
        else:st.success('No unacknowledged rejected requests in the visible history.')
        fields=['timestamp_utc','device','decision','reason','source_ip','attack_type','source']
        buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=fields,extrasaction='ignore')
        writer.writeheader();writer.writerows(data['events'])
        st.download_button('⬇ Export observed events (CSV)',buf.getvalue().encode('utf-8-sig'),
                           file_name='quantumsafe_virtual_gateway_events.csv',mime='text/csv')


def show(actor):
    st.title(f'🛡 QuantumSafe Security Console · v{APP_VERSION}')
    st.caption(f"Logged in: {actor.get('Username','User')} · {'Administrator' if actor.get('RoleName')=='Admin' else 'Security Operator'}")
    st.info('Reference dashboard design integrated with the existing QuantumSafe virtual gateway. Device enrollment and PC B remain in their Administrator panels. The network map is a logical visualization.')
    _live_console()
    _admin_alert_tools(actor)
    st.caption('ML ranking is shadow-only. Virtual HTTP request rejections do not equal network-wide IPS/firewall enforcement.')
