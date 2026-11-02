"""v1.6 major lifecycle: real trained checkpoint, separate folds, hash guard,
independent CSV evaluation, correct normal/attack FPR, persistent catalog."""
import io
import numpy as np
import pandas as pd
import pytest
from quantumsafe import local_training as train
from quantumsafe import model_lifecycle as ml

@pytest.fixture
def store(tmp_path,monkeypatch):
    monkeypatch.setattr(ml,'ROOT',tmp_path/'ML_Artifacts')
    monkeypatch.setattr(ml,'DB',tmp_path/'ML_Artifacts'/'validated_models.sqlite3')
    return tmp_path

def train_sample(algo='Random Forest',split=.3, folds=3):
    # Make both labels present and make a meaningful class separation.
    rng=np.random.default_rng(9)
    n=180
    y=np.where(np.arange(n)%2==0,'normal','attack')
    data=pd.DataFrame({'tcp.len':rng.normal(150,20,n)+(np.arange(n)%2)*200,
                       'tcp.flags':np.arange(n)%3,
                       'mqtt.protoname':np.where(np.arange(n)%4==0,'MQTT','Other'),
                       'Attack_type':y})
    raw=data.to_csv(index=False).encode()
    result=train.run_experiment(raw,'Attack_type',['tcp.len','tcp.flags','mqtt.protoname'],algo,split,folds)
    return data,result

def test_training_real_fpr_normal_class_is_index_one():
    data,result=train_sample()
    assert result['classes']==['attack','normal']
    assert result['heldout']['normal_label']=='normal'
    assert result['heldout']['attack_label']=='attack'
    assert 0<=result['heldout']['false_positive_rate']<=1
    assert len(result['folds'])==3

def test_store_reload_evaluate_and_hash_guard(store):
    data,result=train_sample()
    result['target_mode']='original_multiclass'
    model_id=ml.save_trained(result,source_name='source.csv',target='Attack_type',run_id=7)
    assert ml.inspect_model(model_id)['state']=='stored'
    csv=store/'validation.csv';data.iloc[:45].to_csv(csv,index=False)
    out=ml.evaluate_csv(model_id,str(csv),chunk_size=13)
    assert out['rows']==45 and out['labeled_rows']==45
    assert sum(out['prediction_counts'].values())==45
    assert out['metrics']['macro_f1'] is not None
    assert len(ml.list_models())==1
    assert ml.mark_candidate(model_id,'Independent review',approved=True)=='reviewed_candidate'
    assert ml.inspect_model(model_id)['state']=='reviewed_candidate'
    row=ml._one(model_id)
    path=ml.ROOT/'trained_checkpoints'/row['file_name']
    with path.open('ab') as f:f.write(b'CORRUPTION')
    with pytest.raises(ValueError,match='checksum'):
        ml.evaluate_csv(model_id,str(csv))

def test_retire_disables_offline_evaluation(store):
    data,result=train_sample()
    mid=ml.save_trained(result,source_name='sample.csv',target='Attack_type')
    ml.retire_model(mid,'test')
    csv=store/'data.csv';data.to_csv(csv,index=False)
    with pytest.raises(ValueError,match='Retired'):
        ml.evaluate_csv(mid,str(csv))

@pytest.mark.parametrize('algo',train.algorithms())
def test_all_installed_algorithms_with_individual_folds(store,algo):
    sample,res=train_sample(algo,.2,3)
    assert res['algorithm']==algo
    assert res['split']=='80/20'
    assert [f['fold'] for f in res['folds']]==[1,2,3]
    mid=ml.save_trained(res,source_name=f'{algo}.csv',target='Attack_type')
    assert ml.inspect_model(mid)['algorithm']==algo
    path=store/'external.csv';sample.iloc[:23].to_csv(path,index=False)
    evaluation=ml.evaluate_csv(mid,path,chunk_size=7)
    assert evaluation['rows']==23 and evaluation['labeled_rows']==23
    assert ml.recent_evaluations()[0]['model_id']==mid
