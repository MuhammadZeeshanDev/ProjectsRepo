import pytest
from quantumsafe.message_policy import assess_content

def test_password_request_blocks():
    r=assess_content('Urgent bank verification: send your password')
    assert r['decision']=='BLOCK'
    assert r['source']=='MANUAL_CONTENT_RULES'

def test_safe_sample_allowed():
    assert assess_content('Temperature sensor reading: 23')['decision']=='ALLOW'

def test_unsafe_scheme_blocks():
    assert assess_content('javascript:alert(1)')['decision']=='BLOCK'

def test_empty_rejected():
    with pytest.raises(ValueError):assess_content('  ')

def test_long_rejected():
    with pytest.raises(ValueError):assess_content('x'*4001)
