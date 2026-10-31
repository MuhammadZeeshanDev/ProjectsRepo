from quantumsafe.virtual_network import VirtualGateway

def test_local_http_gateway():
    g = VirtualGateway()
    try:
        assert g.start() > 0
        assert g.send('CCTV')['decision'] == 'ALLOW'
        assert g.send('Unauthorized access')['decision'] == 'BLOCK'
        assert g.send('Tampered message')['decision'] == 'BLOCK'
        assert g.send('Replay attack')['reason'] == 'Replay nonce detected'
    finally:
        g.stop()

def test_rate_limit():
    g=VirtualGateway()
    try:
        g.start()
        assert g.send('Rate limit')['decision']=='BLOCK'
    finally:
        g.stop()
