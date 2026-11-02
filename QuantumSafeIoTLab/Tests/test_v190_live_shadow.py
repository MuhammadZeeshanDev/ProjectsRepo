import time
from quantumsafe.live_ml import LiveShadowWorker


class FakeRouter:
    calls=[]
    def process(self,event):
        self.calls.append(event)
        return {'matches':[{'threat':'test'}],'incompatible_models':[]}


def test_real_observation_only_and_shadow_mode():
    FakeRouter.calls=[]
    worker=LiveShadowWorker(router_factory=FakeRouter,
                            route_provider=lambda:[{'model_id':1,'threat':'test'}])
    assert not worker.submit({'decision':'BLOCK','reading':3})
    assert not worker.submit({'decision':'ALLOW','reading':None})
    assert worker.submit({'decision':'ALLOW','reading':23,'device':'cam-01','source_ip':'127.0.0.1','request_type':'telemetry','identity_verified':True})
    worker.queue.join();worker.stop()
    state=worker.snapshot()
    assert state['processed']==1 and state['matches']==1
    assert FakeRouter.calls[0]['value']==23
    assert 'tcp.dstport' not in FakeRouter.calls[0]
    assert state['mode']=='shadow_only'


def test_missing_routes_never_create_fake_predictions():
    worker=LiveShadowWorker(router_factory=lambda:(_ for _ in ()).throw(AssertionError('should not load model')),
                            route_provider=lambda:[])
    worker.submit({'decision':'ALLOW','reading':5})
    worker.queue.join();worker.stop()
    assert worker.snapshot()['processed']==0
    assert 'No eligible' in worker.snapshot()['last_result']
