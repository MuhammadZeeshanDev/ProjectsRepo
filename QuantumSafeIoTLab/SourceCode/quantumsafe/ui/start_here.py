"""Beginner-friendly guide to the demonstration."""
import streamlit as st
from ..version import APP_VERSION

def show(actor):
    st.title(f'📘 Start Here · QuantumSafe IoT Lab v{APP_VERSION}')
    st.success('Purpose: learn how simulated IoT devices communicate, how suspicious requests are detected, and how monitoring data is saved.')
    st.subheader('What did we build, and why?')
    st.write('IoT means Internet of Things: cameras, sensors and other devices that communicate over networks. This app is a safe **software lab**, not a real camera or router monitoring tool.')
    st.write('We built it to practice network security, show what an allowed or blocked request looks like, save evidence in SQL Server, and explore a trained ML model on a compatible research dataset.')
    st.subheader('Five-minute team demonstration')
    for title,detail in [
        ('1 · Dashboard','Check database connectivity and see monitoring totals.'),
        ('2 · Virtual Gateway','Start the local gateway (127.0.0.1), send CCTV/Sensor normal traffic, then unauthorized/tampered/replay tests.'),
        ('3 · Monitoring','Observe ALLOW and BLOCK events. If SQL storage is initialized, events survive app restart.'),
        ('4 · ML Lab','Upload Edge-IIoTset CSV; the saved Random Forest labels records normal (0) or attack (1).'),
        ('5 · SQL history','Show stored gateway events and saved ML-run summaries. These are **different sources**, not the same live IDS.')]:
        st.markdown(f'**{title}** — {detail}')
    st.subheader('How the system works')
    st.code('Virtual device → Local HTTP gateway → Rule-based decision → SQL events → Dashboard\nEdge-IIoTset CSV → Saved preprocessing → Random Forest → Prediction summary → SQL history',language='text')
    st.subheader('Important words (easy definitions)')
    st.write('**Gateway:** a door that checks requests. **Database:** a register that remembers events. **Model:** a trained pattern detector. **Prediction:** the model’s guess for a row. **Attack alert:** a warning, not proof of a real attack.')
    st.warning('Gateway blocking is rule-based in this lab. CSV model predictions are offline; they do not automatically block live traffic. A 99%+ exploratory score is not proof of real-world detection quality.')
    st.subheader('Who did what?')
    st.write('Python runs the application; Streamlit creates the screens; SQL Server stores records; scikit-learn loads the already-trained Random Forest. See Documentation/TEAM_DEMO_GUIDE.md for speaking notes.')
