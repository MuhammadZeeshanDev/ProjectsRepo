import pytest
from quantumsafe.virtual_gateway_sim import SCENARIOS, evaluate

@pytest.mark.parametrize('scenario,decision', [
    ('Normal CCTV telemetry', 'ALLOW'),
    ('Unauthorized camera access', 'BLOCK'),
    ('Repeated message (replay)', 'BLOCK'),
    ('Modified message (tamper)', 'BLOCK'),
    ('Excessive request rate', 'BLOCK'),
])
def test_simulated_policy(scenario, decision):
    event = evaluate(scenario)
    assert event['decision'] == decision
    assert event['source'] == 'SIMULATED'

def test_unknown_scenario():
    with pytest.raises(ValueError):
        evaluate('not a scenario')
