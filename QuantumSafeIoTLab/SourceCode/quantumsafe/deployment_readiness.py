"""Explicit separation between offline trained data and live gateway features."""
import streamlit as st
def show():
    st.subheader('Live ML deployment — readiness checks')
    st.error('Not connected: the virtual gateway emits application-layer HTTP events; trained Edge-IIoTset models require matching TCP/MQTT features and preprocessing. Running them on invented feature values would produce invalid detections.')
    checks=[('Captured live packet source','MISSING — gateway HTTP event stream is not TCP/MQTT capture'),('Schema and feature order','REQUIRED — match each original model independently'),('Trusted checkpoint validation','REQUIRED — verify origin, hashes, safe loading and library versions'),('Holdout and drift checks','REQUIRED — before production decision'),('Administrator promotion / rollback','REQUIRED — no auto-deploy'),('Model decision policy','REQUIRED — explain labels, thresholds and false positives') ]
    for title,status in checks:st.write('**'+title+'** — '+status)
    st.info('Next development: real feature collector → per-model adapters → isolated evaluator → comparison dashboard → Admin-controlled deployment. The existing rule gateway continues blocking unauthorized requests independently of ML.')
