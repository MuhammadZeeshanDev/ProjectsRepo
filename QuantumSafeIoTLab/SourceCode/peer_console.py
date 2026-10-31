"""Computer B: launch a small standalone sender interface, no SQL dependency."""
import streamlit as st
from quantumsafe.ui import peer_page

st.set_page_config(page_title='QuantumSafe Peer Console', page_icon='📡', layout='wide')
peer_page.show()
