"""v1.5.0 regression tests: device lifecycle, authorization, HTTP and 3 GiB CSV limits."""
import io
import os
import sys
from pathlib import Path
import pytest

SRC = Path(__file__).resolve().parents[1] / 'SourceCode'
sys.path.insert(0, str(SRC))

from quantumsafe.device_registry import DeviceRegistry
from quantumsafe.permissions import PermissionDenied
from quantumsafe.large_csv import checked_csv, headers, representative_sample, MAX_CSV_BYTES
from quantumsafe.local_ai_runtime import find_prolog, local_models, evidence_summary
from quantumsafe.local_prolog_ai import analyze
from quantumsafe.virtual_network import VirtualGateway
from quantumsafe.realtime_alarm import AlarmEngine


def test_registry_enrollment_and_persistence(tmp_path):
    registry = DeviceRegistry(tmp_path/'private.json')
    assert len(registry.active_credentials()) == 3
    registry.enroll('virtual-new-04', 'Back gate camera', 'Camera')
    before = registry.active_credentials()['virtual-new-04']
    restored = DeviceRegistry(tmp_path/'private.json')
    assert restored.active_credentials()['virtual-new-04'] == before
    assert all('token' not in r and 'key_hex' not in r for r in restored.inventory())


def test_registry_disable_rotate_retire(tmp_path):
    registry = DeviceRegistry(tmp_path/'private.json')
    original = registry.active_credentials()['virtual-cctv-01']
    registry.set_state('virtual-cctv-01', 'disabled')
    assert 'virtual-cctv-01' not in registry.active_credentials()
    registry.rotate('virtual-cctv-01')
    registry.set_state('virtual-cctv-01', 'active')
    assert registry.active_credentials()['virtual-cctv-01'] != original
    registry.set_state('virtual-cctv-01', 'retired')
    assert 'virtual-cctv-01' not in registry.active_credentials()
    with pytest.raises(ValueError): registry.set_state('virtual-cctv-01', 'active')
    with pytest.raises(ValueError): registry.enroll('virtual-cctv-01', 'New', 'Other')


def test_registry_rejects_invalid_names(tmp_path):
    r = DeviceRegistry(tmp_path/'devices.json')
    for bad in ('../attack', 'x', 'id with blanks'):
        with pytest.raises(ValueError): r.enroll(bad, 'Device name', 'Camera')
    with pytest.raises(ValueError): r.enroll('valid-dev-1', 'name', 'exploit')


def test_corrupt_registry_not_overwritten(tmp_path):
    p = tmp_path/'devices.json'
    p.write_text('{invalid')
    with pytest.raises(ValueError): DeviceRegistry(p)
    assert p.read_text() == '{invalid'


def _gateway_with_temp_registry(tmp_path):
    gw = VirtualGateway()
    gw.registry = DeviceRegistry(tmp_path/'devices.json')
    gw._reload_registry()
    gw.alarm_engine = AlarmEngine(player=lambda ev: True)
    return gw


def test_operator_cannot_enroll(tmp_path):
    gw = _gateway_with_temp_registry(tmp_path)
    with pytest.raises(PermissionDenied):
        gw.manage_device('enroll', 'virtual-new-04', 'Researcher', 'operator', 'New sensor', 'Sensor')
    assert 'virtual-new-04' not in gw.registered_devices


def test_registration_and_disable_immediately_enforced_http(tmp_path):
    gw = _gateway_with_temp_registry(tmp_path)
    gw.start(port=0)
    try:
        gw.manage_device('enroll', 'virtual-new-04', 'Admin', 'admin', 'New sensor', 'Sensor')
        allowed = gw.send('CCTV', device_override='virtual-new-04')
        assert allowed['decision'] == 'ALLOW'
        from quantumsafe.attacker_client import send_untrusted_to
        denied = send_untrusted_to('virtual-new-04', port=gw.port)
        assert denied['decision'] == 'BLOCK'
        assert denied['reason'] == 'Invalid gateway token'
        assert gw.alarm_engine.total_alerts == 1
        gw.manage_device('disable', 'virtual-new-04', 'Admin')
        denied = send_untrusted_to('virtual-new-04', port=gw.port)
        assert denied['decision'] == 'BLOCK'
        assert denied['reason'] == 'Device is not registered'
        assert gw.alarm_engine.total_alerts == 2
    finally:
        gw.stop()


def test_old_credentials_revoked_immediately(tmp_path):
    gw = _gateway_with_temp_registry(tmp_path)
    device = 'virtual-cctv-01'
    old_token = gw.device_tokens[device]
    gw.manage_device('rotate', device, 'Admin')
    assert gw.device_tokens[device] != old_token
    packet = {'device': device, 'token':gw.token,'device_token':old_token,
              'nonce':'unique-for-test','value':42,'signature':gw.sign(device, 'unique-for-test',42)}
    assert gw.evaluate(packet)['decision'] == 'BLOCK'


def test_large_csv_uniform_bounded_sample(tmp_path):
    p = tmp_path/'train.csv'
    p.write_text('f1,f2,label\n' + ''.join(f'{i},{i%4},{i%2}\n' for i in range(200)))
    assert headers(p) == ['f1', 'f2', 'label']
    a = representative_sample(p, ['f1','f2'], 'label', max_rows=30)
    b = representative_sample(p, ['f1','f2'], 'label', max_rows=30)
    assert a['total_rows'] == 200
    assert len(a['sample']) == 30
    assert a['sample'].equals(b['sample'])
    assert a['sample']['f1'].max() > 50  # not first 30 rows only


def test_csv_size_3gib_limit(tmp_path, monkeypatch):
    p = tmp_path/'huge.csv'
    with p.open('wb') as f:
        f.truncate(MAX_CSV_BYTES+1)  # sparse file, does not actually allocate 3 GiB
    with pytest.raises(ValueError, match='3 GiB'): checked_csv(p)


def test_local_ai_prolog_rule_fallback_and_safe_evidence():
    result = analyze({'algorithm':'Random Forest','heldout':{'false_positive_rate':0.2},'folds':[]},
                     [{'decision':'BLOCK','attack_type':'replay_attack'}], prolog_executable='')
    assert 'Python fallback' in result['engine']
    assert 'high_fpr' in [x['rule'] for x in result['recommendations']]
    evidence = evidence_summary(result, [], [{'device_id':'device1','type':'Sensor','status':'active','token':'DO_NOT_LEAK'}], 'memory', 1)
    assert 'DO_NOT_LEAK' not in str(evidence)


def test_local_ollama_missing_is_safe():
    # Should not contact internet: only fixed http://127.0.0.1:11434.
    assert isinstance(local_models(), list)


def test_prolog_discovery_rejects_other_binaries(tmp_path):
    fake = tmp_path/'python'
    fake.write_text('not prolog')
    assert find_prolog(str(fake)) is None
