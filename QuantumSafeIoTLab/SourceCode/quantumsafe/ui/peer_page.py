"""Shared GUI for Computer B (peer console) and main application sending tab."""
import streamlit as st
from .. import crypto_engine, lan_client

SCENARIOS = [
    ('✅ Normal encrypted reading', 'normal'),
    ('🔴 Tampered ciphertext (must reject)', 'tamper'),
    ('🔁 Replay same packet (must reject second)', 'replay'),
    ('🚫 Unauthorized sender (must reject)', 'unauthorized'),
    ('🛡️ Substituted public key (must detect)', 'key_swap'),
]


def show(inside_main_app=False):
    if not inside_main_app:
        st.title('📡 QuantumSafe Peer Console — Computer B')
        st.info('Runs on this computer. No local SQL Server or admin account needed.')
    st.subheader('Computer B — Sender / security tests')
    st.caption('Use Computer A private IPv4, same port and the exact shared lab secret.')
    host = st.text_input('Gateway IPv4 / computer name', value='127.0.0.1',
                         key='peer_host', help='127.0.0.1 only works on the SAME computer.')
    port = st.number_input('Gateway port', 1024, 65535, 8765, key='peer_port')
    secret = st.text_input('Shared secret from Gateway screen', type='password',
                           key='peer_secret')
    algorithm = st.selectbox('ML-KEM algorithm', list(crypto_engine.ALGORITHMS),
                             key='peer_alg')
    temperature = st.number_input('Virtual temperature (°C)', -50.0, 150.0, 27.5,
                                  step=0.5, key='peer_temp')
    if st.button('🔌 Check Gateway Connection', key='peer_check'):
        try:
            good = lan_client.check_gateway(host.strip(), int(port))
            st.success('Gateway reachable ✅') if good else st.error('Wrong service or protocol.')
        except (ValueError, lan_client.PeerError) as exc:
            st.error(str(exc))
    st.markdown('**One-click security test buttons**')
    for label, name in SCENARIOS:
        if st.button(label, key='case_' + name):
            _run_case(host, int(port), secret, algorithm, float(temperature), name)
    if st.button('🧪 Run ALL 5 Security Tests', type='primary', key='all_peer'):
        if not secret:
            st.error('Enter the shared secret first.')
        else:
            results = []
            with st.spinner('Running tests using real network traffic...'):
                for _, name in SCENARIOS:
                    try:
                        results.append(lan_client.send_case(
                            host.strip(), int(port), secret, algorithm, float(temperature), name))
                    except Exception as exc:
                        results.append({'scenario': name, 'passed': False,
                                        'details': str(exc), 'http_status': None})
            st.session_state['peer_results'] = results
    if st.button('🧪 Run ALL 15 Tests — 3 Algorithms × 5 Scenarios', key='all_alg_peer'):
        if not secret:
            st.error('Enter the shared secret first.')
        else:
            results = []
            with st.spinner('Testing every algorithm and security scenario...'):
                for alg in crypto_engine.ALGORITHMS:
                    for _, name in SCENARIOS:
                        try:
                            result = lan_client.send_case(host.strip(), int(port), secret, alg,
                                                          float(temperature), name)
                        except Exception as exc:
                            result = {'scenario': name, 'passed': False,
                                      'details': str(exc), 'http_status': None}
                        results.append({'algorithm': alg, **result})
            st.session_state['peer_results'] = results
    if 'peer_results' in st.session_state:
        import pandas as pd
        df = pd.DataFrame(st.session_state['peer_results'])
        st.dataframe(df, hide_index=True, width='stretch')
        all_pass = all(item['passed'] for item in st.session_state['peer_results'])
        st.success('All selected security checks passed.') if all_pass else st.warning('Some checks failed; inspect the results.')
        st.download_button('⬇️ Export Test Results CSV', df.to_csv(index=False).encode('utf-8'),
                           'quantumsafe_lan_test_results.csv', 'text/csv')
    st.caption('Tampering, unauthorized requests and replay are deliberately rejected. '
               'These are security controls, NOT intrusion/unknown-attack detection.')


def _run_case(host, port, secret, algorithm, temperature, scenario):
    try:
        result = lan_client.send_case(host.strip(), port, secret, algorithm,
                                      temperature, scenario)
        st.session_state['peer_results'] = [result]
    except Exception as exc:
        st.session_state['peer_results'] = [
            {'scenario': scenario, 'passed': False, 'details': str(exc), 'http_status': None}]
