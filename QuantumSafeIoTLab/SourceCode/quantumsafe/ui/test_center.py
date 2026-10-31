"""Buttons that allow non-coders to run each implemented application check."""
from pathlib import Path
import os
import subprocess
import sys
import streamlit as st
from .. import crypto_engine, sensor_demo, db, security_events
from ..permissions import may_manage_users


def show(actor):
    st.title('🧪 Test Center')
    st.caption('Run one test at a time without typing terminal commands.')
    st.subheader('1 — SQL Server and database')
    if st.button('🔌 Test SQL Server Connection'):
        st.success('SQL Server reachable ✅') if db.database_ready() else st.error('Not connected ❌')
    if st.button('🗄️ Check Database Tables'):
        try:
            names = [r['name'] for r in db.rows(
                'SELECT name FROM sys.tables WHERE name IN '
                "('Users','Experiments','Measurements','SecureDemoTests','AuditLogs','SecurityEvents')")]
            for name in ('Users', 'Experiments', 'Measurements', 'SecureDemoTests',
                         'AuditLogs', 'SecurityEvents'):
                st.write(('✅' if name in names else '❌') + ' ' + name)
            if 'SecurityEvents' not in names:
                st.info('Run Database/02_upgrade_v02.sql in SSMS to enable LAN audit events.')
        except Exception as exc:
            st.error(f'Database check failed: {exc}')
    st.subheader('2 — ML-KEM key agreement')
    for algorithm in crypto_engine.ALGORITHMS:
        if st.button('🔑 Test ' + algorithm):
            _kem_test(algorithm)
    if st.button('🧪 Test ALL 3 ML-KEM Algorithms'):
        for algorithm in crypto_engine.ALGORITHMS:
            _kem_test(algorithm)
    st.subheader('3 — Virtual secure sensor (same PC)')
    algorithm = st.selectbox('Local demo algorithm', list(crypto_engine.ALGORITHMS),
                             key='test_center_algorithm')
    first, second = st.columns(2)
    if first.button('✅ Test Normal Encrypted Message'):
        _demo_test(algorithm, False)
    if second.button('🔴 Test Tampered Message'):
        _demo_test(algorithm, True)
    st.subheader('4 — All code tests (pytest)')
    if not may_manage_users(actor['RoleName']):
        st.info('Only Admin may run the local code test suite. Others can use above checks.')
        return
    st.caption('Runs the bundled Tests/ directory with a fixed safe command; output stays on this screen.')
    if st.button('▶️ Run Automated Tests Now', type='primary'):
        project = Path(__file__).resolve().parents[3]
        try:
            proc = subprocess.run(
                [sys.executable, '-m', 'pytest', '-q', str(project / 'Tests')],
                cwd=project, capture_output=True, text=True, timeout=120,
                env={**os.environ, 'QUANTUMSAFE_TEST_DB': '1'}
            )
            st.code((proc.stdout + '\n' + proc.stderr)[-5500:], language='text')
            if proc.returncode == 0:
                st.success('Automated tests passed ✅ (see any skipped tests above).')
            else:
                st.error('Some tests failed. Read output before continuing.')
        except subprocess.TimeoutExpired:
            st.error('Tests timed out after 120 seconds.')
        except OSError as exc:
            st.error(f'Could not launch tests: {exc}')
    st.info('For two-computer checks open 🌐 LAN Lab → Send / attack tests. '
            'The peer console has separate buttons for normal, tamper, replay, '
            'unauthorized sender and key-substitution tests.')


def _kem_test(algorithm):
    try:
        result = crypto_engine.self_test(algorithm)
        if result['passed']:
            st.success(f"{algorithm}: PASS ✅ · {result['sizes']}")
        else:
            st.error(f'{algorithm}: FAIL ❌')
    except Exception as exc:
        st.error(f'{algorithm}: {exc}')


def _demo_test(algorithm, tamper):
    try:
        answer = sensor_demo.send_reading(algorithm, 27.5, tamper=tamper)
        if answer['passed']:
            st.success(answer['outcome'] + ' — PASS ✅')
        else:
            st.error('Test failed ❌')
    except Exception as exc:
        st.error(f'Test exception: {exc}')
