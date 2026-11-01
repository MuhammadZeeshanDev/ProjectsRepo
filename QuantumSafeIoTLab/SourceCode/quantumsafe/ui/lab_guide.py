"""Beginner-friendly explanations, role permissions and reproducible lab exercises."""
import streamlit as st
from quantumsafe.version import APP_VERSION


def show(actor):
    st.title(f'🧭 QuantumSafe Lab Guide · v{APP_VERSION}')
    st.info('This is an educational, LOCAL virtual lab. It does not monitor your home router or physical IoT hardware.')
    st.header('1 · What are we building?')
    st.write('A virtual IoT security lab: send controlled device requests, observe security decisions, save events to SQL Server, and analyze compatible Edge-IIoTset network records with a saved Random Forest model.')
    st.header('2 · Two different gateways')
    st.write('**Virtual HTTP gateway:** a local test server on 127.0.0.1. It checks device tokens, HMAC signatures, repeated nonces and request rates. **Secure LAN demo:** a separate ML-KEM handshake + encrypted sensor message demonstration. Neither is a full network router.')
    st.header('3 · Why ML-KEM 512 / 768 / 1024?')
    st.write('ML-KEM = Module-Lattice-Based Key-Encapsulation Mechanism. It lets two sides establish a shared secret over an untrusted connection. 512, 768 and 1024 are parameter-set names, **not** key lengths in bits. They target NIST security categories 1, 3 and 5 respectively. Larger sets generally use more bandwidth and computation.')
    st.write('ML-KEM is **cryptography**, not machine learning. The Edge-IIoTset Random Forest is the machine-learning attack classifier. They solve different problems.')
    st.header('4 · What does the 32-character field mean?')
    st.warning('Do not confuse **32 characters** with **32 bytes** or **256 bits**. A 32-character password, a 32-byte random secret, and a 32-byte AES key are different things. Check the label in the specific test screen; do not assume all 32-character inputs are cryptographic keys.')
    st.header('5 · Who can do what?')
    st.table({'Role':['Admin','Researcher','Viewer'], 'Can run lab':['Yes','Yes','No'], 'Can view results':['Yes','Yes','Yes'], 'Can create/disable accounts':['Yes','No','No']})
    st.success('Public signup is disabled. Only an existing Admin creates new accounts and assigns their role. The first Admin is created during initial local setup.')
    st.header('6 · Five-minute team demonstration')
    st.markdown("""1. Sign in as **Researcher**; open **Virtual Gateway** and start local gateway.
2. Send **CCTV** (expected ALLOW), then **Unauthorized access** (expected BLOCK).
3. Try **Tampered message**, **Replay attack**, and **Rate limit**. Watch live events and SQL history.
4. Open **ML Lab**, upload a compatible Edge-IIoTset CSV, run the saved RF model and inspect the Normal/Attack totals.
5. Show **Secure Demo / LAN Lab** for ML-KEM and explain that encrypted transport is separate from attack classification.
6. Sign in as **Admin** to show user management. Viewer should not see lab run controls.""")
    st.header('7 · How to obtain network data')
    st.write('The virtual gateway creates its own local HTTP test events; no external network is required. The RF model needs the ten Edge-IIoTset TCP/MQTT feature columns. Real packet capture requires a separate consent-based capture/feature-extraction pipeline; the current HTTP telemetry events do not contain those fields.')
    st.warning('Live gateway → Random Forest classification is **not implemented** yet: mapping HTTP telemetry into TCP/MQTT features would create misleading predictions. The ML model remains offline CSV inference until a verified compatible capture adapter is available.')
