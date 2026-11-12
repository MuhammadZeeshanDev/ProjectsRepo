"""Admin-only demonstration of real ML-KEM-based encryption between virtual endpoints."""
import streamlit as st
from .. import crypto_engine
from ..ml_engine import incidents


def show(actor, gw):
    if actor.get('RoleName') != 'Admin':
        st.error('Administrator only')
        return
    with st.expander('🔐 ML-KEM · Encrypted Device-to-Device Gateway', expanded=True):
        st.markdown('**Real cryptography, virtual endpoints.** Each simulated enrolled device has an in-memory ML-KEM-768 key pair. '
                    'The source encapsulates a fresh session secret for the recipient; HKDF derives an AES-256-GCM key. '
                    'The gateway relays **ciphertext**, and the receiving virtual device authenticates and decrypts it.')
        st.caption('No plaintext or secret/private keys are stored in SQL. This is an in-process demonstration, NOT physical IoT network encryption, '
                   'router traffic capture, or a substitute for separately authenticated provisioning on real hardware.')
        allowed=[r for r in gw.registry.inventory() if r['status']=='active' and not gw.ips.active(r['id'])]
        info={r['id']:r for r in allowed}
        a,b,c=st.columns(3)
        a.metric('KEM', 'ML-KEM-768')
        b.metric('Payload encryption', 'AES-256-GCM')
        c.metric('Active endpoints', len(allowed))
        if st.button('🔬 Test actual ML-KEM cryptographic library',key='mesh_crypto_selftest'):
            try:
                result=crypto_engine.self_test('ML-KEM-768')
                st.success('PASS: independent encapsulation / decapsulation shared-secret agreement')
                st.json(result)
            except Exception as exc:
                st.error(f'ML-KEM test failed: {type(exc).__name__}: {exc}')
                st.info('Install the project requirements (pqcrypto==1.0.0). Do NOT substitute a simulated cryptographic result.')
        if len(allowed)<2:
            st.warning('Install or enable at least two virtual devices to demonstrate encrypted communication.')
            return
        name=lambda did: f"{info[did]['name']} · {did} · {info[did].get('virtual_ip') or 'virtual address unset'}"
        src=st.selectbox('Source virtual device',list(info),format_func=name,key='qs_mesh_src')
        targets=[x for x in info if x!=src]
        dst=st.selectbox('Destination virtual device',targets,format_func=name,key='qs_mesh_dst')
        content=st.text_input('Virtual sensor message (display only to Administrator)',
                              value='Temperature=24.5 C; status=normal',max_chars=250,key='qs_mesh_message')
        scenario=st.radio('Security test',['Normal encrypted delivery','Tamper with AES-GCM ciphertext','Replay an accepted ciphertext'],
                          horizontal=True,key='qs_mesh_test')
        action={'Normal encrypted delivery':'normal','Tamper with AES-GCM ciphertext':'tamper',
                'Replay an accepted ciphertext':'replay'}[scenario]
        if st.button('🔐 Establish ML-KEM session → Send encrypted message',type='primary',
                     key='qs_mesh_send',disabled=not bool(gw.server)):
            try:
                result=gw.secure_device_message(src,dst,content,scenario=action)
                st.session_state['qs_mesh_last_result']=result
                if result['decision']=='ALLOW':st.success('✅ ALLOW: Virtual destination verified and decrypted the original message.')
                else:st.error('🚫 BLOCK: '+result['reason'])
            except Exception as exc:
                st.error(f'Encrypted message failed: {type(exc).__name__}: {exc}')
        if not gw.server:
            st.info('Start the virtual gateway first to enable this communication test.')
        result=st.session_state.get('qs_mesh_last_result')
        if result:
            st.markdown('**Observed cryptographic operation**')
            st.code(f"{result['sender']} [virtual sender]\n"
                    f"   │  recipient ML-KEM public key · fingerprint {result.get('recipient_public_key_fingerprint','n/a')}\n"
                    f"   ├── ML-KEM-768 encapsulation: {result.get('kem_ciphertext_bytes',0)} encrypted-key bytes\n"
                    f"   └── HKDF-SHA256 → AES-256-GCM ciphertext: {result.get('ciphertext_bytes',0)} bytes\n"
                    f"            ↓ Virtual gateway: ciphertext-only relay\n"
                    f"{result['receiver']} [virtual receiver]\n"
                    f"   └── Decapsulation + authenticated decrypt: {'SUCCESS' if result.get('receiver_opened') else 'REJECTED'}")
            st.caption('Ciphertext SHA-256: '+result.get('ciphertext_sha256','n/a'))
            if result.get('receiver_opened'):
                st.success('Destination plaintext (admin demonstration only): '+str(result.get('delivered_text')))
            else:
                st.info('Plaintext withheld: the receiver rejected this payload. No secret was written to SQL.')
            st.caption('SQL event: queued locally first. Verify actual SQL Server 2022 persistence in SQL Diagnostics below. Event: '+str(result.get('event_id','')))
        with st.expander('🧠 SWI-Prolog security incident reasoning',expanded=False):
            if st.button('Evaluate recorded gateway threats using Prolog',key='qs_prolog_incidents'):
                try:
                    report=incidents.audit(list(gw.events))
                    st.write('Active reasoning engine:',report['engine'])
                    if report['devices']:st.json(report['devices'])
                    else:st.info('No blocked gateway incidents to evaluate yet.')
                except Exception as exc:st.error(f'Prolog incident analysis failed: {type(exc).__name__}: {exc}')
            st.caption('Prolog recommends investigation/key-rotation review; it does not directly disable physical devices.')
