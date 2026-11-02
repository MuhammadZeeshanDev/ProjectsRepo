"""Reference-style monitoring dashboard for existing authenticated QuantumSafe users."""
from __future__ import annotations
import io
import csv
import streamlit as st
import streamlit.components.v1 as components
from ..version import APP_VERSION
from . import security_console
from .. import console_data


@st.fragment(run_every='8s')
def _live_metrics():
    try:
        data,sql_status=security_console.collect()
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


def _viewer_session(gateway, actor, session, clock=None):
    """Issue a short-lived authorized viewer token only for a capable v2 gateway.

    An older cached VirtualGateway instance must NEVER cause a monitoring crash,
    and must NEVER be replaced with an unprotected public viewer endpoint.
    """
    import time
    clock = clock or time.time
    required = ('issue_viewer', 'valid_viewer', 'viewer_state')
    if any(not callable(getattr(gateway, attr, None)) for attr in required):
        return None
    current = clock()
    state = session.get('qs_monitor_viewer')
    healthy = (isinstance(state, dict) and state.get('gateway') == id(gateway)
               and isinstance(state.get('token'), str) and state.get('expires', 0) > current + 60)
    if healthy:
        try:
            healthy = gateway.valid_viewer(state['token'])
        except (AttributeError, TypeError, ValueError):
            healthy = False
    if not healthy:
        # The calling UI has already checked the actor with users.active_actor().
        new_token = gateway.issue_viewer(actor)
        state = {'token': new_token, 'expires': current + 1200,
                 'gateway': id(gateway)}
        session['qs_monitor_viewer'] = state
    return state


def _read_only_fallback(gateway):
    """Fallback is rendered only inside an authenticated Streamlit page."""
    try:
        data, _ = security_console.collect()
        components.html(security_console.render_html(data), height=1080, scrolling=True)
    except Exception as exc:
        # The old gateway may not provide the new registry fields either.
        st.warning('Detailed dashboard unavailable: ' + type(exc).__name__ + '. Restart application after applying compatibility update.')
        events = list(getattr(gateway, 'events', ()))[:50]
        if events:
            safe = [{k: e.get(k) for k in ('timestamp_utc', 'device', 'decision', 'reason', 'source_ip')}
                    for e in events if isinstance(e, dict)]
            st.dataframe(safe, use_container_width=True)
        else:
            st.info('No virtual gateway observations yet.')


def show(actor):
    st.title(f'🛡 QuantumSafe Security Console · v{APP_VERSION}')
    st.caption(f"Logged in: {actor.get('Username','User')} · {'Administrator' if actor.get('RoleName')=='Admin' else 'Security Operator'}")
    st.info('This is a local virtual gateway. Registered devices and PC B remain separate Administrator tools; the topology is a logical map.')
    from .virtual_lab import get_gateway
    gateway = get_gateway()
    gateway_running = bool(getattr(gateway, 'server', None))
    if gateway_running:
        try:
            state = _viewer_session(gateway, actor, st.session_state)
            port = getattr(gateway, 'port', None)
            if state and port:
                components.iframe(f'http://127.0.0.1:{int(port)}/viewer/{state["token"]}',
                                  height=1160, scrolling=True)
                st.caption('Live viewer uses short-lived access token; browser sound must be enabled by clicking its sound button.')
            else:
                # No passwordless fallback on :8765. Only this authenticated UI
                # shows a server-side snapshot until the correct gateway loads.
                st.warning('Running gateway is an older version without authenticated live-view support. Monitoring is in safe read-only mode. Close Streamlit/PC B fully, apply v2.0.1, then restart.')
                _read_only_fallback(gateway)
        except (AttributeError, KeyError, ValueError, TypeError, PermissionError) as exc:
            st.warning('Viewer could not start (' + type(exc).__name__ + '). Showing safe read-only monitoring. Restart the application after upgrading.')
            _read_only_fallback(gateway)
    else:
        st.warning('Virtual gateway is stopped. Administrator: open Devices & Installation and start it for live monitoring.')
        _read_only_fallback(gateway)

    _live_metrics()
    st.subheader('🧠 IDS/IPS Runtime (observed virtual events)')
    ips = getattr(gateway, 'ips', None)
    try:
        contained = sum(1 for x in ips.entries() if x.get('active')) if ips else None
    except Exception:
        contained = None
    shadow = getattr(gateway, 'live_shadow', None)
    try:
        shadow_state = shadow.snapshot() if shadow else {}
    except Exception:
        shadow_state = {}
    a,b,c = st.columns(3)
    a.metric('Local virtual containment', contained if contained is not None else 'Not loaded')
    b.metric('Shadow ML readings assessed', shadow_state.get('processed', 'Not loaded'))
    c.metric('Shadow ML matches', shadow_state.get('matches', 'Not loaded'))
    st.caption('Gateway rules reject unauthorized virtual HTTP telemetry. Shadow ML does not block real network traffic.')
    if shadow_state.get('last_error'):
        st.warning('ML shadow issue: ' + str(shadow_state['last_error']))
    if shadow_state.get('incompatible'):
        st.info(f"{shadow_state['incompatible']} model route(s) have incompatible features. No TCP/MQTT capture is present.")
    try:
        _admin_alert_tools(actor)
    except (AttributeError, KeyError, ValueError, TypeError) as exc:
        st.warning('Alert tools unavailable in this runtime: ' + type(exc).__name__)
    if actor.get('RoleName')=='Admin':
        with st.expander('🔎 System readiness & diagnostics'):
            alarms = getattr(gateway, 'alarm_engine', None)
            d1,d2,d3 = st.columns(3)
            d1.metric('Alarm played', getattr(alarms, 'played', 'Not loaded'))
            d2.metric('Alarm failures', getattr(alarms, 'failures', 'Not loaded'))
            d3.metric('Virtual IPS active', contained if contained is not None else 'Not loaded')
            if alarms and getattr(alarms, 'last_error', None):
                st.error('Windows alarm problem: ' + str(alarms.last_error))
            if getattr(gateway, 'last_persist_error', None):
                st.error('SQL event save issue: ' + str(gateway.last_persist_error))
            if not callable(getattr(gateway, 'issue_viewer', None)):
                st.error('Gateway/dashboard version mismatch: issue_viewer() is missing from the running gateway object. Completely stop both Python/Streamlit processes, install v2.0.1, restart.')
            try:
                from ..ml_engine.selector import find_swipl
                st.write('SWI-Prolog executable:', find_swipl() or 'Not detected (Python fallback)')
            except (ImportError, AttributeError, OSError) as exc:
                st.warning('Prolog runtime check: ' + str(exc))
    st.caption('Localhost virtual IDS/IPS only. Does not imply router-level protection.')
