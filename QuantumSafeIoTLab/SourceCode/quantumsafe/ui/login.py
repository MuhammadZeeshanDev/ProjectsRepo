"""Screen 1: simple username/password form."""
import time
import streamlit as st
from ..auth import sign_in


def show():
    st.title("🔐 QuantumSafe IoT Lab")
    st.caption("Local educational post-quantum cybersecurity application")
    st.subheader("Login")
    with st.form("login"):
        username = st.text_input("Username", max_chars=50)
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", width='stretch')
    if not submitted:
        st.info("Your administrator creates your account. Public signup is disabled.")
        return
    # Simple per-browser delay. The app is localhost only; not an internet auth service.
    last = st.session_state.get("last_failed_login", 0.0)
    if time.monotonic() - last < 2:
        st.warning("Please try again shortly.")
        return
    try:
        user = sign_in(username, password)
        if user:
            st.session_state["actor_id"] = int(user["UserId"])
            st.rerun()
        else:
            st.session_state["last_failed_login"] = time.monotonic()
            st.error("Incorrect username or password, or account disabled.")
    except Exception:
        st.error("Login could not reach the database. Please check SQL Server.")
