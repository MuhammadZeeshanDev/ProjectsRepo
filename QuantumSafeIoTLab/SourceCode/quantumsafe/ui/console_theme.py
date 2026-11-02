"""Shared visual tokens approximating the uploaded QuantumIoTLab dashboard.

Pure styling only: no changes to login, permissions, ML, or security services.
"""
import streamlit as st


def apply_theme():
    st.markdown('''<style>
:root {
  --qs-bg:#E9EEF5;--qs-surface:#FFFFFF;--qs-soft:#F2F5FA;
  --qs-border:#D3DCE8;--qs-ink:#0D1A2B;--qs-accent:#0A68CC;
}
@media (prefers-color-scheme:dark){:root{
  --qs-bg:#080F1A;--qs-surface:#0F1A2A;--qs-soft:#132035;
  --qs-border:#21304A;--qs-ink:#E4ECF7;--qs-accent:#52B5FF;
}}
/* Scoped to Streamlit host, never the isolated reference dashboard iframe. */
.stApp { background-color:var(--qs-bg); }
[data-testid="stSidebar"] {background:var(--qs-surface);border-right:1px solid var(--qs-border)}
[data-testid="stHeader"]{background:transparent}
section[data-testid="stMain"] .block-container {max-width:1450px;padding-top:1.1rem}
.stApp h1,.stApp h2,.stApp h3 {letter-spacing:.02em}
.stApp h1 {font-weight:750;line-height:1.2}
.stApp [data-testid="stMetric"]{background:var(--qs-surface);border:1px solid var(--qs-border);border-radius:10px;padding:12px 14px}
.stApp [data-testid="stMetricValue"]{font-variant-numeric:tabular-nums}
.stApp [data-testid="stExpander"]{border:1px solid var(--qs-border);border-radius:10px;background:var(--qs-surface)}
.stApp div.stButton > button, .stApp div.stDownloadButton > button {border-radius:8px;min-height:37px}
.stApp div[data-testid="stTabs"] [role="tablist"]{gap:4px}
.stApp div[data-testid="stTabs"] [role="tab"]{border-radius:8px 8px 0 0}
.stApp [data-testid="stDataFrame"]{border-radius:10px;overflow:hidden}
</style>''',unsafe_allow_html=True)
