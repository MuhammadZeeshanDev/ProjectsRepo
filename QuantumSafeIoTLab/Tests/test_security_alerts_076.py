from quantumsafe.security_alerts import alarm_eligible, next_alarm_event, event_identity

def ev(i, decision='ALLOW', source='LOCAL_HTTP'):
    return {'event_id':str(i), 'decision':decision, 'source':source, 'device':'virtual-cctv-01'}

def test_ten_normal_events_zero_alarms():
    seen=[]
    for i in range(10):
        event, seen = next_alarm_event([ev(i)], seen)
        assert event is None

def test_one_block_exactly_once():
    events=[ev('attack','BLOCK')]
    found, seen=next_alarm_event(events, [])
    assert found == events[0]
    for _ in range(10):
        found, seen=next_alarm_event(events, seen)
        assert found is None

def test_new_allow_does_not_retrigger_old_block():
    events=[ev('old','BLOCK')]
    _,seen=next_alarm_event(events, [])
    found,seen=next_alarm_event([ev('new'),*events], seen)
    assert found is None

def test_review_unknown_and_untrusted_source_never_alarm():
    for decision,source in [('REVIEW','MANUAL_CONTENT_RULES'),('UNKNOWN','MANUAL_CONTENT_RULES'),('BLOCK','UNVERIFIED')]:
        assert not alarm_eligible(ev(1,decision,source))

def test_two_blocks_select_newest():
    found,seen=next_alarm_event([ev('new','BLOCK'),ev('older','BLOCK')],[])
    assert event_identity(found)=='new'
    assert next_alarm_event([ev('new','BLOCK'),ev('older','BLOCK')],seen)[0] is None
