"""v1.8 release regression: local devices, PC B, ML job persistence and import quarantine."""
import json,os,sys,time
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'SourceCode'))
from quantumsafe.device_registry import DeviceRegistry
from quantumsafe.virtual_network import VirtualGateway
from quantumsafe.permissions import PermissionDenied
from quantumsafe.attacker_client import send_untrusted_device
from quantumsafe.ml_engine import jobs,registry,train,selector,importer

ADMIN={'RoleName':'Admin','Username':'unit_admin'}
OP={'RoleName':'Researcher','Username':'unit_operator'}

def gateway(tmp_path):
    g=VirtualGateway()
    g.registry=DeviceRegistry(tmp_path/'virtual_devices.json')
    g._reload_registry()
    g.alarm_engine.notify=lambda event:None
    return g


def test_enrollment_persists_and_secrets_hidden(tmp_path):
    g=gateway(tmp_path)
    g.manage_device('register','virtual-door-22',ADMIN,name='Door contact',kind='Sensor')
    assert 'virtual-door-22' in g.registered_devices
    again=DeviceRegistry(tmp_path/'virtual_devices.json')
    assert 'virtual-door-22' in again.credentials()
    assert 'token' not in json.dumps(again.inventory())


def test_operator_cannot_register_remove_or_rotate(tmp_path):
    g=gateway(tmp_path)
    for action in ('register','disable','rotate','retire'):
        with pytest.raises(PermissionDenied):
            g.manage_device(action,'virtual-sensor-01',OP,name='Rejected',kind='Sensor')


def test_pc_b_rejection_new_device_and_disable(tmp_path):
    g=gateway(tmp_path)
    g.start(port=0)
    try:
        g.manage_device('register','virtual-door-22',ADMIN,name='Door contact',kind='Sensor')
        ev=g.send('Sensor',device_override='virtual-door-22',reading=33.7)
        assert ev['decision']=='ALLOW' and ev['reading']==33.7
        attack=send_untrusted_device('virtual-door-22',port=g.port)
        assert attack['decision']=='BLOCK'
        g.manage_device('disable','virtual-door-22',ADMIN)
        assert 'virtual-door-22' not in g.registered_devices
        assert send_untrusted_device('virtual-door-22',port=g.port)['decision']=='BLOCK'
        g.manage_device('enable','virtual-door-22',ADMIN)
        assert g.send('Sensor',device_override='virtual-door-22')['decision']=='ALLOW'
        g.manage_device('retire','virtual-door-22',ADMIN)
        with pytest.raises(ValueError):g.manage_device('register','virtual-door-22',ADMIN,name='Again',kind='Sensor')
    finally:g.stop()


def test_keys_rotate(tmp_path):
    g=gateway(tmp_path)
    token=g.device_tokens['virtual-sensor-01']
    g.manage_device('rotate','virtual-sensor-01',ADMIN)
    assert g.device_tokens['virtual-sensor-01'] !=token


def test_migrate_existing_150_registry(tmp_path):
    p=tmp_path/'device_registry.json'
    p.write_text(json.dumps({'version':1,'devices':{'virtual-sensor-01':{
         'name':'Old Sensor','kind':'Sensor','state':'active',
         'key_hex':'ab'*32,'token':'keep-secret','created_utc':'2026','updated_utc':'2026'}}}))
    r=DeviceRegistry(tmp_path/'virtual_devices.json')
    assert r.credentials()['virtual-sensor-01'][2]=='keep-secret'
    assert p.exists()


def test_corrupt_registry_refuses_replacement(tmp_path):
    p=tmp_path/'virtual_devices.json';p.write_text('not json')
    with pytest.raises(json.JSONDecodeError):DeviceRegistry(p)
    assert p.read_text()=='not json'


def training_csv(tmp_path):
    p=tmp_path/'iot.csv'
    p.write_text('tcp.srcport,mqtt.len,Attack_label\n'+''.join(
        f'{100+i%20},{i%13},{int(i%20>9)}\n' for i in range(1000)))
    return p


def test_backend_job_and_persistent_models(tmp_path):
    p=training_csv(tmp_path)
    store=tmp_path/'IDS_Engine'
    jobdb=tmp_path/'jobs.sqlite3'
    jid=jobs.submit_training({'kind':'train','csv':str(p),'label':'Attack_label','normal':'0',
        'features':['tcp.srcport','mqtt.len'],'algorithms':['Random Forest'],
        'max_rows':300,'folds':3,'test_fraction':.3,'binary':False},path=jobdb,root=store)
    for _ in range(100):
        row=next(x for x in jobs.list_jobs(path=jobdb) if x['id']==jid)
        if row['status'] not in ('queued','running'):break
        time.sleep(.3)
    assert row['status']=='completed',row
    saved=registry.models(store)
    assert saved and saved[0]['algorithm']=='Random Forest'
    assert saved[0]['sha256']
    selection=row['result']['prolog_selection']
    assert 'routes' in selection
    assert jobs.list_jobs(path=jobdb)[0]['status']=='completed'


def test_import_quarantine_does_not_route(tmp_path):
    import joblib
    csv=training_csv(tmp_path)
    store=tmp_path/'IDS_Engine'
    created=train.fit_csv(csv,algorithm='Random Forest',label='Attack_label',normal='0',
                          features=['tcp.srcport','mqtt.len'],max_rows=300,folds=3,root=store)
    model,_=registry.load_model(created['model_id'],store)
    trusted=store/'Trusted_Imports';trusted.mkdir()
    p=trusted/'trusted.joblib';joblib.dump(model,p)
    with pytest.raises(PermissionError):importer.import_trusted(p,trust=False,root=store)
    entry=importer.import_trusted(p,trust=True,root=store)
    assert registry.get_model(entry['model_id'],store)['status']=='unverified_import'
    selection=selector.rank(root=store,dataset_sha=registry.get_model(entry['model_id'],store)['dataset_sha256'],persist=False)
    assert not selection['routes']
    evaluated=importer.validate_import(entry['model_id'],csv,root=store)
    assert evaluated['total_rows']>=200
    assert registry.get_model(entry['model_id'],store)['status']=='evaluated'
    after=selector.rank(root=store,dataset_sha=registry.get_model(entry['model_id'],store)['dataset_sha256'],persist=False)
    assert all(x['model_id'] != entry['model_id'] for x in after['routes'].values())


def test_train_all_three_models_with_dedicated_features(tmp_path):
    csv=training_csv(tmp_path)
    store=tmp_path/'all_models'
    available=train.estimator_names()
    for alg in ['Random Forest','XGBoost','LightGBM']:
        if alg not in available:continue
        outcome=train.fit_csv(csv,algorithm=alg,label='Attack_label',normal='0',
                  features=['tcp.srcport','mqtt.len'],max_rows=300,folds=3,root=store)
        assert 0<=outcome['heldout']['macro_f1']<=1
        assert len(outcome['folds'])==3
        assert registry.get_model(outcome['model_id'],store)['algorithm']==alg
    assert len(registry.models(store))==len([x for x in ['Random Forest','XGBoost','LightGBM'] if x in available])


def test_template_import_only_known_classifier(tmp_path):
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    store=tmp_path/'ids'
    trusted=store/'Trusted_Imports';trusted.mkdir(parents=True)
    p=trusted/'rf.joblib';joblib.dump(RandomForestClassifier(n_estimators=10),p)
    with pytest.raises(PermissionError):importer.detect_algorithm_template(p,trust=False,root=store)
    meta=importer.detect_algorithm_template(p,trust=True,root=store)
    assert meta['algorithm']=='Random Forest'
    assert meta['strategy'].startswith('clean_refit')


def test_address_inventory_and_uniqueness(tmp_path):
    r=DeviceRegistry(tmp_path/'virtual_devices.json')
    r.apply('register','virtual-door-22',name='Door contact',kind='Sensor',
            virtual_ip='192.168.50.12',virtual_mac='02:00:00:00:00:12')
    row=next(x for x in r.inventory() if x['id']=='virtual-door-22')
    assert row['virtual_ip']=='192.168.50.12'
    assert row['virtual_mac']=='02:00:00:00:00:12'
    with pytest.raises(ValueError):
        r.apply('register','virtual-door-23',name='Second door',kind='Sensor',virtual_ip='192.168.50.12')


def test_error_on_mislabel_before_training(tmp_path):
    csv=training_csv(tmp_path)
    with pytest.raises(ValueError,match='not present'):
        train.fit_csv(csv,algorithm='Random Forest',label='Attack_label',normal='unknown-normal',
                      features=['tcp.srcport','mqtt.len'],max_rows=300,folds=3,root=tmp_path/'failed')


def test_virtual_device_heartbeat_and_stop(tmp_path):
    from quantumsafe.virtual_devices import VirtualDeviceRunner
    g=gateway(tmp_path)
    runner=VirtualDeviceRunner()
    g.start(port=0)
    try:
        assert runner.start(g,'virtual-sensor-01',interval=2)
        for _ in range(20):
            if any(e.get('device')=='virtual-sensor-01' and e.get('decision')=='ALLOW'
                   and e.get('reading') is not None for e in g.events):break
            time.sleep(.05)
        assert any(e.get('device')=='virtual-sensor-01' and e.get('decision')=='ALLOW'
                   and e.get('reading') is not None for e in g.events)
        runner.stop('virtual-sensor-01')
        assert not runner.running()
    finally:
        runner.stop('virtual-sensor-01');g.stop()
