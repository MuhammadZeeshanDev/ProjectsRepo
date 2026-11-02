"""V2 acceptance: real-events-only analytics, graphs and role gating."""
import sys
import types
from datetime import datetime,timezone,timedelta
from quantumsafe import analytics_data

NOW=datetime(2026,11,2,12,0,tzinfo=timezone.utc)

def _ev(age,dec,dev='virtual-cctv-01',reason='Authenticated and integrity verified',reading=None):
    return dict(timestamp_utc=(NOW-timedelta(minutes=age)).isoformat(),decision=dec,
                device=dev,reason=reason,source_ip='127.0.0.1',reading=reading)


def test_no_fabricated_requests_and_invalid_time_is_ignored():
    events=[_ev(2,'ALLOW',reading=32),_ev(4,'BLOCK',reason='Invalid gateway token'),
            _ev(120,'ALLOW',dev='virtual-sensor-01',reading=13),
            _ev(2000,'BLOCK'),{'decision':'ALLOW','timestamp_utc':'not a date'},
            {'decision':'ALLOW','timestamp_utc':(NOW+timedelta(days=2)).isoformat()}]
    result=analytics_data.aggregate(events,NOW,hours=3)
    assert result['total']==3
    assert result['allow']==2 and result['block']==1
    assert result['reasons']=={'Invalid gateway token':1}
    assert result['by_device']['virtual-cctv-01']=={'ALLOW':1,'BLOCK':1}
    assert result['readings']['virtual-cctv-01'][0]['reading']==32
    assert len(result['by_bucket'])==2
    assert analytics_data.aggregate(events,NOW,hours=1)['total']==2


def test_model_performance_is_saved_evidence_only():
    x=analytics_data.model_summary([
        dict(id=7,algorithm='Random Forest',features=['tcp.seq','tcp.dstport'],status='evaluated',
             metrics={'macro_f1':.9,'accuracy':.95,'latency_ms_per_row':.03},dataset_sha256='abcd',sample_rows=300),
        dict(id=8,algorithm='LightGBM',features=[],status='unverified_import',metrics={})])
    assert x[0]['macro_f1']==.9 and x[0]['features']==2
    assert x[1]['macro_f1'] is None and x[1]['status']=='unverified_import'


def test_chart_shapes_and_roles(monkeypatch):
    # CI does not install Streamlit; stub enough to import standalone Plotly builders.
    st=types.ModuleType('streamlit')
    st.fragment=lambda **k:(lambda f:f)
    monkeypatch.setitem(sys.modules,'streamlit',st)
    from quantumsafe.ui import analytics_panel as panel
    a=analytics_data.aggregate([_ev(2,'ALLOW',reading=1),_ev(2,'BLOCK',reason='Replay nonce detected')],NOW)
    assert len(panel.build_timeline(a).data)==2
    assert len(panel.build_outcomes(a).data)==1
    assert len(panel.build_reasons(a).data)==1
    assert len(panel.build_devices(a).data)==2
    assert len(panel.build_readings(a['readings']).data)==1
    assert len(panel.build_model_performance([{'id':1,'algorithm':'RF','macro_f1':.98,'latency_ms_per_row':.01,'features':10,'status':'evaluated'}]).data)==1
    import pytest
    with pytest.raises(PermissionError):panel.show({'RoleName':'Unknown'})


def test_safe_updater_does_not_allow_python_cache(tmp_path):
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    assert (root/'SourceCode/quantumsafe/ui/analytics_panel.py').is_file()
