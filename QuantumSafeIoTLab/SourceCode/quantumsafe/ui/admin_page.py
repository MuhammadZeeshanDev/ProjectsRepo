"""Professional two-role account management; legacy Viewer migration."""
import streamlit as st
import pandas as pd
from .. import users
from ..permissions import ROLES

LABELS={'Admin':'Administrator — app, ML, AI, accounts','Researcher':'Security Operator — monitoring and incidents'}

def show(actor):
    if actor.get('RoleName')!='Admin':
        st.error('Administrator access required.'); return
    st.title('👥 Team Accounts')
    st.caption('Two roles only. No public signup. Existing Observer accounts need Administrator reassignment.')
    with st.expander('➕ Create team account'):
        with st.form('new_user'):
            name=st.text_input('Username',max_chars=50)
            password=st.text_input('Password (12+ characters)',type='password')
            role=st.selectbox('Role',ROLES,format_func=lambda r: LABELS[r])
            create=st.form_submit_button('Create account')
        if create:
            try:users.create_user(int(actor['UserId']),name,password,role);st.success('Account created.');st.rerun()
            except Exception as exc:st.error('Could not create account: '+str(exc))
    try: all_users=users.list_users(int(actor['UserId']))
    except Exception:st.error('User list unavailable.');return
    if not all_users:st.info('No team accounts found.');return
    st.dataframe(pd.DataFrame(all_users),hide_index=True,use_container_width=True)
    mapping={f"{u['Username']} ({u['RoleName']})":u for u in all_users}
    selection=st.selectbox('Edit team member',list(mapping))
    chosen=mapping[selection]
    selected_role=st.selectbox('Access level',['Admin','Researcher'],index=0 if chosen['RoleName']=='Admin' else 1,format_func=lambda r: LABELS[r],key='edit_role')
    enabled=st.checkbox('Account enabled',value=bool(chosen['IsActive']),key=f"active_{chosen['UserId']}")
    if chosen['RoleName']=='Viewer':st.warning('Legacy Observer account: select Security Operator or Administrator and save. Until reassigned, sign-in is refused.')
    if st.button('💾 Save role and status',type='primary'):
        try:
            aid=int(actor['UserId']);uid=int(chosen['UserId'])
            # Set role before disabling; protections in each database operation.
            if selected_role!=chosen['RoleName']:users.set_role(aid,uid,selected_role)
            if enabled!=bool(chosen['IsActive']):users.set_active(aid,uid,enabled)
            st.success('Team member updated.');st.rerun()
        except Exception as exc:st.error('Could not update account: '+str(exc))
