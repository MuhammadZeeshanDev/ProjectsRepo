"""Local sensor demo with distinct buttons for normal and tamper tests."""
import streamlit as st
from .. import crypto_engine, sensor_demo, experiments


def show(actor):
    st.title('🔒 Local Secure IoT Demo')
    st.caption('One computer: Python virtual sensor → Python virtual gateway.')
    algorithm = st.selectbox('ML-KEM algorithm', list(crypto_engine.ALGORITHMS))
    reading = st.number_input('Temperature (°C)', min_value=-50.0,
                              max_value=150.0, value=27.5, step=0.5)
    a, b = st.columns(2)
    normal = a.button('✅ Send Encrypted Reading', type='primary')
    tamper = b.button('🔴 Test Modified Ciphertext')
    if normal or tamper:
        try:
            result = sensor_demo.send_reading(algorithm, reading, tamper=tamper)
            experiments.save_demo(int(actor['UserId']), result)
        except Exception as exc:
            st.error(f'Test failed: {exc}')
            return
        st.success('PASS ✅ — ' + result['outcome'])
        if not tamper:
            st.metric('Gateway decrypted', result['message'])
        st.caption('Outcome saved in dbo.SecureDemoTests. Secret keys and readings are not saved.')
    st.warning('Local demo assumes a trusted gateway key. For authenticated key '
               'exchange and an actual second device, use 🌐 LAN Lab.')
