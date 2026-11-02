import json
import sys
from pathlib import Path
import pytest

SRC=Path(__file__).resolve().parents[1]/'SourceCode'
sys.path.insert(0,str(SRC))
from quantumsafe.ml_engine import data,registry,selector,train,predict


def sample_csv(tmp_path):
    p=tmp_path/'iot_lab.csv'
    # Three classes, two different protocol features and a tempting leaky ID.
    header='tcp.dstport,mqtt.len,humidity,sensor_type,Device_ID,Attack_label\n'
    rows=[]
    for i in range(900):
        cls='Normal' if i%3==0 else ('Flood' if i%3==1 else 'Probe')
        port=1883 if cls=='Normal' else (23 if cls=='Flood' else 22)
        size=10+(i%7) if cls=='Normal' else 1000+(i%7)
        rows.append(f'{port},{size},{i%72},sensor,{i},{cls}\n')
    p.write_text(header+''.join(rows),encoding='utf-8')
    return p


def test_auto_features_avoids_leak_without_dropping_humidity(tmp_path):
    path=sample_csv(tmp_path)
    p,cols=data.inspect_headers(path)
    assert data.pick_label(cols)=='Attack_label'
    names=data.auto_features(cols,'Attack_label')
    assert 'humidity' in names
    assert 'Device_ID' not in names
    assert 'Attack_label' not in names


def test_stream_sample_deterministic_and_class_balance(tmp_path):
    path=sample_csv(tmp_path)
    a=data.scan_csv(path,max_rows=240)
    b=data.scan_csv(path,max_rows=240)
    assert a['sampled_rows']==240
    assert a['rows_seen']==900
    assert a['sample_class_counts']==b['sample_class_counts']
    assert a['frame'].equals(b['frame'])


def test_all_three_and_integrity(tmp_path):
    path=sample_csv(tmp_path);storage=tmp_path/'store'
    for algo in ('Random Forest','XGBoost','LightGBM'):
        result=train.fit_csv(path,algorithm=algo,root=storage,max_rows=300,folds=3,
                             normal='Normal')
        assert result['model_id']>0
        assert result['heldout']['macro_f1']>.60
        assert set(result['per_class'])=={'Normal','Probe','Flood'}
        bundle,meta=registry.load_model(result['model_id'],root=storage)
        assert 'humidity' in bundle['schema']['features']
        assert meta['metrics']['test_rows']>0
    saved=registry.models(storage)
    assert len(saved)==3
    choice=selector.rank(root=storage,swipl='')
    assert len(choice['routes'])>0
    assert choice['engine'].startswith('Python')
    assert set(choice['routes'])=={'Flood','Probe'}
    assert len(registry.active_routes(storage))==2
    out=predict.predict_csv(saved[0]['id'],path,root=storage,chunk_rows=100,
                            output=tmp_path/'output.csv')
    assert out['rows']==900
    assert Path(out['output']).is_file()
    assert out['stored_alert_examples']<=1500
    # Corrupt bytes: must reject before deserializing.
    target=storage/saved[0]['checkpoint'];target.write_bytes(b'TAMPER')
    with pytest.raises(ValueError,match='integrity mismatch'):
        registry.load_model(saved[0]['id'],storage)
    rerank=selector.rank(root=storage,swipl='')
    assert len(rerank['routes'])>0
    assert rerank['reason']


def test_clean_retrain_new_version(tmp_path):
    path=sample_csv(tmp_path);storage=tmp_path/'store'
    first=train.fit_csv(path,normal='Normal',root=storage,max_rows=240)
    second=train.retrain_model(first['model_id'],path,root=storage,max_rows=240)
    assert second['model_id']!=first['model_id']
    assert registry.get_model(second['model_id'],storage)['parent_id']==first['model_id']
    assert len(registry.models(storage))==2


def test_binary_train_and_retrain_keep_raw_normal(tmp_path):
    path=sample_csv(tmp_path);storage=tmp_path/'store'
    result=train.fit_csv(path,normal='Normal',binary=True,root=storage,max_rows=240)
    assert result['classes']==['attack','normal']
    follow=train.retrain_model(result['model_id'],path,root=storage,max_rows=240)
    assert follow['classes']==['attack','normal']


def test_reject_unlabeled_csv(tmp_path):
    p=tmp_path/'unlabeled.csv';p.write_text('tcp.len,mqtt.len\n10,2\n')
    with pytest.raises(ValueError,match='No recognized'):
        data.scan_csv(p,max_rows=200)


def test_schema_fails_closed_for_missing_features(tmp_path):
    path=sample_csv(tmp_path);storage=tmp_path/'store'
    result=train.fit_csv(path,normal='Normal',root=storage,max_rows=210)
    missing=tmp_path/'incomplete.csv';missing.write_text('tcp.dstport,Attack_label\n443,Normal\n')
    with pytest.raises(ValueError,match='input columns are missing'):
        predict.predict_csv(result['model_id'],missing,root=storage)
    with pytest.raises(ValueError,match='required real network fields'):
        predict.infer_event(result['model_id'],{'tcp.dstport':80},root=storage)


def test_not_all_iot_csv_can_be_labeled(tmp_path):
    p=tmp_path/'bad.csv';p.write_text('tcp.len,Label\n10,Normal\n11,Normal\n')
    with pytest.raises(ValueError,match='class'):
        data.scan_csv(p,max_rows=200)


def test_custom_plugin_registration():
    assert 'Random Forest' in train.estimator_names()
    assert 'XGBoost' in train.estimator_names()
    assert 'LightGBM' in train.estimator_names()


def test_readonly_frontend_has_no_training_controls():
    text=(SRC/'app.py').read_text()
    assert 'ml_lab.show' not in text
    assert 'security_monitor.show' in text


def test_autorouted_real_schema_and_no_automatic_blocking(tmp_path):
    from quantumsafe.ml_engine.shadow import ShadowRouter
    path=sample_csv(tmp_path);storage=tmp_path/'store'
    train.fit_csv(path,algorithm='Random Forest',normal='Normal',root=storage,max_rows=300)
    selector.rank(root=storage,swipl='')
    router=ShadowRouter(storage)
    verdict=router.process({'tcp.dstport':23,'mqtt.len':1030,'humidity':35,'sensor_type':'sensor'})
    assert verdict['mode']=='shadow_only'
    assert verdict['action']=='no_network_blocking_or_key_rotation'
    bad=router.process({'tcp.dstport':23})
    assert bad['models_evaluated']==0
    assert bad['incompatible_models']


def test_incident_rule_facts_and_levels():
    from quantumsafe.ml_engine.incidents import audit
    events=[{'device':'cam-one','decision':'BLOCK','reason':'Invalid HMAC signature'}]*3
    r=audit(events,swipl='')
    assert r['devices']['cam-one']['severity']=='critical'
    assert 'rotate_review' in r['devices']['cam-one']['recommendations']
    assert 'police' not in str(r).casefold()
    clean=audit([{'device':'cam-one','decision':'ALLOW','reason':'fine'}],swipl='')
    assert clean['devices']=={}
