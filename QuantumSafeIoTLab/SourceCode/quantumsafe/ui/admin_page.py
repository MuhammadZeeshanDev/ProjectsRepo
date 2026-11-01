"""Screen 6: administrator adds users and enables/disables accounts."""
import streamlit as st
import pandas as pd
from .. import users
from ..permissions import ROLES


def show(actor):
    st.title("👥 Team Accounts")
    with st.form("new_user"):
        name = st.text_input("New username", max_chars=50)
        password = st.text_input("New password (12+ characters)", type="password")
        role = st.selectbox('Access level', ROLES, format_func=lambda r: {'Admin':'Administrator — settings, security tests and ML', 'Researcher':'Security Operator — monitoring and alerts', 'Viewer':'Observer — overview only'}[r])
        create = st.form_submit_button("Create account")
    if create:
        try:
            users.create_user(int(actor["UserId"]), name, password, role)
            st.success("Account created.")
        except Exception as exc:
            st.error(f"Could not create account: {exc}")
    try:
        all_users = users.list_users(int(actor["UserId"]))
    except Exception:
        st.error("User list could not be loaded.")
        return
    st.dataframe(pd.DataFrame(all_users), hide_index=True, width='stretch')
    if not all_users:
        return
    mapping = {f"{u['Username']} ({u['RoleName']})": u for u in all_users}
    selection = st.selectbox("Select user", list(mapping))
    chosen = mapping[selection]
    new_active = st.checkbox("Account enabled", value=bool(chosen["IsActive"]),
                             key=f"active_{chosen['UserId']}")
    if st.button("Save account status"):
        try:
            users.set_active(int(actor["UserId"]), int(chosen["UserId"]), new_active)
            st.success("Account status updated.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not update status: {exc}")
