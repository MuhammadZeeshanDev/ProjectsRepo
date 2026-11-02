"""Render reference QuantumIoTLab styling as a safe read-only live-data console.

The uploaded FastAPI app is NOT started: it contains an unauthenticated websocket
simulation/control API and an independent SQLite identity database. Instead this
screen reuses existing QuantumSafe authorization, devices and gateway events.
"""
import json
from pathlib import Path
from .. import console_data

TEMPLATE=Path(__file__).resolve().parent/'assets'/'quantum_console.html'


def render_html(payload, polling=False):
    # Prevent </script> from ending the JSON assignment (defence in depth).
    content=json.dumps(console_data.public_snapshot(payload),ensure_ascii=True,allow_nan=False)
    content=content.replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return (TEMPLATE.read_text(encoding='utf-8')
            .replace('__QS_SNAPSHOT_JSON__',content)
            .replace('__QS_ENABLE_POLL__','true' if polling else 'false'))


def collect():
    from .virtual_lab import get_gateway
    from .. import gateway_event_store
    gw=get_gateway()
    sql=[];sql_status='SQL events unavailable'
    sync=getattr(gw, 'sql_sync', None)
    pending=sync.pending_counts() if sync else {'events':0,'devices':0}
    try:
        if sync and sync.last_error and pending['events']:
            sql_status='SQL sync delayed; '+str(pending['events'])+' event(s) queued locally'
        elif gateway_event_store.is_initialized():
            sql=gateway_event_store.recent_events(600)
            sql_status=f'SQL events connected · {pending["events"]} queued'
    except Exception as exc:
        sql_status='SQL events unavailable: '+type(exc).__name__+f' · {pending["events"]} queued locally'
    nmodels=nroutes=0
    try:
        from ..ml_engine import registry
        nmodels=len(registry.models());nroutes=len(registry.active_routes())
    except Exception:pass
    return console_data.snapshot(gw,sql,console_data.acked_uids(),model_count=nmodels,routes=nroutes),sql_status
